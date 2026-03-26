#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虎榜分析 (快速版)
获取当日龙虎榜，识别游资席位，分析买入/卖出，判断次日溢价
"""

import akshare as ak
import pandas as pd
from datetime import datetime

# 知名游资席位映射 (部分常见席位)
YOUSI_SEATS = {
    # 一线游资
    "东方财富证券拉萨团结路第二证券营业部": "拉萨天团",
    "东方财富证券拉萨东环路第二证券营业部": "拉萨天团",
    "东方财富证券拉萨团结路第一证券营业部": "拉萨天团",
    "东方财富证券拉萨东环路第一证券营业部": "拉萨天团",
    "华泰证券深圳益田路荣超商务中心证券营业部": "深圳游资",
    "中信证券上海分公司": "上海游资",
    "中信证券杭州延安路证券营业部": "杭州游资",
    "国泰君安证券上海江苏路证券营业部": "上海游资",
    "中国银河证券绍兴证券营业部": "绍兴游资",
    "招商证券深圳深南东路证券营业部": "深圳游资",
    "华泰证券浙江分公司": "浙江游资",
    "中信建投证券杭州庆春路证券营业部": "杭州游资",
    # 机构席位
    "机构专用": "机构",
    "深股通专用": "北向资金",
    "沪股通专用": "北向资金",
}

def get_lhb_data(date_str=None):
    """获取龙虎榜数据"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    
    try:
        # 获取每日龙虎榜详情
        df = ak.stock_lhb_detail_em(date=date_str)
        return df
    except Exception as e:
        print(f"获取龙虎榜数据失败：{e}")
        return None

def analyze_lhb(df):
    """分析龙虎榜数据"""
    if df is None or df.empty:
        return "无数据"
    
    results = []
    
    # 按股票分组分析
    if '代码' in df.columns:
        stocks = df['代码'].unique()
    elif 'symbol' in df.columns:
        stocks = df['symbol'].unique()
    else:
        return "数据格式异常"
    
    for stock in stocks[:10]:  # 只分析前 10 只股票
        stock_data = df[df['代码'] == stock] if '代码' in df.columns else df[df['symbol'] == stock]
        
        if stock_data.empty:
            continue
            
        stock_name = stock_data.iloc[0].get('名称', '未知')
        
        # 分析买方席位
        buy_seats = []
        sell_seats = []
        
        for _, row in stock_data.iterrows():
            buyer = row.get('买方营业部', '')
            seller = row.get('卖方营业部', '')
            buy_amount = row.get('买入金额', 0)
            sell_amount = row.get('卖出金额', 0)
            
            if buyer and pd.notna(buyer) and buyer != 'nan':
                seat_type = YOUSI_SEATS.get(buyer, "其他席位")
                buy_seats.append((buyer, seat_type, buy_amount))
            
            if seller and pd.notna(seller) and seller != 'nan':
                seat_type = YOUSI_SEATS.get(seller, "其他席位")
                sell_seats.append((seller, seat_type, sell_amount))
        
        # 判断溢价预期
        premium_signal = "中性"
        reasons = []
        
        # 计算机构/游资净买入
        total_buy = sum([x[2] for x in buy_seats]) if buy_seats else 0
        total_sell = sum([x[2] for x in sell_seats]) if sell_seats else 0
        net_buy = total_buy - total_sell
        
        # 识别是否有知名游资
        famous_buy = [x for x in buy_seats if x[1] in ["拉萨天团", "深圳游资", "上海游资", "杭州游资", "绍兴游资"]]
        famous_sell = [x for x in sell_seats if x[1] in ["拉萨天团", "深圳游资", "上海游资", "杭州游资", "绍兴游资"]]
        
        # 识别机构
        inst_buy = [x for x in buy_seats if x[1] == "机构"]
        inst_sell = [x for x in sell_seats if x[1] == "机构"]
        
        if len(inst_buy) > len(inst_sell) and net_buy > 0:
            premium_signal = "看多 ⭐"
            reasons.append("机构净买入")
        elif len(famous_buy) > len(famous_sell) and net_buy > 0:
            premium_signal = "看多"
            reasons.append("游资净买入")
        elif net_sell := (total_sell - total_buy) > 0:
            premium_signal = "看空"
            reasons.append("净卖出")
        else:
            premium_signal = "中性"
            reasons.append("买卖平衡")
        
        results.append({
            'stock': f"{stock_name}({stock})",
            'buy_seats': buy_seats[:3],
            'sell_seats': sell_seats[:3],
            'net_buy': net_buy,
            'premium': premium_signal,
            'reasons': reasons
        })
    
    return results

def format_report(results):
    """格式化报告"""
    if not results:
        return "今日无龙虎榜数据或数据获取失败"
    
    report = []
    report.append("🦞 龙虎榜快速分析")
    report.append("=" * 40)
    report.append(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    
    for item in results:
        report.append(f"📈 {item['stock']}")
        report.append(f"   次日溢价：{item['premium']}")
        report.append(f"   原因：{', '.join(item['reasons'])}")
        report.append(f"   净额：¥{item['net_buy']/10000:.1f}万")
        
        if item['buy_seats']:
            report.append("   买入席位:")
            for seat, seat_type, amount in item['buy_seats'][:2]:
                report.append(f"     • {seat_type}: ¥{amount/10000:.1f}万")
        
        report.append("")
    
    report.append("=" * 40)
    report.append("⚠️ 数据仅供参考，不构成投资建议")
    
    return "\n".join(report)

def main():
    # 获取今日日期
    today = datetime.now().strftime("%Y%m%d")
    
    print(f"正在获取 {today} 龙虎榜数据...")
    
    # 获取数据
    df = get_lhb_data(today)
    
    if df is None:
        # 尝试获取昨日数据
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        print(f"今日数据不可用，尝试获取 {yesterday} 数据...")
        df = get_lhb_data(yesterday)
    
    if df is None or df.empty:
        print("无法获取龙虎榜数据")
        return
    
    print(f"获取到 {len(df)} 条记录")
    
    # 分析数据
    results = analyze_lhb(df)
    
    # 输出报告
    report = format_report(results)
    print("\n" + report)

if __name__ == "__main__":
    main()
