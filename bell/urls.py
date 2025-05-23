"""
URL configuration for python222_admin3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from rest_framework.routers import DefaultRouter
from device.views import DeviceViewSet
from control.views import ControlCommandViewSet

from bell import settings

# 创建路由器
router = DefaultRouter()
router.register(r'devices', DeviceViewSet)
router.register(r'control', ControlCommandViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),  # 用户模块
    path('menu/', include('menu.urls')),  # 权限模块
    path('api/', include(router.urls)),  # API 路由
    path('api/device/', include('device.urls')),
    path('api/control/', include('control.urls')),
    # 配置媒体文件的路由地址
    re_path('media/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT}, name='media')
]
