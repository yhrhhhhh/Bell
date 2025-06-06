import json
import paho.mqtt.client as mqtt
from django.conf import settings
import logging
import uuid
import os
import threading
import time

from .models import Topic, Device

logger = logging.getLogger(__name__)


class MQTTClient:
    _instance = None
    _is_connected = False

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new MQTT client instance")
            cls._instance = super(MQTTClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 只在第一次初始化
        if not hasattr(self, 'client'):
            client_id = f'bell_admin_{uuid.uuid4().hex[:8]}'
            self.client = mqtt.Client(client_id=client_id)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect

            self.broker = settings.MQTT_BROKER
            self.port = settings.MQTT_PORT
            self.username = settings.MQTT_USERNAME
            self.password = settings.MQTT_PASSWORD

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._is_connected = True
            logger.info("Connected to MQTT Broker!")
            
            try:
                # 获取所有主题
                topic_receive_list = list(Topic.objects.values_list('subscribe_topic', flat=True))
                topic_receive_list = [topic.strip() for topic in topic_receive_list if topic and topic.strip()]
                
                if topic_receive_list:
                    subscribed_topics = getattr(self, '_subscribed_topics', set())
                    new_topics = set(topic_receive_list) - subscribed_topics
                    
                    if new_topics:
                        topic_all = [(topic, 0) for topic in new_topics]
                        self.client.subscribe(topic_all)
                        logger.info(f"Subscribed to topics: {new_topics}")
                        subscribed_topics.update(new_topics)
                        setattr(self, '_subscribed_topics', subscribed_topics)
                    
            except Exception as e:
                logger.error(f"Error subscribing to topics: {e}")
                self._is_connected = False
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised"
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            logger.error(f"Failed to connect: {error_msg}")
            self._is_connected = False

    def on_disconnect(self, client, userdata, rc):
        self._is_connected = False
        if rc != 0:
            logger.warning("Unexpected MQTT disconnection")

    def on_message(self, client, userdata, msg):
        """解析上报数据，新设备检验、创建"""
        try:
            message = json.loads(msg.payload.decode())
            topic = msg.topic
            
            cmd = message.get("cmd")
            if cmd == "status_read":
                uuid_current = message.get("uuid")
                if not uuid_current:
                    return
                    
                try:
                    uuid_object = Topic.objects.get(uuid=uuid_current)
                    # 更新网关在线状态
                    uuid_object.online_status = True
                    uuid_object.save()
                except Topic.DoesNotExist:
                    logger.error(f"UUID不存在: {uuid_current}")
                    return
                except Exception as e:
                    logger.error(f"查询Topic错误: {str(e)}")
                    return
                
                device_id_dict_list = message.get("body", {}).get("inUnitMessages")
                if not isinstance(device_id_dict_list, list):
                    return
                    
                for device_info in device_id_dict_list:
                    device_id = device_info.get("a")
                    if not device_id:
                        continue
                        
                    try:
                        device, created = Device.objects.get_or_create(
                            uuid=uuid_object,
                            device_id=device_id,
                            defaults={
                                "name": "未命名设备", 
                                "room_id": 0,
                                "online_status": True
                            }
                        )
                        if not created:
                            device.online_status = True
                            device.save()
                            
                        if created:
                            logger.info(f"新设备: device_id={device_id}")
                            
                        self.process_message(message, uuid_current)
                    except Exception as e:
                        logger.error(f"处理设备错误: {str(e)}")
                        
            elif cmd == "control_write":
                logger.info(f"控制命令响应: {message}")
            elif cmd == "online":
                uuid_current = message.get("uuid")
                if uuid_current:
                    try:
                        # 更新网关在线状态
                        uuid_object = Topic.objects.get(uuid=uuid_current)
                        uuid_object.online_status = True
                        uuid_object.save()
                        
                        # 更新该网关下所有设备的在线状态
                        Device.objects.filter(uuid=uuid_object).update(online_status=True)
                        
                        logger.info(f"设备上线: UUID={uuid_current}")
                    except Topic.DoesNotExist:
                        logger.error(f"UUID不存在: {uuid_current}")
                    except Exception as e:
                        logger.error(f"更新在线状态错误: {str(e)}")
            elif cmd == "offline":
                uuid_current = message.get("uuid")
                if uuid_current:
                    try:
                        # 更新网关离线状态
                        uuid_object = Topic.objects.get(uuid=uuid_current)
                        uuid_object.online_status = False
                        uuid_object.save()
                        
                        # 更新该网关下所有设备的离线状态
                        Device.objects.filter(uuid=uuid_object).update(online_status=False)
                        
                        logger.info(f"设备离线: UUID={uuid_current}")
                    except Topic.DoesNotExist:
                        logger.error(f"UUID不存在: {uuid_current}")
                    except Exception as e:
                        logger.error(f"更新离线状态错误: {str(e)}")

        except json.JSONDecodeError:
            logger.error("JSON解析错误")
        except Exception as e:
            logger.error(f"MQTT消息处理错误: {str(e)}")

    @staticmethod
    def process_message(data, uuid_current):
        """上传消息解析,更新设备的数据状态"""
        try:
            status_convert_dict = {"fa000001400001240240614000100308": {"status": {"1": "running", "0": "stopped", },
                                                                        "mode": {"1": "cooling", "2": "heating",
                                                                                 "3": "fan", "4": "dehumidify",
                                                                                 "0": "auto"}},
                                   "fa000001400001240240614000100317": {"status": {"1": "running", "0": "stopped", },
                                                                        "mode": {"1": "cooling", "2": "heating",
                                                                                 "3": "fan", "4": "dehumidify",
                                                                                 "0": "auto"}}
                                   }
            uuid_object = Topic.objects.get(uuid=uuid_current)
            device_status_info_list = data.get("body", {}).get("inUnitMessages")
            if isinstance(device_status_info_list, list) and device_status_info_list:
                for device_info in device_status_info_list:
                    device_id = device_info.get("a")
                    on_off = device_info.get("o")
                    set_tem = device_info.get("ts")
                    work_mode = device_info.get("w")
                    fan_speed = device_info.get("fs")
                    current_tem = device_info.get("rt")
                    on_off = status_convert_dict.get(uuid_current, {}).get("status", {}).get(str(on_off), {})
                    work_mode = status_convert_dict.get(uuid_current, {}).get("mode", {}).get(str(work_mode), {})
                    if on_off and work_mode:
                        Device.objects.filter(uuid=uuid_object, device_id=device_id).update(
                            current_temp=current_tem,
                            status=on_off,
                            mode=work_mode,
                            fan_speed=fan_speed,
                            set_temp=set_tem,
                            online_status=True
                        )
        except Exception as e:
            logger.error(f"处理消息错误: {e}")

    def start(self):
        """启动MQTT客户端"""
        if self._is_connected:
            return

        try:
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
            logger.info("MQTT客户端已启动")
        except Exception as e:
            logger.error(f"MQTT连接错误: {e}")
            self._is_connected = False

    def stop(self):
        """停止MQTT客户端"""
        if self._is_connected:
            self.client.loop_stop()
            self.client.disconnect()
            self._is_connected = False
            logger.info("MQTT客户端已停止")

    def publish(self, topic, payload, qos=1, retain=False, retry_count=3, retry_delay=1):
        """发布MQTT消息"""
        for attempt in range(retry_count):
            try:
                if not self._is_connected:
                    logger.warning("MQTT客户端未连接，尝试重连...")
                    self.start()
                    timeout = 5
                    start_time = time.time()
                    while not self._is_connected and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                    
                    if not self._is_connected:
                        raise Exception("重连超时")
                
                if isinstance(payload, (dict, list)):
                    payload = json.dumps(payload)
                
                result = self.client.publish(topic, payload, qos=qos, retain=retain)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    result.wait_for_publish(timeout=5.0)
                    return result
                else:
                    raise Exception(f"发布失败: {result.rc}")
                    
            except Exception as e:
                logger.error(f"发布消息失败: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    self._is_connected = False
                else:
                    raise Exception(f"发布消息失败: {str(e)}")
                    
        return None


# 全局MQTT客户端实例
mqtt_client = MQTTClient()
