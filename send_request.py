import requests
import os
import json

# SqlToken接口地址
url = "https://client.sqlpub.com/api/connection"

# 发送请求获取SQL Token
response = requests.get(url)
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