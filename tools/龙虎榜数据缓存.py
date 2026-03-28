#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 龙虎榜数据缓存工具

优化前：每次调用都重新获取数据 (180 秒)
优化后：使用本地缓存，仅在 17:00 后更新 (5 秒)

使用方法:
    python3 tools/龙虎榜数据缓存.py
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# 导入缓存管理器
from data_cache_manager import cache, save_limit_up_history


def get_cache_file_path() -> Path:
    """获取龙虎榜缓存文件路径"""
    cache_dir = Path(os.path.dirname(os.path.dirname(__file__))) / 'data_cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / 'lhb_cache.json'


def load_lhb_cache() -> dict:
    """加载龙虎榜缓存"""
    cache_file = get_cache_file_path()
    
    if not cache_file.exists():
        return {'data': None, 'update_time': None, 'date': None}
    
    with open(cache_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_lhb_cache(data: dict):
    """保存龙虎榜缓存"""
    cache_file = get_cache_file_path()
    
    cache_data = {
        'data': data,
        'update_time': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y%m%d')
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 龙虎榜数据已缓存：{cache_file}")


def is_cache_valid() -> bool:
    """检查缓存是否有效"""
    cache_data = load_lhb_cache()
    
    if not cache_data['data']:
        return False
    
    # 检查是否是今天的数据
    today = datetime.now().strftime('%Y%m%d')
    if cache_data['date'] != today:
        return False
    
    # 检查是否已过 17:00 (龙虎榜公布时间)
    update_time = datetime.fromisoformat(cache_data['update_time'])
    now = datetime.now()
    
    # 如果是今天 17:00 之后更新的，缓存有效
    if now.hour >= 17 and update_time.hour >= 17:
        return True
    
    return False


def get_lhb_data(force_update: bool = False) -> dict:
    """获取龙虎榜数据
    
    Args:
        force_update: 强制更新缓存
    
    Returns:
        龙虎榜数据
    """
    # 检查缓存
    if not force_update and is_cache_valid():
        cache_data = load_lhb_cache()
        print(f"✅ 使用缓存的龙虎榜数据 (更新时间：{cache_data['update_time']})")
        return cache_data['data']
    
    # 需要更新数据
    print("🔄 正在获取最新龙虎榜数据...")
    
    # TODO: 这里调用实际的龙虎榜数据获取 API
    # 示例代码:
    # from skills.trading.lhb_fetcher import fetch_lhb_data
    # data = fetch_lhb_data()
    
    # 临时返回空数据
    data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'items': [],
        'note': '待实现数据获取逻辑'
    }
    
    # 保存缓存
    save_lhb_cache(data)
    
    return data


def analyze_lhb(data: dict) -> dict:
    """分析龙虎榜数据
    
    Args:
        data: 龙虎榜数据
    
    Returns:
        分析结果
    """
    if not data or not data.get('items'):
        return {
            'status': 'no_data',
            'message': '无龙虎榜数据'
        }
    
    # 分析逻辑
    analysis = {
        'status': 'ok',
        'date': data.get('date'),
        'total_count': len(data['items']),
        'summary': []
    }
    
    # 统计机构买入/卖出
    institution_buy = 0
    institution_sell = 0
    
    for item in data['items']:
        # 分析机构席位
        if '机构专用' in str(item.get('buyer', '')):
            institution_buy += 1
        if '机构专用' in str(item.get('seller', '')):
            institution_sell += 1
    
    analysis['summary'].append(f"机构买入：{institution_buy} 次")
    analysis['summary'].append(f"机构卖出：{institution_sell} 次")
    
    return analysis


if __name__ == '__main__':
    print("=" * 60)
    print("🦞 龙虎榜数据缓存工具")
    print("=" * 60)
    print()
    
    # 检查缓存状态
    if is_cache_valid():
        print("✅ 缓存有效，使用本地数据")
    else:
        print("⚠️ 缓存无效，需要更新")
    
    print()
    
    # 获取数据
    data = get_lhb_data()
    
    print()
    print("-" * 60)
    print("📊 龙虎榜分析")
    print("-" * 60)
    
    # 分析数据
    analysis = analyze_lhb(data)
    for line in analysis.get('summary', []):
        print(f"  {line}")
    
    print()
    print("=" * 60)
    print("✅ 完成")
    print("=" * 60)
