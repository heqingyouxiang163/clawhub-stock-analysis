#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取沪深主板涨幅前 30 名
"""

import requests
import time
from datetime import datetime

print("=" * 70)
print("🦞 沪深主板涨幅前 30 名")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print()

# 沪深主板代码范围
# 沪市主板：600xxx, 601xxx, 603xxx, 605xxx
# 深市主板：000xxx, 001xxx, 002xxx, 003xxx

def get_em_main_board():
    """东方财富获取沪深主板涨幅排名"""
    print("📊 东方财富 - 获取沪深主板数据...")
    start = time.time()
    
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    
    # 沪市主板
    params_sh = {
        'pn': 1, 'pz': 500, 'po': 1, 'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2, 'invt': 2, 'fid': 'f3',
        'fs': 'm:1 s:2',  # 沪市主板
        'fields': 'f12,f14,f3,f46'
    }
    
    # 深市主板
    params_sz = {
        'pn': 1, 'pz': 500, 'po': 1, 'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2, 'invt': 2, 'fid': 'f3',
        'fs': 'm:0 s:0,m:0 s:1,m:0 s:2',  # 深市主板
        'fields': 'f12,f14,f3,f46'
    }
    
    all_stocks = []
    
    # 获取沪市
    try:
        resp = requests.get(url, params=params_sh, timeout=10,
                           headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('diff'):
                stocks = data['data']['diff']
                for s in stocks:
                    code = s.get('f12', '')
                    # 过滤沪市主板
                    if code.startswith('600') or code.startswith('601') or \
                       code.startswith('603') or code.startswith('605'):
                        all_stocks.append({
                            'code': code,
                            'name': s.get('f14', ''),
                            'change_pct': s.get('f3', 0),
                            'speed': s.get('f46', 0)  # 涨速
                        })
                print(f"  沪市主板：{len(stocks)}只")
    except Exception as e:
        print(f"  ⚠️ 沪市失败：{str(e)[:40]}")
    
    # 获取深市
    try:
        resp = requests.get(url, params=params_sz, timeout=10,
                           headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('diff'):
                stocks = data['data']['diff']
                for s in stocks:
                    code = s.get('f12', '')
                    # 过滤深市主板
                    if code.startswith('000') or code.startswith('001') or \
                       code.startswith('002') or code.startswith('003'):
                        all_stocks.append({
                            'code': code,
                            'name': s.get('f14', ''),
                            'change_pct': s.get('f3', 0),
                            'speed': s.get('f46', 0)
                        })
                print(f"  深市主板：{len(stocks)}只")
    except Exception as e:
        print(f"  ⚠️ 深市失败：{str(e)[:40]}")
    
    # 排序
    all_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    elapsed = time.time() - start
    print(f"✅ 获取{len(all_stocks)}只，耗时{elapsed*1000:.0f}ms")
    
    return all_stocks


# 获取数据
stocks = get_em_main_board()

print()
print("=" * 70)
print("📈 沪深主板涨幅前 30 名")
print("=" * 70)
print()

if stocks:
    print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>10} {'涨速':>8}")
    print("-" * 50)
    
    for i, s in enumerate(stocks[:30], 1):
        print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+9.1f}% {s['speed']:>+7.1f}%")
    
    print("-" * 50)
    print(f"✅ 总计：30 只")
    print()
    
    # 统计
    top30 = stocks[:30]
    avg_change = sum(s['change_pct'] for s in top30) / 30
    limit_up = sum(1 for s in top30 if s['change_pct'] >= 9.5)
    
    print(f"📊 前 30 统计:")
    print(f"  平均涨幅：{avg_change:+.1f}%")
    print(f"  涨停数量：{limit_up}只")
    print(f"  最高涨幅：{top30[0]['change_pct']:+.1f}% ({top30[0]['name']})")
    print(f"  最低涨幅：{top30[-1]['change_pct']:+.1f}% ({top30[-1]['name']})")
else:
    print("⚠️ 获取失败，东方财富接口可能不可用")

print()
print("=" * 70)
