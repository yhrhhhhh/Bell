from rest_framework import serializers
from .models import Device, DeviceStatus, Building, Floor, Company, Department, DeviceAlarm

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Department
        fields = '__all__'

class DeviceAlarmSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = DeviceAlarm
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)
    floor_name = serializers.CharField(source='floor.name', read_only=True)
    
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
        fields = ['name', 'device_id', 'uuid', 'room_id', 
                 'floor_id', 'building_id', 'set_temp', 'mode']

class DeviceUpdateSerializer(serializers.ModelSerializer):
    """用于更新设备的序列化器"""
    class Meta:
        model = Device
        fields = ['name', 'device_id', 'uuid', 'set_temp', 'mode', 'status']
        
    def update(self, instance, validated_data):
        # 更新字段
        instance.name = validated_data.get('name', instance.name)
        instance.device_id = validated_data.get('device_id', instance.device_id)
        instance.uuid = validated_data.get('uuid', instance.uuid)
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
    """用于生成楼栋-楼层树形结构的序列化器"""
    label = serializers.CharField(source='name')
    children = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = Building
        fields = ['id', 'label', 'children', 'type']
    
    def get_type(self, obj):
        return 'building'
    
    def get_children(self, obj):
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

class CompanyTreeSerializer(serializers.ModelSerializer):
    """用于生成公司-部门树形结构的序列化器"""
    label = serializers.CharField(source='name')
    children = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'label', 'children', 'type']
    
    def get_type(self, obj):
        return 'company'
    
    def get_children(self, obj):
        departments = obj.departments.all()
        return [{
            'id': dept.id,
            'label': dept.name,
            'type': 'department',
            'company_id': obj.id
        } for dept in departments]

class GatewayTreeSerializer(serializers.ModelSerializer):
    """用于生成网关-设备树形结构的序列化器"""
    label = serializers.CharField(source='uuid')
    children = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = ['id', 'label', 'children', 'type']
    
    def get_type(self, obj):
        return 'gateway'
    
    def get_children(self, obj):
        # 获取具有相同uuid的所有设备
        devices = Device.objects.filter(uuid=obj.uuid).exclude(id=obj.id)
        return [{
            'id': device.id,
            'label': device.device_id,
            'type': 'device',
            'gateway_id': obj.id
        } for device in devices]
