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
    class Meta:
        model = Device
        fields = ['name', 'location', 'set_temp', 'is_auto']

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
        print(f"正在获取建筑 {obj.name} 的楼层...")
        floors = obj.floors.all().order_by('floor_number')
        print(f"查询到 {floors.count()} 个楼层")
        result = []
        
        for floor in floors:
            print(f"处理楼层: {floor.name}")
            floor_data = {
                'id': floor.id,
                'label': floor.name,
                'type': 'floor',
                'floor_number': floor.floor_number,
                'building_id': obj.id
            }
            result.append(floor_data)
        
        print(f"楼层数据: {result}")
        return result
