#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 智能分析 (盘中快速版) - 14:00
数据源：AkShare + 腾讯财经
超时：90 秒
"""

import akshare as ak
import pandas as pd
from datetime import datetime

# 用户持仓
HOLDINGS = [
    {"name": "国新能源", "code": "600617", "cost": 4.223, "shares": 2433},
    {"name": "通鼎互联", "code": "002491", "cost": 10.085, "shares": 1000},
]

def get_realtime_data(code):
    """获取实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == code]
        if len(stock) > 0:
            return stock.iloc[0]
    except Exception as e:
        print(f"获取 {code} 行情失败：{e}")
    return None

def calc_score(current, prev_close, high, low, volume):
    """分时图战法评分 (0-100)"""
    score = 50  # 基础分
    
    # 涨跌幅评分 (+/- 30)
    pct = (current - prev_close) / prev_close * 100
    if pct > 5: score += 30
    elif pct > 3: score += 20
    elif pct > 1: score += 10
    elif pct < -5: score -= 30
    elif pct < -3: score -= 20
    elif pct < -1: score -= 10
    
    # 振幅评分 (+/- 20)
    amplitude = (high - low) / prev_close * 100
    if 3 <= amplitude <= 8: score += 20  # 健康振幅
    elif amplitude > 8: score += 10  # 活跃但风险高
    elif amplitude < 2: score -= 10  # 太闷
    
    # 量能评分 (+/- 20)
    if volume > 0:
        # 简化：有成交量就加分
        score += 10
    
    return max(0, min(100, score))

def analyze():
    """主分析函数"""
    print("=" * 60)
    print("🦞 龙虾智能分析 | 2026-03-27 14:00 (盘中)")
    print("=" * 60)
    
    total_profit = 0
    warnings = []
    
    for stock in HOLDINGS:
        code = stock["code"]
        data = get_realtime_data(code)
        
        if data is None:
            print(f"\n❌ {stock['name']}({code}): 数据获取失败")
            continue
        
        current = float(data['最新价'])
        prev_close = float(data['昨收'])
        high = float(data['最高'])
        low = float(data['最低'])
        volume = float(data['成交量']) if '成交量' in data else 0
        
        # 计算盈亏
        profit_pct = (current - stock["cost"]) / stock["cost"] * 100
        profit_amt = (current - stock["cost"]) * stock["shares"]
        total_profit += profit_amt
        
        # 评分
        score = calc_score(current, prev_close, high, low, volume)
        
        # 状态
        status = "🟢" if profit_pct > 0 else "🔴"
        
        print(f"\n{status} {stock['name']}({code})")
        print(f"   现价：¥{current:.2f} | 涨跌：{((current-prev_close)/prev_close*100):+.2f}%")
        print(f"   成本：¥{stock['cost']:.3f} | 盈亏：{profit_pct:+.2f}% ({profit_amt:+.2f}元)")
        print(f"   评分：{score}/100 | 振幅：{((high-low)/prev_close*100):.2f}%")
        
        # 预警
        if profit_pct <= -5:
            warnings.append(f"⚠️ {stock['name']}: 触及止损线 ({profit_pct:.2f}%)")
        elif profit_pct >= 10:
            warnings.append(f"✅ {stock['name']}: 触及止盈线 ({profit_pct:.2f}%)")
        elif score < 40:
            warnings.append(f"⚠️ {stock['name']}: 评分偏低 ({score}分)，建议观望")
    
    # 预警信号
    print("\n" + "=" * 60)
    print("🚨 预警信号")
    if warnings:
        for w in warnings:
            print(f"   {w}")
    else:
        print("   无预警，持仓正常")
    
    # 尾盘建议
    print("\n" + "=" * 60)
    print("📊 尾盘操作建议 (14:00)")
    if total_profit > 0:
        print(f"   总盈亏：+{total_profit:.2f}元 | 建议：持有，观察收盘")
    else:
        print(f"   总盈亏：{total_profit:.2f}元 | 建议：设置好止损，不急于操作")
    
    print("=" * 60)

if __name__ == "__main__":
    analyze()
