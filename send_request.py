import requests
import os
import json
import traceback
import time
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
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 请求状态码: {response.status_code}")
    # 记录GitHub Actions环境检查
    if 'GITHUB_ENV' in os.environ:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GitHub Actions环境检测: 已确认")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GITHUB_ENV路径: {os.environ['GITHUB_ENV']}")
        # 检查文件权限
        try:
            env_file = os.environ['GITHUB_ENV']
            if os.path.exists(env_file):
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GITHUB_ENV文件存在，大小: {os.path.getsize(env_file)} 字节")
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GITHUB_ENV文件权限: r={os.access(env_file, os.R_OK)}, w={os.access(env_file, os.W_OK)}")
            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GITHUB_ENV文件不存在，但环境变量已设置")
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 检查GITHUB_ENV文件时出错: {e}")
    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GitHub Actions环境检测: 未检测到，当前环境变量: {list(os.environ.keys())[:5]}...")
    
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
                github_env_path = os.environ['GITHUB_ENV']
                print(f"在GitHub Actions环境中，尝试写入{github_env_path}")
                try:
                    # 将token写入GitHub环境变量SQL_TOKEN
                    with open(github_env_path, 'a') as f:
                        f.write(f"SQL_TOKEN={sql_token}\n")
                    # 强制刷新文件缓冲区
                    f.flush()
                    os.fsync(f.fileno())
                    print(f"成功更新SQL_TOKEN环境变量")
                except Exception as e:
                    print(f"写入GITHUB_ENV文件时出错: {e}")
                    print(f"GITHUB_ENV路径: {github_env_path}")
                    print(f"尝试写入的内容: SQL_TOKEN={sql_token[:8]}...")  # 只显示token的前几个字符
                    # 继续执行，不中断流程
            else:
                print("不在GitHub Actions环境中，跳过环境变量写入")
                # 在非GitHub环境中，可以将token保存到临时文件供测试使用
                try:
                    with open('sql_token.txt', 'w') as f:
                        f.write(sql_token)
                    print(f"已将token保存到sql_token.txt文件中供本地测试")
                except:
                    pass
            
            print("请求处理完成，成功获取token")
            exit(0)  # 成功退出
        else:
            # 打印详细的错误信息
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 响应中未找到有效的token")
        if isinstance(json_data, dict):
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 响应字典结构: {list(json_data.keys())}")
            if 'errorMessage' in json_data:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误信息: {json_data['errorMessage']}")
            if 'errorCode' in json_data:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误代码: {json_data['errorCode']}")
            if json_data.get('success') is False:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 请求失败: success=false")
            if 'data' in json_data:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] data字段类型: {type(json_data['data'])}")
                if isinstance(json_data['data'], dict):
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] data字段结构: {list(json_data['data'].keys())}")
            
    except json.JSONDecodeError:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 警告: 无法解析JSON响应")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 响应内容: {response.text[:500]}..." if len(response.text) > 500 else response.text)
    
    # 检查状态码
    if response.status_code != 200:
        print(f"警告: 请求返回非200状态码 {response.status_code}")

    print("请求处理完成，但未能成功获取token")
    exit(1)  # 未获取到token，退出码为1
        
except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 请求失败: {e}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误详情: {traceback.format_exc()}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 响应状态: {e.response.status_code}")
            try:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 响应内容: {e.response.text[:500]}..." if len(e.response.text) > 500 else e.response.text)
            except Exception as inner_e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 无法打印响应内容: {inner_e}")
        exit(1)

except Exception as e:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 发生未预期的错误: {e}")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误详情: {traceback.format_exc()}")
    exit(1)