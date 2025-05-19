from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
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
