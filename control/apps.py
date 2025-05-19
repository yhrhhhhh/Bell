from django.apps import AppConfig


class ControlConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "control"

    def ready(self):
        """应用启动时连接到 MQTT 代理服务器"""
        from .mqtt import mqtt_client
        mqtt_client.connect()
