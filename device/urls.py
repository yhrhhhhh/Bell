from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BuildingViewSet, DeviceFilterViewSet
from . import views

router = DefaultRouter()
router.register(r'building', BuildingViewSet)
router.register(r'filter', DeviceFilterViewSet, basename='device-filter')

urlpatterns = [
    path('', include(router.urls)),
    path('list/', views.device_list, name='device-list'),
]
