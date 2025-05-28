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
            logger.info(f"Creating new MQTT client instance in process {os.getpid()}, thread {threading.current_thread().name}")
            cls._instance = super(MQTTClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 只在第一次初始化
        if not hasattr(self, 'client'):
            client_id = f'bell_admin_{uuid.uuid4().hex[:8]}'
            logger.info(f"Initializing MQTT client with ID {client_id} in process {os.getpid()}")
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
            logger.info(f"Connected to MQTT Broker! Process: {os.getpid()}, Thread: {threading.current_thread().name}")
            
            try:
                # 获取所有主题
                topic_receive_list = list(Topic.objects.values_list('subscribe_topic', flat=True))
                # 清理主题字符串
                topic_receive_list = [topic.strip() for topic in topic_receive_list if topic and topic.strip()]
                
                if topic_receive_list:
                    # 检查是否已经订阅
                    subscribed_topics = getattr(self, '_subscribed_topics', set())
                    new_topics = set(topic_receive_list) - subscribed_topics
                    
                    if new_topics:
                        topic_all = [(topic, 0) for topic in new_topics]
                        self.client.subscribe(topic_all)
                        logger.info(f"Subscribed to new topics: {new_topics}")
                        # 更新已订阅主题集合
                        subscribed_topics.update(new_topics)
                        setattr(self, '_subscribed_topics', subscribed_topics)
                    else:
                        logger.info("All topics already subscribed")
                else:
                    logger.warning("No valid topics found to subscribe")
                    
            except Exception as e:
                logger.error(f"Error subscribing to topics: {e}")
                self._is_connected = False
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised",
                6: "Connection refused - not available",
                7: "Connection refused - protocol error"
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            logger.error(f"Failed to connect: {error_msg}")
            self._is_connected = False

    def on_disconnect(self, client, userdata, rc):
        self._is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection. Code: {rc}, Process: {os.getpid()}, Thread: {threading.current_thread().name}")
        else:
            logger.info(f"Disconnected from MQTT broker. Process: {os.getpid()}, Thread: {threading.current_thread().name}")

    def on_message(self, client, userdata, msg):
        """解析上报数据，新设备检验、创建"""
        try:
            message = json.loads(msg.payload.decode())
            topic = msg.topic
            logger.info(f"收到MQTT消息: topic={topic}, payload={message}")
            
            cmd = message.get("cmd")
            if cmd == "status_read":
                uuid_current = message.get("uuid")
                if not uuid_current:
                    logger.warning("收到的消息中没有UUID字段")
                    return
                    
                logger.info(f"正在查找UUID: {uuid_current}")
                try:
                    uuid_object = Topic.objects.get(uuid=uuid_current)
                except Topic.DoesNotExist:
                    logger.error(f"在数据库中找不到UUID: {uuid_current}")
                    # 可以在这里添加创建Topic的逻辑，如果需要的话
                    return
                except Exception as e:
                    logger.error(f"查询Topic时发生错误: {str(e)}")
                    return
                
                device_id_dict_list = message.get("body", {}).get("inUnitMessages")
                if not isinstance(device_id_dict_list, list):
                    logger.warning(f"消息体格式错误: {message.get('body')}")
                    return
                    
                logger.info(f"处理设备列表: {device_id_dict_list}")
                for device_info in device_id_dict_list:
                    device_id = device_info.get("a")
                    if not device_id:
                        logger.warning(f"设备信息中没有device_id: {device_info}")
                        continue
                        
                    try:
                        device, created = Device.objects.get_or_create(
                            uuid=uuid_object,
                            device_id=device_id,
                            defaults={"name": "未命名设备", "room_id": 0}
                        )
                        if created:
                            logger.info(f"创建了新设备: id={device.id}, device_id={device_id}")
                        else:
                            logger.info(f"找到已存在的设备: id={device.id}, device_id={device_id}")
                            
                        self.process_message(message, uuid_current)
                    except Exception as e:
                        logger.error(f"处理设备 {device_id} 时发生错误: {str(e)}")
                        
            elif cmd == "control_write":
                # 下发成功的状态，记录日志
                logger.info(f"收到控制命令响应: {message}")
            elif cmd == "online":
                # 处理设备上线消息
                uuid_current = message.get("uuid")
                if not uuid_current:
                    logger.warning("收到的online消息中没有UUID字段")
                    return
                    
                logger.info(f"设备上线: UUID={uuid_current}, 信号强度={message.get('body', {}).get('fg', 'unknown')}")
            else:
                logger.warning(f"未知的命令类型: {cmd}")

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}, payload: {msg.payload}")
        except Exception as e:
            logger.error(f"MQTT消息处理错误: {str(e)}")
            logger.exception("详细错误信息:")

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
                            set_temp=set_tem
                        )
        except Exception as e:
            logger.error(f"process message function error: {e}")
            return e

    def start(self):
        """启动MQTT客户端"""
        logger.info(f"Attempting to start MQTT client in process {os.getpid()}, thread {threading.current_thread().name}")
        
        if self._is_connected:
            logger.warning(f"MQTT client is already connected in process {os.getpid()}")
            return

        try:
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
            logger.info(f"MQTT client started in process {os.getpid()}")
        except Exception as e:
            logger.error(f"MQTT connection error in process {os.getpid()}: {e}")
            self._is_connected = False

    def stop(self):
        """停止MQTT客户端"""
        logger.info(f"Attempting to stop MQTT client in process {os.getpid()}")
        if self._is_connected:
            self.client.loop_stop()
            self.client.disconnect()
            self._is_connected = False
            logger.info(f"MQTT client stopped in process {os.getpid()}")

    def publish(self, topic, payload, qos=1, retain=False, retry_count=3, retry_delay=1):
        """
        发布MQTT消息
        :param topic: 主题
        :param payload: 消息内容
        :param qos: 服务质量等级
        :param retain: 是否保留消息
        :param retry_count: 重试次数
        :param retry_delay: 重试延迟（秒）
        """
        for attempt in range(retry_count):
            try:
                if not self._is_connected:
                    logger.warning(f"MQTT客户端未连接，尝试重连... (尝试 {attempt + 1}/{retry_count})")
                    self.start()
                    # 等待连接建立
                    timeout = 5  # 连接超时时间（秒）
                    start_time = time.time()
                    while not self._is_connected and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                    
                    if not self._is_connected:
                        raise Exception("重连超时")
                
                # 确保payload是有效的JSON字符串
                if isinstance(payload, (dict, list)):
                    payload = json.dumps(payload)
                
                # 发布消息
                result = self.client.publish(topic, payload, qos=qos, retain=retain)
                
                # 等待消息发送完成
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    result.wait_for_publish(timeout=5.0)  # 等待最多5秒
                    logger.info(f"成功发布消息到 {topic}: {payload}")
                    return result
                else:
                    raise Exception(f"发布失败，错误码: {result.rc}")
                    
            except Exception as e:
                logger.error(f"发布消息失败 (尝试 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt < retry_count - 1:  # 如果不是最后一次尝试
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    # 重置连接状态
                    self._is_connected = False
                else:
                    logger.error("发布消息最终失败")
                    raise Exception(f"发布消息失败: {str(e)}")
                    
        return None


# 全局MQTT客户端实例
mqtt_client = MQTTClient()
