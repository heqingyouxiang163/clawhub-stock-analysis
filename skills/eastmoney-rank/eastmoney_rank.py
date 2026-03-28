#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富 - 实时涨幅榜
获取沪深 A 股全市场实时涨幅排名
"""

import requests
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# ==================== 配置区 ====================

CACHE_FILE = "/home/admin/openclaw/workspace/temp/涨幅榜缓存.json"
CACHE_TTL = 120  # 2 分钟缓存


# ==================== 缓存管理 ====================

def load_cache():
    """加载缓存"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 检查是否过期
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


# ==================== 数据获取 ====================

def fetch_market_page(page, page_size=500, market_type=''):
    """
    获取单页股票数据
    
    Args:
        page: 页码 (从 1 开始)
        page_size: 每页数量 (最大 500)
        market_type: 市场类型 ('m:0'深市，'m:1'沪市，空=全部)
    
    Returns:
        list: 股票数据列表
    """
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    
    # 市场筛选
    if market_type:
        fs = market_type
    else:
        fs = "m:0+m:1"  # 深市 + 沪市
    
    params = {
        'pn': page,
        'pz': page_size,
        'po': 1,  # 降序
        'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2,
        'invt': 2,
        'fid': 'f3',  # 按涨幅排序
        'fs': fs,
        'fields': 'f12,f14,f3,f11,f17,f18,f19,f20,f37,f38,f45'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10,
                               headers={'User-Agent': 'Mozilla/5.0'})
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        if data.get('data') and data['data'].get('diff'):
            stocks = data['data']['diff']
            
            result = []
            for s in stocks:
                code = s.get('f12', '')
                name = s.get('f14', '')
                change_pct = s.get('f3', 0)
                current = s.get('f20', 0)
                
                # 过滤无效数据
                if not code or not name or current <= 0:
                    continue
                
                # 过滤 ST 股 (可选)
                # if 'ST' in name:
                #     continue
                
                result.append({
                    'code': code,
                    'name': name,
                    'change_pct': change_pct,
                    'current': current,
                    'open': s.get('f11', 0),
                    'high': s.get('f17', 0),
                    'low': s.get('f18', 0),
                    'prev_close': s.get('f19', 0),
                    'amount': s.get('f37', 0),
                    'turnover': s.get('f38', 0),
                    'pe': s.get('f45', 0)
                })
            
            return result
        else:
            return []
            
    except Exception as e:
        print(f"⚠️ 获取第{page}页失败：{str(e)[:40]}")
        return []


def get_full_rank(use_cache=True, exclude_st=False, exclude_cyb=False, exclude_kcb=False):
    """
    获取全市场涨幅榜
    
    Args:
        use_cache: 是否使用缓存
        exclude_st: 排除 ST 股
        exclude_cyb: 排除创业板 (300/301)
        exclude_kcb: 排除科创板 (688/689)
    
    Returns:
        list: 股票数据列表，按涨幅降序排列
    """
    # 检查缓存
    if use_cache:
        cached = load_cache()
        if cached:
            print(f"✅ 使用缓存 ({len(cached)}只)")
            return cached
    
    print("📊 获取全市场涨幅榜...")
    start = time.time()
    
    all_stocks = []
    page = 1
    
    while True:
        stocks = fetch_market_page(page)
        
        if not stocks:
            break
        
        all_stocks.extend(stocks)
        print(f"  第{page}页：{len(stocks)}只 (累计{len(all_stocks)}只)")
        
        # 如果返回数量不足 500，说明已是最后一页
        if len(stocks) < 500:
            break
        
        page += 1
        time.sleep(0.3)  # 避免请求过快
    
    # 过滤
    if exclude_st:
        all_stocks = [s for s in all_stocks if 'ST' not in s['name']]
    
    if exclude_cyb:
        all_stocks = [s for s in all_stocks if not s['code'].startswith(('300', '301'))]
    
    if exclude_kcb:
        all_stocks = [s for s in all_stocks if not s['code'].startswith(('688', '689'))]
    
    # 保存缓存
    save_cache(all_stocks)
    
    elapsed = time.time() - start
    print(f"✅ 获取完成：{len(all_stocks)}只，耗时{elapsed:.1f}秒")
    
    return all_stocks


def get_rank_range(min_pct, max_pct, use_cache=True):
    """
    获取指定涨幅范围的股票
    
    Args:
        min_pct: 最小涨幅
        max_pct: 最大涨幅
        use_cache: 是否使用缓存
    
    Returns:
        list: 符合条件的股票，按涨幅降序
    """
    stocks = get_full_rank(use_cache=use_cache)
    
    result = [s for s in stocks if min_pct <= s['change_pct'] <= max_pct]
    result.sort(key=lambda x: x['change_pct'], reverse=True)
    
    return result


def get_limit_up_stocks(use_cache=True):
    """
    获取涨停股 (涨幅≥9.5%)
    
    Args:
        use_cache: 是否使用缓存
    
    Returns:
        list: 涨停股列表
    """
    stocks = get_full_rank(use_cache=use_cache)
    
    result = [s for s in stocks if s['change_pct'] >= 9.5]
    result.sort(key=lambda x: x['change_pct'], reverse=True)
    
    return result


def get_main_board_rank(use_cache=True):
    """
    获取沪深主板涨幅榜 (排除创业板/科创板)
    
    Args:
        use_cache: 是否使用缓存
    
    Returns:
        list: 沪深主板股票列表
    """
    return get_full_rank(use_cache=use_cache, exclude_cyb=True, exclude_kcb=True)


def get_market_stats(use_cache=True):
    """
    获取市场涨幅分布统计
    
    Args:
        use_cache: 是否使用缓存
    
    Returns:
        dict: 涨幅分布统计
    """
    stocks = get_full_rank(use_cache=use_cache)
    
    stats = {
        'limit_up': 0,      # ≥9.5%
        'strong_8_10': 0,   # 8-9.5%
        'strong_7_8': 0,    # 7-8%
        'rising_5_7': 0,    # 5-7%
        'rising_3_5': 0,    # 3-5%
        'rising_0_3': 0,    # 0-3%
        'falling': 0,       # <0%
    }
    
    for s in stocks:
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


# ==================== 导入依赖 ====================

import os


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 75)
    print("🦞 东方财富 - 实时涨幅榜")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 获取全市场
    stocks = get_full_rank(use_cache=False)
    
    print()
    print("=" * 75)
    print("📊 涨幅分布:")
    print("=" * 75)
    
    stats = get_market_stats()
    print(f"  涨停 (≥9.5%)：  {stats['limit_up']:4}只")
    print(f"  8-9.5%:        {stats['strong_8_10']:4}只")
    print(f"  7-8%:          {stats['strong_7_8']:4}只")
    print(f"  5-7%:          {stats['rising_5_7']:4}只")
    print(f"  3-5%:          {stats['rising_3_5']:4}只")
    print(f"  0-3%:          {stats['rising_0_3']:4}只")
    print(f"  下跌：          {stats['falling']:4}只")
    print("=" * 75)
    
    # 涨幅 5%-7%
    target = get_rank_range(5, 7)
    
    print(f"\n📈 涨幅 5%-7% 股票 ({len(target)}只):")
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
    
    print("=" * 75)
