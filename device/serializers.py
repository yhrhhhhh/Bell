from rest_framework import serializers
from .models import Device, DeviceStatus, Building, Floor, Company, Department, Topic

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
    subscribe_topic = serializers.CharField(write_only=True)
    publish_topic = serializers.CharField(write_only=True)
    
    class Meta:
        model = Device
        fields = '__all__'

    def validate(self, data):
        # 验证必填字段
        required_fields = ['name', 'device_id', 'uuid_value', 'subscribe_topic', 'publish_topic', 'company', 'department', 'floor']
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError({field: ['该字段是必填项。']})
        
        # 验证部门是否存在且属于选择的公司
        if data['department'].company != data['company']:
            raise serializers.ValidationError({'department': ['所选部门不属于选择的公司。']})
        
        # 验证UUID并获取或创建Topic
        uuid_value = data.pop('uuid_value')
        subscribe_topic = data.pop('subscribe_topic')
        publish_topic = data.pop('publish_topic')
        
        try:
            # 创建或更新Topic记录
            topic, created = Topic.objects.update_or_create(
                uuid=uuid_value,
                defaults={
                    'subscribe_topic': subscribe_topic,
                    'publish_topic': publish_topic
                }
            )
            # 将Topic对象添加到数据中
            data['uuid'] = topic
        except Exception as e:
            raise serializers.ValidationError({'uuid_value': [f'UUID处理错误: {str(e)}']})
        
        # 根据floor自动设置building
        try:
            floor = data['floor']
            if isinstance(floor, (int, str)):
                floor = Floor.objects.get(id=floor)
                data['floor'] = floor
            data['building'] = floor.building
        except Floor.DoesNotExist:
            raise serializers.ValidationError({'floor': ['未找到指定的楼层。']})
        except Exception as e:
            raise serializers.ValidationError({'floor': [f'楼层处理错误: {str(e)}']})
        
        return data

class DeviceUpdateSerializer(serializers.ModelSerializer):
    """用于更新设备的序列化器"""
    uuid_value = serializers.CharField(required=False)  # UUID值
    subscribe_topic = serializers.CharField(required=False)  # 订阅主题
    publish_topic = serializers.CharField(required=False)  # 发布主题
    
    class Meta:
        model = Device
        fields = ['name', 'device_id', 'uuid_value', 'subscribe_topic', 'publish_topic', 'set_temp', 'mode', 'status']
        
    def update(self, instance, validated_data):
        # 如果提供了uuid相关信息，更新Topic表
        if any(key in validated_data for key in ['uuid_value', 'subscribe_topic', 'publish_topic']):
            from .models import Topic
            uuid_value = validated_data.pop('uuid_value', None)
            subscribe_topic = validated_data.pop('subscribe_topic', None)
            publish_topic = validated_data.pop('publish_topic', None)
            
            if uuid_value:
                # 更新或创建Topic记录
                topic, created = Topic.objects.update_or_create(
                    uuid=uuid_value,
                    defaults={
                        'subscribe_topic': subscribe_topic or f'device/{uuid_value}/status',
                        'publish_topic': publish_topic or f'device/{uuid_value}/control'
                    }
                )
                # 更新设备的uuid关联
                instance.uuid = topic
        
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
