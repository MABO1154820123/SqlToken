#!/usr/bin/env python3
"""
自动检查 SQL 服务是否返回 401，仅在需要时获取新 token 并写入 GitHub 仓库变量 SQL_TOKEN
需在 GitHub Actions 里设置：
  secrets.TOKEN          有 repo 权限的 GitHub PAT
  secrets.DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD
环境变量会自动注入，无需改动脚本。
"""

import os
import sys
import json
import time
import requests
import re
from urllib.parse import urljoin

# ---------- 配置 ----------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO  = os.getenv("GITHUB_REPO")
SQL_API_URL  = "https://www.sqlpub.com/api/login"
TEST_SQL_URL = "https://client.sqlpub.com/api/database/execute"

DB_CFG = {
    "username": "mapo1154820123@outlook.com",
    "password": "9sl5L4iKnpAP49dj",
    "type": "Account"
}
# --------------------------


def set_repo_var(token: str, owner: str, repo: str, name: str, value: str) -> bool:
    """创建或更新 GitHub Actions 仓库变量"""
    sess = requests.Session()
    sess.headers.update(
        {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
    )

    # 变量是否存在决定用 PATCH 还是 POST
    url_get = f"https://api.github.com/repos/{owner}/{repo}/actions/variables/{name}"
    resp = sess.get(url_get)
    method, url = (
        ("PATCH", url_get) if resp.status_code == 200 else ("POST", f"https://api.github.com/repos/{owner}/{repo}/actions/variables")
    )
    print(f"[INFO] {'更新' if method == 'PATCH' else '创建'}仓库变量: {name}")

    resp = sess.request(method, url, json={"name": name, "value": value})
    if resp.status_code in (200, 201, 204):
        print(f"[SUCCESS] 变量 {name} 写入完成")
        return True
    print(f"[ERROR] 写入变量失败: {resp.status_code} {resp.text}")
    return False


def need_fresh_token() -> bool:
    """发送测试 SQL，若返回 401 则说明 token 失效，需要重新获取"""
    # 先从仓库变量里取出当前 SQL_TOKEN（如果存在）
    sess = requests.Session()
    sess.headers.update(
        {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
    )
    url_get = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/variables/SQL_TOKEN"
    resp = sess.get(url_get)
    if resp.status_code != 200:
        print("[INFO] 未找到 SQL_TOKEN 变量，视为需要首次获取")
        return True

    current_token = resp.json().get("value", "").strip()
    if not current_token:
        print("[INFO] SQL_TOKEN 为空，需要重新获取")
        return True

    # 用当前 token 调用 SQL 接口
    try:
        r = requests.post(
            TEST_SQL_URL,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": f"Bearer {current_token}",
            },
            json={"sql": "select 1;"},
            timeout=10,
        )
        if r.status_code == 401:
            print("[INFO] 测试 SQL 返回 401，Token 已失效，需要重新获取")
            return True
        r.raise_for_status()
        print("[INFO] 当前 SQL_TOKEN 仍有效，无需更新")
        return False
    except Exception as e:
        print(f"[WARN] 测试 SQL 请求异常: {e}，视为需要重新获取")
        return True


def fetch_sql_token() -> str:
    """请求 SQL 服务获取全新 token（带 CSRF 和 Cookie）"""
    base_url = "https://www.sqlpub.com"
    login_page = base_url + "/login"
    api_url = base_url + "/api/login"

    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })

    # 1. 先 GET 登录页，拿 Cookie + CSRF
    r = sess.get(login_page, timeout=15)
    r.raise_for_status()

    # 从页面里抠 _token
    m = re.search(r'name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']', r.text)
    if not m:
        raise RuntimeError("登录页未找到 CSRF token")
    csrf_token = m.group(1)

    # 2. 组装带 CSRF 的登录数据
    payload = {
        "username": DB_CFG["username"],
        "password": DB_CFG["password"],
        "type": DB_CFG["type"],
        "_token": csrf_token
    }

    # 3. 发 JSON 登录请求
    sess.headers.update({
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": base_url,
        "Referer": login_page
    })
    rsp = sess.post(api_url, json=payload, timeout=15)
    rsp.raise_for_status()

    data = rsp.json()
    if not (data.get("success") and data.get("data", {}).get("token")):
        raise RuntimeError(f"API 返回异常: {data}")

    return data["data"]["token"]


def main() -> None:
    print(f"[INFO] 开始执行: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if not GITHUB_TOKEN:
        print("[ERROR] 缺少 GITHUB_TOKEN")
        sys.exit(1)

    # 1. 判断是否需要更新 token
    if not need_fresh_token():
        print("[SUCCESS] 任务完成（无需更新）")
        return

    # 2. 获取新 token
    try:
        sql_token = fetch_sql_token()
        print("[SUCCESS] 成功获取 SQL Token")
    except Exception as e:
        print(f"[ERROR] 获取 SQL Token 失败: {e}")
        sys.exit(1)

    # 3. 写回仓库变量
    ok = set_repo_var(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "SQL_TOKEN", sql_token)
    if not ok:
        sys.exit(1)
    print("[SUCCESS] 任务完成（已更新）")


if __name__ == "__main__":
    main()
