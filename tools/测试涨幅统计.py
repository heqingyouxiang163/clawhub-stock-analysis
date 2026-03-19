#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试腾讯财经涨幅数据准确性
统计今日收盘涨幅 5%-7% 的沪深股票数量
"""

import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
from 腾讯财经_API import get_all_stock_pool
from datetime import datetime


def is_main_board(code):
    """判断是否沪深主板 (排除创业板/科创板)"""
    # 沪市主板：600/601/603/605
    # 深市主板：000/001/002/003
    # 创业板：300/301 (排除)
    # 科创板：688/689 (排除)
    
    if code.startswith('6'):
        return code[:3] in ['600', '601', '603', '605']
    elif code.startswith('0'):
        return code[:3] in ['000', '001', '002', '003']
    return False


def main():
    print("=" * 75)
    print("🦞 腾讯财经 - 涨幅 5%-7% 沪深主板股票统计")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 获取全部股票池
    data = get_all_stock_pool()
    
    if not data:
        print("❌ 获取数据失败")
        return
    
    # 筛选沪深主板 + 涨幅 5%-7%
    target_stocks = []
    
    for code, d in data.items():
        change_pct = d.get('change_pct', 0)
        
        # 只统计沪深主板
        if not is_main_board(code):
            continue
        
        # 涨幅 5%-7%
        if 5 <= change_pct <= 7:
            target_stocks.append({
                'code': code,
                'name': d.get('name', '?'),
                'change_pct': change_pct,
                'current': d.get('current', 0)
            })
    
    # 按涨幅排序
    target_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    # 输出结果
    print(f"📊 统计结果:")
    print(f"  股票池总数：{len(data)}只")
    print(f"  沪深主板数：{sum(1 for c in data if is_main_board(c))}只")
    print(f"  涨幅 5%-7%:  {len(target_stocks)}只")
    print()
    
    if target_stocks:
        print(f"📈 涨幅 5%-7% 股票列表 ({len(target_stocks)}只):")
        print()
        print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>8} {'现价':>10}")
        print("-" * 50)
        
        for i, s in enumerate(target_stocks, 1):
            print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+7.1f}% ¥{s['current']:>8.2f}")
        
        print("-" * 50)
    else:
        print("⚠️ 股票池中无涨幅 5%-7% 的沪深主板股票")
    
    print()
    
    # 完整涨幅分布
    print("📊 完整涨幅分布 (仅沪深主板):")
    
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
        count = sum(1 for c, d in data.items() 
                   if is_main_board(c) and min_pct <= d.get('change_pct', 0) < max_pct)
        if count > 0:
            print(f"  {name:<15} {count:3}只")
    
    print("=" * 75)
    
    # 验证提示
    print()
    print("💡 数据验证提示:")
    print(f"  • 腾讯财经股票池：{len(data)}只 (沪深 300+ 热点)")
    print(f"  • 实际全市场沪深主板：约 3500 只")
    print(f"  • 覆盖率：约 {len(data)/35:.1f}%")
    print()
    print("⚠️ 注意：腾讯财经只返回部分股票，不是全市场数据")
    print("   如需完整涨幅榜，建议对比东方财富/同花顺数据")
    print("=" * 75)


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

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    main()
