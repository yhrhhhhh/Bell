import json
import logging

import paho.mqtt.client as mqtt
from django.conf import settings
from django.utils import timezone

from .models import Topic, Device

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.broker = settings.MQTT_BROKER
        self.port = settings.MQTT_PORT
        self.username = settings.MQTT_USERNAME
        self.password = settings.MQTT_PASSWORD

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            # 订阅所有存在的主题
            topic_receive_list = list(Topic.objects.values_list('subscribe_topic', flat=True))
            topic_all = [(i, 0) for i in topic_receive_list]
            self.client.subscribe(topic_all)
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        """解析上报数据"""
        try:
            message = json.loads(msg.payload.decode())
            # 暂时不日志记录所有收到消息
            topic = msg.topic
            # logger.info(f"Received `{message}` from `{topic}` topic")
            uuid_current = message.get("uuid")
            if not uuid_current:
                return

            uuid_object = Topic.objects.filter(uuid=uuid_current).first()
            if uuid_object is None:
                return
            cmd = message.get("cmd")
            if cmd == "status_read":
                # 所有设备状态上报信息
                self.process_message(message, uuid_object)
                # 判断是否有新设备
                self.create_device(message, uuid_object)
                logger.info(f"所有数据状态上报 `{message}` from topic：`{topic}` ")
            elif cmd == "status_report":
                # 状态改变数据上报
                self.process_message(message, uuid_object)
                logger.info(f"状态改变数据上报 `{message}` from topic：`{topic}` ")
            elif cmd == "online":
                # 在线状态消息上报，更新时间自动更新
                # logger.info(f"更新网管状态：{timezone.localtime(timezone.now())}")
                Topic.objects.filter(uuid=uuid_current).update(online_status=True,
                                                               updated_at=timezone.localtime(timezone.now()))

        except Exception as e:
            logger.error(f"MQTT process message error: {e}")

    @staticmethod
    def process_message(data, uuid_object):
        """上传消息解析,更新设备的数据状态"""
        try:
            device_status_info_list = data.get("body", {}).get("inUnitMessages")
            online_status_dict = {"LOST": False, "": True}  # 为空目前
            if isinstance(device_status_info_list, list) and device_status_info_list:
                for device_info in device_status_info_list:
                    device_id = device_info.get("a")
                    status = device_info.get("o")
                    set_temp = device_info.get("ts")
                    mode = device_info.get("w")
                    fan_speed = device_info.get("fs")
                    current_tem = device_info.get("rt")
                    online_status_str = device_info.get("acs")
                    online_status_code = online_status_dict.get(online_status_str)
                    MQTTClient.update_data(uuid_object=uuid_object, device_id=device_id, current_tem=current_tem,
                                           status=status, mode=mode, fan_speed=fan_speed, set_temp=set_temp,
                                           online_status=online_status_code)
        except Exception as e:
            logger.error(f"process_message function error: {e}")

    @staticmethod
    def update_data(uuid_object, device_id, current_tem=None, status=None, mode=None, fan_speed=None, set_temp=None,
                    online_status=None):
        try:
            status_convert_dict = {"fa000001400001240240614000100308": {"status": {"1": "running", "0": "stopped", },
                                                                        "mode": {"1": "cooling", "2": "heating",
                                                                                 "3": "fan", "4": "dehumidify",
                                                                                 "0": "auto"}},
                                   "fa000001400001240240614000100317": {"status": {"1": "running", "0": "stopped", },
                                                                        "mode": {"1": "cooling", "2": "heating",
                                                                                 "3": "fan", "4": "dehumidify",
                                                                                 "0": "auto"}},
                                   "fa000001400001240240615000100165": {"status": {"1": "running", "0": "stopped", },
                                                                        "mode": {"1": "cooling", "2": "heating",
                                                                                 "3": "fan", "4": "dehumidify",
                                                                                 "0": "auto"}},
                                   }
            status = status_convert_dict[f"{uuid_object.uuid}"]["status"][str(status)] if status else None
            mode = status_convert_dict[f"{uuid_object.uuid}"]["mode"][str(mode)] if mode else None
            update_fields = {k: v for k, v in {
                'current_temp': current_tem,
                'status': status,
                'mode': mode,
                'fan_speed': fan_speed,
                'set_temp': set_temp,
                'online_status': online_status,
                'last_updated': timezone.localtime(timezone.now())

            }.items() if v is not None}
            Device.objects.filter(uuid=uuid_object, device_id=device_id).update(**update_fields)
        except Exception as e:
            logger.error(f"update_data function error: {e}")

    @staticmethod
    def create_device(message, uuid_object):
        """创建设备"""
        try:
            device_id_dict_list = message.get("body", {}).get("inUnitMessages")
            if isinstance(device_id_dict_list, list) and device_id_dict_list:
                device_id_list = [i.get("a") for i in device_id_dict_list]
                # 判断这些设备是否都在数据库中 如果不存在的需要通过Device 模型创建
                for device_id in device_id_list:
                    if device_id:
                        device, created = Device.objects.get_or_create(
                            uuid=uuid_object,
                            device_id=device_id,
                            defaults={"name": "未命名设备",
                                      "room_id": 0}
                        )
                        if created:
                            logger.info(f"Created new device {device.id}")
        except Exception as e:
            logger.error(f"create device function error: {e}")

    def start(self):
        try:
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            self.client.connect(self.broker, self.port)
            self.client.loop_start()  # 使用loop_start而不是loop_forever
            logger.info("MQTT client started")
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")

    def publish(self, topic, payload, qos=1, retain=False):
        """
        发布MQTT消息
        :param topic: 主题
        :param payload: 消息内容
        :param qos: 服务质量等级
        :param retain: 是否保留消息
        """
        try:
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            logger.info(f"Published to {topic}: {payload}")
            return result
        except Exception as e:
            logger.error(f"Publish failed: {e}")


# 全局MQTT客户端实例
mqtt_client = MQTTClient()
