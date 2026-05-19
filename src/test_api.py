#!/usr/bin/env python3
"""APIテスト — トークン取得のエラー詳細確認"""

import requests

station = "fmnanami"

# テスト1: POST with JSON body
headers = {"Origin": "https://www.jcbasimul.com", "Content-Type": "application/json"}
url = f"https://api.radimo.smen.biz/api/v1/select_stream?station={station}&channel=0&quality=high&burst=5"

# bodyあり
res = requests.post(url, headers=headers, json={"station": station}, timeout=10)
print(f"Test1 (POST json): {res.status_code}")
print(f"  Body: {res.text[:500]}")

# bodyなし
res2 = requests.post(url, headers=headers, timeout=10)
print(f"Test2 (POST no body): {res2.status_code}")
print(f"  Body: {res2.text[:500]}")

# 単純GET
res3 = requests.get(url, headers=headers, timeout=10)
print(f"Test3 (GET): {res3.status_code}")
print(f"  Body: {res3.text[:500]}")
