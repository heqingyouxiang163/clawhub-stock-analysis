#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓股成交量 + 情绪自动化分析系统
每日收盘后自动运行，生成次日操作建议
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# ==================== 配置区 ====================

# 持仓配置
HOLDINGS = [
    {
        "code": "002455",
        "name": "百川股份",
        "cost": 16.318,
        "shares": 500,
    },
    {
        "code": "603538",
        "name": "美诺华",
        "cost": 24.370,
        "shares": 500,
    },
]

# 输出目录
OUTPUT_DIR = "/home/admin/openclaw/workspace/temp/分析报告"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== 涨停质量评估 ====================

def evaluate_limit_up_quality(df, main_flow_data):
    """评估涨停质量 (A/B/C 级)"""
    if df is None or len(df) < 5:
        return {"grade": "N/A", "score": 0, "details": "数据不足"}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    # 判断是否涨停
    is_limit_up = latest['涨跌幅'] >= 9.5
    
    if not is_limit_up:
        return {"grade": "非涨停", "score": 0, "details": "当日未涨停"}
    
    score = 0
    details = []
    
    # 1. 涨停时间 (根据 K 线推断)
    # 简化：用涨跌幅和成交量推断
    if latest['涨跌幅'] >= 9.8:
        # 强势涨停
        score += 30
        details.append("强势涨停")
    else:
        score += 15
        details.append("普通涨停")
    
    # 2. 量比
    vol_ma5 = df['成交量'].rolling(5).mean().iloc[-2] if len(df) > 1 else latest['成交量']
    volume_ratio = latest['成交量'] / vol_ma5 if vol_ma5 > 0 else 1
    
    if 1.5 <= volume_ratio <= 3:
        score += 25
        details.append(f"量比健康 ({volume_ratio:.1f}倍)")
    elif 3 < volume_ratio <= 5:
        score += 15
        details.append(f"量比偏高 ({volume_ratio:.1f}倍)")
    elif volume_ratio > 5:
        score += 5
        details.append(f"量比过高 ({volume_ratio:.1f}倍，警惕)")
    else:
        score += 10
        details.append(f"缩量涨停")
    
    # 3. 超大单流向
    super_large = main_flow_data.get("super_large", 0)
    if super_large > 3000:
        score += 30
        details.append(f"超大单大幅流入 (+{super_large/1000:.1f}千万)")
    elif super_large > 1000:
        score += 20
        details.append(f"超大单流入 (+{super_large/1000:.1f}千万)")
    elif super_large > 0:
        score += 10
        details.append(f"超大单小幅流入")
    else:
        score += 0
        details.append(f"超大单流出 ({super_large/1000:.1f}千万，警惕)")
    
    # 评级
    if score >= 70:
        grade = "A"
        desc = "🟢 A 级 (连板概率 60%+)"
    elif score >= 50:
        grade = "B"
        desc = "🟡 B 级 (连板概率 30-60%)"
    else:
        grade = "C"
        desc = "🔴 C 级 (连板概率<30%)"
    
    return {
        "grade": grade,
        "desc": desc,
        "score": score,
        "details": details,
        "volume_ratio": volume_ratio,
        "is_limit_up": is_limit_up,
    }

# ==================== 低开跌停风险评估 ====================

def evaluate_limit_down_risk(df, main_flow_data, prev_day_info=None):
    """评估低开跌停风险 (用于昨日涨停股)"""
    if df is None or len(df) < 5:
        return {"risk_level": "未知", "score": 0, "warnings": []}
    
    latest = df.iloc[-1]
    
    # 检查是否是高位股
    recent_gains = []
    for i in range(min(5, len(df))):
        gain = df.iloc[-(i+1)]['涨跌幅']
        recent_gains.append(gain)
    
    consecutive_limit_ups = sum(1 for g in recent_gains if g >= 9.5)
    
    risk_score = 0
    warnings = []
    
    # 1. 连板高度风险
    if consecutive_limit_ups >= 5:
        risk_score += 30
        warnings.append(f"⚠️ 连续{consecutive_limit_ups}板，高位退潮风险")
    elif consecutive_limit_ups >= 3:
        risk_score += 20
        warnings.append(f"⚠️ 连续{consecutive_limit_ups}板，注意分化")
    
    # 2. 涨停质量风险
    if prev_day_info and prev_day_info.get("grade") == "C":
        risk_score += 25
        warnings.append("⚠️ 昨日涨停质量差 (C 级)")
    
    # 3. 资金流向风险
    super_large = main_flow_data.get("super_large", 0)
    if super_large < -3000:
        risk_score += 25
        warnings.append(f"⚠️ 超大单大幅流出 ({super_large/1000:.1f}千万)")
    elif super_large < 0:
        risk_score += 10
        warnings.append(f"⚠️ 超大单流出 ({super_large/1000:.1f}千万)")
    
    # 4. 量比风险
    vol_ma5 = df['成交量'].rolling(5).mean().iloc[-1]
    volume_ratio = latest['成交量'] / vol_ma5 if vol_ma5 > 0 else 1
    
    if volume_ratio > 5:
        risk_score += 20
        warnings.append(f"⚠️ 量比过高 ({volume_ratio:.1f}倍，警惕巨量)")
    
    # 风险等级
    if risk_score >= 70:
        risk_level = "🔴🔴🔴 极高风险"
        action = "集合竞价坚决止损"
    elif risk_score >= 50:
        risk_level = "🔴🔴 高风险"
        action = "反抽坚决卖出"
    elif risk_score >= 30:
        risk_level = "🔴 中高风险"
        action = "设置止损，准备逃命"
    else:
        risk_level = "🟡 中等风险"
        action = "观察集合竞价"
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "warnings": warnings,
        "action": action,
        "consecutive_limit_ups": consecutive_limit_ups,
    }

def generate_limit_down_warning(code, name, risk_info, tech_indicators):
    """生成低开跌停预警和应对预案"""
    if risk_info.get("risk_score", 0) < 30:
        return None
    
    warning = f"""
⚠️【低开跌停风险预警】⚠️

风险等级：{risk_info.get('risk_level', '未知')}
风险得分：{risk_info.get('risk_score', 0)}/100

风险因素:
"""
    for w in risk_info.get("warnings", []):
        warning += f"  {w}\n"
    
    warning += f"""
应对预案:
  📋 集合竞价 (9:15-9:25):
    IF 跌停封单 > 10 万手 → 挂跌停价卖出
    IF 低开 -8% 以下 → 准备止损
    IF 低开 -5% 至 -8% → 等待反抽
  
  📋 开盘后:
    IF 快速杀向跌停 → 反抽卖出
    IF 反抽不翻红 → 坚决卖出
    IF 跌破 -9% → 止损清仓
  
  📋 必须止损的信号:
    1. 高开低走翻绿 → 立即清仓
    2. 跌破昨日涨停价 → 止损卖出
    3. 超大单大幅流出 → 卖出
    4. 反抽无力 → 逃命机会

💡 心态提醒:
  - 接受亏损，止损是保命
  - 反抽就是逃命机会，不要等翻红
  - 一次大亏需要多次盈利弥补
  - 留得本金在，不怕没机会
"""
    
    return warning
    """评估涨停质量 (A/B/C 级)"""
    if df is None or len(df) < 5:
        return {"grade": "N/A", "score": 0, "details": "数据不足"}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    # 判断是否涨停
    is_limit_up = latest['涨跌幅'] >= 9.5
    
    if not is_limit_up:
        return {"grade": "非涨停", "score": 0, "details": "当日未涨停"}
    
    score = 0
    details = []
    
    # 1. 涨停时间 (根据 K 线推断)
    # 简化：用涨跌幅和成交量推断
    if latest['涨跌幅'] >= 9.8:
        # 强势涨停
        score += 30
        details.append("强势涨停")
    else:
        score += 15
        details.append("普通涨停")
    
    # 2. 量比
    vol_ma5 = df['成交量'].rolling(5).mean().iloc[-2] if len(df) > 1 else latest['成交量']
    volume_ratio = latest['成交量'] / vol_ma5 if vol_ma5 > 0 else 1
    
    if 1.5 <= volume_ratio <= 3:
        score += 25
        details.append(f"量比健康 ({volume_ratio:.1f}倍)")
    elif 3 < volume_ratio <= 5:
        score += 15
        details.append(f"量比偏高 ({volume_ratio:.1f}倍)")
    elif volume_ratio > 5:
        score += 5
        details.append(f"量比过高 ({volume_ratio:.1f}倍，警惕)")
    else:
        score += 10
        details.append(f"缩量涨停")
    
    # 3. 超大单流向
    super_large = main_flow_data.get("super_large", 0)
    if super_large > 3000:
        score += 30
        details.append(f"超大单大幅流入 (+{super_large/1000:.1f}千万)")
    elif super_large > 1000:
        score += 20
        details.append(f"超大单流入 (+{super_large/1000:.1f}千万)")
    elif super_large > 0:
        score += 10
        details.append(f"超大单小幅流入")
    else:
        score += 0
        details.append(f"超大单流出 ({super_large/1000:.1f}千万，警惕)")
    
    # 评级
    if score >= 70:
        grade = "A"
        desc = "🟢 A 级 (连板概率 60%+)"
    elif score >= 50:
        grade = "B"
        desc = "🟡 B 级 (连板概率 30-60%)"
    else:
        grade = "C"
        desc = "🔴 C 级 (连板概率<30%)"
    
    return {
        "grade": grade,
        "desc": desc,
        "score": score,
        "details": details,
        "volume_ratio": volume_ratio,
        "is_limit_up": is_limit_up,
    }

# ==================== 数据获取 ====================

def get_stock_data(code, start_date="20251001", retries=3):
    """获取股票历史行情数据 (带重试)"""
    for i in range(retries):
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, adjust="qfq")
            if len(df) > 0:
                return df
        except Exception as e:
            if i < retries - 1:
                print(f"  获取 {code} 数据失败，重试 {i+1}/{retries}...")
                import time
                time.sleep(2)
            else:
                print(f"获取 {code} 数据失败：{e}")
    return None

def get_market_sentiment():
    """获取市场情绪数据"""
    try:
        # 涨跌家数
        df = ak.stock_market_activity_legu()
        if not df.empty:
            up = df[df['类型'] == '上涨']['数量'].values[0] if len(df[df['类型'] == '上涨']) > 0 else 0
            down = df[df['类型'] == '下跌']['数量'].values[0] if len(df[df['类型'] == '下跌']) > 0 else 0
            return {
                "up": up,
                "down": down,
                "ratio": up / down if down > 0 else 999
            }
    except Exception as e:
        print(f"获取市场情绪失败：{e}")
    
    return {"up": 0, "down": 0, "ratio": 1}

def get_north_flow():
    """获取北向资金流向"""
    try:
        df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
        if not df.empty:
            latest = df.iloc[0]
            return float(latest.get('净买入额', 0))
    except Exception as e:
        print(f"获取北向资金失败：{e}")
    return 0

def get_main_flow(code):
    """获取主力资金流向 (含超大单/大单)"""
    try:
        # 获取个股资金流向
        df = ak.stock_individual_fund_flow_rank(indicator="今日")
        if not df.empty:
            stock_row = df[df["代码"] == code]
            if not stock_row.empty:
                row = stock_row.iloc[0]
                return {
                    "total": float(row.get("主力净流入 - 净额", 0)),
                    "super_large": float(row.get("超大单净流入 - 净额", 0)),
                    "large": float(row.get("大单净流入 - 净额", 0)),
                    "medium": float(row.get("中单净流入 - 净额", 0)),
                    "small": float(row.get("小单净流入 - 净额", 0)),
                }
    except Exception as e:
        print(f"获取主力流向失败：{e}")
    return {"total": 0, "super_large": 0, "large": 0, "medium": 0, "small": 0}

# ==================== 指标计算 ====================

def calculate_volume_indicators(df):
    """计算成交量指标"""
    if df is None or len(df) < 20:
        return {}
    
    latest = df.iloc[-1]
    
    # 量比
    vol_ma5 = df['成交量'].rolling(5).mean().iloc[-1]
    vol_ma20 = df['成交量'].rolling(20).mean().iloc[-1]
    volume_ratio = latest['成交量'] / vol_ma20 if vol_ma20 > 0 else 1
    
    # 成交量趋势
    vol_trend = "放量" if volume_ratio > 1.5 else ("缩量" if volume_ratio < 0.8 else "正常")
    
    # 量价关系
    price_change = latest['涨跌幅']
    if price_change > 0 and volume_ratio > 1.5:
        vol_price_relation = "量增价涨"
        vol_price_score = 10
    elif price_change > 0 and volume_ratio < 0.8:
        vol_price_relation = "量缩价涨"
        vol_price_score = 5
    elif price_change < 0 and volume_ratio > 1.5:
        vol_price_relation = "量增价跌"
        vol_price_score = 0
    elif price_change < 0 and volume_ratio < 0.8:
        vol_price_relation = "量缩价跌"
        vol_price_score = 5
    else:
        vol_price_relation = "量价平稳"
        vol_price_score = 5
    
    # 是否天量/地量
    vol_60_high = df['成交量'].rolling(60).max().iloc[-1]
    vol_60_low = df['成交量'].rolling(60).min().iloc[-1]
    
    if latest['成交量'] >= vol_60_high * 0.95:
        vol_status = "天量"
        vol_status_score = 0
    elif latest['成交量'] <= vol_60_low * 1.05:
        vol_status = "地量"
        vol_status_score = 5
    else:
        vol_status = "正常"
        vol_status_score = 10
    
    # 量比得分
    if 1.5 <= volume_ratio <= 3:
        volume_ratio_score = 10
    elif 0.8 <= volume_ratio < 1.5 or 3 < volume_ratio <= 5:
        volume_ratio_score = 5
    else:
        volume_ratio_score = 0
    
    return {
        "volume_ratio": round(volume_ratio, 2),
        "vol_trend": vol_trend,
        "vol_price_relation": vol_price_relation,
        "vol_price_score": vol_price_score,
        "vol_status": vol_status,
        "vol_status_score": vol_status_score,
        "volume_ratio_score": volume_ratio_score,
        "vol_ma5": int(vol_ma5),
        "vol_ma20": int(vol_ma20),
    }

def calculate_technical_indicators(df):
    """计算技术指标"""
    if df is None or len(df) < 60:
        return {}
    
    latest = df.iloc[-1]
    close = latest['收盘']
    
    # 均线
    ma5 = df['收盘'].rolling(5).mean().iloc[-1]
    ma10 = df['收盘'].rolling(10).mean().iloc[-1]
    ma20 = df['收盘'].rolling(20).mean().iloc[-1]
    ma60 = df['收盘'].rolling(60).mean().iloc[-1]
    
    # 均线排列
    if ma5 > ma10 > ma20 > ma60:
        ma_pattern = "强多头"
        ma_score = 15
    elif ma5 > ma10 > ma20:
        ma_pattern = "多头"
        ma_score = 12
    elif ma5 < ma10 < ma20 < ma60:
        ma_pattern = "强空头"
        ma_score = 0
    elif ma5 < ma10 < ma20:
        ma_pattern = "空头"
        ma_score = 3
    else:
        ma_pattern = "纠缠"
        ma_score = 7
    
    # MACD
    exp12 = df['收盘'].ewm(span=12, adjust=False).mean()
    exp26 = df['收盘'].ewm(span=26, adjust=False).mean()
    macd = exp12 - exp26
    signal = macd.ewm(span=9, adjust=False).mean()
    
    if macd.iloc[-1] > signal.iloc[-1]:
        macd_status = "金叉"
        macd_score = 10
    else:
        macd_status = "死叉"
        macd_score = 3
    
    # RSI
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1]
    
    if rsi_val > 70:
        rsi_status = "超买"
        rsi_score = 3
    elif rsi_val < 30:
        rsi_status = "超卖"
        rsi_score = 10
    else:
        rsi_status = "中性"
        rsi_score = 6
    
    # 布林带
    bb_middle = df['收盘'].rolling(20).mean()
    bb_std = df['收盘'].rolling(20).std()
    bb_upper = bb_middle + (bb_std * 2)
    bb_lower = bb_middle - (bb_std * 2)
    
    bb_position = (close - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100
    
    if bb_position > 80:
        bb_status = "接近上轨"
        bb_score = 6
    elif bb_position < 20:
        bb_status = "接近下轨"
        bb_score = 10
    else:
        bb_status = "轨道中部"
        bb_score = 7
    
    return {
        "close": round(close, 2),
        "change": latest['涨跌幅'],
        "ma5": round(ma5, 2),
        "ma10": round(ma10, 2),
        "ma20": round(ma20, 2),
        "ma60": round(ma60, 2),
        "ma_pattern": ma_pattern,
        "ma_score": ma_score,
        "macd_status": macd_status,
        "macd_score": macd_score,
        "rsi": round(rsi_val, 2),
        "rsi_status": rsi_status,
        "rsi_score": rsi_score,
        "bb_position": round(bb_position, 1),
        "bb_status": bb_status,
        "bb_score": bb_score,
    }

def calculate_sentiment_score(north_flow, main_flow_data, market_ratio):
    """计算情绪得分 (重点：超大单/大单)"""
    # 北向资金得分 (15 分)
    if north_flow > 50:
        north_score = 15
    elif north_flow > 20:
        north_score = 12
    elif north_flow > -20:
        north_score = 8
    elif north_flow > -50:
        north_score = 3
    else:
        north_score = 0
    
    # 🎯 超大单得分 (25 分) - 最高权重
    super_large = main_flow_data.get("super_large", 0)
    if super_large > 5000:  # 5000 万以上
        super_large_score = 25
    elif super_large > 2000:
        super_large_score = 20
    elif super_large > 0:
        super_large_score = 15
    elif super_large > -1000:
        super_large_score = 8
    elif super_large > -3000:
        super_large_score = 3
    else:
        super_large_score = 0
    
    # 🎯 大单得分 (15 分)
    large = main_flow_data.get("large", 0)
    if large > 3000:  # 3000 万以上
        large_score = 15
    elif large > 1000:
        large_score = 12
    elif large > 0:
        large_score = 8
    elif large > -1000:
        large_score = 3
    else:
        large_score = 0
    
    # 🎯 主力 - 散户差值得分 (10 分)
    small = main_flow_data.get("small", 0)
    total_main = super_large + large
    diff_score_base = total_main - small  # 主力 - 散户
    if diff_score_base > 5000:
        diff_score = 10
    elif diff_score_base > 2000:
        diff_score = 8
    elif diff_score_base > 0:
        diff_score = 5
    elif diff_score_base > -2000:
        diff_score = 3
    else:
        diff_score = 0
    
    # 市场涨跌比得分 (10 分)
    if market_ratio > 3:
        market_score = 10
    elif market_ratio > 2:
        market_score = 8
    elif market_ratio > 1:
        market_score = 5
    elif market_ratio > 0.5:
        market_score = 3
    else:
        market_score = 0
    
    return {
        "north_flow": round(north_flow, 2),
        "north_score": north_score,
        "super_large_flow": round(super_large, 2),
        "super_large_score": super_large_score,
        "large_flow": round(large, 2),
        "large_score": large_score,
        "small_flow": round(small, 2),
        "diff_score": diff_score,
        "market_ratio": round(market_ratio, 2),
        "market_score": market_score,
        "sentiment_total": north_score + super_large_score + large_score + diff_score + market_score,
    }

# ==================== 综合评分 ====================

def calculate_total_score(vol_indicators, tech_indicators, sentiment_indicators):
    """计算综合评分"""
    # 成交量维度 (40 分)
    vol_score = (
        vol_indicators.get("volume_ratio_score", 5) +
        vol_indicators.get("vol_price_score", 5) +
        vol_indicators.get("vol_status_score", 5) +
        10  # 基础分
    )
    
    # 技术面维度 (25 分)
    tech_score = (
        tech_indicators.get("ma_score", 7) * 0.5 +
        tech_indicators.get("macd_score", 6) * 0.5 +
        tech_indicators.get("rsi_score", 6) * 0.5 +
        tech_indicators.get("bb_score", 7) * 0.5
    )
    
    # 🎯 情绪维度 (35 分) - 提高权重，突出大单/超大单
    sentiment_score = sentiment_indicators.get("sentiment_total", 20)
    
    total = vol_score + tech_score + sentiment_score
    
    return {
        "vol_score": round(vol_score, 1),
        "tech_score": round(tech_score, 1),
        "sentiment_score": round(sentiment_score, 1),
        "total": round(total, 1),
    }

def get_rating_and_action(total_score, cost, close):
    """根据评分给出评级和操作建议"""
    profit_pct = ((close - cost) / cost) * 100
    
    if total_score >= 80:
        rating = "🟢🟢 强烈看好"
        if profit_pct > 10:
            action = "持有，部分止盈 (30%)"
        else:
            action = "持有/加仓"
    elif total_score >= 60:
        rating = "🟢 看好"
        action = "持有"
    elif total_score >= 40:
        rating = "🟡 中性"
        action = "观望"
    elif total_score >= 20:
        rating = "🔴 看空"
        action = "减仓"
    else:
        rating = "🔴🔴 强烈看空"
        action = "止损/清仓"
    
    return rating, action

def generate_next_day_strategy(code, name, tech_indicators, close, limit_up_info=None, sentiment_data=None):
    """生成次日操作策略 (含涨停连板预案)"""
    ma5 = tech_indicators.get("ma5", close)
    ma20 = tech_indicators.get("ma20", close)
    change = tech_indicators.get("change", 0)
    
    # 支撑位和压力位
    support = round(min(ma5, ma20, close * 0.95), 2)
    resistance = round(max(ma5 * 1.05, close * 1.1), 2)
    
    # 止损止盈
    stop_loss = round(close * 0.92, 2)
    take_profit = round(close * 1.15, 2)
    
    strategy = f"""
【次日操作策略】

关键价位:
  支撑位：{support} 元
  压力位：{resistance} 元
  止损位：{stop_loss} 元 (-8%)
  止盈位：{take_profit} 元 (+15%)
"""
    
    # 如果是涨停股，加入连板预案
    if limit_up_info and limit_up_info.get("is_limit_up", False):
        grade = limit_up_info.get("grade", "N/A")
        desc = limit_up_info.get("desc", "")
        
        strategy += f"""
【涨停连板预案】🔥
  涨停质量：{desc}
  
  集合竞价观察 (9:15-9:25):
    IF 高开 8%+ 且封单>2 亿 → 连板概率 70%，持有/加仓
    IF 高开 5-8% 且封单 1-2 亿 → 连板概率 50%，持有观望
    IF 高开<5% 或封单<5000 万 → 连板概率 30%，减仓止盈
  
  高开 5%+ 专项预案:
    ✅ 强势连板型 (高开 7-10%, 封单>1 亿)
      → 持有，快速涨停可加仓
    
    ⚠️ 高开回落型 (高开 5-8%, 竞价巨量)
      → IF 跌破开盘价 → 立即卖出
      → IF 翻绿 → 清仓
    
    🟡 高开震荡型 (高开 5-7%, 封单稳定)
      → IF 震荡不破开盘价 → 持有
      → IF 跌破开盘价 3% → 减仓
    
    必须止损的情况:
      1. 高开低走翻绿 → 立即清仓
      2. 跌破昨日涨停价 → 止损卖出
      3. 超大单大幅流出 → 卖出
"""
    else:
        strategy += f"""
盘前预案:
  IF 高开 > 2% → 持有，冲高止盈
  IF 平开 ±1% → 观察 30 分钟
  IF 低开 < -2% → 反抽卖出

盘中执行:
  IF 跌破 {support} → 减仓/止损
  IF 突破 {resistance} → 持有/加仓
  IF 亏损达 -8% → 无条件止损
"""
    
    return strategy

# ==================== 报告生成 ====================

def generate_report():
    """生成分析报告"""
    print("=" * 70)
    print("持仓股成交量 + 情绪自动化分析系统")
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    # 获取市场情绪
    print("\n📊 获取市场数据...")
    market_sentiment = get_market_sentiment()
    north_flow = get_north_flow()
    
    print(f"  涨跌比：{market_sentiment['up']}:{market_sentiment['down']} = {market_sentiment['ratio']:.2f}")
    print(f"  北向资金：{north_flow} 亿元")
    
    results = []
    
    for stock in HOLDINGS:
        code = stock["code"]
        name = stock["name"]
        cost = stock["cost"]
        shares = stock["shares"]
        
        print(f"\n{'='*70}")
        print(f"📈 {name} ({code})")
        print(f"{'='*70}")
        
        # 获取数据
        df = get_stock_data(code)
        if df is None or len(df) < 20:
            print("  数据不足，跳过分析")
            continue
        
        # 获取主力流向
        main_flow = get_main_flow(code)
        
        # 计算指标
        vol_indicators = calculate_volume_indicators(df)
        tech_indicators = calculate_technical_indicators(df)
        sentiment_indicators = calculate_sentiment_score(north_flow, main_flow, market_sentiment['ratio'])
        
        # 🎯 涨停质量评估
        limit_up_info = evaluate_limit_up_quality(df, main_flow)
        
        # ⚠️ 低开跌停风险评估 (如果是涨停股)
        limit_down_risk = None
        if limit_up_info.get("is_limit_up", False):
            limit_down_risk = evaluate_limit_down_risk(df, main_flow, limit_up_info)
        
        # 综合评分
        scores = calculate_total_score(vol_indicators, tech_indicators, sentiment_indicators)
        
        # 评级和操作建议
        close = tech_indicators.get("close", 0)
        rating, action = get_rating_and_action(scores["total"], cost, close)
        
        # 持仓盈亏
        position_value = close * shares
        profit = (close - cost) * shares
        profit_pct = ((close - cost) / cost) * 100
        
        # 输出结果
        print(f"\n【基础数据】")
        print(f"  现价：{close} 元")
        print(f"  成本：{cost} 元")
        print(f"  持仓：{shares} 股")
        print(f"  市值：{position_value:.2f} 元")
        print(f"  盈亏：{profit:+.2f} 元 ({profit_pct:+.2f}%)")
        
        print(f"\n【成交量指标】")
        print(f"  量比：{vol_indicators.get('volume_ratio', 'N/A')}")
        print(f"  趋势：{vol_indicators.get('vol_trend', 'N/A')}")
        print(f"  量价关系：{vol_indicators.get('vol_price_relation', 'N/A')}")
        print(f"  状态：{vol_indicators.get('vol_status', 'N/A')}")
        
        print(f"\n【技术指标】")
        print(f"  均线排列：{tech_indicators.get('ma_pattern', 'N/A')}")
        print(f"  MACD: {tech_indicators.get('macd_status', 'N/A')}")
        print(f"  RSI: {tech_indicators.get('rsi', 'N/A')} ({tech_indicators.get('rsi_status', 'N/A')})")
        print(f"  布林带：{tech_indicators.get('bb_status', 'N/A')}")
        
        print(f"\n【情绪指标】🎯 重点参考")
        print(f"  北向资金：{sentiment_indicators.get('north_flow', 'N/A')} 亿元 (得分：{sentiment_indicators.get('north_score', 0)}/15)")
        print(f"  ─────────────────────────────────")
        print(f"  🚀 超大单：{sentiment_indicators.get('super_large_flow', 'N/A')} 万元 (得分：{sentiment_indicators.get('super_large_score', 0)}/25)")
        print(f"  💼 大单：{sentiment_indicators.get('large_flow', 'N/A')} 万元 (得分：{sentiment_indicators.get('large_score', 0)}/15)")
        print(f"  📊 中单：{main_flow.get('medium', 0)} 万元")
        print(f"  👥 小单：{sentiment_indicators.get('small_flow', 'N/A')} 万元")
        print(f"  ─────────────────────────────────")
        print(f"  主力 - 散户差值：{sentiment_indicators.get('diff_score', 0)}/10")
        print(f"  涨跌比：{sentiment_indicators.get('market_ratio', 'N/A')} (得分：{sentiment_indicators.get('market_score', 0)}/10)")
        
        print(f"\n【综合评分】")
        print(f"  成交量：{scores['vol_score']}/40")
        print(f"  技术面：{scores['tech_score']}/25")
        print(f"  情绪面：{scores['sentiment_score']}/35 (超大单 + 大单为核心)")
        print(f"  ─────────────────")
        print(f"  总分：{scores['total']}/100")
        print(f"  评级：{rating}")
        print(f"  建议：{action}")
        
        # 🎯 涨停质量评估
        if limit_up_info.get("is_limit_up", False):
            print(f"\n【涨停质量评估】🔥")
            print(f"  评级：{limit_up_info.get('desc', 'N/A')}")
            print(f"  得分：{limit_up_info.get('score', 0)}/100")
            for detail in limit_up_info.get('details', []):
                print(f"  - {detail}")
            
            # ⚠️ 低开跌停风险预警
            if limit_down_risk and limit_down_risk.get("risk_score", 0) >= 30:
                print(f"\n{'='*70}")
                warning = generate_limit_down_warning(code, name, limit_down_risk, tech_indicators)
                print(warning)
        
        # 次日策略
        next_day_strategy = generate_next_day_strategy(code, name, tech_indicators, close, limit_up_info, sentiment_indicators)
        print(next_day_strategy)
        
        results.append({
            "code": code,
            "name": name,
            "close": close,
            "cost": cost,
            "shares": shares,
            "profit": profit,
            "profit_pct": profit_pct,
            "vol_indicators": vol_indicators,
            "tech_indicators": tech_indicators,
            "sentiment_indicators": sentiment_indicators,
            "limit_up_info": limit_up_info,
            "limit_down_risk": limit_down_risk,
            "scores": scores,
            "rating": rating,
            "action": action,
        })
    
    # 保存报告
    report_path = os.path.join(OUTPUT_DIR, f"分析报告_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "market_sentiment": market_sentiment,
            "north_flow": north_flow,
            "stocks": results,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 报告已保存：{report_path}")
    print("=" * 70)
    
    return results

# ==================== 主程序 ====================

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    results = generate_report()
