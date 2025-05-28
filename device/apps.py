from django.apps import AppConfig


class DeviceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "device"

    def ready(self):
        # 只在主进程启动时运行，避免在迁移等操作时运行
        import os
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('RUN_MAIN') is None:
            from .mqtt_client import mqtt_client
            mqtt_client.start()