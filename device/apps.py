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


            """Django启动时自动加载定时任务"""
            if not hasattr(self, '_already_loaded'):
                from .cron import scheduler  # 触发cron.py的初始化
                self._already_loaded = True