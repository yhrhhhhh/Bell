import json
import time
from copy import deepcopy
from django.http import JsonResponse, HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction  # 添加事务导入
from .models import Device, DeviceStatus, Building, Floor, Company, Department, Topic
from .mqtt_client import mqtt_client, logger
from django.views.decorators.csrf import csrf_exempt
from .serializers import (
    DeviceSerializer, DeviceStatusSerializer, DeviceCreateSerializer,
    DeviceUpdateSerializer, BuildingTreeSerializer, CompanySerializer,
    DepartmentSerializer, CompanyTreeSerializer, GatewayTreeSerializer,
    FloorSerializer, BuildingSerializer
)
from urllib.parse import quote
from io import BytesIO
import xlwt


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
        logger.info("\n=== 批量控制请求开始 ===")
        logger.info(f"请求数据: {request.data}")

        device_ids = request.data.get('device_ids', [])
        control_data = request.data.get('control', {})

        logger.info(f"设备IDs: {device_ids}")
        logger.info(f"控制数据: {control_data}")

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
            # 获取所有需要控制的设备
            devices = Device.objects.filter(id__in=device_ids).select_related('uuid')
            logger.info(f"查询到的设备数量: {devices.count()}")

            if not devices.exists():
                logger.error(f"未找到指定ID的设备: {device_ids}")
                return Response({"error": "未找到指定的设备"}, status=status.HTTP_404_NOT_FOUND)

            # 按UUID分组设备，以便批量下发
            devices_by_uuid = {}
            for device in devices:
                logger.info(f"处理设备: ID={device.id}, Name={device.name}, UUID={device.uuid}")

                if not device.uuid:
                    error_msg = "设备未绑定UUID"
                    logger.error(f"设备 {device.id} {error_msg}")
                    results['failed'].append(device.id)
                    results['details'][device.id] = error_msg
                    continue

                if device.uuid.uuid not in devices_by_uuid:
                    devices_by_uuid[device.uuid.uuid] = {
                        'publish_topic': device.uuid.publish_topic,
                        'devices': []
                    }
                devices_by_uuid[device.uuid.uuid]['devices'].append(device)

            # 对每个UUID下的设备进行批量控制
            for uuid, data in devices_by_uuid.items():
                device_ids_list = [device.device_id for device in data['devices']]
                publish_topic = data['publish_topic']

                logger.info(f"准备发送控制命令到UUID: {uuid}")
                logger.info(f"发布主题: {publish_topic}")
                logger.info(f"设备列表: {device_ids_list}")

                # 构建MQTT payload
                payload = {
                    "sn": 12,
                    "cmd": "control_write",
                    "uuid": uuid,
                    "body": {
                        "addrs": device_ids_list,
                    }
                }

                # 根据控制数据添加相应的控制字段
                device_status_convert_dict = {
                    "fa000001400001240240614000100308": {
                        "onOff": {"running": 1, "stopped": 0},
                        "workMode": {"auto": 0, "cooling": 1, "heating": 2, "fan": 3, "dehumidify": 4},
                        "fanSpeed": {}
                    },
                    "fa000001400001240240614000100317": {
                        "onOff": {"running": 1, "stopped": 0},
                        "workMode": {"auto": 0, "cooling": 1, "heating": 2, "fan": 3, "dehumidify": 4},
                        "fanSpeed": {}
                    }
                }

                if uuid not in device_status_convert_dict:
                    error_msg = f"设备UUID {uuid} 不在状态转换字典中"
                    logger.error(error_msg)
                    for device in data['devices']:
                        results['failed'].append(device.id)
                        results['details'][device.id] = error_msg
                    continue

                # 添加控制参数
                try:
                    if 'running' in control_data:
                        payload["body"]["onOff"] = device_status_convert_dict[uuid]["onOff"][
                            "running" if control_data['running'] else "stopped"]
                    if 'temp' in control_data:
                        payload["body"]["tempSet"] = float(control_data['temp'])
                    if 'mode' in control_data:
                        payload["body"]["workMode"] = device_status_convert_dict[uuid]["workMode"][control_data['mode']]
                    if 'fan_speed' in control_data:
                        payload["body"]["fanSpeed"] = int(control_data['fan_speed'])
                except Exception as e:
                    error_msg = f"构建控制参数失败: {str(e)}"
                    logger.error(error_msg)
                    for device in data['devices']:
                        results['failed'].append(device.id)
                        results['details'][device.id] = error_msg
                    continue

                # 发送MQTT消息
                try:
                    logger.info(f"下发批量控制命令: {payload}, topic: {publish_topic}")
                    mqtt_client.publish(publish_topic, json.dumps(payload))

                    # 添加到成功列表
                    for device in data['devices']:
                        results['success'].append(device.id)

                    # 发送状态查询命令
                    time.sleep(2)  # 等待2秒后查询状态
                    query_payload = {
                        "sn": 11,
                        "cmd": "status_read",
                        "uuid": uuid,
                        "body": {
                            "cmd": "addrs",
                            "addrs": device_ids_list
                        }
                    }
                    mqtt_client.publish(publish_topic, json.dumps(query_payload))

                except Exception as e:
                    error_msg = f"MQTT发送失败: {str(e)}"
                    logger.error(error_msg)
                    for device in data['devices']:
                        results['failed'].append(device.id)
                        results['details'][device.id] = error_msg

            # 获取更新后的设备列表
            updated_devices = Device.objects.filter(id__in=device_ids)
            serializer = DeviceSerializer(updated_devices, many=True)

            logger.info("\n=== 批量控制请求完成 ===")
            logger.info(f"成功: {len(results['success'])}个, 失败: {len(results['failed'])}个")
            return Response({
                "message": f"成功发送{len(results['success'])}个设备的控制命令，失败{len(results['failed'])}个设备",
                "results": results,
                "devices": serializer.data
            })

        except Exception as e:
            logger.error(f"\n批量控制失败: {str(e)}")
            return Response({
                "error": f"控制失败：{str(e)}",
                "results": results
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))

            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    serializer_class = BuildingSerializer  # 修改默认序列化器

    def get_serializer_class(self):
        """根据不同的action返回不同的序列化器"""
        if self.action == 'tree':
            return BuildingTreeSerializer
        return BuildingSerializer

    def destroy(self, request, *args, **kwargs):
        """删除建筑时，将关联设备的building字段设为null"""
        building = self.get_object()
        # 获取关联的设备
        devices = Device.objects.filter(building=building)
        # 将设备的building字段设为null
        devices.update(building=None)
        # 删除建筑（会自动删除关联的楼层，因为是CASCADE关系）
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def floors(self, request, pk=None):
        """获取指定建筑的楼层列表"""
        building = self.get_object()
        floors = Floor.objects.filter(building=building)
        serializer = FloorSerializer(floors, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取建筑和楼层的树形结构"""
        buildings = Building.objects.prefetch_related('floors').all()
        serializer = BuildingTreeSerializer(buildings, many=True)
        return Response(serializer.data)


class FloorViewSet(viewsets.ModelViewSet):
    """楼层视图集"""
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer

    def destroy(self, request, *args, **kwargs):
        """删除楼层时，将关联设备的floor字段设为null"""
        floor = self.get_object()
        # 获取关联的设备
        devices = Device.objects.filter(floor=floor)
        # 将设备的floor字段设为null
        devices.update(floor=None)
        # 删除楼层
        return super().destroy(request, *args, **kwargs)


class CompanyViewSet(viewsets.ModelViewSet):
    """公司视图集"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def destroy(self, request, *args, **kwargs):
        """删除公司时，将关联设备的company字段设为null"""
        company = self.get_object()
        # 获取关联的设备
        devices = Device.objects.filter(company=company)
        # 将设备的company字段设为null
        devices.update(company=None, department=None)
        # 删除公司（会自动删除关联的部门，因为是CASCADE关系）
        return super().destroy(request, *args, **kwargs)


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门视图集"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def destroy(self, request, *args, **kwargs):
        """删除部门时，将关联设备的department字段设为null"""
        department = self.get_object()
        # 获取关联的设备
        devices = Device.objects.filter(department=department)
        # 将设备的department字段设为null
        devices.update(department=None)
        # 删除部门
        return super().destroy(request, *args, **kwargs)

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
        unique_topics = Topic.objects.all()
        gateway_tree = []

        for topic in unique_topics:
            devices = Device.objects.filter(uuid=topic)
            device_count = devices.count()

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

                gateway_tree.append(gateway_node)

        return Response(gateway_tree)

    except Exception as e:
        logger.error(f"获取网关树失败: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_all_trees(request):
    """获取所有组织架构树形结构"""
    try:
        buildings = Building.objects.all()
        companies = Company.objects.all()
        unique_topics = Topic.objects.all()

        # 构建网关树
        gateway_tree = []
        for topic in unique_topics:
            devices = Device.objects.filter(uuid=topic)
            device_count = devices.count()

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

                gateway_tree.append(gateway_node)

        building_tree = BuildingTreeSerializer(buildings, many=True).data
        company_tree = CompanyTreeSerializer(companies, many=True).data

        return Response({
            'building_tree': building_tree,
            'company_tree': company_tree,
            'gateway_tree': gateway_tree
        })
    except Exception as e:
        logger.error(f"获取组织架构数据失败: {str(e)}")
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


@api_view(['GET'])
def get_uuid_topics(request):
    """获取所有UUID和对应的Topic信息"""
    try:
        topics = Topic.objects.all()
        topic_list = []
        for topic in topics:
            topic_list.append({
                'uuid': topic.uuid,
                'subscribe_topic': topic.subscribe_topic,
                'publish_topic': topic.publish_topic
            })
        return Response({
            'code': 200,
            'data': topic_list
        })
    except Exception as e:
        return Response({
            'code': 500,
            'error': str(e)
        })


@api_view(["POST"])
def send_command(request):
    """单个设备、单个属性 下发"""
    if request.method == 'POST':
        try:
            issue_property = request.data.get('property')
            uuid = request.data.get('uuid')
            device_id = request.data.get('device_id')
            value = request.data.get('value')
            if not (device_id and uuid):
                return JsonResponse({"error": "device_id or uuid is missing"}, status=400)

            device_status_convert_dict = {
                "fa000001400001240240614000100308": {"onOff": {"running": 1, "stopped": 0, },
                                                     "workMode": {"auto": 0, "cooling": 1, "heating": 2, "fan": 3,
                                                                  "dehumidify": 4, }, "fanSpeed": {}, },
                "fa000001400001240240614000100317": {"onOff": {"running": 1, "stopped": 0, },
                                                     "workMode": {"auto": 0, "cooling": 1, "heating": 2, "fan": 3,
                                                                  "dehumidify": 4, }, "fanSpeed": {}, },
                "fa000001400001240240615000100165": {"onOff": {"running": 1, "stopped": 0, },
                                                     "workMode": {"auto": 0, "cooling": 1, "heating": 2, "fan": 3,
                                                                  "dehumidify": 4, }, "fanSpeed": {}, },
                "example_0": {"onOff": {"running": 0, "stopped": 1, },
                              "workMode": {"auto": 0, "cooling": 1, "heating": 2, "fan": 3, "dehumidify": 4, },
                              "fanSpeed": {}, }}

            # 检查设备是否存在
            try:
                device = (
                    Device.objects
                    .filter(uuid__uuid=uuid, device_id=device_id)
                    .select_related('uuid')
                    .only('uuid__publish_topic', 'name', 'status')
                    .first()
                )
                if not device:
                    return JsonResponse({"error": "Device not found"}, status=404)

                topic = device.uuid.publish_topic
            except Exception as e:
                logger.error(f"查询设备失败: {str(e)}")
                return JsonResponse({"error": "Failed to query device"}, status=500)

            # 构造控制命令
            payload = {
                "sn": 12,
                "cmd": "control_write",
                "uuid": uuid,
                "body": {
                    "addrs": [f"{device_id}", ],
                }
            }
            if issue_property == "fanSpeed":
                payload["body"][f"{issue_property}"] = int(value)
            elif issue_property == "tempSet":
                payload["body"][f"{issue_property}"] = float(value)
            else:
                payload["body"][f"{issue_property}"] = device_status_convert_dict[f"{uuid}"][f"{issue_property}"][
                    f"{value}"]

            topic_publish = (
                Device.objects
                .filter(uuid__uuid=uuid, device_id=device_id)
                .select_related('uuid')
                .only('uuid__publish_topic')
                .first()
            )
            topic = topic_publish.uuid.publish_topic
            logger.info(f"下发命令: {payload}, topic: {topic}")
            payload_json = json.dumps(payload)
            mqtt_client.publish(topic, payload_json)
            return JsonResponse({'status': 'Command has been issued to the device.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@api_view(['GET'])
def query_all_device_status(request):
    """查询所有设备状态"""
    try:
        # 获取所有不重复的UUID
        uuids = Topic.objects.values_list('uuid', flat=True).distinct()

        for uuid_current in uuids:
            # 构造消息
            message = {
                "sn": 11,  # 序列号
                "cmd": "status_read",
                "uuid": uuid_current,
                "body": {
                    "cmd": "addrs",
                    "addrs": ["1-3-1-0"]  # 固定地址格式
                }
            }

            # 获取发布主题
            try:
                topic = Topic.objects.get(uuid=uuid_current)
                publish_topic = topic.publish_topic

                # 发布消息
                logger.info(f"正在查询设备状态: UUID={uuid_current}")
                mqtt_client.publish(publish_topic, message)

            except Topic.DoesNotExist:
                logger.error(f"找不到UUID对应的Topic: {uuid_current}")
            except Exception as e:
                logger.error(f"发送状态查询命令失败: {str(e)}")
                continue

        return Response({"message": "状态查询命令已发送"})

    except Exception as e:
        logger.error(f"查询设备状态失败: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def export_devices_excel(request):
    """导出设备列表到CSV"""
    try:
        # 创建响应
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="devices.csv"'

        # 获取所有设备信息
        devices = Device.objects.select_related(
            'uuid',
            'floor__building',
            'company',
            'department'
        ).all()

        # 写入表头
        headers = ['网关ID', '内机ID', '内机名称', '建筑', '楼栋', '公司', '部门']
        response.write(','.join(headers) + '\n')

        # 写入数据
        for device in devices:
            row = [
                device.uuid.uuid if device.uuid else '',
                device.device_id or '',
                device.name or '',
                device.floor.building.name if device.floor and device.floor.building else '',
                device.floor.name if device.floor else '',
                device.company.name if device.company else '',
                device.department.name if device.department else ''
            ]
            # 处理可能包含逗号的字段，用双引号包围
            row = ['"' + str(field).replace('"', '""') + '"' for field in row]
            response.write(','.join(row) + '\n')

        return response

    except Exception as e:
        logger.error(f"导出CSV失败: {str(e)}")
        return JsonResponse({'error': '导出失败', 'detail': str(e)}, status=500)


# 重新添加DeviceFilterViewSet
class DeviceFilterViewSet(viewsets.ModelViewSet):
    """设备筛选视图集"""
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    def list(self, request, *args, **kwargs):
        """重写list方法以支持多条件筛选"""
        queryset = self.get_queryset()
        building_id = self.request.query_params.get('building_id')
        floor_id = self.request.query_params.get('floor_id')
        name = self.request.query_params.get('name')
        status = self.request.query_params.get('status')
        company_id = self.request.query_params.get('company_id')
        department_id = self.request.query_params.get('department_id')
        uuid = self.request.query_params.get('uuid')
        device_id = self.request.query_params.get('device_id')

        if building_id:
            queryset = queryset.filter(building_id=building_id)

        if floor_id:
            try:
                floor = Floor.objects.filter(id=floor_id).first()
                if floor:
                    queryset = queryset.filter(floor_id=floor.id)
            except Exception as e:
                logger.error(f"楼层筛选出错: {str(e)}")

        if name:
            queryset = queryset.filter(name__icontains=name)

        if status:
            queryset = queryset.filter(status=status)

        if company_id:
            queryset = queryset.filter(company_id=company_id)

        if department_id:
            queryset = queryset.filter(department_id=department_id)

        if uuid:
            queryset = queryset.filter(uuid__uuid=uuid)

        if device_id:
            queryset = queryset.filter(device_id=device_id)

        # 预加载相关数据
        queryset = queryset.select_related(
            'company', 'department', 'building', 'floor', 'uuid'
        )

        # 序列化数据
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
