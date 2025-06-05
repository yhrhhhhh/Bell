from django.db import models

# Create your models here.

class Company(models.Model):
    """公司模型"""
    name = models.CharField(max_length=100, verbose_name="公司名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="公司编码")
    description = models.TextField(null=True, blank=True, verbose_name="公司描述")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "公司"
        verbose_name_plural = "公司管理"

class Department(models.Model):
    """部门模型"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments', verbose_name="所属公司")
    name = models.CharField(max_length=100, verbose_name="部门名称")
    code = models.CharField(max_length=50, verbose_name="部门编码")
    description = models.TextField(null=True, blank=True, verbose_name="部门描述")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return f"{self.company.name}-{self.name}"
    
    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门管理"

class Building(models.Model):
    """建筑物模型"""
    name = models.CharField(max_length=100, verbose_name="建筑名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="建筑编码")
    description = models.TextField(null=True, blank=True, verbose_name="建筑描述")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "建筑"
        verbose_name_plural = "建筑管理"

class Floor(models.Model):
    """楼层模型"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors', verbose_name="所属建筑")
    name = models.CharField(max_length=50, verbose_name="楼层名称")
    floor_number = models.IntegerField(verbose_name="楼层号")
    description = models.TextField(null=True, blank=True, verbose_name="楼层描述")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return f"{self.building.name}-{self.name}"
    
    class Meta:
        verbose_name = "楼层"
        verbose_name_plural = "楼层管理"
        ordering = ['building', 'floor_number']

class Topic(models.Model):
    """MQTT Topic模型"""
    uuid = models.CharField(max_length=100, unique=True, verbose_name='UUID')
    subscribe_topic = models.CharField(max_length=255, verbose_name='订阅Topic路径', db_index=True)
    publish_topic = models.CharField(max_length=255, verbose_name='发布Topic路径', db_index=True)
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    # TODO 在线状态字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'MQTT Topic'
        verbose_name_plural = verbose_name
        db_table = 'device_mqtt_topic'
        indexes = [
            models.Index(fields=['subscribe_topic']),
            models.Index(fields=['publish_topic'])
        ]

    def __str__(self):
        return f"{self.uuid} - Sub:{self.subscribe_topic} Pub:{self.publish_topic}"

    @classmethod
    def get_topics(cls):
        """获取所有不重复的Topic列表"""
        subscribe_topics = cls.objects.values_list('subscribe_topic', flat=True).distinct()
        publish_topics = cls.objects.values_list('publish_topic', flat=True).distinct()
        return list(set(list(subscribe_topics) + list(publish_topics)))

class Device(models.Model):
    """设备模型"""
    STATUS_CHOICES = (
        ('running', '运行'),
        ('stopped', '停止'),
        ('fault', '故障'),
    )
    
    MODE_CHOICES = (
        ('auto', '自动'),
        ('cooling', '制冷'),
        ('heating', '制热'),
        ('fan', '送风'),
        ('dehumidify', '除湿'),
    )
    
    FAN_SPEED_AUTO = 0
    FAN_SPEED_HIGH = 1
    FAN_SPEED_MEDIUM = 2
    FAN_SPEED_LOW = 4
    FAN_SPEED_GENTLE = 6
    
    FAN_SPEED_CHOICES = [
        (FAN_SPEED_AUTO, '自动'),
        (FAN_SPEED_HIGH, '高速'),
        (FAN_SPEED_MEDIUM, '中速'),
        (FAN_SPEED_LOW, '低速'),
        (FAN_SPEED_GENTLE, '微风'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="设备名称")
    device_id = models.CharField(max_length=100, db_index=True, verbose_name="设备ID")
    uuid = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="UUID", related_name='devices')
    room_id = models.IntegerField(verbose_name="房间ID")
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='devices', verbose_name="所属楼层", null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='devices', verbose_name="所属建筑", null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='devices', verbose_name="所属公司", null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='devices', verbose_name="所属部门", null=True, blank=True)
    current_temp = models.FloatField(default=25.0, verbose_name="当前温度")
    set_temp = models.FloatField(default=25.0, verbose_name="设定温度")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='stopped', verbose_name="运行状态")
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='cooling', verbose_name="运行模式")
    fan_speed = models.IntegerField(choices=FAN_SPEED_CHOICES, default=FAN_SPEED_AUTO, verbose_name="风速")
    running_time = models.FloatField(default=0.0, verbose_name="运行时间(小时)")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return f"{self.name}-{self.device_id}"
    
    class Meta:
        verbose_name = "设备"
        verbose_name_plural = "设备管理"
        unique_together = [('device_id', 'uuid')]

class DeviceStatus(models.Model):
    """设备状态历史记录"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="status_history", verbose_name="设备")
    current_temp = models.FloatField(verbose_name="当前温度")
    set_temp = models.FloatField(verbose_name="设定温度")
    status = models.CharField(max_length=20, verbose_name="运行状态")
    mode = models.CharField(max_length=20, verbose_name="运行模式")
    fan_speed = models.IntegerField(verbose_name="风速", default=0)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="记录时间")

    class Meta:
        verbose_name = "设备状态记录"
        verbose_name_plural = "设备状态历史"
        ordering = ['-timestamp']
