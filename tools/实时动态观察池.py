#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时动态观察池 - 腾讯财经版
用途：只用腾讯财经，确保稳定性
策略：
1. 腾讯财经获取大盘股 + 热点股
2. 手动补充 5-8% 区间热点股
3. 实时抽查验证
"""

import requests
import time
import random
from datetime import datetime


def fetch_from_qq_main(limit=150):
    """腾讯财经 - 大盘股 + 热点股"""
    try:
        # 沪深 300 + 热点股
        codes = [
            # 涨停热点
            'sh600569', 'sh600643', 'sh600370', 'sh603929', 'sh603248',
            'sh600545', 'sh600227', 'sh600683', 'sh600302', 'sh603738',
            'sz000890', 'sz002427', 'sz002278', 'sz002724', 'sz001278',
            # 5-8% 区间 (手动补充)
            'sz002995', 'sz002730', 'sz000717', 'sz002175', 'sh603093',
            # 沪深 300 部分
            'sh600036', 'sh601318', 'sh600519', 'sh600030', 'sh601398',
            'sh601288', 'sh600000', 'sh600887', 'sh601166', 'sh600048',
            'sh601328', 'sh600276', 'sh601857', 'sh601088', 'sh600028',
            'sh600031', 'sh601988', 'sh600585', 'sh600016', 'sh601390',
            'sz000333', 'sz002415', 'sz000651', 'sz000858', 'sz002594',
            'sz000001', 'sz000002', 'sz002466', 'sz002460', 'sz002469',
            'sz000063', 'sz000100', 'sz000538', 'sz000568', 'sz000596',
            'sz000625', 'sz000661', 'sz000725', 'sz000776', 'sz000895',
            'sz000938', 'sz000963', 'sz001979', 'sz002001', 'sz002007',
            'sz002027', 'sz002032', 'sz002049', 'sz002129', 'sz002142',
            'sz002179', 'sz002230', 'sz002241', 'sz002252', 'sz002271',
            'sz002304', 'sz002311', 'sz002326', 'sz002340', 'sz002352',
            'sz002371', 'sz002409', 'sz002410', 'sz002422', 'sz002432',
            'sz002456', 'sz002459', 'sz002463', 'sz002475', 'sz002487',
            'sz002493', 'sz002497', 'sz002506', 'sz002507', 'sz002508',
        ]
        
        code_list = ','.join(codes[:150])
        url = f"http://qt.gtimg.cn/q={code_list}"
        headers = {'Referer': 'https://stockapp.finance.qq.com/'}
        
        start = time.time()
        response = requests.get(url, headers=headers, timeout=8)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            text = response.content.decode('gbk')
            lines = text.strip().split(';')
            stocks = []
            
            for line in lines:
                if '=' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        data = parts[1].strip('"').split('~')
                        if len(data) >= 32:
                            stocks.append({
                                'code': data[2] if len(data) > 2 else '',
                                'name': data[1] if len(data) > 1 else '',
                                'current': float(data[3]) if len(data) > 3 and data[3] else 0,
                                'change_pct': float(data[32]) if len(data) > 32 else 0,
                                'source': 'qq_main',
                                'elapsed': elapsed
                            })
            
            stocks.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
            print(f"✅ 腾讯财经：{len(stocks)}只 ({elapsed*1000:.0f}ms)")
            return stocks
    except Exception as e:
        print(f"⚠️ 腾讯失败：{str(e)[:40]}")
    
    return []


def validate_stock_data(code, expected_change_pct):
    """验证单只股票数据"""
    try:
        prefix = 'sh' if code.startswith('6') else 'sz'
        url = f"http://qt.gtimg.cn/q={prefix}{code}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            text = r.content.decode('gbk')
            if '=' in text:
                data = text.split('=')[1].strip('"').split('~')
                if len(data) > 32:
                    actual_change = float(data[32]) if data[32] else 0
                    if abs(actual_change - expected_change_pct) < 1.5:
                        return True
    except:
        pass
    return False


def get_realtime_watchlist(limit=100, use_cache=True):
    """获取实时观察池"""
    from 数据缓存 import cache
    
    cache_key = f"watchlist_qq:{limit}"
    
    # 缓存 (2 分钟)
    if use_cache:
        cached = cache.get(cache_key)
        if cached and isinstance(cached, list) and len(cached) > 0:
            print(f"📦 缓存命中：{len(cached)}只")
            return cached
    
    # 获取腾讯财经数据
    stocks = fetch_from_qq_main(limit)
    
    if not stocks:
        print("❌ 腾讯财经失败")
        return None
    
    # 抽查验证
    print("🔬 抽查验证...")
    sample_size = min(5, len(stocks))
    sample_indices = random.sample(range(len(stocks)), sample_size)
    
    valid_count = 0
    for idx in sample_indices:
        stock = stocks[idx]
        if validate_stock_data(stock['code'], stock['change_pct']):
            valid_count += 1
            print(f"  ✅ {stock['code']} {stock['name']} ({stock['change_pct']}%)")
        else:
            print(f"  ⚠️ {stock['code']} {stock['name']} (可能偏差)")
    
    validation_rate = valid_count / sample_size if sample_size > 0 else 0
    print(f"📊 验证通过率：{validation_rate*100:.0f}%")
    
    if validation_rate < 0.8:
        print("⚠️ 验证不通过，不缓存")
        cache.delete(cache_key)
        return None
    
    # 缓存
    watch_codes = [s['code'] for s in stocks[:limit]]
    if use_cache and watch_codes:
        cache.set(cache_key, watch_codes, ttl=120)
        print(f"💾 已缓存 (120 秒)")
    
    return watch_codes


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 75)
    print("🦞 实时动态观察池 - 腾讯财经版")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    watchlist = get_realtime_watchlist(limit=100, use_cache=False)
    
    if watchlist:
        print(f"\n✅ 获取到 {len(watchlist)} 只")
        print(f"前 20 只：{watchlist[:20]}")
    else:
        print("\n❌ 获取失败")

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"
✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"
✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"
✅ **总耗时**: {total_elapsed/60:.1f}分钟")
