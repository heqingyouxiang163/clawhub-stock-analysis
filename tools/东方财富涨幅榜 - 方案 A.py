#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富涨幅榜 + 腾讯财经价格
方案 A：东方财富获取全市场排名，腾讯财经补充准确价格
"""

import requests
import time
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


CACHE_FILE = "/home/admin/openclaw/workspace/temp/全市场涨幅榜缓存.json"
CACHE_TTL = 120  # 2 分钟


# ==================== 东方财富 - 获取涨幅排名 ====================

def fetch_em_rank_batch(page=1, page_size=500):
    """东方财富获取单页涨幅排名"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': page,
        'pz': page_size,
        'po': 1,
        'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2,
        'invt': 2,
        'fid': 'f3',
        'fs': 'm:0+m:1',  # 深市 + 沪市
        'fields': 'f12,f14,f3'  # 代码、名称、涨幅
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10,
                           headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('diff'):
                return data['data']['diff']
    except Exception as e:
        print(f"⚠️ 东方财富失败：{str(e)[:40]}")
    
    return []


def get_em_full_rank():
    """东方财富获取全市场涨幅排名"""
    print("📊 东方财富 - 获取涨幅排名...")
    start = time.time()
    
    all_stocks = []
    
    for page in range(1, 20):  # 最多 20 页 (10000 只)
        stocks = fetch_em_rank_batch(page)
        
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
        
        print(f"  第{page}页：{len(stocks)}只 (累计{len(all_stocks)}只)")
        
        if len(stocks) < 500:
            break
        
        time.sleep(0.2)
    
    elapsed = time.time() - start
    print(f"✅ 获取{len(all_stocks)}只股票排名，耗时{elapsed:.1f}秒")
    
    return all_stocks


# ==================== 腾讯财经 - 获取价格 ====================

def fetch_tencent_price_batch(codes):
    """腾讯财经批量获取价格"""
    if not codes:
        return {}
    
    # 转腾讯格式
    symbols = []
    for code in codes:
        if code.startswith('6'):
            symbols.append(f"sh{code}")
        else:
            symbols.append(f"sz{code}")
    
    code_list = ','.join(symbols[:150])  # 最多 150 只
    url = f"http://qt.gtimg.cn/q={code_list}"
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            text = resp.content.decode('gbk')
            lines = text.strip().split(';')
            
            result = {}
            for line in lines:
                if '=' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        data = parts[1].strip('"').split('~')
                        if len(data) >= 32 and data[3]:
                            code = data[2]
                            current = float(data[3]) if data[3] else 0
                            result[code] = {
                                'current': current,
                                'name': data[1] or '?',
                                'change_pct': float(data[32]) if len(data) > 32 else 0,
                                'open': float(data[5]) if len(data) > 5 else 0,
                                'high': float(data[6]) if len(data) > 6 else 0,
                                'low': float(data[7]) if len(data) > 7 else 0,
                                'prev_close': float(data[4]) if len(data) > 4 else 0,
                                'amount': float(data[37]) if len(data) > 37 else 0,
                                'turnover': float(data[39]) if len(data) > 39 else 0
                            }
            
            return result
    except Exception as e:
        print(f"⚠️ 腾讯财经失败：{str(e)[:40]}")
    
    return {}


def get_tencent_prices(codes, batch_size=150):
    """分批获取腾讯财经价格"""
    all_prices = {}
    
    print("📊 腾讯财经 - 获取价格数据...")
    
    # 多线程并发获取
    batches = [codes[i:i+batch_size] for i in range(0, len(codes), batch_size)]
    
    def fetch_batch(batch):
        return fetch_tencent_price_batch(batch)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_batch, batch): i for i, batch in enumerate(batches)}
        
        completed = 0
        for future in as_completed(futures):
            prices = future.result()
            all_prices.update(prices)
            completed += 1
            print(f"  批次{completed}/{len(batches)}: {len(prices)}只 (累计{len(all_prices)}只)")
    
    return all_prices


# ==================== 数据合并 ====================

def merge_data(em_stocks, tc_prices):
    """合并东方财富排名和腾讯财经价格"""
    merged = []
    
    for s in em_stocks:
        code = s['code']
        
        if code in tc_prices:
            p = tc_prices[code]
            merged.append({
                'code': code,
                'name': p['name'],
                'current': p['current'],
                'change_pct': p['change_pct'],
                'open': p.get('open', 0),
                'high': p.get('high', 0),
                'low': p.get('low', 0),
                'prev_close': p.get('prev_close', 0),
                'amount': p.get('amount', 0),
                'turnover': p.get('turnover', 0)
            })
        else:
            # 腾讯财经没有的股票，保留涨幅数据
            merged.append({
                'code': code,
                'name': s['name'],
                'current': 0,
                'change_pct': s['change_pct']
            })
    
    # 按涨幅排序
    merged.sort(key=lambda x: x['change_pct'], reverse=True)
    
    return merged


# ==================== 缓存管理 ====================

def load_cache():
    """加载缓存"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if time.time() - data.get('timestamp', 0) < CACHE_TTL:
                    return data.get('stocks', [])
    except:
        pass
    return None


def save_cache(stocks):
    """保存缓存"""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.time(),
                'stocks': stocks
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存缓存失败：{e}")


# ==================== 主接口 ====================

def get_full_rank(use_cache=True):
    """
    获取全市场涨幅榜 (东方财富排名 + 腾讯财经价格)
    
    Args:
        use_cache: 是否使用缓存
    
    Returns:
        list: 股票数据列表，按涨幅降序
    """
    # 检查缓存
    if use_cache:
        cached = load_cache()
        if cached:
            print(f"✅ 使用缓存 ({len(cached)}只)")
            return cached
    
    print("=" * 75)
    print("🦞 东方财富 + 腾讯财经 - 全市场涨幅榜")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 东方财富获取排名
    em_stocks = get_em_full_rank()
    print()
    
    # 腾讯财经获取价格
    codes = [s['code'] for s in em_stocks]
    tc_prices = get_tencent_prices(codes)
    print()
    
    # 合并数据
    merged = merge_data(em_stocks, tc_prices)
    
    # 保存缓存
    save_cache(merged)
    
    print("=" * 75)
    print(f"📊 获取完成：{len(merged)}只")
    print(f"  有价格数据：{sum(1 for s in merged if s['current'] > 0)}只")
    print(f"  无价格数据：{sum(1 for s in merged if s['current'] == 0)}只")
    print("=" * 75)
    
    return merged


def get_rank_range(min_pct, max_pct, use_cache=True):
    """获取指定涨幅范围的股票"""
    stocks = get_full_rank(use_cache=use_cache)
    result = [s for s in stocks if min_pct <= s['change_pct'] <= max_pct and s['current'] > 0]
    result.sort(key=lambda x: x['change_pct'], reverse=True)
    return result


def get_market_stats(use_cache=True):
    """获取市场涨幅分布统计"""
    stocks = get_full_rank(use_cache=use_cache)
    
    stats = {
        'limit_up': 0,
        'strong_8_10': 0,
        'strong_7_8': 0,
        'rising_5_7': 0,
        'rising_3_5': 0,
        'rising_0_3': 0,
        'falling': 0,
    }
    
    for s in stocks:
        if s['current'] == 0:  # 跳过无价格数据
            continue
        
        pct = s['change_pct']
        if pct >= 9.5:
            stats['limit_up'] += 1
        elif pct >= 8:
            stats['strong_8_10'] += 1
        elif pct >= 7:
            stats['strong_7_8'] += 1
        elif pct >= 5:
            stats['rising_5_7'] += 1
        elif pct >= 3:
            stats['rising_3_5'] += 1
        elif pct >= 0:
            stats['rising_0_3'] += 1
        else:
            stats['falling'] += 1
    
    return stats


# ==================== 测试 ====================

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print()
    stocks = get_full_rank(use_cache=False)
    
    print()
    print("📊 涨幅分布:")
    print()
    
    stats = get_market_stats()
    print(f"  涨停 (≥9.5%)：  {stats['limit_up']:4}只")
    print(f"  8-9.5%:        {stats['strong_8_10']:4}只")
    print(f"  7-8%:          {stats['strong_7_8']:4}只")
    print(f"  5-7%:          {stats['rising_5_7']:4}只")
    print(f"  3-5%:          {stats['rising_3_5']:4}只")
    print(f"  0-3%:          {stats['rising_0_3']:4}只")
    print(f"  下跌：          {stats['falling']:4}只")
    print()
    
    # 涨幅 5%-7%
    target = get_rank_range(5, 7)
    
    print(f"📈 涨幅 5%-7% 股票 ({len(target)}只):")
    print()
    
    if target:
        print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>8} {'现价':>10}")
        print("-" * 50)
        
        for i, s in enumerate(target[:30], 1):
            print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+7.1f}% ¥{s['current']:>8.2f}")
        
        if len(target) > 30:
            print(f"... 还有 {len(target)-30}只")
        
        print("-" * 50)
        print(f"✅ 总计：{len(target)}只")
    else:
        print("⚠️ 无涨幅 5%-7% 的股票")
    
    print()
