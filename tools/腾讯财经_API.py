#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯财经 API - 统一数据获取接口
替代 akshare/东方财富，提供稳定的实时数据
"""

import requests
import time
from datetime import datetime


# ==================== 配置区 ====================

# 腾讯财经 API 端点
TENCENT_API = "http://qt.gtimg.cn/q={}"

# 沪深 300 + 热点股票列表 (约 200 只)
STOCK_POOL = [
    # 涨停热点
    'sh600569', 'sh600643', 'sh600370', 'sh603929', 'sh603248',
    'sh600545', 'sh600227', 'sh600683', 'sh600302', 'sh603738',
    'sz000890', 'sz002427', 'sz002278', 'sz002724', 'sz001278',
    # 5-8% 主升浪 (手动补充)
    'sz002995', 'sz002730', 'sz000717', 'sz002175', 'sh603093',
    # 沪深 300 核心
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


# ==================== 核心函数 ====================

def code_to_symbol(code):
    """股票代码转腾讯格式 (002828 -> sz002828)"""
    code = str(code).zfill(6)
    if code.startswith('6'):
        return f"sh{code}"
    else:
        return f"sz{code}"


def fetch_tencent_data(codes):
    """
    从腾讯财经获取股票数据
    
    Args:
        codes: 股票代码列表 (如 ['002828', '603778'])
    
    Returns:
        dict: {代码：数据字典}
    """
    if not codes:
        return {}
    
    # 转腾讯格式
    symbols = [code_to_symbol(c) for c in codes]
    code_list = ','.join(symbols[:150])  # 最多 150 只
    
    url = TENCENT_API.format(code_list)
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
        start = time.time()
        response = requests.get(url, headers=headers, timeout=8)
        elapsed = time.time() - start
        
        if response.status_code != 200:
            print(f"⚠️ 腾讯财经 HTTP {response.status_code}")
            return {}
        
        text = response.content.decode('gbk')
        lines = text.strip().split(';')
        
        result = {}
        for line in lines:
            if '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    data = parts[1].strip('"').split('~')
                    if len(data) >= 32:
                        # 腾讯格式解析
                        code = data[2] if len(data) > 2 else ''
                        name = data[1] if len(data) > 1 else ''
                        current = float(data[3]) if len(data) > 3 and data[3] else 0
                        prev_close = float(data[4]) if len(data) > 4 and data[4] else current
                        open_p = float(data[5]) if len(data) > 5 and data[5] else current
                        high = float(data[6]) if len(data) > 6 and data[6] else current
                        low = float(data[7]) if len(data) > 7 and data[7] else current
                        change_pct = float(data[32]) if len(data) > 32 else 0
                        amount = float(data[37]) if len(data) > 37 else 0
                        turnover = float(data[39]) if len(data) > 39 else 0
                        
                        result[code] = {
                            'code': code,
                            'name': name,
                            'current': current,
                            'prev_close': prev_close,
                            'open': open_p,
                            'high': high,
                            'low': low,
                            'change_pct': change_pct,
                            'amount': amount,  # 成交额 (元)
                            'turnover': turnover,  # 换手率 (%)
                            'elapsed': elapsed,
                            'success': True
                        }
        
        return result
        
    except Exception as e:
        print(f"⚠️ 腾讯财经失败：{str(e)[:50]}")
        return {}


def get_single_stock(code):
    """
    获取单只股票数据
    
    Args:
        code: 股票代码 (如 '002828')
    
    Returns:
        dict: 股票数据
    """
    result = fetch_tencent_data([code])
    return result.get(code, {'success': False, 'error': '获取失败'})


def get_multiple_stocks(codes):
    """
    获取多只股票数据
    
    Args:
        codes: 股票代码列表
    
    Returns:
        dict: {代码：数据}
    """
    return fetch_tencent_data(codes)


def get_all_stock_pool():
    """
    获取全部股票池数据
    
    Returns:
        dict: 所有股票数据
    """
    # 分批获取 (每批 150 只)
    all_data = {}
    
    for i in range(0, len(STOCK_POOL), 150):
        batch = STOCK_POOL[i:i+150]
        # 去掉 sh/sz 前缀
        codes = [c[2:] if len(c) > 2 else c for c in batch]
        batch_data = fetch_tencent_data(codes)
        all_data.update(batch_data)
        time.sleep(0.1)  # 避免请求过快
    
    return all_data


# ==================== 兼容 akshare 接口 ====================

def get_realtime_data_akshare_style(code):
    """
    兼容 akshare 接口风格
    返回类似 akshare 的数据结构
    """
    data = get_single_stock(code)
    
    if not data.get('success'):
        return {
            'success': False,
            'error': data.get('error', '获取失败'),
            'data': {}
        }
    
    # 转换为 akshare 风格
    return {
        'success': True,
        'data': {
            'code': data['code'],
            'name': data['name'],
            'current': data['current'],
            'open': data['open'],
            'high': data['high'],
            'low': data['low'],
            'prev_close': data['prev_close'],
            'change_pct': data['change_pct'],
            'change': data['current'] - data['prev_close'],
            'amount': data['amount'],
            'turnover': data['turnover'],
            'volume': data['amount'] / data['current'] if data['current'] > 0 else 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }


# ==================== 测试函数 ====================

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 75)
    print("🦞 腾讯财经 API - 数据获取测试")
    print("=" * 75)
    
    # 测试单只股票
    print("\n1. 测试单只股票 (002828 贝肯能源):")
    data = get_single_stock('002828')
    if data.get('success'):
        print(f"   {data['code']} {data['name']}: ¥{data['current']:.2f} ({data['change_pct']:+.1f}%)")
        print(f"   耗时：{data['elapsed']*1000:.0f}ms")
    else:
        print(f"   ❌ 获取失败")
    
    # 测试多只股票
    print("\n2. 测试多只股票 (持仓股):")
    codes = ['002828', '002342', '603778']
    data = get_multiple_stocks(codes)
    for code in codes:
        if code in data:
            d = data[code]
            print(f"   {code} {d['name']}: ¥{d['current']:.2f} ({d['change_pct']:+.1f}%)")
        else:
            print(f"   {code}: ❌ 获取失败")
    
    # 测试股票池
    print("\n3. 测试股票池 (前 10 只):")
    all_data = get_all_stock_pool()
    for i, (code, d) in enumerate(list(all_data.items())[:10]):
        print(f"   {i+1}. {code} {d['name']}: ¥{d['current']:.2f} ({d['change_pct']:+.1f}%)")
    
    print(f"\n✅ 股票池总数：{len(all_data)}只")
    print("=" * 75)

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"✅ **总耗时**: {total_elapsed/60:.1f}分钟")
