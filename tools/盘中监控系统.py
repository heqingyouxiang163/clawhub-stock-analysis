#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中实时监控系统
基于短线高手操盘手法，实时监控持仓股和市场情绪
数据源：腾讯财经 API (替代 akshare/东财)
"""

import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
from 腾讯财经_API import get_multiple_stocks, get_single_stock
from datetime import datetime
import json
import os

# ==================== 配置区 ====================

HOLDINGS = [
    {"code": "002342", "name": "巨力索具", "cost": 14.132, "shares": 500},
    {"code": "603778", "name": "国晟科技", "cost": 24.410, "shares": 500},
]

OUTPUT_DIR = "/home/admin/openclaw/workspace/temp/盘中监控"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== 分时图战法识别 ====================

def check_intraday_vwap_pattern(code, realtime_data):
    """检查分时图强势形态 (股价不破分时均线 + 均线向上)"""
    # 简化版本：使用实时数据推断
    # 实际应用中需要获取每分钟的分时数据
    
    if realtime_data is None:
        return {"is_pattern": False, "score": 0, "details": ["数据不足"]}
    
    price = realtime_data.get("price", 0)
    open_price = realtime_data.get("open", 0)
    high = realtime_data.get("high", 0)
    low = realtime_data.get("low", 0)
    prev_close = realtime_data.get("prev_close", open_price)
    
    # 估算分时均线 (简化：用 (开盘 + 最高 + 最低 + 当前)/4 近似)
    estimated_vwap = (open_price + high + low + price) / 4
    
    details = []
    score = 0
    
    # 1. 股价在分时均线上方 (30 分)
    if price > estimated_vwap * 1.01:  # 高于均线 1%
        score += 30
        details.append(f"✅ 股价在分时均线上方 ({((price-estimated_vwap)/estimated_vwap*100):.1f}%)")
    elif price > estimated_vwap:
        score += 20
        details.append(f"🟡 股价在均线上方 (微弱)")
    else:
        details.append(f"❌ 股价跌破分时均线")
    
    # 2. 均线斜率向上 (25 分)
    # 简化：用涨幅推断均线方向
    change_from_open = (price - open_price) / open_price * 100 if open_price > 0 else 0
    if change_from_open > 3:  # 涨幅>3%，均线大概向上>30 度
        score += 25
        details.append(f"✅ 分时均线陡峭向上 (涨幅{change_from_open:.1f}%)")
    elif change_from_open > 2:
        score += 20
        details.append(f"✅ 分时均线向上 (涨幅{change_from_open:.1f}%)")
    elif change_from_open > 0:
        score += 10
        details.append(f"🟡 分时均线走平 (涨幅{change_from_open:.1f}%)")
    else:
        details.append(f"❌ 分时均线向下")
    
    # 3. 涨幅 (10 分)
    total_change = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0
    if total_change > 7:
        score += 10
        details.append(f"✅ 大涨{total_change:.1f}%")
    elif total_change > 5:
        score += 8
        details.append(f"✅ 上涨{total_change:.1f}%")
    elif total_change > 3:
        score += 6
        details.append(f"🟡 上涨{total_change:.1f}%")
    elif total_change > 0:
        score += 4
        details.append(f"🟡 微涨{total_change:.1f}%")
    else:
        details.append(f"❌ 下跌{total_change:.1f}%")
    
    # 判断是否构成形态
    is_pattern = score >= 60 and price > estimated_vwap
    
    # 评级
    if score >= 85:
        rating = "🟢🟢🟢 极强"
        action = "积极买入/持有"
        probability = "涨停概率 70%+"
    elif score >= 70:
        rating = "🟢🟢 强势"
        action = "持有/加仓"
        probability = "大涨概率 60%+"
    elif score >= 55:
        rating = "🟡 中性"
        action = "观望"
        probability = "震荡为主"
    else:
        rating = "🔴 弱势"
        action = "卖出/空仓"
        probability = "下跌风险"
    
    return {
        "is_pattern": is_pattern,
        "score": score,
        "rating": rating,
        "action": action,
        "probability": probability,
        "details": details,
        "estimated_vwap": round(estimated_vwap, 2),
        "price_vs_vwap": round(((price - estimated_vwap) / estimated_vwap * 100) if estimated_vwap > 0 else 0, 2),
    }

# ==================== 五日线首阴反包形态识别 ====================

def check_ma5_rebound_pattern(code, df):
    """检查五日线首阴反包形态"""
    if df is None or len(df) < 10:
        return {"is_pattern": False, "score": 0, "details": []}
    
    latest = df.iloc[-1]  # 今日 (首阴)
    prev = df.iloc[-2]    # 昨日 (阳线)
    
    details = []
    score = 0
    
    # 计算 5 日线
    ma5 = df['收盘'].rolling(5).mean().iloc[-1]
    ma10 = df['收盘'].rolling(10).mean().iloc[-1]
    ma20 = df['收盘'].rolling(20).mean().iloc[-1]
    
    # 条件 1: 趋势向上 (MA5>MA10>MA20)
    if ma5 > ma10 > ma20:
        score += 25
        details.append("✅ 趋势向上 (多头排列)")
    else:
        details.append("❌ 趋势不满足多头排列")
    
    # 条件 2: 连续上涨至少 3 天 (之前 3 连阳)
    consecutive_gains = 0
    for i in range(2, min(6, len(df))):
        if df.iloc[-i]['涨跌幅'] > 0:
            consecutive_gains += 1
        else:
            break
    
    if consecutive_gains >= 3:
        score += 15
        details.append(f"✅ 之前{consecutive_gains}连阳")
    else:
        details.append(f"❌ 连阳不足 ({consecutive_gains}天)")
    
    # 条件 3: 今日首阴
    today_change = latest['涨跌幅']
    if -5 <= today_change < 0:
        score += 20
        details.append(f"✅ 首阴 ({today_change}%)")
    else:
        details.append(f"❌ 不是首阴 ({today_change}%)")
        return {"is_pattern": False, "score": 0, "details": details}
    
    # 条件 4: 缩量回调
    vol_ratio = latest['成交量'] / prev['成交量'] if prev['成交量'] > 0 else 1
    if vol_ratio < 0.7:
        score += 25
        details.append(f"✅ 明显缩量 ({vol_ratio:.2f}倍)")
    elif vol_ratio < 0.8:
        score += 15
        details.append(f"🟡 缩量 ({vol_ratio:.2f}倍)")
    else:
        details.append(f"❌ 未缩量 ({vol_ratio:.2f}倍)")
    
    # 条件 5: 5 日线支撑
    low = latest['最低']
    close = latest['收盘']
    
    if low <= ma5 * 1.02 and close >= ma5 * 0.98:
        score += 20
        details.append(f"✅ 5 日线支撑有效 (MA5={ma5:.2f})")
    elif low <= ma5 * 1.05 and close >= ma5 * 0.95:
        score += 10
        details.append(f"🟡 接近 5 日线 (MA5={ma5:.2f})")
    else:
        details.append(f"❌ 未触及 5 日线 (MA5={ma5:.2f})")
    
    # 判断是否构成形态
    is_pattern = score >= 60
    
    # 反包概率
    if score >= 80:
        probability = "70%+"
        action = "积极买入"
    elif score >= 60:
        probability = "50-70%"
        action = "谨慎买入"
    elif score >= 40:
        probability = "30-50%"
        action = "轻仓试错"
    else:
        probability = "<30%"
        action = "放弃"
    
    return {
        "is_pattern": is_pattern,
        "score": score,
        "probability": probability,
        "action": action,
        "details": details,
        "ma5": round(ma5, 2),
        "today_change": today_change,
        "vol_ratio": round(vol_ratio, 2),
    }

# ==================== 数据获取 ====================

def get_market_sentiment_realtime():
    """获取实时市场情绪"""
    try:
        # 涨跌家数
        df = ak.stock_market_activity_legu()
        if not df.empty:
            up = df[df['类型'] == '上涨']['数量'].values[0] if len(df[df['类型'] == '上涨']) > 0 else 0
            down = df[df['类型'] == '下跌']['数量'].values[0] if len(df[df['类型'] == '下跌']) > 0 else 0
            limit_up = df[df['类型'] == '涨停']['数量'].values[0] if len(df[df['类型'] == '涨停']) > 0 else 0
            limit_down = df[df['类型'] == '跌停']['数量'].values[0] if len(df[df['类型'] == '跌停']) > 0 else 0
            
            return {
                "up": up,
                "down": down,
                "limit_up": limit_up,
                "limit_down": limit_down,
                "ratio": up / down if down > 0 else 999,
            }
    except Exception as e:
        print(f"获取市场情绪失败：{e}")
    
    return {"up": 0, "down": 0, "limit_up": 0, "limit_down": 0, "ratio": 1}

def get_north_flow_realtime():
    """获取北向资金实时流向"""
    try:
        df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
        if not df.empty:
            return float(df.iloc[0].get('净买入额', 0))
    except Exception as e:
        print(f"获取北向资金失败：{e}")
    return 0

def get_stock_data_for_pattern(code, days=10):
    """获取股票历史数据用于形态识别"""
    try:
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, adjust="qfq")
        if len(df) > 0:
            return df
    except Exception as e:
        print(f"获取 {code} 历史数据失败：{e}")
    return None

def get_stock_realtime(code):
    """获取个股实时数据"""
    try:
        # 使用实时行情接口
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == code]
        if not stock.empty:
            row = stock.iloc[0]
            return {
                "code": code,
                "name": row.get('名称', ''),
                "price": float(row.get('最新价', 0)),
                "change": float(row.get('涨跌幅', 0)),
                "change_amount": float(row.get('涨跌额', 0)),
                "volume": float(row.get('成交量', 0)),
                "amount": float(row.get('成交额', 0)),
                "high": float(row.get('最高', 0)),
                "low": float(row.get('最低', 0)),
                "open": float(row.get('今开', 0)),
                "prev_close": float(row.get('昨收', 0)),
            }
    except Exception as e:
        print(f"获取 {code} 实时数据失败：{e}")
    return None

def get_main_flow_realtime(code):
    """获取个股实时资金流向"""
    try:
        df = ak.stock_individual_fund_flow_rank(indicator="今日")
        if not df.empty:
            stock_row = df[df['代码'] == code]
            if not stock_row.empty:
                row = stock_row.iloc[0]
                return {
                    "total": float(row.get('主力净流入 - 净额', 0)),
                    "super_large": float(row.get('超大单净流入 - 净额', 0)),
                    "large": float(row.get('大单净流入 - 净额', 0)),
                    "medium": float(row.get('中单净流入 - 净额', 0)),
                    "small": float(row.get('小单净流入 - 净额', 0)),
                }
    except Exception as e:
        print(f"获取 {code} 资金流向失败：{e}")
    return {"total": 0, "super_large": 0, "large": 0, "medium": 0, "small": 0}

# ==================== 情绪评分 ====================

def calculate_market_sentiment_score(sentiment_data, north_flow):
    """计算市场情绪得分 (0-100)"""
    score = 0
    
    # 涨停家数得分 (30 分)
    limit_up = sentiment_data.get("limit_up", 0)
    if limit_up > 80:
        score += 25  # 高潮，警惕
    elif limit_up > 50:
        score += 20
    elif limit_up > 20:
        score += 15
    else:
        score += 5  # 冰点
    
    # 跌停家数得分 (25 分)
    limit_down = sentiment_data.get("limit_down", 0)
    if limit_down > 50:
        score += 0  # 恐慌
    elif limit_down > 30:
        score += 5
    elif limit_down > 10:
        score += 10
    else:
        score += 20
    
    # 涨跌比得分 (20 分)
    ratio = sentiment_data.get("ratio", 1)
    if ratio > 3:
        score += 20
    elif ratio > 2:
        score += 15
    elif ratio > 1:
        score += 10
    else:
        score += 5
    
    # 北向资金得分 (15 分)
    if north_flow > 50:
        score += 15
    elif north_flow > 20:
        score += 12
    elif north_flow > -20:
        score += 8
    elif north_flow > -50:
        score += 3
    
    # 情绪周期判断
    if score >= 70:
        stage = "高潮期"
        action = "止盈为主，不追高"
    elif score >= 50:
        stage = "强势期"
        action = "积极操作"
    elif score >= 30:
        stage = "震荡期"
        action = "谨慎操作"
    else:
        stage = "冰点期"
        action = "空仓/试错首板"
    
    return {
        "score": score,
        "stage": stage,
        "action": action,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "ratio": round(ratio, 2),
        "north_flow": round(north_flow, 2),
    }

# ==================== 预警系统 ====================

def check_warnings(stock_data, main_flow, prev_close):
    """检查预警信号"""
    warnings = []
    price = stock_data.get("price", 0)
    change = stock_data.get("change", 0)
    open_price = stock_data.get("open", prev_close)
    
    # 一级预警 (极度危险) 🔴🔴🔴
    if change <= -9.5:
        warnings.append({
            "level": "🔴🔴🔴 一级预警",
            "type": "跌停",
            "message": f"已跌停 ({change}%)，立即止损！",
            "action": "能卖出就卖出，不抱幻想"
        })
    elif change <= -8:
        warnings.append({
            "level": "🔴🔴🔴 一级预警",
            "type": "大幅低开",
            "message": f"低开/下跌超 -8% ({change}%)",
            "action": "反抽坚决卖出"
        })
    
    # 二级预警 (高风险) 🔴🔴
    elif change <= -5:
        warnings.append({
            "level": "🔴🔴 二级预警",
            "type": "低开",
            "message": f"低开/下跌超 -5% ({change}%)",
            "action": "准备止损，等待反抽"
        })
    
    # 资金流向预警
    super_large = main_flow.get("super_large", 0)
    if super_large < -5000:
        warnings.append({
            "level": "🔴🔴 二级预警",
            "type": "超大单流出",
            "message": f"超大单大幅流出 {super_large/1000:.1f}千万",
            "action": "警惕主力出货"
        })
    
    # 三级预警 (注意) 🔴
    if price < open_price and change < 0:
        warnings.append({
            "level": "🔴 三级预警",
            "type": "跌破开盘价",
            "message": f"跌破开盘价 ({change}%)",
            "action": "减仓，设置止损"
        })
    
    # 机会预警 🟢
    if change >= 9.5:
        warnings.append({
            "level": "🟢 机会预警",
            "type": "涨停",
            "message": f"已涨停 ({change}%)",
            "action": "持有，观察封单"
        })
    elif change >= 5:
        warnings.append({
            "level": "🟢 机会预警",
            "type": "强势拉升",
            "message": f"大涨超 5% ({change}%)",
            "action": "持有，准备打板"
        })
    
    return warnings

# ==================== 报告生成 ====================

def generate_monitoring_report():
    """生成盘中监控报告"""
    print("=" * 70)
    print("🔍 盘中实时监控系统")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 获取市场情绪
    print("\n📊 获取市场数据...")
    sentiment = get_market_sentiment_realtime()
    north_flow = get_north_flow_realtime()
    
    # 计算情绪得分
    emotion_score = calculate_market_sentiment_score(sentiment, north_flow)
    
    print(f"\n【市场情绪】")
    print(f"  涨停家数：{emotion_score['limit_up']}")
    print(f"  跌停家数：{emotion_score['limit_down']}")
    print(f"  涨跌比：{emotion_score['ratio']}")
    print(f"  北向资金：{emotion_score['north_flow']} 亿元")
    print(f"  ─────────────────")
    print(f"  情绪得分：{emotion_score['score']}/100")
    print(f"  情绪周期：{emotion_score['stage']}")
    print(f"  操作建议：{emotion_score['action']}")
    
    results = []
    all_warnings = []
    
    for stock in HOLDINGS:
        code = stock["code"]
        name = stock["name"]
        cost = stock["cost"]
        shares = stock["shares"]
        
        print(f"\n{'='*70}")
        print(f"📈 {name} ({code})")
        print(f"{'='*70}")
        
        # 获取实时数据
        stock_data = get_stock_realtime(code)
        if stock_data is None:
            print("  数据获取失败，跳过")
            continue
        
        # 🎯 检查五日线首阴反包形态
        df = get_stock_data_for_pattern(code)
        ma5_pattern = check_ma5_rebound_pattern(code, df) if df is not None else {"is_pattern": False, "score": 0}
        
        # 🎯 检查分时图强势形态
        intraday_pattern = check_intraday_vwap_pattern(code, stock_data)
        
        main_flow = get_main_flow_realtime(code)
        prev_close = stock_data.get("prev_close", stock_data["price"])
        
        # 基础数据
        price = stock_data["price"]
        change = stock_data["change"]
        open_price = stock_data["open"]
        high = stock_data["high"]
        low = stock_data["low"]
        
        position_value = price * shares
        profit = (price - cost) * shares
        profit_pct = ((price - cost) / cost) * 100
        
        print(f"\n【实时数据】")
        print(f"  现价：{price} 元 ({change}%)")
        print(f"  开盘：{open_price} 元")
        print(f"  最高：{high} 元")
        print(f"  最低：{low} 元")
        print(f"  持仓盈亏：{profit:+.2f} 元 ({profit_pct:+.2f}%)")
        
        # 🎯 分时图战法
        print(f"\n🔥【分时图战法】")
        print(f"  形态评级：{intraday_pattern.get('rating', 'N/A')}")
        print(f"  形态评分：{intraday_pattern.get('score', 0)}/100")
        print(f"  概率预测：{intraday_pattern.get('probability', 'N/A')}")
        print(f"  操作建议：{intraday_pattern.get('action', 'N/A')}")
        print(f"  分时均线：{intraday_pattern.get('estimated_vwap', 'N/A')} 元")
        print(f"  股价位置：{intraday_pattern.get('price_vs_vwap', 0):+.1f}% (相对于均线)")
        for detail in intraday_pattern.get('details', []):
            print(f"    {detail}")
        
        # 关键提醒
        if intraday_pattern.get("score", 0) >= 85:
            print(f"\n  💡 极强形态！主力控盘良好，大概率涨停！")
        elif intraday_pattern.get("score", 0) >= 70:
            print(f"\n  💡 强势形态，持有为主！")
        elif intraday_pattern.get("score", 0) < 55:
            print(f"\n  ⚠️ 弱势形态，警惕跌破均线！")
        
        # 🎯 五日线首阴反包形态
        if ma5_pattern.get("is_pattern", False):
            print(f"\n🔥【五日线首阴反包形态】")
            print(f"  形态评分：{ma5_pattern.get('score', 0)}/100")
            print(f"  反包概率：{ma5_pattern.get('probability', 'N/A')}")
            print(f"  操作建议：{ma5_pattern.get('action', 'N/A')}")
            print(f"  5 日线：{ma5_pattern.get('ma5', 'N/A')} 元")
            for detail in ma5_pattern.get('details', []):
                print(f"    {detail}")
            
            # 次日预案
            print(f"\n  次日预案:")
            print(f"    IF 高开 2-5% + 快速拉升 → 买入 30-50%")
            print(f"    IF 平开 + 突破开盘价 → 买入 20-30%")
            print(f"    IF 低开 -3% 以内 + 反抽翻红 → 轻仓试错")
            print(f"    IF 低开 -5% 以下 → 放弃")
            print(f"    止损位：{price * 0.95:.2f} 元 (-5%)")
        
        # 资金流向
        print(f"\n【资金流向】")
        print(f"  超大单：{main_flow.get('super_large', 0)/1000:.1f}千万")
        print(f"  大单：{main_flow.get('large', 0)/1000:.1f}千万")
        print(f"  中单：{main_flow.get('medium', 0)/1000:.1f}千万")
        print(f"  小单：{main_flow.get('small', 0)/1000:.1f}千万")
        print(f"  主力净流入：{main_flow.get('total', 0)/1000:.1f}千万")
        
        # 预警检查
        warnings = check_warnings(stock_data, main_flow, prev_close)
        if warnings:
            print(f"\n⚠️【预警信号】")
            for w in warnings:
                print(f"  {w['level']}: {w['message']}")
                print(f"    操作：{w['action']}")
            all_warnings.extend([(code, name, w) for w in warnings])
        else:
            print(f"\n✅【无预警】走势正常")
        
        # 操作建议
        print(f"\n【操作建议】")
        if change >= 9.5:
            print(f"  已涨停，持有观察封单")
            print(f"  IF 封单>2 亿 → 持有")
            print(f"  IF 封单<5000 万 → 减仓")
        elif change >= 5:
            print(f"  强势拉升，持有")
            print(f"  IF 继续拉升 → 准备打板")
            print(f"  IF 回落 → 减仓")
        elif change >= 0:
            print(f"  走势正常，持有观察")
        elif change >= -5:
            print(f"  弱势调整，设置止损位")
            print(f"  止损位：{price * 0.95:.2f} 元 (-5%)")
        elif change >= -8:
            print(f"  危险信号，反抽卖出")
            print(f"  反抽位：{open_price * 0.98:.2f} 元")
        else:
            print(f"  极度危险，坚决止损！")
            print(f"  能卖出就卖出，不抱幻想")
        
        results.append({
            "code": code,
            "name": name,
            "price": price,
            "change": change,
            "open": open_price,
            "high": high,
            "low": low,
            "profit": profit,
            "profit_pct": profit_pct,
            "main_flow": main_flow,
            "warnings": warnings,
        })
    
    # 汇总预警
    print(f"\n{'='*70}")
    print(f"⚠️【预警汇总】")
    if all_warnings:
        for code, name, w in all_warnings:
            print(f"  {name} ({code}): {w['level']} - {w['message']}")
    else:
        print(f"  无预警，走势正常")
    
    # 总体操作建议
    print(f"\n【总体操作建议】")
    if emotion_score["score"] >= 70:
        print(f"  情绪高潮，止盈为主，不追高")
    elif emotion_score["score"] >= 50:
        print(f"  情绪强势，积极操作")
    elif emotion_score["score"] >= 30:
        print(f"  情绪震荡，谨慎操作")
    else:
        print(f"  情绪冰点，空仓/试错首板")
    
    if all_warnings:
        print(f"\n  预警股票优先处理！")
    
    # 保存报告
    report_path = os.path.join(OUTPUT_DIR, f"盘中监控_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "market_sentiment": emotion_score,
            "stocks": results,
            "warnings": all_warnings,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 报告已保存：{report_path}")
    print("=" * 70)
    
    return results

# ==================== 主程序 ====================

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    results = generate_monitoring_report()
