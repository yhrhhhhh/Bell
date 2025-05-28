import json

import paho.mqtt.client as mqtt
from django.conf import settings
import logging

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
        """解析上报数据，新设备检验、创建"""
        try:
            message = json.loads(msg.payload.decode())
            topic = msg.topic
            logger.info(f"Received `{message}` from `{topic}` topic")
            if message.get("cmd") == "status_read":
                uuid_current = message.get("uuid")
                uuid_object = Topic.objects.get(uuid=uuid_current)
                if uuid_object is None:
                    return
                self.process_message(message, uuid_current)
                device_id_dict_list = message.get("body", {}).get("inUnitMessages")
                if isinstance(device_id_dict_list, list) and device_id_dict_list:
                    device_id_list = [i.get("a") for i in device_id_dict_list]
                    # 判断这些设备是否都在数据库中 如果不存在的需要通过Device 模型创建
                    for device_id in device_id_list:
                        device, created = Device.objects.get_or_create(
                            uuid=uuid_object,
                            device_id=device_id,
                            defaults={"name": "未命名设备",
                                      "room_id": 0}
                        )
                        if created:
                            logger.info(f"Created new device {device.id}")
            elif message.get("cmd") == "control_write":
                # 下发成功的状态，暂时不管
                pass

        except Exception as e:
            logger.error(f"MQTT process message error: {e}")

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
