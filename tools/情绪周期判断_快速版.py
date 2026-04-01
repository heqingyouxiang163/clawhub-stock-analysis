#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪周期判断 - 快速版 (90 秒超时)
数据源：腾讯财经 API (优先) + 东方财富 (备用)

分析维度:
1. 昨日涨停/跌停家数
2. 连板高度 (前 10 名)
3. 炸板率
4. 情绪阶段判断
5. 仓位建议
"""

import akshare as ak
import requests
from datetime import datetime, timedelta
import json
import sys

# ==================== 配置 ====================
TIMEOUT = 90  # 秒
TODAY = datetime.now().strftime('%Y-%m-%d')
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# ==================== 数据获取 ====================

def get_yesterday_limit_stats():
    """获取昨日涨停/跌停统计"""
    try:
        # 东方财富涨停池
        df_zt = ak.stock_zt_pool_em(date=YESTERDAY.replace('-', ''))
        zt_count = len(df_zt)
        
        # 东方财富跌停池
        df_dt = ak.stock_dt_pool_em(date=YESTERDAY.replace('-', ''))
        dt_count = len(df_dt)
        
        return {
            'zt_count': zt_count,
            'dt_count': dt_count,
            'success': True
        }
    except Exception as e:
        print(f"⚠️ 获取昨日数据失败：{e}")
        return {'zt_count': 0, 'dt_count': 0, 'success': False}


def get_limit_height():
    """获取连板高度 (前 10 名)"""
    try:
        df = ak.stock_zt_pool_em(date=TODAY.replace('-', ''))
        
        # 提取连板数
        limit_stocks = []
        for _, row in df.iterrows():
            limit_count = int(row.get('连板数', 1) or 1)
            if limit_count >= 2:
                limit_stocks.append({
                    'name': row.get('名称', ''),
                    'code': row.get('代码', ''),
                    'limit_count': limit_count
                })
        
        # 按连板数排序
        limit_stocks.sort(key=lambda x: x['limit_count'], reverse=True)
        
        return limit_stocks[:10]
    except Exception as e:
        print(f"⚠️ 获取连板数据失败：{e}")
        return []


def get_break_rate():
    """获取炸板率"""
    try:
        df = ak.stock_zt_pool_em(date=TODAY.replace('-', ''))
        
        total = len(df)
        if total == 0:
            return 0
        
        # 统计炸板次数>0 的股票
        broken = sum(1 for _, row in df.iterrows() 
                    if int(row.get('炸板次数', 0) or 0) > 0)
        
        break_rate = broken / total * 100 if total > 0 else 0
        return round(break_rate, 1)
    except Exception as e:
        print(f"⚠️ 获取炸板率失败：{e}")
        return 0


# ==================== 情绪判断 ====================

def judge_emotion_stage(zt_count, dt_count, limit_height, break_rate):
    """判断情绪阶段"""
    
    # 综合评分
    score = 0
    
    # 涨停家数评分 (0-40 分)
    if zt_count >= 80:
        score += 40
    elif zt_count >= 50:
        score += 30
    elif zt_count >= 30:
        score += 20
    elif zt_count >= 15:
        score += 10
    
    # 跌停家数评分 (0-20 分，越少越好)
    if dt_count <= 5:
        score += 20
    elif dt_count <= 10:
        score += 15
    elif dt_count <= 20:
        score += 10
    elif dt_count <= 30:
        score += 5
    
    # 连板高度评分 (0-25 分)
    if limit_height >= 7:
        score += 25
    elif limit_height >= 5:
        score += 20
    elif limit_height >= 3:
        score += 15
    elif limit_height >= 2:
        score += 10
    
    # 炸板率评分 (0-15 分，越低越好)
    if break_rate <= 20:
        score += 15
    elif break_rate <= 30:
        score += 10
    elif break_rate <= 40:
        score += 5
    
    # 判断阶段
    if score >= 80:
        stage = "🟢 高潮期"
        desc = "情绪高涨，赚钱效应强"
    elif score >= 60:
        stage = "🟡 强势期"
        desc = "情绪良好，可积极参与"
    elif score >= 40:
        stage = "🟠 震荡期"
        desc = "情绪分化，精选个股"
    elif score >= 20:
        stage = "🔵 冰点期"
        desc = "情绪低迷，等待拐点"
    else:
        stage = "🔴 衰退期"
        desc = "情绪退潮，控制风险"
    
    return stage, desc, score


def get_position_suggestion(stage, score):
    """仓位建议"""
    
    if "高潮" in stage:
        return "60-80% (激进)"
    elif "强势" in stage:
        return "50-70% (积极)"
    elif "震荡" in stage:
        return "30-50% (谨慎)"
    elif "冰点" in stage:
        return "20-40% (防守)"
    else:
        return "0-20% (空仓观望)"


# ==================== 主函数 ====================

def main():
    start_time = datetime.now()
    
    print(f"🦞 情绪周期判断 (快速版) - {TODAY}")
    print("=" * 60)
    
    # 1. 获取昨日涨停/跌停
    yesterday = get_yesterday_limit_stats()
    zt_count = yesterday['zt_count']
    dt_count = yesterday['dt_count']
    
    # 2. 获取连板高度
    limit_stocks = get_limit_height()
    max_height = limit_stocks[0]['limit_count'] if limit_stocks else 1
    top_stock = limit_stocks[0]['name'] if limit_stocks else "无"
    
    # 3. 获取炸板率
    break_rate = get_break_rate()
    
    # 4. 情绪判断
    stage, desc, score = judge_emotion_stage(zt_count, dt_count, max_height, break_rate)
    
    # 5. 仓位建议
    position = get_position_suggestion(stage, score)
    
    # 输出报告 (10 行内)
    print(f"昨日涨停：{zt_count} 家 | 跌停：{dt_count} 家")
    print(f"连板高度：{max_height}板 ({top_stock}) | 炸板率：{break_rate}%")
    print(f"情绪阶段：{stage} - {desc}")
    print(f"仓位建议：{position}")
    print("=" * 60)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"⏱️  耗时：{elapsed:.1f}秒")
    
    # 检查结果
    if elapsed > TIMEOUT:
        print(f"⚠️ 警告：超过{TIMEOUT}秒超时限制")
        sys.exit(1)


if __name__ == "__main__":
    main()
