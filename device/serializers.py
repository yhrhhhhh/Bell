from rest_framework import serializers
from .models import Device, DeviceStatus

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'
        
class DeviceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStatus
        fields = '__all__'
        
class DeviceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['name', 'device_id', 'location', 'room_id', 
                 'floor_id', 'building_id', 'set_temp', 'mode']

class DeviceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['name', 'location', 'set_temp', 'is_auto']
