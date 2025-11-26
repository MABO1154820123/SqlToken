#!/usr/bin/env python3
"""
自动请求 SQL 服务获取 token → 写入 GitHub 仓库变量 SQL_TOKEN
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

# ---------- 配置 ----------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO  = os.getenv("GITHUB_REPO")
SQL_API_URL  = "https://client.sqlpub.com/api/connection"

DB_CFG = {
    "host":     os.getenv("DB_HOST"),
    "port":     int(os.getenv("DB_PORT", 0)),
    "dbName":   os.getenv("DB_NAME"),
    "dbUser":   os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
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


def main() -> None:
    print(f"[INFO] 开始执行: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if not GITHUB_TOKEN:
        print("[ERROR] 缺少 GITHUB_TOKEN")
        sys.exit(1)

    # 1. 请求 SQL 服务拿 token
    print(f"[INFO] 请求 SQL API: {SQL_API_URL}")
    try:
        rsp = requests.post(
            SQL_API_URL,
            headers={"accept": "application/json", "content-type": "application/json"},
            json=DB_CFG,
            timeout=10,
        )
        rsp.raise_for_status()
        data = rsp.json()
        if not (data.get("success") and data.get("data", {}).get("token")):
            raise RuntimeError("API 返回格式异常，未找到 token")
        sql_token = data["data"]["token"]
        print("[SUCCESS] 成功获取 SQL Token")
    except Exception as e:
        print(f"[ERROR] 获取 SQL Token 失败: {e}")
        sys.exit(1)

    # 2. 写回仓库变量
    ok = set_repo_var(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "SQL_TOKEN", sql_token)
    if not ok:
        sys.exit(1)
    print("[SUCCESS] 任务完成")


if __name__ == "__main__":
    main()