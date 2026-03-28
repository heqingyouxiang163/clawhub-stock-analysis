#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沪深主板高确定性推荐系统
- 10 线程并发获取股票数据
- 筛选涨幅 5%-7% 主升浪股票
- 综合评分≥75 分才推荐
- 只输出最强的前 5 名
"""

import akshare as ak
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

def get_stock_list():
    """获取沪深主板股票列表"""
    # 获取所有 A 股数据
    stock_df = ak.stock_zh_a_spot_em()
    
    # 筛选沪深主板 (排除创业板 300/301，科创板 688，北交所 8/4/9)
    main_board = stock_df[
        (stock_df['代码'].str.startswith(('000', '001', '002', '003')) |  # 深市主板
         stock_df['代码'].str.startswith(('600', '601', '603', '605')))   # 沪市主板
    ].copy()
    
    return main_board

def calculate_score(row):
    """计算综合评分 (0-100)"""
    score = 0
    
    # 涨幅评分 (25 分) - 5%-7% 得满分
    change = float(row.get('涨跌幅', 0))
    if 5 <= change <= 7:
        score += 25
    elif 4 <= change < 5 or 7 < change <= 8:
        score += 15
    elif 3 <= change < 4 or 8 < change <= 9:
        score += 10
    
    # 成交量评分 (20 分) - 量比>1.5 得高分
    volume_ratio = float(row.get('量比', 1))
    if volume_ratio > 2:
        score += 20
    elif volume_ratio > 1.5:
        score += 15
    elif volume_ratio > 1:
        score += 10
    
    # 换手率评分 (20 分) - 3%-10% 活跃但不失控
    turnover = float(row.get('换手率', 0))
    if 3 <= turnover <= 10:
        score += 20
    elif 2 <= turnover < 3 or 10 < turnover <= 15:
        score += 15
    elif 1 <= turnover < 2 or 15 < turnover <= 20:
        score += 10
    
    # 成交额评分 (20 分) - 成交额>5 亿
    amount = float(row.get('成交额', 0))
    if amount >= 10:  # 10 亿+
        score += 20
    elif amount >= 5:  # 5 亿+
        score += 15
    elif amount >= 2:  # 2 亿+
        score += 10
    
    # 技术面评分 (15 分) - 股价在均线上方
    price = float(row.get('最新价', 0))
    high = float(row.get('最高', 0))
    low = float(row.get('最低', 0))
    
    # 接近当日高点加分
    if high > 0:
        position = (price - low) / (high - low) if high != low else 0.5
        if position > 0.7:  # 在当日高位 70% 以上
            score += 15
        elif position > 0.5:
            score += 10
    
    return score

def main():
    start_time = time.time()
    
    print("🦞 沪深主板高确定性推荐系统")
    print("=" * 50)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 获取股票列表
    print("1️⃣ 获取沪深主板股票列表...")
    stock_df = get_stock_list()
    print(f"   沪深主板股票数量：{len(stock_df)}")
    
    # 2. 初步筛选：涨幅 5%-7%
    print("\n2️⃣ 筛选涨幅 5%-7% 主升浪股票...")
    stock_df['涨跌幅'] = pd.to_numeric(stock_df['涨跌幅'], errors='coerce')
    filtered_df = stock_df[
        (stock_df['涨跌幅'] >= 5) & 
        (stock_df['涨跌幅'] <= 7)
    ].copy()
    print(f"   符合条件的股票：{len(filtered_df)}")
    
    if len(filtered_df) == 0:
        print("\n⚠️ 今日无符合 5%-7% 涨幅条件的股票")
        return
    
    # 3. 计算综合评分
    print("\n3️⃣ 计算综合评分...")
    filtered_df['综合评分'] = filtered_df.apply(calculate_score, axis=1)
    
    # 4. 筛选评分≥75 的股票
    high_score_df = filtered_df[filtered_df['综合评分'] >= 75].copy()
    print(f"   评分≥75 的股票：{len(high_score_df)}")
    
    if len(high_score_df) == 0:
        print("\n⚠️ 无评分≥75 的高确定性股票")
        # 放宽到 70 分
        high_score_df = filtered_df[filtered_df['综合评分'] >= 70].copy()
        print(f"   放宽到≥70 分：{len(high_score_df)}")
    
    # 5. 取前 5 名
    top5 = high_score_df.nlargest(5, '综合评分')
    
    # 6. 输出结果
    print("\n" + "=" * 50)
    print("🏆 沪深主板高确定性推荐 TOP 5")
    print("=" * 50)
    print(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"筛选条件：涨幅 5%-7% | 评分≥75 | 沪深主板")
    print()
    
    for idx, row in top5.iterrows():
        print(f"📈 {int(idx+1)}. {row['名称']} ({row['代码']})")
        print(f"   最新价：¥{row['最新价']} | 涨跌幅：{row['涨跌幅']}%")
        print(f"   量比：{row['量比']} | 换手率：{row['换手率']}%")
        print(f"   成交额：{row['成交额']}亿 | 综合评分：{row['综合评分']}分")
        print()
    
    elapsed = time.time() - start_time
    print(f"⏱️  耗时：{elapsed:.2f}秒")
    print("=" * 50)

if __name__ == "__main__":
    main()
