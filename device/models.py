from django.db import models


class AirConditioner(models.Model):
    # 运行模式选项
    MODE_AUTO = 0
    MODE_COOL = 1
    MODE_HEAT = 2
    MODE_FAN = 3
    MODE_DRY = 4
    MODE_CHOICES = [
        (MODE_AUTO, '自动'),
        (MODE_COOL, '制冷'),
        (MODE_HEAT, '制热'),
        (MODE_FAN, '送风'),
        (MODE_DRY, '除湿'),
    ]

    # 风速选项
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

    # 设备基本信息
    name = models.CharField('设备名称', max_length=100, blank=False, null=False)
    uuid = models.CharField('设备UUID', max_length=36, blank=False, null=False)
    address = models.CharField('设备地址', max_length=200, blank=False, null=False)

    # 位置信息
    room_id = models.CharField('房间ID', max_length=50, blank=True, null=True)
    floor = models.CharField('所属楼层', max_length=50, blank=True, null=True)
    building = models.CharField('所属建筑', max_length=50, blank=True, null=True)
    company = models.CharField('所属公司', max_length=50, blank=True, null=True)
    department = models.CharField('所属部门', max_length=50, blank=True, null=True)

    # 温度相关
    current_temperature = models.FloatField('房间温度', blank=False, null=False, default=20.0)
    target_temperature = models.FloatField('设定温度', blank=False, null=False, default=20.0)
    last_set_temperature = models.FloatField('操作员最后设置温度', blank=False, null=False, default=20.0)

    # 运行状态
    is_running = models.BooleanField('运行状态', blank=False, null=False, default=False)
    mode = models.IntegerField('运行模式', choices=MODE_CHOICES, blank=False, null=False, default=MODE_AUTO)
    fan_speed = models.IntegerField('风速', choices=FAN_SPEED_CHOICES, blank=False, null=False, default=FAN_SPEED_AUTO)

    # 警报信息
    alarm_code = models.CharField('警报代码', max_length=20, blank=True, null=True)

    # 时间信息
    last_updated = models.DateTimeField('最后更新时间', auto_now=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '空调设备'  # 单数名称
        verbose_name_plural = '空调设备'  # 复数名称
        ordering = ['-last_updated'] # 当查询该模型时，返回的结果集默认按哪个字段排序。
        constraints = [
            models.UniqueConstraint(
                fields=['uuid', 'address'],
                name='unique_uuid_address'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.uuid})({self.address})"