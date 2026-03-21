#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据获取 - 盘中/盘后自适应
盘中：腾讯财经快速版 (68% 覆盖率，<10 秒)
盘后：akshare 全量版 (100% 覆盖率，60 秒+)
"""

import requests
import time
from datetime import datetime, time as dt_time
from concurrent.futures import ThreadPoolExecutor, as_completed


# ==================== 配置区 ====================

# 腾讯财经扩展股票池 (1500+ 只活跃股)
TENCENT_POOL = []

# 沪市主板
for i in list(range(0, 200)) + list(range(300, 400)) + list(range(500, 600)):
    TENCENT_POOL.append(f"sh600{i:03d}")
for i in range(0, 150):
    TENCENT_POOL.append(f"sh601{i:03d}")
for i in list(range(0, 200)) + list(range(300, 400)):
    TENCENT_POOL.append(f"sh603{i:03d}")
for i in range(0, 50):
    TENCENT_POOL.append(f"sh605{i:03d}")

# 深市主板
for i in list(range(0, 200)) + list(range(300, 400)) + list(range(500, 600)):
    TENCENT_POOL.append(f"sz000{i:03d}")
for i in range(0, 100):
    TENCENT_POOL.append(f"sz001{i:03d}")
for i in list(range(0, 300)) + list(range(400, 500)):
    TENCENT_POOL.append(f"sz002{i:03d}")
for i in range(0, 100):
    TENCENT_POOL.append(f"sz003{i:03d}")

TENCENT_POOL = list(set(TENCENT_POOL))


# ==================== 时间判断 ====================

def is_trading_time():
    """判断是否在交易时间内"""
    now = datetime.now()
    t = now.time()
    
    # 周末
    if now.weekday() >= 5:
        return False
    
    # 交易时段
    if dt_time(9, 25) <= t <= dt_time(11, 30):
        return True
    if dt_time(13, 0) <= t <= dt_time(15, 0):
        return True
    
    return False


# ==================== 腾讯财经快速获取 ====================

def fetch_tencent_batch(symbols):
    """批量获取腾讯财经数据"""
    code_list = ','.join(symbols)
    url = f"http://qt.gtimg.cn/q={code_list}"
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        text = response.content.decode('gbk')
        lines = text.strip().split(';')
        
        result = []
        for line in lines:
            if '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    data = parts[1].strip('"').split('~')
                    if len(data) >= 32 and data[3]:
                        code = data[2]
                        name = data[1] or '?'
                        current = float(data[3]) if data[3] else 0
                        change_pct = float(data[32]) if len(data) > 32 else 0
                        
                        if current > 0:
                            result.append({
                                'code': code,
                                'name': name,
                                'current': current,
                                'change_pct': change_pct,
                                'source': 'tencent'
                            })
        
        return result
    except:
        return []


def get_tencent_fast():
    """腾讯财经快速获取 (多线程)"""
    batch_size = 150  # 增大批次
    batches = [TENCENT_POOL[i:i+batch_size] for i in range(0, len(TENCENT_POOL), batch_size)]
    
    all_stocks = []
    
    # 多线程并发 (10 个线程)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_tencent_batch, batch): i for i, batch in enumerate(batches)}
        
        for future in as_completed(futures):
            stocks = future.result()
            all_stocks.extend(stocks)
    
    return all_stocks


# ==================== akshare 全量获取 ====================

def get_akshare_full():
    """akshare 全量获取"""
    try:
        import akshare as ak
        
        print("📊 获取全市场数据 (akshare)...")
        df = ak.stock_zh_a_spot_em()
        
        result = []
        for _, row in df.iterrows():
            result.append({
                'code': row['代码'],
                'name': row['名称'],
                'current': row['最新价'],
                'change_pct': row['涨跌幅'],
                'source': 'akshare'
            })
        
        return result
    except Exception as e:
        print(f"⚠️ akshare 失败：{str(e)[:50]}")
        return []


# ==================== 智能获取接口 ====================

def get_market_data(force_full=False):
    """
    智能获取市场数据
    
    Args:
        force_full: 强制获取全量数据
    
    Returns:
        list: 股票数据列表
    """
    if force_full or not is_trading_time():
        # 盘后：使用 akshare 全量
        print("🌙 盘后模式：获取全量数据...")
        stocks = get_akshare_full()
        
        if not stocks:
            print("⚠️ akshare 失败，降级到腾讯财经...")
            stocks = get_tencent_fast()
    else:
        # 盘中：使用腾讯财经快速
        print("☀️ 盘中模式：快速获取...")
        stocks = get_tencent_fast()
    
    return stocks


def get_rank_range(min_pct, max_pct, stocks=None):
    """
    获取指定涨幅范围的股票
    
    Args:
        min_pct: 最小涨幅
        max_pct: 最大涨幅
        stocks: 股票列表 (None 则自动获取)
    
    Returns:
        list: 符合条件的股票
    """
    if stocks is None:
        stocks = get_market_data()
    
    result = [s for s in stocks if min_pct <= s['change_pct'] <= max_pct]
    result.sort(key=lambda x: x['change_pct'], reverse=True)
    
    return result


# ==================== 主函数 ====================

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 75)
    print("🦞 智能数据获取 - 盘中/盘后自适应")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 强制使用腾讯财经快速版测试
    print("📊 测试模式：腾讯财经快速版")
    print()
    
    # 获取数据
    start = time.time()
    stocks = get_tencent_fast()
    elapsed = time.time() - start
    
    print()
    print("=" * 75)
    print(f"📊 获取结果:")
    print(f"  股票数：{len(stocks)}只")
    print(f"  耗时：{elapsed:.1f}秒")
    print("=" * 75)
    
    # 涨幅分布
    print()
    print("📊 涨幅分布:")
    
    ranges = [
        ('涨停 (≥9.5%)', 9.5, 999),
        ('8-9.5%', 8, 9.5),
        ('7-8%', 7, 8),
        ('5-7%', 5, 7),
        ('3-5%', 3, 5),
        ('0-3%', 0, 3),
        ('下跌 (<0%)', -999, 0)
    ]
    
    for name, min_pct, max_pct in ranges:
        count = sum(1 for s in stocks if min_pct <= s['change_pct'] < max_pct)
        if count > 0:
            print(f"  {name:<15} {count:4}只")
    
    print("=" * 75)
    
    # 涨幅 5%-7%
    target = get_rank_range(5, 7, stocks)
    
    print(f"\n📈 涨幅 5%-7% 股票 ({len(target)}只):")
    
    if target:
        for i, s in enumerate(target[:20], 1):
            print(f"{i:2}. {s['code']} {s['name']:8} ¥{s['current']:7.2f} {s['change_pct']:+6.1f}%")
        
        if len(target) > 20:
            print(f"... 还有 {len(target)-20}只")
    
    print("=" * 75)

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"✅ **总耗时**: {total_elapsed/60:.1f}分钟")
