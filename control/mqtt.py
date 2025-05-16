import json
import paho.mqtt.client as mqtt
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MQTTClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MQTTClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        
        # 设置 MQTT 服务器连接参数
        self.broker_host = getattr(settings, 'MQTT_BROKER_HOST', 'localhost')
        self.broker_port = getattr(settings, 'MQTT_BROKER_PORT', 1883)
        self.username = getattr(settings, 'MQTT_USERNAME', None)
        self.password = getattr(settings, 'MQTT_PASSWORD', None)
        
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
            
        self._initialized = True
    
    def connect(self):
        """连接到 MQTT 代理服务器"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {str(e)}")
    
    def disconnect(self):
        """断开与 MQTT 代理服务器的连接"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def on_connect(self, client, userdata, flags, rc):
        """连接回调函数"""
        if rc == 0:
            logger.info("Successfully connected to MQTT broker")
            # 订阅设备状态主题
            client.subscribe("device/+/status")
        else:
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")
    
    def on_message(self, client, userdata, msg):
        """消息接收回调函数"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message on topic {msg.topic}: {payload}")
            
            # 处理设备状态更新
            if msg.topic.startswith("device/") and msg.topic.endswith("/status"):
                device_id = msg.topic.split("/")[1]
                self.handle_device_status_update(device_id, payload)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode message payload: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def on_publish(self, client, userdata, mid):
        """发布回调函数"""
        logger.info(f"Message {mid} published successfully")
    
    def publish_command(self, device_id, command_type, parameters):
        """发布控制命令到 MQTT"""
        topic = f"device/{device_id}/command"
        payload = {
            "command_type": command_type,
            "parameters": parameters,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            message_info = self.client.publish(topic, json.dumps(payload), qos=1)
            if message_info.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Command published successfully to {topic}")
                return True
            else:
                logger.error(f"Failed to publish command to {topic}")
                return False
        except Exception as e:
            logger.error(f"Error publishing command: {str(e)}")
            return False
    
    def handle_device_status_update(self, device_id, status_data):
        """处理设备状态更新"""
        from device.models import Device
        try:
            device = Device.objects.get(device_id=device_id)
            # 更新设备状态
            if 'temperature' in status_data:
                device.current_temp = status_data['temperature']
            if 'status' in status_data:
                device.status = status_data['status']
            if 'mode' in status_data:
                device.mode = status_data['mode']
            device.save()
            
            # 创建状态历史记录
            from device.models import DeviceStatus
            DeviceStatus.objects.create(
                device=device,
                current_temp=device.current_temp,
                set_temp=device.set_temp,
                status=device.status,
                mode=device.mode
            )
        except Device.DoesNotExist:
            logger.error(f"Device with ID {device_id} not found")
        except Exception as e:
            logger.error(f"Error updating device status: {str(e)}")

# 创建全局 MQTT 客户端实例
mqtt_client = MQTTClient() 