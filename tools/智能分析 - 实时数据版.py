#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分析 - 实时数据技能版 (优化版)
使用 realtime-monitor-3min 技能 + 持仓分析
"""

import sys
import os
import time
import json

# 添加实时数据技能路径
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/realtime-monitor-3min')

from realtime_monitor import get_realtime_data
from datetime import datetime


# 统一引用持仓配置文件
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
from 持仓配置 import HOLDINGS


def main():
    """智能分析主函数"""
    start = time.time()
    
    print("=" * 80)
    print("🧠 智能分析 - 实时数据技能版")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 获取持仓股实时数据
    print("📊 获取持仓股数据...")
    codes = [h['code'] for h in HOLDINGS]
    stocks_data = get_realtime_data(codes, use_cache=False)
    
    step1_time = time.time()
    print(f"✅ 获取{len(stocks_data)}只，耗时{(step1_time-start)*1000:.0f}毫秒")
    print()
    
    # 分析每只持仓
    print("-" * 80)
    print("📈 持仓分析")
    print("-" * 80)
    print()
    
    total_profit = 0
    for holding in HOLDINGS:
        code = holding['code']
        cost = holding['cost']
        
        # 查找对应数据
        stock = next((s for s in stocks_data if s['code'] == code), None)
        if not stock:
            continue
        
        current = stock.get('current', 0)
        change_pct = stock.get('change_pct', 0)
        
        # 计算盈亏
        profit_pct = (current - cost) / cost * 100
        profit_str = f"+{profit_pct:.2f}%" if profit_pct > 0 else f"{profit_pct:.2f}%"
        
        # 评分
        score = 0
        if change_pct > 5:
            score += 40
        elif change_pct > 3:
            score += 30
        elif change_pct > 0:
            score += 20
        else:
            score += 10
        
        if current > cost * 1.05:
            score += 30
        elif current > cost:
            score += 20
        
        rating = "🟢 强势" if score >= 60 else "🟡 震荡" if score >= 40 else "🔴 弱势"
        
        print(f"{code} {holding['name']}")
        print(f"   现价：¥{current:.2f}  涨幅：{change_pct:+.1f}%")
        print(f"   成本：¥{cost:.3f}  盈亏：{profit_str}")
        print(f"   评分：{score}分  {rating}")
        print()
        
        total_profit += profit_pct
    
    print("-" * 80)
    print(f"⏱️ 总耗时：{(time.time()-start)*1000:.0f}毫秒")
    print("=" * 80)
    
    # 返回结果
    return {
        'holdings': HOLDINGS,
        'stocks_data': stocks_data,
        'duration_ms': (time.time() - start) * 1000,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


if __name__ == "__main__":
    result = main()
    
    # 简洁操作建议
    print()
    print("💡 操作建议:")
    print("   - 强势股：持有/加仓")
    print("   - 震荡股：观望")
    print("   - 弱势股：考虑止损")
    print("   - 设置好止损位 (-5%)")
