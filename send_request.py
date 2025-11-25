import os
import json
import requests
import time

# 核心配置
# 从环境变量获取GitHub Token，工作流文件中已将secrets.TOKEN映射为GITHUB_TOKEN
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_OWNER = 'MABO1154820123'
GITHUB_REPO = 'SqlToken'
SQL_API_URL = 'https://client.sqlpub.com/api/connection'

# 数据库连接配置（从环境变量获取，带默认值）
connection_config = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'dbName': os.environ.get('DB_NAME', 'app_info'),
    'dbUser': os.environ.get('DB_USER', 'mb1154820'),
    'password': os.environ.get('DB_PASSWORD', 'pJbkyzeYJX1bQKTt')
}

def set_github_repo_variable(token, owner, repo, var_name, var_value):
    """使用GitHub API设置仓库变量"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    
    # 先检查变量是否存在
    get_url = f'https://api.github.com/repos/{owner}/{repo}/actions/variables/{var_name}'
    response = requests.get(get_url, headers=headers)
    
    # 根据变量是否存在选择更新或创建
    if response.status_code == 200:
        # 更新现有变量
        url = get_url
        method = 'PATCH'
        print(f"[INFO] 更新GitHub仓库变量: {var_name}")
    else:
        # 创建新变量
        url = f'https://api.github.com/repos/{owner}/{repo}/actions/variables'
        method = 'POST'
        print(f"[INFO] 创建GitHub仓库变量: {var_name}")
    
    # 发送请求
    data = {'name': var_name, 'value': var_value}
    response = requests.request(method, url, headers=headers, json=data)
    
    if response.status_code in [200, 201, 204]:
        print(f"[SUCCESS] 成功{'更新' if method == 'PATCH' else '创建'}变量: {var_name}")
        return True
    else:
        print(f"[ERROR] 设置变量失败: {response.status_code} - {response.text}")
        return False

def main():
    """主函数"""
    print(f"[INFO] 开始执行: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] 目标仓库: {GITHUB_OWNER}/{GITHUB_REPO}")
    
    # 1. 获取SQL Token
    print(f"[INFO] 发送请求到SQL API: {SQL_API_URL}")
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    try:
        response = requests.post(
            SQL_API_URL,
            headers=headers,
            json=connection_config,
            timeout=10
        )
        
        print(f"[INFO] API响应状态: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        if data.get('success') and data.get('data') and 'token' in data['data']:
            sql_token = data['data']['token']
            print(f"[SUCCESS] 成功获取SQL Token")
            
            # 2. 设置到GitHub仓库变量
            if GITHUB_TOKEN:
                success = set_github_repo_variable(
                    token=GITHUB_TOKEN,
                    owner=GITHUB_OWNER,
                    repo=GITHUB_REPO,
                    var_name='SQL_TOKEN',
                    var_value=sql_token
                )
                
                if success:
                    print("[SUCCESS] 任务完成: SQL Token已成功设置到GitHub仓库变量")
                    return 0
                else:
                    print("[ERROR] 任务失败: 无法设置GitHub仓库变量")
                    return 1
            else:
                print("[ERROR] 缺少GITHUB_TOKEN，无法设置仓库变量")
                return 1
        else:
            print(f"[ERROR] API响应中未找到有效token: {data}")
            return 1
    
    except Exception as e:
        print(f"[ERROR] 执行过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
