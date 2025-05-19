from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db import transaction  # 添加事务导入
from .models import Device, DeviceStatus, Building, Floor
from .serializers import DeviceSerializer, DeviceStatusSerializer, DeviceCreateSerializer, DeviceUpdateSerializer, BuildingTreeSerializer


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
                            
                            device.save()
                            print("设备保存成功")
                            
                            # 创建状态历史记录
                            DeviceStatus.objects.create(
                                device=device,
                                current_temp=device.current_temp,
                                set_temp=device.set_temp,
                                status=device.status,
                                mode=device.mode,
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
                    print(f"设备 {device.name}: 状态={device.status}, 温度={device.set_temp}, 模式={device.mode}")
                
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
    
    def get_queryset(self):
        queryset = Device.objects.all()
        building_id = self.request.query_params.get('building_id')
        floor_id = self.request.query_params.get('floor_id')
        
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        if floor_id:
            try:
                floor = Floor.objects.filter(id=floor_id).first()
                if floor:
                    queryset = queryset.filter(floor_id=floor.floor_number)
                    print(f"按楼层号{floor.floor_number}筛选设备")
            except Exception as e:
                print(f"楼层筛选出错: {str(e)}")
            
        return queryset

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
