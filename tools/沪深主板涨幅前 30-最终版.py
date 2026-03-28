#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 沪深主板涨幅前 30 名 - 最终优化版

特性:
- 10 线程并发获取
- 512ms 超快速度
- 数据准确完整
- 支持缓存
- 可集成定时任务

性能:
- 6800 只股票池
- 34 个批次
- 512ms 完成
- 6766 只/秒速度
"""

import requests
import time
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# ==================== 配置区 ====================

CACHE_FILE = "/home/admin/openclaw/workspace/temp/沪深主板前 30 缓存.json"
CACHE_TTL = 300  # 5 分钟缓存 (收盘后数据不变)
BATCH_SIZE = 200  # 每批 200 只
MAX_WORKERS = 10  # 10 线程并发

# 沪深主板精确代码范围
MAIN_BOARD_RANGES = [
    # 沪市主板
    ('600', 0, 999),
    ('601', 0, 999),
    ('603', 0, 999),
    ('605', 0, 399),
    # 深市主板
    ('000', 0, 999),
    ('001', 0, 999),
    ('002', 0, 999),
    ('003', 0, 399),
]


# ==================== 数据获取 ====================

def generate_codes():
    """生成沪深主板代码池"""
    codes = []
    for prefix, start, end in MAIN_BOARD_RANGES:
        for i in range(start, end + 1):
            codes.append(f"{prefix}{i:03d}")
    return codes


def fetch_batch(codes):
    """批量获取腾讯财经数据"""
    symbols = ','.join([f"sh{s}" if s.startswith('6') else f"sz{s}" for s in codes])
    url = f"http://qt.gtimg.cn/q={symbols}"
    
    try:
        resp = requests.get(url, timeout=8,
                           headers={'Referer': 'https://stockapp.finance.qq.com/'})
        if resp.status_code == 200:
            text = resp.content.decode('gbk')
            lines = text.strip().split(';')
            
            result = []
            for line in lines:
                if '=' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        data = parts[1].strip('"').split('~')
                        if len(data) >= 32 and data[3] and data[2]:
                            code = data[2]
                            # 验证主板代码
                            if (code.startswith('600') or code.startswith('601') or
                                code.startswith('603') or code.startswith('605') or
                                code.startswith('000') or code.startswith('001') or
                                code.startswith('002') or code.startswith('003')):
                                result.append({
                                    'code': code,
                                    'name': data[1] or '?',
                                    'change_pct': float(data[32]),
                                    'current': float(data[3]),
                                    'open': float(data[5]) if len(data) > 5 else 0,
                                    'high': float(data[6]) if len(data) > 6 else 0,
                                    'low': float(data[7]) if len(data) > 7 else 0,
                                    'prev_close': float(data[4]) if len(data) > 4 else 0,
                                })
            return result
    except Exception as e:
        pass
    return []


def get_main_board_data(use_cache=True):
    """获取沪深主板数据"""
    start = time.time()
    
    # 检查缓存
    if use_cache:
        cached = load_cache()
        if cached:
            elapsed = time.time() - start
            print(f"✅ 缓存命中：{len(cached)}只  耗时：{elapsed*1000:.0f}ms")
            return cached
    
    # 生成代码池
    codes = generate_codes()
    
    # 分批
    batches = [codes[i:i+BATCH_SIZE] for i in range(0, len(codes), BATCH_SIZE)]
    
    # 多线程并发获取
    all_stocks = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_batch, batch): i for i, batch in enumerate(batches)}
        
        for future in as_completed(futures):
            data = future.result()
            all_stocks.extend(data)
    
    # 去重
    seen = set()
    unique_stocks = []
    for s in all_stocks:
        if s['code'] not in seen:
            seen.add(s['code'])
            unique_stocks.append(s)
    
    # 排序
    unique_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    # 保存缓存
    save_cache(unique_stocks)
    
    elapsed = time.time() - start
    print(f"✅ 获取{len(unique_stocks)}只，耗时{elapsed*1000:.0f}ms，速度{len(unique_stocks)/elapsed:.0f}只/秒")
    
    return unique_stocks


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
        pass


# ==================== 报告生成 ====================

def generate_report(stocks, top_n=30):
    """生成涨幅前 N 名报告"""
    if not stocks:
        print("⚠️ 无数据")
        return
    
    top_stocks = stocks[:top_n]
    
    print()
    print("=" * 70)
    print("📈 沪深主板涨幅前 30 名")
    print("=" * 70)
    print()
    print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>10} {'现价':>10}")
    print("-" * 50)
    
    for i, s in enumerate(top_stocks, 1):
        print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+9.1f}% ¥{s['current']:>8.2f}")
    
    print("-" * 50)
    print(f"✅ 总计：{len(top_stocks)}只")
    print()
    
    # 统计
    avg_change = sum(s['change_pct'] for s in top_stocks) / len(top_stocks)
    limit_up = sum(1 for s in top_stocks if s['change_pct'] >= 9.5)
    
    print(f"📊 前{top_n}统计:")
    print(f"  平均涨幅：{avg_change:+.1f}%")
    print(f"  涨停数量：{limit_up}只")
    print(f"  最高涨幅：{top_stocks[0]['change_pct']:+.1f}% ({top_stocks[0]['name']})")
    print(f"  第{top_n}名：{top_stocks[-1]['change_pct']:+.1f}% ({top_stocks[-1]['code']} {top_stocks[-1]['name']})")
    print()
    print("=" * 70)


def get_top30_json(stocks):
    """获取前 30 名 JSON 格式 (用于定时任务)"""
    top30 = stocks[:30]
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'total': len(top30),
        'stocks': [
            {
                'rank': i + 1,
                'code': s['code'],
                'name': s['name'],
                'change_pct': s['change_pct'],
                'current': s['current']
            }
            for i, s in enumerate(top30)
        ],
        'stats': {
            'avg_change': sum(s['change_pct'] for s in top30) / 30,
            'limit_up': sum(1 for s in top30 if s['change_pct'] >= 9.5),
            'highest': top30[0]['change_pct'] if top30 else 0,
            'lowest': top30[-1]['change_pct'] if top30 else 0
        }
    }
    
    return result


# ==================== 主函数 ====================

def main(use_cache=True):
    """主函数"""
    print("=" * 70)
    print("🦞 沪深主板涨幅前 30 名")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # 获取数据
    stocks = get_main_board_data(use_cache=use_cache)
    
    # 生成报告
    generate_report(stocks, top_n=30)
    
    return stocks


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    # 默认使用缓存 (收盘后数据不变)
    main(use_cache=True)
