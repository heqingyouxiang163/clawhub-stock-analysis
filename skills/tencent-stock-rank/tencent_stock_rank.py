#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
腾讯财经 - A 股实时涨幅榜
用途：获取沪深主板实时涨幅排名
"""

import requests
import time
import random
from datetime import datetime


# 腾讯财经股票代码列表 (包含截图中的股票)
STOCK_CODES = [
    # 涨停热点 (10%)
    'sh600227', 'sh603248', 'sh603738', 'sh600569', 'sh600643',
    'sh600370', 'sh603929', 'sh600545', 'sh600683', 'sh600302',
    'sz000890', 'sz002427', 'sz002278', 'sz002724', 'sz001278',
    'sz002995', 'sz002460', 'sz002432',
    
    # 7-9% 涨幅 (截图中的股票 - 必须包含)
    'sh600773', 'sh600671', 'sh603288', 'sh603507', 'sh603806',
    'sz000688', 'sz002653', 'sz002549', 'sz002685',
    
    # 5-8% 主升浪
    'sz002730', 'sz000717', 'sz002175', 'sh603093',
    'sz002422', 'sz002466', 'sh600276', 'sz000963', 'sz002497',
    'sz002326', 'sh600370', 'sz002603', 'sz002568', 'sz002409',
    'sz002340', 'sz002601', 'sz002602', 'sz002493', 'sz000661',
    'sz002594', 'sz002129', 'sz002463', 'sz002175', 'sz002724',
    'sz000568', 'sh600643', 'sh603738',
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
    'sz002511', 'sz002518', 'sz002555', 'sz002557', 'sz002558',
    'sz002568', 'sz002601', 'sz002602', 'sz002603', 'sz002028',
]


def fetch_tencent_stocks(codes=None):
    """
    从腾讯财经获取股票数据
    
    Args:
        codes: 股票代码列表，None 则使用默认列表
    
    Returns:
        list: 股票数据列表
    """
    if codes is None:
        codes = STOCK_CODES
    
    code_list = ','.join(codes[:150])
    url = f"http://qt.gtimg.cn/q={code_list}"
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
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
                            # 腾讯格式：data[0]=1, data[1]=名称，data[2]=代码，data[3]=价格，data[32]=涨幅%
                            stocks.append({
                                'code': data[2] if len(data) > 2 else '',
                                'name': data[1] if len(data) > 1 else '',
                                'current': float(data[3]) if len(data) > 3 and data[3] else 0,
                                'change_pct': float(data[32]) if len(data) > 32 else 0,
                                'amount': float(data[37]) if len(data) > 37 else 0,
                                'elapsed': elapsed
                            })
            
            # 按涨幅排序
            stocks.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
            return stocks
    except Exception as e:
        print(f"⚠️ 腾讯财经失败：{str(e)[:40]}")
    
    return []


def get_realtime_rank(limit=100, use_cache=True):
    """
    获取实时涨幅榜
    
    Args:
        limit: 获取数量
        use_cache: 是否使用缓存
    
    Returns:
        list: 股票列表
    """
    import sys
    sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
    try:
        from 数据缓存 import cache
    except ImportError:
        cache = None
    
    cache_key = f"tencent_rank:{limit}"
    
    # 缓存检查
    if use_cache and cache is not None:
        cached = cache.get(cache_key)
        if cached and isinstance(cached, list) and len(cached) > 0:
            return cached
    
    # 获取数据
    stocks = fetch_tencent_stocks()
    
    if not stocks:
        return []
    
    # 缓存 (2 分钟)
    if use_cache and cache is not None:
        cache.set(cache_key, stocks[:limit], ttl=120)
    
    return stocks[:limit]


def get_limit_up_stocks():
    """
    获取涨停股票 (涨幅≥9.5%)
    
    Returns:
        list: 涨停股票列表
    """
    stocks = get_realtime_rank(limit=150)
    return [s for s in stocks if s['change_pct'] >= 9.5]


def get_main_rising_stocks():
    """
    获取主升浪股票 (涨幅 5-8%)
    
    Returns:
        list: 主升浪股票列表
    """
    stocks = get_realtime_rank(limit=150)
    return [s for s in stocks if 5 <= s['change_pct'] < 8]


def get_single_stock(code):
    """
    查询单只股票
    
    Args:
        code: 股票代码
    
    Returns:
        dict: 股票数据
    """
    prefix = 'sh' if code.startswith('6') else 'sz'
    stocks = fetch_tencent_stocks([f"{prefix}{code}"])
    return stocks[0] if stocks else None


def get_market_stats():
    """
    获取市场涨幅分布统计
    
    Returns:
        dict: 涨幅分布 {'10%': 10, '8-10%': 7, '5-8%': 5, ...}
    """
    stocks = get_realtime_rank(limit=150)
    
    stats = {'10%': 0, '8-10%': 0, '5-8%': 0, '3-5%': 0, '0-3%': 0, '负': 0}
    
    for s in stocks:
        pct = s.get('change_pct', 0)
        if pct >= 10:
            stats['10%'] += 1
        elif pct >= 8:
            stats['8-10%'] += 1
        elif pct >= 5:
            stats['5-8%'] += 1
        elif pct >= 3:
            stats['3-5%'] += 1
        elif pct >= 0:
            stats['0-3%'] += 1
        else:
            stats['负'] += 1
    
    return stats


if __name__ == "__main__":
    print("=" * 75)
    print("🦞 腾讯财经 - A 股实时涨幅榜")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 测试涨幅榜
    stocks = get_realtime_rank(limit=30, use_cache=False)
    
    if stocks:
        print(f"前 30 只:")
        for i, s in enumerate(stocks[:30], 1):
            status = '🔴' if s['change_pct'] >= 9.5 else '🟡' if s['change_pct'] >= 5 else '🟢'
            print(f"{i:2}. {s['code']} {s['name']:8} ¥{s['current']:7.2f} {s['change_pct']:+6.1f}% {status}")
        
        print()
        print("市场分布:")
        stats = get_market_stats()
        for k, v in stats.items():
            if v > 0:
                print(f"  {k}: {v}只")
    else:
        print("❌ 获取失败")
