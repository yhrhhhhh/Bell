import requests


# 1. 登录获取 Token
def get_auth_token():
	login_url = "http://127.0.0.1:8000/user/login/"  # 替换为你的登录接口URL
	login_data = {
		"username": "Exoa",  # 替换为实际用户名
		"password": "123456"  # 替换为实际密码
	}
	try:
		response = requests.post(login_url, json=login_data)
		response.raise_for_status()  # 检查请求是否成功
		token = response.json()["token"]  # 从响应中提取 token
		print(f"获取 Token 成功: {token}")
		return token
	except Exception as e:
		print(f"登录失败: {e}")
		return None


# 2. 测试需要认证的接口（示例：send_command）
def test_protected_api(token):
	url = "http://127.0.0.1:8000/api/device/send/"  # 替换为你的接口URL
	headers = {
		"Authorization": f"{token}",  # JWT Token 的固定格式
		"Content-Type": "application/json"
	}
	#  下发属性property:"onOff": 开关, "tempSet": 温度设定, "workMode": 工作模式, "fanSpeed": 风速,
	data = {
		"property": "onOff",
		"uuid": "fa000001400001240240614000100317",  # 替换为你的设备UUID
		"device_id": "1-3-1-0",  # 替换为你的设备ID
		"value": 'running' # 根据属性填写
	}
	try:
		response = requests.post(url, json=data, headers=headers)
		print("\n测试结果:")
		print(f"状态码: {response.status_code}")
		print(f"响应内容: {response.text}")
	except Exception as e:
		print(f"请求失败: {e}")


def test_get_api(token):
	url = "http://127.0.0.1:8000/api/device/update_status/"
	headers = {"Authorization": f"{token}"}
	try:
		response = requests.get(url, headers=headers)
		print(response.text)
	except Exception as e:
		print(f"请求失败: {e}")


# 主流程
if __name__ == "__main__":
	# 第一步：获取 Token
	token = get_auth_token()
	if token:
		# 第二步：测试需要认证的接口
		test_protected_api(token)
		# test_get_api(token)
