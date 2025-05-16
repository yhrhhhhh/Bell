from django.db import models

# Create your models here.

class Device(models.Model):
    """设备模型"""
    STATUS_CHOICES = (
        ('running', '运行'),
        ('stopped', '停止'),
        ('fault', '故障'),
    )
    
    MODE_CHOICES = (
        ('cooling', '制冷'),
        ('heating', '制热'),
        ('fan', '送风'),
        ('dehumidify', '除湿'),
    )
    
    name = models.CharField(max_length=100, verbose_name="设备名称")
    device_id = models.CharField(max_length=100, unique=True, verbose_name="设备ID")
    location = models.CharField(max_length=255, verbose_name="设备位置")
    room_id = models.IntegerField(verbose_name="房间ID")
    floor_id = models.IntegerField(verbose_name="楼层ID")
    building_id = models.IntegerField(verbose_name="建筑ID")
    current_temp = models.FloatField(default=25.0, verbose_name="当前温度")
    set_temp = models.FloatField(default=25.0, verbose_name="设定温度")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='stopped', verbose_name="运行状态")
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='cooling', verbose_name="运行模式")
    is_auto = models.BooleanField(default=False, verbose_name="是否自动控制")
    running_time = models.FloatField(default=0.0, verbose_name="运行时间(小时)")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return f"{self.name}-{self.device_id}"
    
    class Meta:
        verbose_name = "设备"
        verbose_name_plural = "设备管理"


class DeviceStatus(models.Model):
    """设备状态历史记录"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="status_history", verbose_name="设备")
    current_temp = models.FloatField(verbose_name="当前温度")
    set_temp = models.FloatField(verbose_name="设定温度")
    status = models.CharField(max_length=20, verbose_name="运行状态")
    mode = models.CharField(max_length=20, verbose_name="运行模式")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="记录时间")
    
    class Meta:
        verbose_name = "设备状态记录"
        verbose_name_plural = "设备状态历史"
        ordering = ['-timestamp']
