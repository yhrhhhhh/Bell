from django.apps import AppConfig
import os
import sys


class DeviceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "device"

    def ready(self):
        # 只在主进程中启动MQTT客户端
        # Django开发服务器会启动两次，一次是主进程，一次是重载进程
        # RUN_MAIN=true 表示这是在重载进程中运行
        if os.environ.get('RUN_MAIN') == 'true':
            # 确保不在管理命令中运行
            if 'runserver' in sys.argv:
                from .mqtt_client import mqtt_client
                mqtt_client.start()