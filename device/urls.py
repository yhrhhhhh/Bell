from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceViewSet, BuildingViewSet, CompanyViewSet, DepartmentViewSet,
    DeviceFilterViewSet, get_building_tree, get_company_tree, get_gateway_tree,
    get_all_trees, search_topic, create_or_update_topic, topic_list, get_uuid_topics, send_command,
    query_all_device_status, export_devices_excel
)

router = DefaultRouter()
router.register(r'devices', DeviceViewSet)
router.register(r'buildings', BuildingViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'filter', DeviceFilterViewSet, basename='device-filter')

urlpatterns = [
    path('', include(router.urls)),
    path('building/tree/', get_building_tree, name='building-tree'),
    path('company/tree/', get_company_tree, name='company-tree'),
    path('gateway/tree/', get_gateway_tree, name='gateway-tree'),
    path('all/trees/', get_all_trees, name='all-trees'),
    path('topic/search/', search_topic, name='search-topic'),
    path('topic/create_or_update/', create_or_update_topic, name='create-or-update-topic'),
    path('topic/list/', topic_list, name='topic-list'),
    path('topic/uuid-list/', get_uuid_topics, name='uuid-topics'),
    path('send/', send_command, name='mqtt-send'),
    path('update_status/', query_all_device_status, name='mqtt-query-all-status'),
    path('export/', export_devices_excel, name='export-devices-excel'),
]
