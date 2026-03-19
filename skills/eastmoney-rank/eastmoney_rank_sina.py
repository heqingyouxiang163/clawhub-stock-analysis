#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪财经 + 东方财富涨幅榜
东方财富获取涨幅排名，新浪财经获取准确价格
"""

import requests
import time
import json
from datetime import datetime
import os


CACHE_FILE = "/home/admin/openclaw/workspace/temp/涨幅榜缓存.json"
CACHE_TTL = 120


def fetch_em_rank(page=1):
    """东方财富获取涨幅排名"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': page,
        'pz': 500,
        'po': 1,
        'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2,
        'invt': 2,
        'fid': 'f3',
        'fs': 'm:0+m:1',
        'fields': 'f12,f14,f3'  # 只取代码、名称、涨幅
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('diff'):
                return data['data']['diff']
    except:
        pass
    return []


def fetch_sina_price(codes):
    """新浪财经获取价格"""
    if not codes:
        return {}
    
    # 批量获取 (每次 60 只)
    symbols = []
    for code in codes[:60]:
        if code.startswith('6'):
            symbols.append(f"sh{code}")
        else:
            symbols.append(f"sz{code}")
    
    code_list = ','.join(symbols)
    url = f"http://hq.sinajs.cn/list={code_list}"
    
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            text = resp.content.decode('gbk')
            lines = text.strip().split(';')
            
            result = {}
            for line in lines:
                if '=' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        data = parts[1].strip('"').split(',')
                        if len(data) >= 32 and data[3]:
                            symbol = parts[0].split('_')[-1]
                            code = symbol[2:]  # 去掉 sh/sz
                            
                            current = float(data[3]) if data[3] else 0
                            result[code] = {
                                'current': current,
                                'name': data[0],
                                'change_pct': float(data[32]) if data[32] else 0
                            }
            
            return result
    except:
        pass
    
    return {}


def get_full_rank(use_cache=True):
    """获取全市场涨幅榜"""
    # 检查缓存
    if use_cache and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                if time.time() - data.get('timestamp', 0) < CACHE_TTL:
                    print(f"✅ 使用缓存 ({len(data['stocks'])}只)")
                    return data['stocks']
        except:
            pass
    
    print("📊 获取全市场涨幅榜...")
    start = time.time()
    
    # 东方财富获取排名
    all_stocks = []
    for page in range(1, 100):
        stocks = fetch_em_rank(page)
        if not stocks:
            break
        
        for s in stocks:
            code = s.get('f12', '')
            name = s.get('f14', '')
            change_pct = s.get('f3', 0)
            
            if code and name:
                all_stocks.append({
                    'code': code,
                    'name': name,
                    'change_pct': change_pct
                })
        
        if len(stocks) < 500:
            break
    
    print(f"  获取{len(all_stocks)}只股票排名")
    
    # 新浪财经获取价格
    print("📊 获取实时价格...")
    codes = [s['code'] for s in all_stocks]
    
    all_data = []
    for i in range(0, len(codes), 60):
        batch = codes[i:i+60]
        prices = fetch_sina_price(batch)
        
        for code in batch:
            if code in prices:
                p = prices[code]
                all_data.append({
                    'code': code,
                    'name': p['name'],
                    'current': p['current'],
                    'change_pct': p['change_pct']
                })
        
        print(f"  批次{len(all_data)}只")
        time.sleep(0.2)
    
    # 保存缓存
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'stocks': all_data
        }, f, ensure_ascii=False)
    
    elapsed = time.time() - start
    print(f"✅ 获取完成：{len(all_data)}只，耗时{elapsed:.1f}秒")
    
    return all_data


def get_rank_range(min_pct, max_pct, use_cache=True):
    """获取指定涨幅范围"""
    stocks = get_full_rank(use_cache=use_cache)
    result = [s for s in stocks if min_pct <= s['change_pct'] <= max_pct]
    result.sort(key=lambda x: x['change_pct'], reverse=True)
    return result


if __name__ == "__main__":
    print("=" * 75)
    print("🦞 新浪财经 + 东方财富 - 实时涨幅榜")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    stocks = get_full_rank(use_cache=False)
    
    print()
    print("=" * 75)
    print("📊 涨幅分布:")
    print("=" * 75)
    
    ranges = [
        ('涨停 (≥9.5%)', 9.5, 999),
        ('8-9.5%', 8, 9.5),
        ('7-8%', 7, 8),
        ('5-7%', 5, 7),
        ('3-5%', 3, 5),
        ('0-3%', 0, 3),
        ('下跌 (<0%)', -999, 0)
    ]
    
    for name, min_p, max_p in ranges:
        count = sum(1 for s in stocks if min_p <= s['change_pct'] < max_p)
        if count > 0:
            print(f"  {name:<15} {count:4}只")
    
    print("=" * 75)
    
    # 涨幅 5%-7%
    target = get_rank_range(5, 7, use_cache=True)
    
    print(f"\n📈 涨幅 5%-7% 股票 ({len(target)}只):")
    
    if target:
        for i, s in enumerate(target[:30], 1):
            print(f"{i:2}. {s['code']} {s['name']:8} ¥{s['current']:7.2f} {s['change_pct']:+6.1f}%")
        
        if len(target) > 30:
            print(f"... 还有 {len(target)-30}只")
    
    print("=" * 75)
