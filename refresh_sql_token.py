#!/usr/bin/env python3
"""
自动检查 SQL 服务是否返回 401，仅在需要时获取新 token 并写入 GitHub 仓库变量 SQL_TOKEN
"""
import os
import sys
import time
import requests

# -------------------- 配置 --------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER") or "MABO1154820123"
GITHUB_REPO  = os.getenv("GITHUB_REPO") or "SqlToken"

# 新接口
CONN_URL = "https://client.sqlpub.com/api/connection"
TEST_URL = "https://client.sqlpub.com/api/database/execute"

# 连接信息
CONN_CFG = {
    "host": "127.0.0.1",
    "port": 3306,
    "dbName": "app_info",
    "dbUser": "mb1154820",
    "password": "pJbkyzeYJX1bQKTt"
}
# ---------------------------------------------


def set_repo_var(token, owner, repo, name, value):
    sess = requests.Session()
    sess.headers.update({
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })
    url_get = f"https://api.github.com/repos/{owner}/{repo}/actions/variables/{name}"
    resp = sess.get(url_get)
    method, url = (("PATCH", url_get) if resp.status_code == 200 else
                   ("POST", f"https://api.github.com/repos/{owner}/{repo}/actions/variables"))
    print(f"[INFO] {'更新' if method == 'PATCH' else '创建'}仓库变量: {name}")
    resp = sess.request(method, url, json={"name": name, "value": value})
    if resp.status_code in (200, 201, 204):
        print(f"[SUCCESS] 变量 {name} 写入完成")
        return True
    print(f"[ERROR] 写入变量失败: {resp.status_code} {resp.text}")
    return False


def need_fresh_token():
    """用 select 1 测试当前 token 是否 401"""
    if not GITHUB_OWNER or not GITHUB_REPO:
        print("[INFO] 未配置 GITHUB_OWNER / GITHUB_REPO，视为首次获取")
        return True
    sess = requests.Session()
    sess.headers.update({
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    })
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/variables/SQL_TOKEN"
    resp = sess.get(url)
    if resp.status_code != 200:
        print("[INFO] 未找到 SQL_TOKEN 变量，视为首次获取")
        return True
    token = resp.json().get("value", "").strip()
    if not token:
        print("[INFO] SQL_TOKEN 为空，需要重新获取")
        return True
    try:
        r = requests.post(TEST_URL, json={"sql": "select 1;"},
                          headers={"Authorization": f"Bearer {token}",
                                   "Content-Type": "application/json"},
                          timeout=10)
        if r.status_code == 401:
            print("[INFO] 测试 SQL 返回 401，Token 已失效")
            return True
        r.raise_for_status()
        print("[INFO] 当前 SQL_TOKEN 仍有效，无需更新")
        return False
    except Exception as e:
        print(f"[WARN] 测试请求异常: {e}，视为需要重新获取")
        return True


def fetch_sql_token() -> str:
    """通过 /api/connection 换取新 token"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://client.sqlpub.com",
        "Referer": "https://client.sqlpub.com"
    }
    r = requests.post(CONN_URL, json=CONN_CFG, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"连接失败: {data}")
    token = data.get("data", {}).get("token")
    if not token:
        raise RuntimeError(f"返回无 token: {data}")
    return token


def main():
    print(f"[INFO] 开始执行: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if not GITHUB_TOKEN:
        print("[ERROR] 缺少 GITHUB_TOKEN")
        sys.exit(1)

    if not need_fresh_token():
        print("[SUCCESS] 任务完成（无需更新）")
        return

    try:
        token = fetch_sql_token()
        print("[SUCCESS] 成功获取 SQL Token")
    except Exception as e:
        print(f"[ERROR] 获取 SQL Token 失败: {e}")
        sys.exit(1)

    if set_repo_var(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "SQL_TOKEN", token):
        print("[SUCCESS] 任务完成（已更新）")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
