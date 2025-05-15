import json
from datetime import datetime

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from rest_framework_jwt.settings import api_settings

from menu.models import SysMenu, SysMenuSerializer
from bell import settings
from user.models import SysUser, SysUserSerializer


class LoginView(View):

    def buildTreeMenu(self, sysMenuList):
        resultMenuList: list[SysMenu] = list()
        for menu in sysMenuList:
            # 寻找子节点
            for e in sysMenuList:
                if e.parent_id == menu.id:
                    if not hasattr(menu, "children"):
                        menu.children = list()
                    menu.children.append(e)
            # 判断父节点，添加到集合
            if menu.parent_id == 0:
                resultMenuList.append(menu)
        return resultMenuList

    def post(self, request):
        # 从请求体获取JSON数据
        try:
            data = json.loads(request.body.decode('utf-8'))
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                return JsonResponse({'code': 400, 'info': '用户名和密码不能为空！'})
                
            user = SysUser.objects.get(username=username, password=password)
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            # 将用户对象传递进去，获取到该对象的属性值
            payload = jwt_payload_handler(user)
            # 将属性值编码成jwt格式的字符串
            token = jwt_encode_handler(payload)

        except SysUser.DoesNotExist:
            return JsonResponse({'code': 500, 'info': '用户名或者密码错误！'})
        except json.JSONDecodeError:
            return JsonResponse({'code': 400, 'info': '无效的请求格式，期望JSON。'})
        except Exception as e:
            print(f"Login error: {e}")
            return JsonResponse({'code': 500, 'info': '登录时发生错误！'})
            
        return JsonResponse(
            {'code': 200, 'token': token, 'user': SysUserSerializer(user).data, 'info': '登录成功'})

class SaveView(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        if data['id'] == -1:  # 添加
            obj_sysUser = SysUser(username=data['username'], password=data['password'],
                                  email=data['email'], phonenumber=data['phonenumber'],
                                  status=data['status'],
                                  remark=data['remark'])
            obj_sysUser.create_time = datetime.now().date()
            obj_sysUser.avatar = 'default.jpg'
            obj_sysUser.password = "123456"
            obj_sysUser.save()
        else:  # 修改
            obj_sysUser = SysUser(id=data['id'], username=data['username'], password=data['password'],
                                  avatar=data['avatar'], email=data['email'], phonenumber=data['phonenumber'],
                                  login_date=data['login_date'], status=data['status'], create_time=data['create_time'],
                                  update_time=data['update_time'], remark=data['remark'])
            obj_sysUser.update_time = datetime.now().date()
            obj_sysUser.save()
        return JsonResponse({'code': 200})


class ActionView(View):

    def get(self, request):
        """
        根据id获取用户信息
        :param request:
        :return:
        """
        id = request.GET.get("id")
        user_object = SysUser.objects.get(id=id)
        return JsonResponse({'code': 200, 'user': SysUserSerializer(user_object).data})

    def delete(self, request):
        """
        删除操作
        :param request:
        :return:
        """
        idList = json.loads(request.body.decode("utf-8"))
        SysUser.objects.filter(id__in=idList).delete()
        return JsonResponse({'code': 200})


class CheckView(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        username = data['username']
        print("username=", username)
        if SysUser.objects.filter(username=username).exists():
            return JsonResponse({'code': 500})
        else:
            return JsonResponse({'code': 200})


class PwdView(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        id = data['id']
        oldPassword = data['oldPassword']
        newPassword = data['newPassword']
        obj_user = SysUser.objects.get(id=id)
        if obj_user.password == oldPassword:
            obj_user.password = newPassword
            obj_user.update_time = datetime.now().date()
            obj_user.save()
            return JsonResponse({'code': 200})
        else:
            return JsonResponse({'code': 500, 'errorInfo': '原密码错误！'})


class ImageView(View):

    def post(self, request):
        file = request.FILES.get('avatar')
        print("file:", file)
        if file:
            file_name = file.name
            suffixName = file_name[file_name.rfind("."):]
            new_file_name = datetime.now().strftime('%Y%m%d%H%M%S') + suffixName
            file_path = str(settings.MEDIA_ROOT) + "\\userAvatar\\" + new_file_name
            print("file_path:", file_path)
            try:
                with open(file_path, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                return JsonResponse({'code': 200, 'title': new_file_name})
            except:
                return JsonResponse({'code': 500, 'errorInfo': '上传头像失败'})


class AvatarView(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        id = data['id']
        avatar = data['avatar']
        obj_user = SysUser.objects.get(id=id)
        obj_user.avatar = avatar
        obj_user.save()
        return JsonResponse({'code': 200})


class SearchView(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        pageNum = data['pageNum']  # 当前页
        pageSize = data['pageSize']  # 每页大小
        query = data['query']  # 查询参数
        print(pageSize, pageNum)
        userListPage = Paginator(SysUser.objects.filter(username__icontains=query), pageSize).page(pageNum)
        print(userListPage)
        obj_users = userListPage.object_list.values()  # 转成字典
        users = list(obj_users)  # 把外层的容器转成List
        # 不再查询角色信息，添加一个空的roleList
        for user in users:
            user['roleList'] = []
        total = SysUser.objects.filter(username__icontains=query).count()
        return JsonResponse({'code': 200, 'userList': users, 'total': total})


# 重置密码
class PasswordView(View):

    def get(self, request):
        id = request.GET.get("id")
        user_object = SysUser.objects.get(id=id)
        user_object.password = "123456"
        user_object.update_time = datetime.now().date()
        user_object.save()
        return JsonResponse({'code': 200})


# 用户状态修改
class StatusView(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        id = data['id']
        status = data['status']
        user_object = SysUser.objects.get(id=id)
        user_object.status = status
        user_object.save()
        return JsonResponse({'code': 200})
