from django.contrib import admin
from .models import Device, Topic, Company, Department, Building, Floor, DeviceStatus

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'device_id', 'uuid', 'status', 'online_status', 'current_temp', 'set_temp', 'mode', 'fan_speed')
    list_filter = ('status', 'mode', 'fan_speed', 'online_status')
    search_fields = ('name', 'device_id', 'uuid')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'subscribe_topic', 'publish_topic', 'online_status', 'description', 'created_at', 'updated_at']
    search_fields = ['uuid', 'subscribe_topic', 'publish_topic', 'description']
    list_filter = ['created_at', 'updated_at', 'online_status']

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'create_time')
    search_fields = ('name', 'code')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'code', 'create_time')
    list_filter = ('company',)
    search_fields = ('name', 'code')

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'create_time')
    search_fields = ('name', 'code')

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'floor_number', 'create_time')
    list_filter = ('building',)
    search_fields = ('name',)

@admin.register(DeviceStatus)
class DeviceStatusAdmin(admin.ModelAdmin):
    list_display = ('device', 'current_temp', 'set_temp', 'status', 'mode', 'fan_speed', 'timestamp')
    list_filter = ('status', 'mode', 'fan_speed')
    search_fields = ('device__name', 'device__device_id')
