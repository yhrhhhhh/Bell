from django.db import models
from rest_framework import serializers
from datetime import datetime


# Create your models here.
class SysUser(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, verbose_name="用户名")
    password = models.CharField(max_length=100, verbose_name="密码")
    avatar = models.CharField(max_length=255, null=True, verbose_name="用户头像")
    email = models.CharField(max_length=100, null=True, verbose_name="用户邮箱")
    phonenumber = models.CharField(max_length=11, null=True, verbose_name="手机号码")
    login_date = models.DateField(null=True, verbose_name="最后登录时间")
    status = models.IntegerField(null=True, verbose_name="帐号状态（0正常 1停用）")
    create_time = models.DateField(null=True, verbose_name="创建时间", )
    update_time = models.DateField(null=True, verbose_name="更新时间")
    remark = models.CharField(max_length=500, null=True, verbose_name="备注")

    class Meta:
        db_table = "sys_user"


class SysUserSerializer(serializers.ModelSerializer):
    login_date = serializers.SerializerMethodField()
    create_time = serializers.SerializerMethodField()
    update_time = serializers.SerializerMethodField()

    class Meta:
        model = SysUser
        fields = '__all__'

    def get_login_date(self, obj):
        if obj.login_date and isinstance(obj.login_date, datetime):
            return obj.login_date.date()
        return obj.login_date

    def get_create_time(self, obj):
        if obj.create_time and isinstance(obj.create_time, datetime):
            return obj.create_time.date()
        return obj.create_time

    def get_update_time(self, obj):
        if obj.update_time and isinstance(obj.update_time, datetime):
            return obj.update_time.date()
        return obj.update_time
