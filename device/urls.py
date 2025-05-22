from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'device', views.DeviceViewSet, basename='device')
router.register(r'building', views.BuildingViewSet, basename='building')
router.register(r'filter', views.DeviceFilterViewSet, basename='device-filter')
router.register(r'company', views.CompanyViewSet, basename='company')
router.register(r'department', views.DepartmentViewSet, basename='department')

urlpatterns = [
    path('', include(router.urls)),
    path('building/tree/', views.get_building_tree, name='building_tree'),
    path('company/tree/', views.get_company_tree, name='company_tree'),
    path('gateway/tree/', views.get_gateway_tree, name='gateway_tree'),
    path('all/trees/', views.get_all_trees, name='all_trees'),
]
