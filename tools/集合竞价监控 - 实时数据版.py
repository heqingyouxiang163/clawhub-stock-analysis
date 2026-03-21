#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集合竞价监控 - 实时数据技能版 (优化版)
使用 realtime-monitor-3min 技能，速度提升 100 倍
"""

import sys
import os
import time

# 添加实时数据技能路径
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/realtime-monitor-3min')

from realtime_monitor import get_realtime_data, get_full_market_scan
from datetime import datetime


def main():
    """集合竞价监控主函数"""
    start = time.time()
    
    print("=" * 80)
    print("📊 集合竞价监控 - 实时数据技能版")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 使用实时数据技能获取全市场数据
    print("📊 获取全市场数据 (实时数据技能 v2.0)...")
    stocks = get_full_market_scan(use_cache=False)
    
    step1_time = time.time()
    print(f"✅ 获取{len(stocks)}只股票，耗时{(step1_time-start)*1000:.0f}毫秒")
    print()
    
    # 筛选涨幅前 30 名
    print("🔍 筛选涨幅前 30 名...")
    top30 = sorted(stocks, key=lambda x: x.get('change_pct', 0), reverse=True)[:30]
    
    step2_time = time.time()
    print(f"✅ 筛选完成，耗时{(step2_time-step1_time)*1000:.0f}毫秒")
    print()
    
    # 输出简洁报告
    print("-" * 80)
    print("📈 集合竞价涨幅榜 (前 30 名)")
    print("-" * 80)
    print()
    
    for i, stock in enumerate(top30, 1):
        code = stock.get('code', '')
        name = stock.get('name', '')
        change_pct = stock.get('change_pct', 0)
        current = stock.get('current', 0)
        
        print(f"{i:2}. {code} {name:<10} {change_pct:+6.1f}% ¥{current:>8.2f}")
    
    print()
    print("-" * 80)
    print(f"✅ 总计：{len(top30)}只")
    print(f"⏱️ 总耗时：{(time.time()-start)*1000:.0f}毫秒")
    print("=" * 80)
    
    # 返回结果供 AI 处理
    return {
        'stocks': top30,
        'duration_ms': (time.time() - start) * 1000,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


if __name__ == "__main__":
    result = main()
    
    # 简洁输出 (减少 AI 处理时间)
    print()
    print("💡 操作建议:")
    print("   - 关注涨幅前 5 名")
    print("   - 注意成交量配合")
    print("   - 设置好止损位")
