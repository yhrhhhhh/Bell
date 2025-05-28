# from django.shortcuts import render
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from .models import ControlCommand, BatchCommand
# from .serializers import (
#     ControlCommandSerializer, ControlCommandCreateSerializer,
#     BatchCommandSerializer, BatchCommandCreateSerializer
# )
# from device.models import Device
# from .mqtt import mqtt_client
# import datetime
#
#
# class ControlCommandViewSet(viewsets.ModelViewSet):
#     """控制命令视图集"""
#     queryset = ControlCommand.objects.all()
#     serializer_class = ControlCommandSerializer
#
#     def get_serializer_class(self):
#         if self.action == 'create':
#             return ControlCommandCreateSerializer
#         return ControlCommandSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         # 创建命令
#         command = serializer.save()
#
#         # 发送命令到 MQTT
#         success = mqtt_client.publish_command(
#             command.device.device_id,
#             command.command_type,
#             command.parameters
#         )
#
#         if success:
#             command.status = 'sent'
#             command.execute_time = datetime.datetime.now()
#             command.save()
#         else:
#             command.status = 'failed'
#             command.save()
#             return Response(
#                 {"error": "Failed to send command to device"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
#
#     @action(detail=False, methods=['post'])
#     def batch_control(self, request):
#         """批量控制设备"""
#         devices = request.data.get('devices', [])
#         command_type = request.data.get('command_type')
#         parameters = request.data.get('parameters', {})
#
#         if not devices or not command_type:
#             return Response(
#                 {"error": "devices and command_type are required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         commands = []
#         success_count = 0
#         fail_count = 0
#
#         for device_id in devices:
#             try:
#                 device = Device.objects.get(id=device_id)
#                 command = ControlCommand.objects.create(
#                     device=device,
#                     command_type=command_type,
#                     parameters=parameters
#                 )
#
#                 # 发送命令到 MQTT
#                 success = mqtt_client.publish_command(
#                     device.device_id,
#                     command_type,
#                     parameters
#                 )
#
#                 if success:
#                     command.status = 'sent'
#                     command.execute_time = datetime.datetime.now()
#                     success_count += 1
#                 else:
#                     command.status = 'failed'
#                     fail_count += 1
#
#                 command.save()
#                 commands.append(command)
#             except Device.DoesNotExist:
#                 fail_count += 1
#                 continue
#
#         serializer = ControlCommandSerializer(commands, many=True)
#         return Response({
#             'commands': serializer.data,
#             'success_count': success_count,
#             'fail_count': fail_count
#         })
#
#     @action(detail=False, methods=['post'])
#     def send_command(self, request):
#         """发送单个控制命令"""
#         device_id = request.data.get('device_id')
#         command_type = request.data.get('command_type')
#         parameters = request.data.get('parameters', {})
#
#         if not device_id or not command_type:
#             return Response(
#                 {"error": "device_id and command_type are required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         try:
#             device = Device.objects.get(id=device_id)
#             command = ControlCommand.objects.create(
#                 device=device,
#                 command_type=command_type,
#                 parameters=parameters
#             )
#
#             # 发送命令到 MQTT
#             success = mqtt_client.publish_command(
#                 device.device_id,
#                 command_type,
#                 parameters
#             )
#
#             if success:
#                 command.status = 'sent'
#                 command.execute_time = datetime.datetime.now()
#             else:
#                 command.status = 'failed'
#
#             command.save()
#             serializer = ControlCommandSerializer(command)
#             return Response(serializer.data)
#         except Device.DoesNotExist:
#             return Response(
#                 {"error": "Device not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#
# class BatchCommandViewSet(viewsets.ModelViewSet):
#     """批量控制命令视图集"""
#     queryset = BatchCommand.objects.all()
#     serializer_class = BatchCommandSerializer
#
#     def get_serializer_class(self):
#         if self.action == 'create':
#             return BatchCommandCreateSerializer
#         return BatchCommandSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         batch_command = serializer.save()
#
#         # 处理批量命令
#         self.process_batch_command(batch_command)
#
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
#
#     def process_batch_command(self, batch_command):
#         """处理批量命令"""
#         devices = batch_command.target_devices.all()
#         batch_command.status = 'executing'
#         batch_command.save()
#
#         for device in devices:
#             try:
#                 # 创建单个控制命令
#                 command = ControlCommand.objects.create(
#                     device=device,
#                     command_type=batch_command.command_type,
#                     command_value=batch_command.command_value
#                 )
#
#                 # 更新设备状态
#                 if batch_command.command_type == 'set_status':
#                     device.status = batch_command.command_value
#                 elif batch_command.command_type == 'set_temp':
#                     device.set_temp = float(batch_command.command_value)
#                 elif batch_command.command_type == 'set_mode':
#                     device.mode = batch_command.command_value
#                 device.save()
#
#                 # 更新命令状态
#                 command.status = 'sent'
#                 command.execute_time = datetime.datetime.now()
#                 command.save()
#
#                 batch_command.success_count += 1
#             except Exception as e:
#                 batch_command.fail_count += 1
#                 print(f"批量命令执行错误: {str(e)}")
#
#         batch_command.status = 'completed'
#         batch_command.save()
