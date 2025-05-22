from django.contrib import admin
from .models import Device, DeviceTopic, Company, Department, Building, Floor, DeviceStatus

@admin.register(DeviceTopic)
class DeviceTopicAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'topic', 'get_device_name', 'create_time', 'update_time')
    list_filter = ('create_time', 'update_time')
    search_fields = ('uuid', 'topic', 'description')
    readonly_fields = ('create_time', 'update_time')
    ordering = ('-create_time',)
    
    def get_device_name(self, obj):
        device = obj.device
        return device.name if device else '未关联设备'
    get_device_name.short_description = '设备名称'

# 注册其他模型
admin.site.register(Device)
admin.site.register(Company)
admin.site.register(Department)
admin.site.register(Building)
admin.site.register(Floor)
admin.site.register(DeviceStatus)
