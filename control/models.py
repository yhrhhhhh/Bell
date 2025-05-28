# from django.db import models
# from device.models import Device
#
# class ControlCommand(models.Model):
#     """控制命令模型"""
#     STATUS_CHOICES = (
#         ('pending', '待执行'),
#         ('sent', '已发送'),
#         ('success', '执行成功'),
#         ('failed', '执行失败'),
#     )
#
#     device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="commands", verbose_name="设备")
#     command_type = models.CharField(max_length=50, verbose_name="命令类型")
#     command_value = models.CharField(max_length=255, verbose_name="命令值")
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="执行状态")
#     create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
#     execute_time = models.DateTimeField(null=True, blank=True, verbose_name="执行时间")
#     result = models.TextField(null=True, blank=True, verbose_name="执行结果")
#
#     class Meta:
#         verbose_name = "控制命令"
#         verbose_name_plural = "控制命令管理"
#         ordering = ['-create_time']
#
# class BatchCommand(models.Model):
#     """批量控制命令"""
#     STATUS_CHOICES = (
#         ('pending', '待执行'),
#         ('executing', '执行中'),
#         ('completed', '已完成'),
#         ('failed', '执行失败'),
#     )
#
#     name = models.CharField(max_length=100, verbose_name="批量命令名称")
#     command_type = models.CharField(max_length=50, verbose_name="命令类型")
#     command_value = models.CharField(max_length=255, verbose_name="命令值")
#     target_devices = models.ManyToManyField(Device, related_name="batch_commands", verbose_name="目标设备")
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="执行状态")
#     success_count = models.IntegerField(default=0, verbose_name="成功数量")
#     fail_count = models.IntegerField(default=0, verbose_name="失败数量")
#     create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
#
#     class Meta:
#         verbose_name = "批量命令"
#         verbose_name_plural = "批量命令管理"
#         ordering = ['-create_time']
#
