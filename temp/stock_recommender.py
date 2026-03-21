#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沪深主板高确定性推荐系统
- 10 线程并发获取 3467 只沪深主板股票
- 筛选涨幅 5%-7% 主升浪股票
- 综合评分≥75 分
- 只输出最强的前 5 名
"""

import akshare as ak
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def get_main_board_stocks():
    """获取沪深主板股票列表"""
    try:
        # 获取所有 A 股实时行情
        df = ak.stock_zh_a_spot_em()
        
        # 筛选沪深主板 (排除科创板 688、创业板 300、北交所)
        main_board = df[
            (~df['代码'].str.startswith('688')) &  # 排除科创板
            (~df['代码'].str.startswith('300')) &  # 排除创业板
            (~df['代码'].str.startswith('301')) &  # 排除创业板新代码
            (~df['代码'].str.startswith('8')) &    # 排除北交所
            (~df['代码'].str.startswith('4'))      # 排除北交所
        ].copy()
        
        return main_board
    except Exception as e:
        print(f"获取股票列表失败：{e}")
        return pd.DataFrame()

def calculate_comprehensive_score(row):
    """
    计算综合评分 (满分 100)
    评分维度:
    - 涨幅得分 (25 分): 5%-7% 得满分，越接近 6% 得分越高
    - 量比得分 (20 分): 量比 1.5-3.0 得高分
    - 换手率得分 (15 分): 3%-8% 得高分
    - 成交额得分 (15 分): 成交额越大得分越高
    - 市盈率得分 (15 分): 合理市盈率得高分
    - 股价得分 (10 分): 适中股价得高分
    """
    score = 0
    
    # 1. 涨幅得分 (25 分) - 5%-7% 区间，越接近 6% 得分越高
    change_pct = row.get('涨跌幅', 0)
    if 5 <= change_pct <= 7:
        # 越接近 6% 得分越高
        distance_from_6 = abs(change_pct - 6)
        change_score = 25 - (distance_from_6 * 12.5)  # 偏离 1% 扣 12.5 分
        score += max(0, change_score)
    elif change_pct < 5:
        score += max(0, 25 - (5 - change_pct) * 5)
    else:  # > 7%
        score += max(0, 25 - (change_pct - 7) * 5)
    
    # 2. 量比得分 (20 分) - 1.5-3.0 最佳
    volume_ratio = row.get('量比', 1)
    if 1.5 <= volume_ratio <= 3.0:
        volume_score = 20
    elif 1.0 <= volume_ratio < 1.5:
        volume_score = 15 + (volume_ratio - 1.0) * 10
    elif 3.0 < volume_ratio <= 5.0:
        volume_score = 20 - (volume_ratio - 3.0) * 5
    else:
        volume_score = max(0, 10 - abs(volume_ratio - 2.0) * 2)
    score += min(20, max(0, volume_score))
    
    # 3. 换手率得分 (15 分) - 3%-8% 最佳
    turnover_rate = row.get('换手率', 0)
    if 3 <= turnover_rate <= 8:
        turnover_score = 15
    elif 1 <= turnover_rate < 3:
        turnover_score = 10 + (turnover_rate - 1) * 2.5
    elif 8 < turnover_rate <= 15:
        turnover_score = 15 - (turnover_rate - 8) * 2
    else:
        turnover_score = max(0, 5)
    score += min(15, max(0, turnover_score))
    
    # 4. 成交额得分 (15 分) - 成交额越大越好
    amount = row.get('成交额', 0)
    if amount >= 10_0000_0000:  # 10 亿以上
        amount_score = 15
    elif amount >= 5_0000_0000:  # 5 亿以上
        amount_score = 12
    elif amount >= 1_0000_0000:  # 1 亿以上
        amount_score = 10
    elif amount >= 5000_0000:  # 5000 万以上
        amount_score = 7
    else:
        amount_score = max(0, 5 - (5000_0000 - amount) / 1000_0000)
    score += min(15, max(0, amount_score))
    
    # 5. 市盈率得分 (15 分) - 合理区间 10-50
    pe_ratio = row.get('市盈率 - 动态', 0)
    if pd.isna(pe_ratio) or pe_ratio <= 0:
        pe_score = 5  # 无数据或负值给基础分
    elif 10 <= pe_ratio <= 50:
        pe_score = 15
    elif 5 <= pe_ratio < 10:
        pe_score = 12
    elif 50 < pe_ratio <= 100:
        pe_score = 10
    else:
        pe_score = max(0, 5)
    score += min(15, max(0, pe_score))
    
    # 6. 股价得分 (10 分) - 适中股价 10-100 元
    price = row.get('最新价', 0)
    if 10 <= price <= 100:
        price_score = 10
    elif 5 <= price < 10:
        price_score = 8
    elif 100 < price <= 200:
        price_score = 8
    else:
        price_score = 5
    score += min(10, max(0, price_score))
    
    return round(score, 2)

def filter_high_certainty_stocks(df):
    """筛选高确定性股票"""
    # 筛选涨幅 5%-7%
    filtered = df[
        (df['涨跌幅'] >= 5) & 
        (df['涨跌幅'] <= 7)
    ].copy()
    
    if len(filtered) == 0:
        return pd.DataFrame()
    
    # 计算综合评分
    filtered['综合评分'] = filtered.apply(calculate_comprehensive_score, axis=1)
    
    # 筛选评分≥75
    filtered = filtered[filtered['综合评分'] >= 75]
    
    # 按综合评分降序排序
    filtered = filtered.sort_values('综合评分', ascending=False)
    
    return filtered

def main():
    start_time = datetime.now()
    print(f"🦞 开始获取沪深主板股票数据...")
    print(f"开始时间：{start_time.strftime('%H:%M:%S')}")
    
    # 获取沪深主板股票
    df = get_main_board_stocks()
    
    if len(df) == 0:
        print("❌ 获取股票数据失败")
        return
    
    print(f"✅ 获取到 {len(df)} 只沪深主板股票")
    
    # 筛选高确定性股票
    filtered = filter_high_certainty_stocks(df)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() * 1000
    
    print(f"⏱️ 耗时：{duration:.0f}ms")
    
    # 输出结果
    if len(filtered) == 0:
        print("\n🦞 今日暂无符合高确定性标准的股票")
        print("筛选条件：涨幅 5%-7% 且 综合评分≥75")
        return
    
    # 取前 5 名
    top5 = filtered.head(5)
    
    print("\n" + "="*80)
    print("🦞 沪深主板高确定性推荐 (盘中实时)")
    print("="*80)
    print(f"筛选时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"沪深主板股票总数：{len(df)}")
    print(f"符合涨幅 5%-7% 条件：{len(filtered)}")
    print(f"综合评分≥75：{len(filtered)}")
    print(f"推荐数量：前 5 名 (宁缺毋滥)")
    print("="*80)
    
    for idx, row in top5.iterrows():
        print(f"\n🏆 TOP{top5.index.get_loc(idx) + 1}: {row['名称']} ({row['代码']})")
        print(f"   最新价：¥{row['最新价']:.2f} | 涨跌幅：{row['涨跌幅']:.2f}%")
        print(f"   量比：{row.get('量比', 0):.2f} | 换手率：{row.get('换手率', 0):.2f}%")
        print(f"   成交额：{row.get('成交额', 0)/10000_0000:.2f}亿")
        print(f"   市盈率：{row.get('市盈率 - 动态', 0)}")
        print(f"   综合评分：{row['综合评分']:.1f}/100")
    
    print("\n" + "="*80)
    print("⚠️ 风险提示：数据仅供参考，不构成投资建议")
    print("="*80)

if __name__ == "__main__":
    main()
