#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3 分钟实时监控 - 独立运行脚本
可直接运行或作为定时任务执行
"""

import sys
import time
from datetime import datetime

# 添加技能路径
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/realtime-monitor-3min')

from realtime_monitor import (
    get_realtime_data,
    get_full_market_scan,
    get_stocks_in_range,
    get_limit_up_stocks,
    start_monitoring,
    stop_monitoring
)


# ==================== 配置区 ====================

# 从统一持仓配置导入
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
from 持仓配置 import HOLDINGS

# 你的持仓股/关注股 (从持仓配置自动获取)
WATCHLIST = [h['code'] for h in HOLDINGS] if HOLDINGS else ['002342', '603778', '002828']

# 监控间隔 (秒)
MONITOR_INTERVAL = 180  # 3 分钟


# ==================== 回调函数 ====================

def on_data_update(data):
    """数据更新回调"""
    print("\n" + "=" * 75)
    print(f"📊 数据更新 - {data['timestamp']}")
    print("=" * 75)
    
    for s in data['stocks']:
        code = s['code']
        name = s['name']
        current = s.get('current', 0)
        change_pct = s.get('change_pct', 0)
        
        # 显示所有股票
        if current > 0:
            emoji = "🔺" if change_pct > 0 else "🔻" if change_pct < 0 else "⚪"
            print(f"{emoji} {code} {name}: ¥{current:.2f} ({change_pct:+.1f}%)")
    
    print("=" * 75)


def on_significant_change(data):
    """显著变化预警回调"""
    alerts = []
    
    for s in data['stocks']:
        change_pct = s.get('change_pct', 0)
        
        if change_pct >= 7:
            alerts.append(f"🚨 大涨预警：{s['code']} {s['name']} +{change_pct:.1f}%")
        elif change_pct <= -5:
            alerts.append(f"⚠️ 止损预警：{s['code']} {s['name']} {change_pct:.1f}%")
    
    if alerts:
        print("\n" + "!" * 75)
        print("🚨 重要提醒")
        print("!" * 75)
        for alert in alerts:
            print(f"  {alert}")
        print("!" * 75)


# ==================== 主函数 ====================

def run_once():
    """运行一次监控"""
    print(f"\n🦞 3 分钟实时监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    
    # 获取持仓股数据
    data = get_realtime_data(WATCHLIST)
    
    print(f"\n📊 持仓股监控 ({len(data)}只):")
    print("-" * 75)
    
    for s in data:
        code = s['code']
        name = s['name']
        current = s.get('current', 0)
        change_pct = s.get('change_pct', 0)
        
        if current > 0:
            emoji = "🔺" if change_pct > 0 else "🔻" if change_pct < 0 else "⚪"
            print(f"{emoji} {code} {name}: ¥{current:.2f} ({change_pct:+.1f}%)")
        else:
            print(f"⚪ {code} {name}: 无数据")
    
    print("-" * 75)
    
    # 检测显著变化
    on_significant_change({'stocks': data})


def run_continuous():
    """持续监控模式"""
    print(f"\n🦞 启动持续监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控股票：{WATCHLIST}")
    print(f"监控间隔：{MONITOR_INTERVAL}秒")
    print("按 Ctrl+C 停止监控\n")
    
    start_monitoring(
        interval=MONITOR_INTERVAL,
        codes=WATCHLIST,
        callback=on_data_update
    )
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断，停止监控...")
        stop_monitoring()
        print("✅ 监控已停止")


def scan_market():
    """全市场扫描"""
    print(f"\n🦞 全市场扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    
    # 获取全市场数据
    stocks = get_full_market_scan(use_cache=False)
    
    # 统计
    limit_up = [s for s in stocks if s.get('change_pct', 0) >= 9.5 and s.get('current', 0) > 0]
    rising_5_8 = [s for s in stocks if 5 <= s.get('change_pct', 0) < 8 and s.get('current', 0) > 0]
    
    print(f"\n📊 市场统计:")
    print(f"  全市场股票：{len(stocks)}只")
    print(f"  涨停股：{len(limit_up)}只")
    print(f"  主升浪 (5-8%): {len(rising_5_8)}只")
    
    # 显示涨停股
    if limit_up:
        print(f"\n🔥 涨停股 ({len(limit_up)}只):")
        print("-" * 75)
        for i, s in enumerate(limit_up[:20], 1):
            print(f"{i:2}. {s['code']} {s['name']}: +{s['change_pct']:.1f}% ¥{s['current']:.2f}")
        if len(limit_up) > 20:
            print(f"... 还有 {len(limit_up)-20}只")
    
    # 显示主升浪
    if rising_5_8:
        print(f"\n📈 主升浪 (5-8%, {len(rising_5_8)}只):")
        print("-" * 75)
        for i, s in enumerate(rising_5_8[:20], 1):
            print(f"{i:2}. {s['code']} {s['name']}: +{s['change_pct']:.1f}% ¥{s['current']:.2f}")
        if len(rising_5_8) > 20:
            print(f"... 还有 {len(rising_5_8)-20}只")
    
    print("=" * 75)


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='3 分钟实时监控脚本')
    parser.add_argument('mode', choices=['once', 'continuous', 'scan'],
                       help='运行模式：once=运行一次，continuous=持续监控，scan=全市场扫描')
    
    args = parser.parse_args()
    
    if args.mode == 'once':
        run_once()
    elif args.mode == 'continuous':
        run_continuous()
    elif args.mode == 'scan':
        scan_market()
