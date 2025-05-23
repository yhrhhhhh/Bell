# Generated by Django 5.1.4 on 2025-05-16 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sysuser",
            options={
                "ordering": ["-create_time"],
                "verbose_name": "用户",
                "verbose_name_plural": "用户管理",
            },
        ),
        migrations.AlterField(
            model_name="sysuser",
            name="avatar",
            field=models.ImageField(
                blank=True, null=True, upload_to="avatar/%Y/%m", verbose_name="用户头像"
            ),
        ),
        migrations.AlterField(
            model_name="sysuser",
            name="create_time",
            field=models.DateTimeField(
                auto_now_add=True, null=True, verbose_name="创建时间"
            ),
        ),
        migrations.AlterField(
            model_name="sysuser",
            name="email",
            field=models.EmailField(
                blank=True, max_length=100, null=True, verbose_name="用户邮箱"
            ),
        ),
        migrations.AlterField(
            model_name="sysuser",
            name="login_date",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="最后登录时间"
            ),
        ),
        migrations.AlterField(
            model_name="sysuser",
            name="phonenumber",
            field=models.CharField(
                blank=True, max_length=11, null=True, verbose_name="手机号码"
            ),
        ),
        migrations.AlterField(
            model_name="sysuser",
            name="remark",
            field=models.CharField(
                blank=True, max_length=500, null=True, verbose_name="备注"
            ),
        ),
        migrations.AlterField(
            model_name="sysuser",
            name="status",
            field=models.BooleanField(
                default=True, verbose_name="帐号状态（True正常 False停用）"
            ),
        ),
        migrations.AlterField(
            model_name="sysuser",
            name="update_time",
            field=models.DateTimeField(
                auto_now=True, null=True, verbose_name="更新时间"
            ),
        ),
    ]
