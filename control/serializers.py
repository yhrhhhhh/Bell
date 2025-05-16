from rest_framework import serializers
from .models import ControlCommand, BatchCommand
from device.serializers import DeviceSerializer

class ControlCommandSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = ControlCommand
        fields = '__all__'
        
class ControlCommandCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlCommand
        fields = ['device', 'command_type', 'parameters', 'priority']
        
class BatchCommandSerializer(serializers.ModelSerializer):
    devices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchCommand
        fields = '__all__'
    
    def get_devices_count(self, obj):
        return obj.target_devices.count()
        
class BatchCommandCreateSerializer(serializers.ModelSerializer):
    device_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    
    class Meta:
        model = BatchCommand
        fields = ['name', 'command_type', 'command_value', 'device_ids']
    
    def create(self, validated_data):
        device_ids = validated_data.pop('device_ids')
        batch_command = BatchCommand.objects.create(**validated_data)
        from device.models import Device
        devices = Device.objects.filter(id__in=device_ids)
        batch_command.target_devices.set(devices)
        return batch_command
