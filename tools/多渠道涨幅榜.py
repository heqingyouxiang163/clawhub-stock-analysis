#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多渠道获取涨幅榜 - 实时动态观察池
用途：从多个数据源获取涨幅榜，确保稳定性
"""

import requests
import time
from datetime import datetime


def fetch_from_eastmoney(limit=100):
    """
    东方财富涨幅榜
    
    Returns:
        list: 股票列表 [{'code', 'name', 'change_pct', 'amount', 'current'}, ...]
    """
    try:
        url = "http://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': 1,
            'pz': limit,
            'po': 1,
            'np': 1,
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': 2,
            'invt': 2,
            'fid': 'f3',
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2',
            'fields': 'f12,f14,f2,f3,f5,f6,f107,f108'
        }
        headers = {'Referer': 'http://quote.eastmoney.com/'}
        
        start = time.time()
        response = requests.get(url, params=params, headers=headers, timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                stocks = []
                for s in data['data']['diff']:
                    stocks.append({
                        'code': s['f12'],
                        'name': s['f14'],
                        'current': s['f2'],
                        'change_pct': s['f3'],
                        'volume': s['f5'],
                        'amount': s['f6'],
                        'turnover': s.get('f107', 0),
                        'volume_ratio': s.get('f108', 0),
                        'source': 'eastmoney',
                        'elapsed': elapsed
                    })
                print(f"✅ 东方财富：{len(stocks)}只 (耗时：{elapsed*1000:.1f}ms)")
                return stocks
    except Exception as e:
        print(f"❌ 东方财富失败：{e}")
    
    return []


def fetch_from_sina(limit=100):
    """
    新浪财经涨幅榜 (通过板块获取)
    
    说明：新浪没有直接的涨幅榜 API，通过沪深 A 股板块获取
    """
    try:
        stocks = []
        
        # 获取沪市 A 股
        for market in ['sh', 'sz']:
            url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num={limit//2}&sort=symbol&order=desc&node={market}&_s_r_a=page"
            headers = {'Referer': 'https://finance.sina.com.cn/'}
            
            start = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    for s in data:
                        try:
                            change_pct = float(s.get('changepercent', 0) or 0)
                            stocks.append({
                                'code': s.get('code', ''),
                                'name': s.get('name', ''),
                                'current': float(s.get('trade', 0) or 0),
                                'change_pct': change_pct,
                                'volume': float(s.get('volume', 0) or 0),
                                'amount': float(s.get('turnover', 0) or 0),
                                'source': 'sina',
                                'elapsed': elapsed
                            })
                        except:
                            continue
                    
                    print(f"✅ 新浪财经：{len([s for s in data if s.get('code')])}只 (耗时：{elapsed*1000:.1f}ms)")
            except Exception as e:
                print(f"❌ 新浪财经失败：{e}")
        
        # 按涨幅排序
        stocks.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
        return stocks[:limit]
    except Exception as e:
        print(f"❌ 新浪财经失败：{e}")
    
    return []


def fetch_from_qq(limit=100):
    """
    腾讯财经涨幅榜
    
    说明：腾讯也没有直接的涨幅榜 API，通过列表获取
    """
    try:
        # 腾讯沪深 A 股列表
        url = "http://qt.gtimg.cn/q=sh600000,sz000001"  # 示例，实际需要批量获取
        # 腾讯接口比较复杂，暂时不实现
        print("⚠️ 腾讯财经：暂不支持涨幅榜")
    except Exception as e:
        print(f"❌ 腾讯财经失败：{e}")
    
    return []


def get_top_gainers(limit=100, use_cache=True):
    """
    获取涨幅榜 (多渠道，带缓存)
    
    Args:
        limit: 获取数量
        use_cache: 是否使用缓存
    
    Returns:
        list: 涨幅榜股票列表
    """
    cache_key = f"top_gainers:{limit}"
    
    # 尝试从缓存获取 (5 分钟有效期)
    if use_cache:
        from 数据缓存 import get_cache, set_cache
        cached = get_cache(cache_key)
        if cached:
            print(f"📦 缓存命中：{len(cached)}只")
            return cached
    
    # 多渠道获取 (优先级：东方财富 > 新浪 > 备用池)
    stocks = []
    
    # 1. 东方财富 (优先)
    stocks = fetch_from_eastmoney(limit)
    
    if not stocks:
        # 2. 新浪财经 (备用)
        stocks = fetch_from_sina(limit)
    
    if not stocks:
        # 3. 备用池
        print("⚠️ 所有渠道失败，使用备用池...")
        backup_pool = [
            '600370',  '600227', '600683', '603929', '603248',
            '600545', '600302', '002427', '002278', '002724', '001278',
            '603738', '002020', '000639', '603421', '000620',
            '600569', '600643', '600396', '002256', '600751', '600152',
            '002466', '002460', '002469', '600278', '000858',
            '600383', '600048', '000002', '600887',
        ]
        stocks = [{'code': code, 'source': 'backup'} for code in backup_pool]
        print(f"🔄 备用池：{len(stocks)}只")
    
    # 缓存结果 (5 分钟)
    if use_cache and stocks:
        from 数据缓存 import set_cache
        set_cache(cache_key, stocks, ttl=300)
    
    return stocks


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 75)
    print("🦞 多渠道涨幅榜获取")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    stocks = get_top_gainers(limit=100, use_cache=False)
    
    print()
    print("=" * 75)
    print("📈 涨幅前 10:")
    print("=" * 75)
    for i, s in enumerate(stocks[:10], 1):
        print(f"{i}. {s['code']} {s.get('name', 'N/A')} - {s.get('change_pct', 0):+.1f}% ({s.get('amount', 0)/100000000:.1f}亿) [{s.get('source', 'unknown')}]")
    
    print()
    print("=" * 75)
    print(f"总计：{len(stocks)}只")
    print("=" * 75)

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"✅ **总耗时**: {total_elapsed/60:.1f}分钟")
