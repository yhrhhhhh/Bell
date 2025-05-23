from rest_framework import serializers
from .models import Device, DeviceStatus, Building, Floor, Company, Department

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Department
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)
    floor_name = serializers.CharField(source='floor.name', read_only=True)
    uuid_info = serializers.SerializerMethodField()
    uuid_value = serializers.CharField(source='uuid.uuid', read_only=True)
    
    class Meta:
        model = Device
        fields = '__all__'

    def get_uuid_info(self, obj):
        if obj.uuid:
            return {
                'uuid': obj.uuid.uuid,
                'topic': {
                    'subscribe': obj.uuid.subscribe_topic,
                    'publish': obj.uuid.publish_topic
                }
            }
        return None
        
class DeviceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStatus
        fields = '__all__'
        
class DeviceCreateSerializer(serializers.ModelSerializer):
    uuid_value = serializers.CharField(write_only=True)
    
    class Meta:
        model = Device
        fields = '__all__'

    def validate(self, data):
        # 验证必填字段
        required_fields = ['name', 'device_id', 'uuid_value', 'company', 'department', 'floor']
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError({field: ['该字段是必填项。']})
        
        # 验证部门是否存在且属于选择的公司
        if data['department'].company != data['company']:
            raise serializers.ValidationError({'department': ['所选部门不属于选择的公司。']})
        
        # 验证UUID并获取或创建Topic
        uuid_value = data.pop('uuid_value')
        try:
            topic, created = Topic.objects.get_or_create(
                uuid=uuid_value,
                defaults={
                    'subscribe_topic': f'device/{uuid_value}/status',
                    'publish_topic': f'device/{uuid_value}/control'
                }
            )
            data['uuid'] = topic
        except Exception as e:
            raise serializers.ValidationError({'uuid_value': [f'UUID处理错误: {str(e)}']})
        
        return data
        
    def create(self, validated_data):
        try:
            # 从validated_data中取出uuid和topic
            uuid_str = validated_data.pop('uuid')
            topic_str = validated_data.pop('topic')
            
            # 创建或获取Topic对象
            from .models import Topic
            topic_obj, _ = Topic.objects.get_or_create(
                uuid=uuid_str,
                defaults={'topic': topic_str}
            )
            
            # 获取相关对象
            company = Company.objects.get(id=validated_data.pop('company_id'))
            department = Department.objects.get(id=validated_data.pop('department_id'))
            floor = Floor.objects.get(id=validated_data.pop('floor_id'))
            
            # 创建设备实例
            device = Device(
                uuid=uuid_str,  # 直接使用uuid字符串
                company=company,
                department=department,
                floor=floor,
                building=floor.building,
                **validated_data
            )
            device.save()
            
            return device
            
        except Exception as e:
            raise serializers.ValidationError(str(e))

class DeviceUpdateSerializer(serializers.ModelSerializer):
    """用于更新设备的序列化器"""
    topic = serializers.CharField(required=False)  # 添加topic字段
    
    class Meta:
        model = Device
        fields = ['name', 'device_id', 'uuid', 'topic', 'set_temp', 'mode', 'status']
        
    def update(self, instance, validated_data):
        # 如果提供了uuid和topic，更新Topic表
        if 'uuid' in validated_data and 'topic' in validated_data:
            from .models import Topic
            uuid_str = validated_data.pop('uuid')
            topic_str = validated_data.pop('topic')
            
            # 更新或创建Topic记录
            Topic.objects.update_or_create(
                uuid=uuid_str,
                defaults={'topic': topic_str}
            )
            
            # 更新设备的uuid
            instance.uuid = uuid_str
        elif 'uuid' in validated_data:
            # 如果只提供了uuid，直接更新
            instance.uuid = validated_data.pop('uuid')
        
        # 更新其他字段
        instance.name = validated_data.get('name', instance.name)
        instance.device_id = validated_data.get('device_id', instance.device_id)
        instance.set_temp = validated_data.get('set_temp', instance.set_temp)
        instance.mode = validated_data.get('mode', instance.mode)
        instance.status = validated_data.get('status', instance.status)
        
        try:
            instance.save()
            return instance
        except Exception as e:
            raise serializers.ValidationError(str(e))

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
    label = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = ['id', 'label', 'children', 'type']
    
    def get_label(self, obj):
        return obj.uuid.uuid if obj.uuid else None
    
    def get_type(self, obj):
        return 'gateway'
    
    def get_children(self, obj):
        if not obj.uuid:
            return []
        # 获取具有相同uuid的所有设备
        devices = Device.objects.filter(uuid=obj.uuid).exclude(id=obj.id)
        return [{
            'id': device.id,
            'label': device.name or device.device_id,  # 优先使用设备名称
            'type': 'device',
            'status': device.status,
            'uuid': device.uuid.uuid if device.uuid else None,  # 使用Topic的uuid字段
            'device_id': device.device_id  # 添加device_id字段
        } for device in devices]
