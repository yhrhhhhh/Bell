from rest_framework import serializers
from .models import Device, DeviceStatus, Building, Floor

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
    """用于更新设备的序列化器"""
    class Meta:
        model = Device
        fields = ['name', 'device_id', 'location', 'set_temp', 'mode', 'status']
        
    def update(self, instance, validated_data):
        
        # 更新字段
        instance.name = validated_data.get('name', instance.name)
        instance.device_id = validated_data.get('device_id', instance.device_id)
        instance.location = validated_data.get('location', instance.location)
        instance.set_temp = validated_data.get('set_temp', instance.set_temp)
        instance.mode = validated_data.get('mode', instance.mode)
        instance.status = validated_data.get('status', instance.status)
        
        try:
            instance.save()
            return instance
        except Exception as e:
            raise

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'name', 'floor_number', 'description']

class BuildingSerializer(serializers.ModelSerializer):
    floors = FloorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Building
        fields = ['id', 'name', 'code', 'description', 'floors']

class BuildingTreeSerializer(serializers.ModelSerializer):
    """用于生成树形结构的序列化器"""
    label = serializers.CharField(source='name')
    children = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = Building
        fields = ['id', 'label', 'children', 'type']
    
    def get_type(self, obj):
        """返回节点类型"""
        return 'building'
    
    def get_children(self, obj):
        """获取楼层作为子节点"""
        floors = obj.floors.all().order_by('floor_number')
        result = []
        
        for floor in floors:
            floor_data = {
                'id': floor.id,
                'label': floor.name,
                'type': 'floor',
                'floor_number': floor.floor_number,
                'building_id': obj.id
            }
            result.append(floor_data)

        return result
