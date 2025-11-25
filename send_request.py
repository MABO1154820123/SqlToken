import requests
import os
import json
from urllib.parse import urlencode

# SqlToken接口地址
url = "https://client.sqlpub.com/api/connection"

# 数据库连接配置
connection_config = {
    'host':'127.0.0.1',
    'port':3306,
    'dbName':'app_info',
    'dbUser':'mb1154820',
    'password':'pJbkyzeYJX1bQKTt'
}

# 准备请求头（按照tokenTool.js的格式）
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'content-type': 'application/json',  # 使用JSON格式，而不是urlencoded
    'origin': 'https://client.sqlpub.com',
    'referer': 'https://client.sqlpub.com/workbench',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
}

# 发送POST请求获取SQL Token
try:
    print(f"正在发送请求到 {url}")
    # 使用JSON格式发送请求体，设置超时为10秒
    response = requests.post(
        url, 
        headers=headers, 
        data=json.dumps(connection_config),  # 使用json.dumps而不是urlencode
        timeout=10  # 设置超时，类似于tokenTool.js中的AbortSignal.timeout
    )
    
    # 打印请求状态和响应信息用于调试
    print(f"请求状态码: {response.status_code}")
    
    # 解析JSON响应
    try:
        json_data = response.json()
        print(f"响应数据: {json_data}")
        
        # 根据tokenTool.js的响应格式，token在data.token中
        if isinstance(json_data, dict) and json_data.get('success') and json_data.get('data') and 'token' in json_data['data']:
            sql_token = json_data['data']['token']
            print(f"成功获取token: {sql_token}")
            
            # 检查是否在GitHub Actions环境中
            if 'GITHUB_ENV' in os.environ:
                # 将token写入GitHub环境变量SQL_TOKEN
                with open(os.environ['GITHUB_ENV'], 'a') as f:
                    f.write(f"SQL_TOKEN={sql_token}\n")
                print(f"Successfully updated SQL_TOKEN variable")
            
            print("请求处理完成，成功获取token")
            exit(0)  # 成功退出
        else:
            # 打印详细的错误信息
            print("响应中未找到有效的token")
            if isinstance(json_data, dict):
                if 'errorMessage' in json_data:
                    print(f"错误信息: {json_data['errorMessage']}")
                if 'errorCode' in json_data:
                    print(f"错误代码: {json_data['errorCode']}")
                if json_data.get('success') is False:
                    print("请求失败: success=false")
            
    except json.JSONDecodeError:
        print(f"警告: 无法解析JSON响应")
        print(f"响应内容: {response.text}")
    
    # 检查状态码
    if response.status_code != 200:
        print(f"警告: 请求返回非200状态码 {response.status_code}")

    print("请求处理完成，但未能成功获取token")
    exit(1)  # 未获取到token，退出码为1
        
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"响应状态: {e.response.status_code}")
        try:
            print(f"响应内容: {e.response.text}")
        except:
            print("无法打印响应内容")
    exit(1)

except Exception as e:
    print(f"发生未预期的错误: {e}")
    exit(1)