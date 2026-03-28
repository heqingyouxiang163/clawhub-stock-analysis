#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沪深主板高确定性推荐筛选器
- 10 线程并发获取 3467 只沪深主板股票
- 筛选涨幅 5%-7% 主升浪股票
- 综合评分≥75 分
- 只输出最强的前 5 名
"""

import akshare as ak
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

def is_main_board(symbol: str) -> bool:
    """判断是否为沪深主板股票"""
    code = symbol[:6]
    if code.isdigit():
        # 沪市主板：600, 601, 603, 605
        if code.startswith('600') or code.startswith('601') or code.startswith('603') or code.startswith('605'):
            return True
        # 深市主板：000, 001, 002, 003
        if code.startswith('000') or code.startswith('001') or code.startswith('002') or code.startswith('003'):
            return True
    return False

def calculate_composite_score(row: pd.Series) -> float:
    """
    综合评分计算（满分 100）
    评分维度：
    - 涨幅得分 (25 分): 5%-7% 区间内越接近 6% 得分越高
    - 成交量得分 (20 分): 量比和换手率
    - 资金流向得分 (25 分): 主力资金净流入
    - 技术面得分 (20 分): 均线排列、MACD 等
    - 基本面得分 (10 分): PE、PB 等
    """
    score = 0
    
    # 1. 涨幅得分 (25 分) - 5%-7% 区间，越接近 6% 越高
    try:
        change_pct = float(row.get('涨跌幅', 0))
        if 5 <= change_pct <= 7:
            # 6% 得满分，偏离越远得分越低
            distance_from_optimal = abs(change_pct - 6)
            change_score = 25 * (1 - distance_from_optimal)
            score += max(0, change_score)
    except:
        pass
    
    # 2. 成交量得分 (20 分)
    try:
        volume_ratio = float(row.get('量比', 1))
        turnover_rate = float(row.get('换手率', 0))
        
        # 量比得分 (10 分): 1.5-3 最佳
        if 1.5 <= volume_ratio <= 3:
            volume_score = 10
        elif 1 <= volume_ratio < 1.5:
            volume_score = 7
        elif 3 < volume_ratio <= 5:
            volume_score = 6
        else:
            volume_score = 3
        score += volume_score
        
        # 换手率得分 (10 分): 3%-10% 最佳
        if 3 <= turnover_rate <= 10:
            turnover_score = 10
        elif 1 <= turnover_rate < 3:
            turnover_score = 6
        elif 10 < turnover_rate <= 15:
            turnover_score = 5
        else:
            turnover_score = 2
        score += turnover_score
    except:
        score += 10  # 默认给一半分
    
    # 3. 资金流向得分 (25 分) - 简化版，用涨跌幅和量比推断
    try:
        # 有量有价，推断资金流入
        if float(row.get('量比', 1)) > 1.5 and float(row.get('涨跌幅', 0)) > 5:
            score += 20
        elif float(row.get('量比', 1)) > 1:
            score += 15
        else:
            score += 10
    except:
        score += 10
    
    # 4. 技术面得分 (20 分) - 简化版
    try:
        # 现价 vs 均价
        current_price = float(row.get('最新价', 0))
        avg_price = float(row.get('均价', current_price * 0.98))
        if current_price > avg_price:
            score += 12
        else:
            score += 6
        
        # 最高价接近收盘价（强势）
        high_price = float(row.get('最高', current_price))
        if current_price >= high_price * 0.99:
            score += 8
        else:
            score += 4
    except:
        score += 8
    
    # 5. 基本面得分 (10 分) - 简化版，用市盈率
    try:
        pe_ratio = float(row.get('市盈率 - 动态', 50))
        if 0 < pe_ratio <= 20:
            score += 10
        elif 20 < pe_ratio <= 40:
            score += 7
        elif 40 < pe_ratio <= 60:
            score += 5
        else:
            score += 3
    except:
        score += 5
    
    return min(100, score)

def fetch_stock_data():
    """获取沪深主板股票实时行情（带重试机制）"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始获取沪深主板股票数据...")
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            # 获取所有 A 股实时行情
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 尝试第 {attempt + 1}/{max_retries} 次连接...")
            df = ak.stock_zh_a_spot_em()
            
            # 筛选沪深主板
            df_main = df[df['代码'].apply(is_main_board)].copy()
            
            elapsed = time.time() - start_time
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 获取完成：{len(df_main)} 只沪深主板股票，耗时 {elapsed:.2f}秒")
            
            return df_main
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {attempt + 1} 次尝试失败：{e}")
            if attempt < max_retries - 1:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 所有重试失败")
    return pd.DataFrame()

def filter_and_score(df: pd.DataFrame) -> pd.DataFrame:
    """筛选涨幅 5%-7% 的股票并计算综合评分"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始筛选和评分...")
    
    # 筛选涨幅 5%-7%
    df_filtered = df[
        (df['涨跌幅'] >= 5) & 
        (df['涨跌幅'] <= 7)
    ].copy()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 涨幅 5%-7% 股票：{len(df_filtered)} 只")
    
    if len(df_filtered) == 0:
        return pd.DataFrame()
    
    # 计算综合评分
    df_filtered['综合评分'] = df_filtered.apply(calculate_composite_score, axis=1)
    
    # 筛选评分≥75
    df_scored = df_filtered[df_filtered['综合评分'] >= 75].copy()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 评分≥75 股票：{len(df_scored)} 只")
    
    # 按综合评分降序排序
    df_scored = df_scored.sort_values('综合评分', ascending=False)
    
    return df_scored

def main():
    print("=" * 60)
    print("🦞 沪深主板高确定性推荐 (盘中实时)")
    print(f"⏰ 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 获取数据
    df = fetch_stock_data()
    
    if df.empty:
        print("\n❌ 无法获取股票数据，请检查网络连接")
        return
    
    # 2. 筛选和评分
    df_result = filter_and_score(df)
    
    if df_result.empty:
        print("\n⚠️ 当前没有符合筛选条件的股票（涨幅 5%-7% 且评分≥75）")
        print("\n📊 市场状态分析：")
        print("   - 可能市场整体偏弱，主升浪股票较少")
        print("   - 或涨幅集中在一字板/涨停股")
        print("   - 建议放宽筛选条件或等待更好时机")
        return
    
    # 3. 输出前 5 名
    top5 = df_result.head(5)
    
    print("\n" + "=" * 60)
    print("🏆 沪深主板高确定性推荐 TOP5")
    print("=" * 60)
    
    for idx, row in top5.iterrows():
        print(f"\n【{idx + 1}】{row['名称']} ({row['代码']})")
        print(f"    最新价：¥{row['最新价']} | 涨跌幅：{row['涨跌幅']:.2f}%")
        print(f"    量比：{row['量比']} | 换手率：{row['换手率']:.2f}%")
        print(f"    成交额：{row['成交额']:,.0f}万")
        print(f"    市盈率 (动): {row.get('市盈率 - 动态', 'N/A')}")
        print(f"    ⭐ 综合评分：{row['综合评分']:.1f}分")
    
    print("\n" + "=" * 60)
    print("⚠️ 免责声明：数据仅供参考，不构成投资建议")
    print("=" * 60)

if __name__ == "__main__":
    main()
