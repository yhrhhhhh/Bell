import json

from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.http import JsonResponse
from .mqtt_client import mqtt_client, logger

@csrf_exempt  # 后续用户认证后可关闭禁用
@require_http_methods(["POST"])
def send_command(request):
    if request.method == 'POST':
        try:
            # 后续添加Django权限检查
            command = request.POST.get('command') # 下发类型
            # payload = request.POST.get('payload')
            topic = settings.MQTT_TOPIC_POST
            payload = {
                "sn": 6,
                "cmd": "status_read",
                "uuid": "fa000001400001240240614000100308",
                "body": {
                    "cmd": "all"
                }
            }
            payload_json = json.dumps(payload)
            mqtt_client.publish(topic, payload_json)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# TODO: 手动拉取更新全部当前状态
