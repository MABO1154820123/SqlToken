import requests
import os
import json
from urllib.parse import urlencode

# SqlToken接口地址
url = "https://client.sqlpub.com/api/connection"

# 数据库连接配置
connection_config = {
    'host': '127.0.0.1',
    'port': '3306',
    'dbName': 'app_info',
    'dbUser': 'mb1154820',
    'password': 'pJbkyzeYJX1bQKTt'
}

# 准备请求头
headers = {
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
}

# 发送POST请求获取SQL Token
try:
    response = requests.post(url, headers=headers, data=urlencode(connection_config))
    response.raise_for_status()  # 确保请求成功
    
    # 解析JSON响应
    json_data = response.json()
    
    # 提取token字段
    if 'token' in json_data:
        sql_token = json_data['token']
        
        # 将token写入GitHub环境变量SQL_TOKEN
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"SQL_TOKEN={sql_token}\n")
        
        print(f"Successfully updated SQL_TOKEN variable")
    else:
        print("Error: 'token' field not found in response")
        print(f"Response data: {json_data}")
        exit(1)
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response status: {e.response.status_code}")
        try:
            print(f"Response content: {e.response.text}")
        except:
            print("Unable to print response content")
    exit(1)