# from django.apps import AppConfig
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class ControlConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "control"
#
#     def ready(self):
#         """应用启动时连接到 MQTT 代理服务器"""
#         try:
#             from .mqtt import mqtt_client
#             if not mqtt_client.connect():
#                 logger.warning("Failed to connect to MQTT broker during startup, will retry on demand")
#         except Exception as e:
#             logger.error(f"Error initializing MQTT client: {str(e)}")
