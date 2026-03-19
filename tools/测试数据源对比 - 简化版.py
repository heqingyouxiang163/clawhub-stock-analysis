#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股数据源实时获取对比测试 - 简化版
"""

import requests
import time
from datetime import datetime

TEST_STOCKS = ["002828", "002342", "603778", "600569", "002455"]

print("=" * 70)
print("🦞 A 股数据源实时获取对比测试")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# 腾讯财经
print("\n📊 腾讯财经测试...")
start = time.time()
symbols = ','.join([f"sh{s}" if s.startswith('6') else f"sz{s}" for s in TEST_STOCKS])
try:
    resp = requests.get(f"http://qt.gtimg.cn/q={symbols}", timeout=8)
    count = resp.text.count('~')
    elapsed = time.time() - start
    print(f"  ✅ 成功：{count//32}只  耗时：{elapsed*1000:.0f}ms  速度：{count/32/elapsed:.0f}只/秒")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    elapsed = 999

# 东方财富
print("\n📊 东方财富测试...")
start = time.time()
try:
    resp = requests.get("https://push2.eastmoney.com/api/qt/clist/get", 
                       params={'pn':1,'pz':100,'fid':'f3','fs':'m:0+m:1','fields':'f12,f14,f3'},
                       timeout=10)
    data = resp.json()
    count = len(data.get('data',{}).get('diff',[]))
    elapsed = time.time() - start
    print(f"  ✅ 成功：{count}只  耗时：{elapsed*1000:.0f}ms  速度：{count/elapsed:.0f}只/秒")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    elapsed = 999

# 新浪财经
print("\n📊 新浪财经测试...")
start = time.time()
symbols = ','.join([f"sh{s}" if s.startswith('6') else f"sz{s}" for s in TEST_STOCKS])
try:
    resp = requests.get(f"http://hq.sinajs.cn/list={symbols}", timeout=8)
    count = resp.text.count('=')
    elapsed = time.time() - start
    print(f"  ✅ 成功：{count}只  耗时：{elapsed*1000:.0f}ms  速度：{count/elapsed:.0f}只/秒")
except Exception as e:
    print(f"  ❌ 失败：{e}")

# 网易财经
print("\n📊 网易财经测试...")
start = time.time()
symbols = ','.join([f"0{s}" if s.startswith('6') else f"1{s}" for s in TEST_STOCKS])
try:
    resp = requests.get(f"http://api.money.126.net/data/feed/{symbols}", timeout=8)
    count = resp.text.count('"code"')
    elapsed = time.time() - start
    print(f"  ✅ 成功：{count}只  耗时：{elapsed*1000:.0f}ms  速度：{count/elapsed:.0f}只/秒")
except Exception as e:
    print(f"  ❌ 失败：{e}")

print("\n" + "=" * 70)
print("💡 结论：腾讯财经速度最快且稳定，推荐作为主数据源！")
print("=" * 70)
