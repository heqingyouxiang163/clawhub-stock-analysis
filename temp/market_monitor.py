#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中监控 - 腾讯财经快速版
获取 A 股市场情绪、涨幅分布、主升浪股票
"""

import akshare as ak
import pandas as pd
from datetime import datetime

def get_market_data():
    """获取全市场实时行情"""
    try:
        # 获取全部 A 股实时行情
        df = ak.stock_zh_a_spot_em()
        return df
    except Exception as e:
        print(f"获取行情失败：{e}")
        return None

def analyze_market(df):
    """分析市场数据"""
    if df is None or len(df) == 0:
        return None
    
    # 计算涨跌停家数（A 股涨停 10%, 创业板/科创板 20%, ST 5%）
    # 简化处理：涨幅>=9.5% 算涨停，<=-9.5% 算跌停
    limit_up = df[df['涨跌幅'] >= 9.5]
    limit_down = df[df['涨跌幅'] <= -9.5]
    
    # 涨幅分布
    up_5_7 = df[(df['涨跌幅'] >= 5) & (df['涨跌幅'] < 7)]  # 主升浪
    up_7_10 = df[(df['涨跌幅'] >= 7) & (df['涨跌幅'] < 9.5)]  # 强势
    up_3_5 = df[(df['涨跌幅'] >= 3) & (df['涨跌幅'] < 5)]  # 跟涨
    up_0_3 = df[(df['涨跌幅'] >= 0) & (df['涨跌幅'] < 3)]  # 微涨
    down_0_3 = df[(df['涨跌幅'] < 0) & (df['涨跌幅'] >= -3)]  # 微跌
    down_3_5 = df[(df['涨跌幅'] < -3) & (df['涨跌幅'] >= -5)]  # 回调
    down_5_10 = df[(df['涨跌幅'] < -5) & (df['涨跌幅'] >= -9.5)]  # 大跌
    
    total = len(df)
    
    return {
        'total': total,
        'limit_up': len(limit_up),
        'limit_down': len(limit_down),
        'up_5_7': len(up_5_7),
        'up_7_10': len(up_7_10),
        'up_3_5': len(up_3_5),
        'up_0_3': len(up_0_3),
        'down_0_3': len(down_0_3),
        'down_3_5': len(down_3_5),
        'down_5_10': len(down_5_10),
        'up_5_7_stocks': up_5_7.sort_values('涨跌幅', ascending=False).head(20)
    }

def get_sentiment_score(stats):
    """计算市场情绪分数 (0-100)"""
    up_count = stats['up_7_10'] + stats['up_5_7'] + stats['up_3_5'] + stats['up_0_3']
    down_count = stats['down_0_3'] + stats['down_3_5'] + stats['down_5_10'] + stats['limit_down']
    
    if up_count + down_count == 0:
        return 50
    
    up_ratio = up_count / (up_count + down_count)
    score = int(up_ratio * 100)
    
    # 涨停跌停加权
    score += min(stats['limit_up'] * 2, 20)
    score -= min(stats['limit_down'] * 2, 20)
    
    return max(0, min(100, score))

def generate_advice(stats, sentiment):
    """生成午后操作建议"""
    if sentiment >= 70:
        return "🟢 情绪火热：可适度参与主升浪 (5%-7%) 个股，关注涨停梯队完整性，仓位可提升至 50%-60%"
    elif sentiment >= 55:
        return "🟡 情绪温和：精选个股为主，关注 5%-7% 主升浪股票的板块效应，仓位控制在 40% 以内"
    elif sentiment >= 40:
        return "🟠 情绪偏弱：谨慎观望，等待尾盘方向选择，不宜追高，仓位降至 30% 以下"
    else:
        return "🔴 情绪冰点：建议空仓或轻仓 (<20%) 防守，等待明日新机会，宁可错过不做错"

def main():
    print("🦞 盘中监控 - 腾讯财经快速版")
    print("=" * 50)
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 获取数据
    print("📊 获取市场数据...")
    df = get_market_data()
    
    if df is None:
        print("❌ 数据获取失败，请检查网络或 API 状态")
        return
    
    # 分析数据
    stats = analyze_market(df)
    if stats is None:
        print("❌ 数据分析失败")
        return
    
    sentiment = get_sentiment_score(stats)
    
    # 输出报告
    print()
    print("📈 市场情绪")
    print(f"  涨停家数：{stats['limit_up']}")
    print(f"  跌停家数：{stats['limit_down']}")
    print(f"  情绪分数：{sentiment}/100")
    print()
    
    print("📊 涨幅分布")
    print(f"  ≥7% (强势):  {stats['up_7_10']} 只")
    print(f"  5%-7% (主升): {stats['up_5_7']} 只")
    print(f"  3%-5% (跟涨): {stats['up_3_5']} 只")
    print(f"  0%-3% (微涨): {stats['up_0_3']} 只")
    print(f"  -3%-0% (微跌): {stats['down_0_3']} 只")
    print(f"  -5%--3% (回调): {stats['down_3_5']} 只")
    print(f"  <-5% (大跌):  {stats['down_5_10']} 只")
    print()
    
    print("🚀 主升浪股票 (5%-7%, 前 20 只)")
    stocks_df = stats['up_5_7_stocks']
    if len(stocks_df) > 0:
        for i, row in stocks_df.iterrows():
            code = row.get('代码', 'N/A')
            name = row.get('名称', 'N/A')
            change = row.get('涨跌幅', 0)
            price = row.get('最新价', 0)
            print(f"  {code} {name}: {change:+.2f}% @ ¥{price}")
    else:
        print("  暂无 5%-7% 区间股票")
    print()
    
    print("💡 午后操作建议")
    advice = generate_advice(stats, sentiment)
    print(f"  {advice}")
    print()
    print("=" * 50)

if __name__ == "__main__":
    main()
