from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'device', views.DeviceViewSet, basename='device')
router.register(r'building', views.BuildingViewSet, basename='building')
router.register(r'filter', views.DeviceFilterViewSet, basename='device-filter')

urlpatterns = [
    path('', include(router.urls)),
]
