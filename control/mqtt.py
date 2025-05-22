import paho.mqtt.client as mqtt
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # 从Django设置中获取MQTT配置
        self.broker = settings.MQTT_BROKER
        self.port = settings.MQTT_PORT
        self.username = settings.MQTT_USERNAME
        self.password = settings.MQTT_PASSWORD
        self.topic = settings.MQTT_TOPIC_RECEIVE

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            #TODO：处理自动上报的空调数据 更新数据库
            self.client.subscribe(self.topic)
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        # 处理不同反馈信息
        logger.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        # 在这里处理接收到的消息
        # 可以触发Django信号或调用其他处理函数

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
            raise

# 全局MQTT客户端实例
mqtt_client = MQTTClient()