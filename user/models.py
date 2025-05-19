from django.db import models
from rest_framework import serializers
from datetime import datetime


# Create your models here.
class SysUser(models.Model):
    """用户模型"""
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, verbose_name="用户名")
    password = models.CharField(max_length=100, verbose_name="密码")
    avatar = models.ImageField(upload_to='avatar/%Y/%m', null=True, blank=True, verbose_name="用户头像")
    email = models.EmailField(max_length=100, null=True, blank=True, verbose_name="用户邮箱")
    phonenumber = models.CharField(max_length=11, null=True, blank=True, verbose_name="手机号码")
    login_date = models.DateTimeField(null=True, blank=True, verbose_name="最后登录时间")
    status = models.BooleanField(default=True, verbose_name="帐号状态（True正常 False停用）")
    create_time = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="更新时间")
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name="备注")

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户管理"
        db_table = "sys_user"
        ordering = ['-create_time']


class SysUserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    class Meta:
        model = SysUser
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }
