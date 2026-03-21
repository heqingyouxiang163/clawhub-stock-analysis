#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中监控 - 实时数据技能版 (优化版)
使用 realtime-monitor-3min 技能，速度提升 100 倍
"""

import sys
import os
import time

# 添加实时数据技能路径
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/realtime-monitor-3min')

from realtime_monitor import get_realtime_data, get_full_market_scan, get_stocks_in_range
from datetime import datetime


def main():
    """盘中监控主函数"""
    start = time.time()
    
    print("=" * 80)
    print("📊 盘中监控 - 实时数据技能版")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 使用实时数据技能获取全市场数据
    print("📊 获取全市场数据 (实时数据技能 v2.0)...")
    stocks = get_full_market_scan(use_cache=False)
    
    step1_time = time.time()
    print(f"✅ 获取{len(stocks)}只股票，耗时{(step1_time-start)*1000:.0f}毫秒")
    print()
    
    # 统计市场情绪
    limit_up = len([s for s in stocks if s.get('change_pct', 0) >= 9.5])
    falling = len([s for s in stocks if s.get('change_pct', 0) < 0])
    rising = len([s for s in stocks if s.get('change_pct', 0) > 0])
    
    # 筛选主升浪 (5-8%)
    print("🔍 筛选主升浪股票 (5-8%)...")
    main_rising = get_stocks_in_range(5, 8, use_cache=True)
    
    step2_time = time.time()
    print(f"✅ 找到{len(main_rising)}只，耗时{(step2_time-step1_time)*1000:.0f}毫秒")
    print()
    
    # 输出简洁报告
    print("-" * 80)
    print("📈 市场情绪")
    print("-" * 80)
    print(f"   涨停：{limit_up}只")
    print(f"   上涨：{rising}只")
    print(f"   下跌：{falling}只")
    print()
    
    print("-" * 80)
    print("🚀 主升浪股票 (5-8%，前 20 名)")
    print("-" * 80)
    print()
    
    for i, stock in enumerate(main_rising[:20], 1):
        code = stock.get('code', '')
        name = stock.get('name', '')
        change_pct = stock.get('change_pct', 0)
        current = stock.get('current', 0)
        turnover = stock.get('turnover', 0)
        
        print(f"{i:2}. {code} {name:<10} {change_pct:+6.1f}% ¥{current:>8.2f} 换手{turnover:>5.1f}%")
    
    print()
    print("-" * 80)
    print(f"✅ 总计：{len(main_rising)}只")
    print(f"⏱️ 总耗时：{(time.time()-start)*1000:.0f}毫秒")
    print("=" * 80)
    
    # 返回结果
    return {
        'limit_up': limit_up,
        'rising': rising,
        'falling': falling,
        'main_rising': main_rising[:20],
        'duration_ms': (time.time() - start) * 1000,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


if __name__ == "__main__":
    result = main()
    
    # 简洁操作建议
    print()
    print("💡 午后操作建议:")
    if result['limit_up'] > 50:
        print("   - 市场情绪火热，可积极操作")
    elif result['limit_up'] > 20:
        print("   - 市场情绪正常，选择性参与")
    else:
        print("   - 市场情绪低迷，谨慎观望")
    print("   - 关注主升浪前 5 名")
    print("   - 设置好止损位")
