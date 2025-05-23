from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db import transaction  # 添加事务导入
from .models import Device, DeviceStatus, Building, Floor, Company, Department, Topic
from .serializers import (
    DeviceSerializer, DeviceStatusSerializer, DeviceCreateSerializer, 
    DeviceUpdateSerializer, BuildingTreeSerializer, CompanySerializer,
    DepartmentSerializer, CompanyTreeSerializer, GatewayTreeSerializer
)


class DeviceViewSet(viewsets.ModelViewSet):
    """设备视图集，提供设备的增删改查功能"""
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DeviceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DeviceUpdateSerializer
        return DeviceSerializer
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """获取设备状态"""
        device = self.get_object()
        return Response({
            'id': device.id,
            'name': device.name,
            'current_temp': device.current_temp,
            'set_temp': device.set_temp,
            'status': device.status,
            'mode': device.mode,
            'fan_speed': device.fan_speed,
            'running_time': device.running_time,
            'is_auto': device.is_auto,
            'last_updated': device.last_updated,
        })
    
    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """获取设备状态历史"""
        device = self.get_object()
        history = DeviceStatus.objects.filter(device=device)
        page = self.paginate_queryset(history)
        if page is not None:
            serializer = DeviceStatusSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = DeviceStatusSerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_building(self, request):
        """按建筑筛选设备"""
        building_id = request.query_params.get('building_id')
        if building_id:
            devices = Device.objects.filter(building_id=building_id)
            serializer = DeviceSerializer(devices, many=True)
            return Response(serializer.data)
        return Response({"error": "missing building_id parameter"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_floor(self, request):
        """按楼层筛选设备"""
        floor_id = request.query_params.get('floor_id')
        if floor_id:
            devices = Device.objects.filter(floor_id=floor_id)
            print(devices)
            serializer = DeviceSerializer(devices, many=True)
            return Response(serializer.data)
        return Response({"error": "missing floor_id parameter"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_room(self, request):
        """按房间筛选设备"""
        room_id = request.query_params.get('room_id')
        if room_id:
            devices = Device.objects.filter(room_id=room_id)
            serializer = DeviceSerializer(devices, many=True)
            return Response(serializer.data)
        return Response({"error": "missing room_id parameter"}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取设备树形结构数据"""
        # 获取所有建筑
        buildings = {}
        floors = {}
        rooms = {}
        
        # 先获取所有设备
        devices = Device.objects.all()
        result = []
        
        # 构建树形结构
        for device in devices:
            # 处理建筑
            if device.building_id not in buildings:
                building_data = {
                    'id': f'building_{device.building_id}',
                    'name': f'建筑{device.building_id}',  # 这里可以从建筑表获取实际名称
                    'type': 'building',
                    'children': []
                }
                buildings[device.building_id] = building_data
                result.append(building_data)
            
            # 处理楼层
            floor_key = f"{device.building_id}_{device.floor_id}"
            if floor_key not in floors:
                floor_data = {
                    'id': f'floor_{floor_key}',
                    'name': f'{device.floor_id}层',  # 这里可以从楼层表获取实际名称
                    'type': 'floor',
                    'children': []
                }
                floors[floor_key] = floor_data
                buildings[device.building_id]['children'].append(floor_data)
            
            # 处理房间
            room_key = f"{device.building_id}_{device.floor_id}_{device.room_id}"
            if room_key not in rooms:
                room_data = {
                    'id': f'room_{room_key}',
                    'name': f'房间{device.room_id}',  # 这里可以从房间表获取实际名称
                    'type': 'room',
                    'children': []
                }
                rooms[room_key] = room_data
                floors[floor_key]['children'].append(room_data)
            
            # 添加设备
            device_data = {
                'id': f'device_{device.id}',
                'name': device.name,
                'device_id': device.device_id,
                'type': 'device',
                'status': device.status,
                'current_temp': device.current_temp,
                'set_temp': device.set_temp
            }
            rooms[room_key]['children'].append(device_data)
        
        return Response(result)

    @action(detail=False, methods=['post'], url_path='batch-delete', url_name='batch_delete')
    def batch_delete(self, request):
        """批量删除设备"""
        device_ids = request.data.get('device_ids', [])
        if not device_ids:
            return Response({"error": "没有提供要删除的设备ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            devices = Device.objects.filter(id__in=device_ids)
            deleted_count = devices.count()
            devices.delete()
            return Response({
                "message": f"成功删除{deleted_count}个设备",
                "deleted_count": deleted_count
            })
        except Exception as e:
            return Response({"error": f"删除失败：{str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='batch-control', url_name='batch_control')
    def batch_control(self, request):
        """批量控制设备"""
        print("\n=== 批量控制请求开始 ===")
        print("请求数据:", request.data)
        
        device_ids = request.data.get('device_ids', [])
        control_data = request.data.get('control', {})
        
        print("设备IDs:", device_ids)
        print("控制数据:", control_data)
        
        if not device_ids:
            return Response({"error": "没有提供要控制的设备ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not control_data:
            return Response({"error": "没有提供控制参数"}, status=status.HTTP_400_BAD_REQUEST)
        
        results = {
            'success': [],
            'failed': [],
            'details': {}
        }
        
        try:
            with transaction.atomic():  # 添加事务支持
                # 首先刷新获取最新的设备数据
                devices = Device.objects.filter(id__in=device_ids).select_for_update()
                print(f"\n找到{devices.count()}个设备")
                updated_count = 0
                
                for device in devices:
                    try:
                        print(f"\n正在更新设备: {device.name} (ID: {device.id})")
                        
                        # 计算需要更新的字段
                        updates_needed = {}
                        
                        # 检查运行状态是否需要更新
                        if 'running' in control_data:
                            new_status = 'running' if control_data['running'] else 'stopped'
                            if new_status != device.status:
                                updates_needed['status'] = new_status
                        
                        # 检查温度是否需要更新
                        if 'temp' in control_data:
                            new_temp = float(control_data['temp'])
                            if abs(new_temp - device.set_temp) > 0.01:  # 使用小数点比较
                                updates_needed['temp'] = new_temp
                        
                        # 检查模式是否需要更新
                        if 'mode' in control_data:
                            new_mode = control_data['mode']
                            if new_mode != device.mode:
                                updates_needed['mode'] = new_mode
                        
                        # 检查风速是否需要更新
                        if 'fan_speed' in control_data:
                            new_fan_speed = int(control_data['fan_speed'])
                            if new_fan_speed != device.fan_speed:
                                updates_needed['fan_speed'] = new_fan_speed
                        
                        print("需要更新的字段:", updates_needed)
                        
                        # 只有在有需要更新的字段时才进行更新
                        if updates_needed:
                            print("执行更新操作...")
                            # 更新设备状态
                            if 'status' in updates_needed:
                                device.status = updates_needed['status']
                            if 'temp' in updates_needed:
                                device.set_temp = updates_needed['temp']
                            if 'mode' in updates_needed:
                                device.mode = updates_needed['mode']
                            if 'fan_speed' in updates_needed:
                                device.fan_speed = updates_needed['fan_speed']
                            
                            device.save()
                            print("设备保存成功")
                            
                            # 创建状态历史记录
                            DeviceStatus.objects.create(
                                device=device,
                                current_temp=device.current_temp,
                                set_temp=device.set_temp,
                                status=device.status,
                                mode=device.mode,
                                fan_speed=device.fan_speed,  # 添加风速记录
                                change_type='batch'  # 添加更改类型
                            )
                            print("状态历史记录创建成功")
                            
                            updated_count += 1
                            results['success'].append(device.id)
                        else:
                            print("没有需要更新的字段，跳过更新")
                            results['details'][device.id] = "无需更新"
                            
                    except Exception as e:
                        print(f"更新设备 {device.id} 失败: {str(e)}")
                        results['failed'].append(device.id)
                        results['details'][device.id] = str(e)
                
                # 重新获取设备列表并序列化
                updated_devices = Device.objects.filter(id__in=device_ids)
                print("\n最终的设备状态:")
                for device in updated_devices:
                    print(f"设备 {device.name}: 状态={device.status}, 温度={device.set_temp}, 模式={device.mode}, 风速={device.fan_speed}")
                
                serializer = DeviceSerializer(updated_devices, many=True)
                
                print("\n=== 批量控制请求完成 ===")
                return Response({
                    "message": f"成功更新{len(results['success'])}个设备，失败{len(results['failed'])}个设备",
                    "results": results,
                    "devices": serializer.data
                })
                
        except Exception as e:
            print(f"\n批量控制失败: {str(e)}")
            return Response({
                "error": f"控制失败：{str(e)}",
                "results": results
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        print("\n=== 设备更新请求开始 ===")
        print("请求数据:", request.data)
        print("设备ID:", kwargs.get('pk'))
        
        try:
            instance = self.get_object()
            print("当前设备信息:", {
                'id': instance.id,
                'name': instance.name,
                'device_id': instance.device_id,
                'floor_id': instance.floor.id if instance.floor else None,
                'set_temp': instance.set_temp,
                'mode': instance.mode,
                'status': instance.status
            })
            
            serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
            print("序列化器:", serializer.__class__.__name__)
            
            if serializer.is_valid():
                print("验证通过的数据:", serializer.validated_data)
                self.perform_update(serializer)
                print("更新后的设备信息:", {
                    'id': instance.id,
                    'name': instance.name,
                    'device_id': instance.device_id,
                    'floor_id': instance.floor.id if instance.floor else None,
                    'set_temp': instance.set_temp,
                    'mode': instance.mode,
                    'status': instance.status
                })
                return Response(serializer.data)
            else:
                print("验证错误:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print("更新过程中出现错误:", str(e))
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            print("=== 设备更新请求结束 ===\n")

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        """按公司筛选设备"""
        company_id = request.query_params.get('company_id')
        if company_id:
            devices = Device.objects.filter(company_id=company_id)
            serializer = DeviceSerializer(devices, many=True)
            return Response(serializer.data)
        return Response({"error": "missing company_id parameter"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """按部门筛选设备"""
        department_id = request.query_params.get('department_id')
        if department_id:
            devices = Device.objects.filter(department_id=department_id)
            serializer = DeviceSerializer(devices, many=True)
            return Response(serializer.data)
        return Response({"error": "missing department_id parameter"}, status=status.HTTP_400_BAD_REQUEST)

class BuildingViewSet(viewsets.ModelViewSet):
    """建筑视图集"""
    queryset = Building.objects.all()
    serializer_class = BuildingTreeSerializer
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取建筑和楼层的树形结构"""
        print("\n=== 开始生成建筑树形结构 ===")
        
        buildings = Building.objects.prefetch_related('floors').all()
        print(f"\n查询到的建筑数量: {buildings.count()}")
        
        for building in buildings:
            print(f"\n建筑: {building.name} (ID: {building.id})")
            floors = building.floors.all()
            print(f"  楼层数量: {floors.count()}")
            for floor in floors:
                print(f"  - {floor.name} (ID: {floor.id}, 楼层号: {floor.floor_number})")
        
        serializer = BuildingTreeSerializer(buildings, many=True)
        data = serializer.data
        print("\n序列化后的数据:")
        for building in data:
            print(f"\n建筑: {building['label']} (ID: {building['id']})")
            for floor in building['children']:
                print(f"  - {floor['label']} (ID: {floor['id']}, 楼层号: {floor.get('floor_number')})")
        
        # 确保返回的是列表
        if not isinstance(data, list):
            data = [data]
            
        return Response(data)

# 重命名为DeviceFilterViewSet以避免与上面的DeviceViewSet冲突
class DeviceFilterViewSet(viewsets.ModelViewSet):
    """设备筛选视图集"""
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    
    def list(self, request, *args, **kwargs):
        """重写list方法以支持多条件筛选"""
        print("\n=== 开始设备查询 ===")
        queryset = self.get_queryset()
        building_id = self.request.query_params.get('building_id')
        floor_id = self.request.query_params.get('floor_id')
        name = self.request.query_params.get('name')
        status = self.request.query_params.get('status')
        company_id = self.request.query_params.get('company_id')
        department_id = self.request.query_params.get('department_id')
        uuid = self.request.query_params.get('uuid')
        device_id = self.request.query_params.get('device_id')
        
        print(f"查询参数: building_id={building_id}, floor_id={floor_id}, name={name}, "
              f"status={status}, company_id={company_id}, department_id={department_id}, "
              f"uuid={uuid}, device_id={device_id}")
        
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        
        if floor_id:
            try:
                floor = Floor.objects.filter(id=floor_id).first()
                if floor:
                    queryset = queryset.filter(floor_id=floor.id)
                    print(f"按楼层ID {floor.id} 筛选设备")
            except Exception as e:
                print(f"楼层筛选出错: {str(e)}")
        
        if name:
            queryset = queryset.filter(name__icontains=name)
            print(f"按名称'{name}'筛选设备")
        
        if status:
            queryset = queryset.filter(status=status)
            print(f"按状态'{status}'筛选设备")
            
        if company_id:
            queryset = queryset.filter(company_id=company_id)
            
        if department_id:
            queryset = queryset.filter(department_id=department_id)
            
        if uuid:
            queryset = queryset.filter(uuid__uuid=uuid)
            print(f"按UUID '{uuid}' 筛选设备")
            
        if device_id:
            queryset = queryset.filter(device_id=device_id)
            print(f"按设备ID '{device_id}' 筛选设备")
        
        # 预加载相关数据
        queryset = queryset.select_related(
            'company', 'department', 'building', 'floor', 'uuid'
        )
        
        # 序列化数据
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        
        print(f"\n查询到 {len(response_data)} 个设备")
        print("=== 设备查询完成 ===\n")
        
        return Response(response_data)

@api_view(['GET'])
def device_list(request):
    """设备列表API，支持按楼层和建筑筛选"""
    queryset = Device.objects.all()
    
    # 获取筛选参数
    building_id = request.query_params.get('building_id')
    floor_id = request.query_params.get('floor_id')
    name = request.query_params.get('name')
    status = request.query_params.get('status')
    
    # 应用筛选条件
    if floor_id:
        try:
            # 先从Floor表获取floor_number
            floor = Floor.objects.filter(id=floor_id).first()
            if floor:
                queryset = queryset.filter(floor_id=floor.floor_number)
            else:
                return Response({"error": f"未找到ID为{floor_id}的楼层"}, status=400)
        except Exception as e:
            return Response({"error": f"楼层筛选出错: {str(e)}"}, status=400)
    
    if building_id:
        queryset = queryset.filter(building_id=building_id)
    
    if name:
        queryset = queryset.filter(name__icontains=name)
    
    if status:
        queryset = queryset.filter(status=status)
    
    # 序列化并返回结果
    serializer = DeviceSerializer(queryset, many=True)
    return Response(serializer.data)

class CompanyViewSet(viewsets.ModelViewSet):
    """公司视图集"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    """部门视图集"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    
    @action(detail=False, methods=['get'])
    def by_company(self, request):
        """按公司筛选部门"""
        company_id = request.query_params.get('company_id')
        if company_id:
            departments = Department.objects.filter(company_id=company_id)
            serializer = DepartmentSerializer(departments, many=True)
            return Response(serializer.data)
        return Response({"error": "missing company_id parameter"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_building_tree(request):
    """获取楼栋-楼层树形结构"""
    buildings = Building.objects.all()
    serializer = BuildingTreeSerializer(buildings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_company_tree(request):
    """获取公司-部门树形结构"""
    companies = Company.objects.all()
    serializer = CompanyTreeSerializer(companies, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_gateway_tree(request):
    """获取网关-设备树形结构"""
    try:
        print("\n=== 开始生成网关树 ===")
        # 获取所有不重复的UUID，排除空值
        unique_topics = Topic.objects.all()
        
        print(f"找到的唯一Topic数量: {unique_topics.count()}")
        
        # 构建网关树
        gateway_tree = []
        for topic in unique_topics:
            # 获取该UUID下的所有设备
            devices = Device.objects.filter(uuid=topic)
            device_count = devices.count()
            print(f"\nUUID: {topic.uuid}, 设备数量: {device_count}")
            
            if device_count > 0:
                gateway_node = {
                    'id': topic.uuid,
                    'label': f"{topic.uuid}",
                    'type': 'gateway',
                    'topic': {
                        'subscribe': topic.subscribe_topic,
                        'publish': topic.publish_topic
                    },
                    'children': []
                }
                
                # 添加该UUID下的所有设备
                for device in devices:
                    device_node = {
                        'id': str(device.id),
                        'label': device.name or device.device_id,
                        'type': 'device',
                        'status': device.status,
                        'uuid': topic.uuid,
                        'device_id': device.device_id,
                        'current_temp': device.current_temp,
                        'set_temp': device.set_temp,
                        'mode': device.mode,
                        'fan_speed': device.fan_speed
                    }
                    gateway_node['children'].append(device_node)
                    print(f"添加设备: {device.name or device.device_id}")
                
                gateway_tree.append(gateway_node)
        
        print("\n=== 网关树生成完成 ===")
        print(f"总网关数量: {len(gateway_tree)}")
        return Response(gateway_tree)
        
    except Exception as e:
        print(f"获取网关树失败: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_all_trees(request):
    """获取所有组织架构树形结构"""
    try:
        print("\n=== 开始生成所有树形结构 ===")
        buildings = Building.objects.all()
        companies = Company.objects.all()
        
        # 获取所有不重复的UUID
        unique_topics = Topic.objects.all()
        
        print(f"找到的唯一Topic数量: {unique_topics.count()}")
        
        # 构建网关树
        gateway_tree = []
        for topic in unique_topics:
            # 获取该UUID下的所有设备
            devices = Device.objects.filter(uuid=topic)
            device_count = devices.count()
            print(f"\nUUID: {topic.uuid}, 设备数量: {device_count}")
            
            if device_count > 0:
                gateway_node = {
                    'id': topic.uuid,
                    'label': f"{topic.uuid}",
                    'type': 'gateway',
                    'topic': {
                        'subscribe': topic.subscribe_topic,
                        'publish': topic.publish_topic
                    },
                    'children': []
                }
                
                # 添加该UUID下的所有设备
                for device in devices:
                    device_node = {
                        'id': str(device.id),
                        'label': device.name or device.device_id,
                        'type': 'device',
                        'status': device.status,
                        'uuid': topic.uuid,
                        'device_id': device.device_id,
                        'current_temp': device.current_temp,
                        'set_temp': device.set_temp,
                        'mode': device.mode,
                        'fan_speed': device.fan_speed
                    }
                    gateway_node['children'].append(device_node)
                    print(f"添加设备: {device.name or device.device_id}")
                
                gateway_tree.append(gateway_node)

        building_tree = BuildingTreeSerializer(buildings, many=True).data
        company_tree = CompanyTreeSerializer(companies, many=True).data

        print("\n=== 树形结构生成完成 ===")
        print(f"建筑数量: {len(building_tree)}")
        print(f"公司数量: {len(company_tree)}")
        print(f"网关数量: {len(gateway_tree)}")
        
        return Response({
            'building_tree': building_tree,
            'company_tree': company_tree,
            'gateway_tree': gateway_tree
        })
    except Exception as e:
        print(f"获取组织架构数据失败: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def search_topic(request):
    """根据UUID搜索Topic"""
    uuid = request.GET.get('uuid')
    if not uuid:
        return Response({"error": "UUID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        topic = Topic.objects.get(uuid=uuid)
        return Response({
            "subscribe_topic": topic.subscribe_topic,
            "publish_topic": topic.publish_topic,
            "description": topic.description
        })
    except Topic.DoesNotExist:
        return Response({"topic": None}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def create_or_update_topic(request):
    """创建或更新Topic"""
    uuid = request.data.get('uuid')
    subscribe_topic = request.data.get('subscribe_topic')
    publish_topic = request.data.get('publish_topic')
    description = request.data.get('description')

    if not uuid or (not subscribe_topic and not publish_topic):
        return Response({
            "error": "UUID and at least one topic (subscribe or publish) are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 尝试查找现有的Topic
        topic_obj, created = Topic.objects.update_or_create(
            uuid=uuid,
            defaults={
                'subscribe_topic': subscribe_topic,
                'publish_topic': publish_topic,
                'description': description
            }
        )

        return Response({
            'success': True,
            'created': created,
            'topic': {
                'uuid': topic_obj.uuid,
                'subscribe_topic': topic_obj.subscribe_topic,
                'publish_topic': topic_obj.publish_topic,
                'description': topic_obj.description
            }
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def topic_list(request):
    """获取所有不重复的Topic列表"""
    try:
        topics = Topic.get_topics()
        return Response(list(topics))
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
