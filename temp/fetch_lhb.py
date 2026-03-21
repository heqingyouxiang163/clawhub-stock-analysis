#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虎榜数据获取脚本
使用 akshare 获取东方财富龙虎榜数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime

def get_lhb_data(date_str=None):
    """获取龙虎榜数据"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    
    try:
        # 获取每日龙虎榜详情（需要 start_date 和 end_date）
        lhb_df = ak.stock_lhb_detail_em(start_date=date_str, end_date=date_str)
        return lhb_df
    except Exception as e:
        print(f"获取龙虎榜数据失败：{e}")
        return None

def analyze_lhb(lhb_df):
    """分析龙虎榜数据"""
    if lhb_df is None or len(lhb_df) == 0:
        print("无龙虎榜数据")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 龙虎榜数据分析 ({len(lhb_df)} 只股票)")
    print(f"{'='*60}\n")
    
    # 知名游资席位
    famous_youzi = [
        "中信证券上海分公司",
        "华泰证券深圳益田路",
        "国泰君安上海江苏路",
        "中信证券北京总部",
        "海通证券深圳分公司华富路",
        "中国银河证券绍兴",
        "中信证券杭州延安路",
        "华鑫证券上海宛平南路",
        "南京证券南京大钟亭",
        "国泰君安南京太平南路"
    ]
    
    # 机构席位标识
    institution_keywords = ["机构专用", "深股通专用", "沪股通专用"]
    
    results = []
    
    for idx, row in lhb_df.iterrows():
        stock_name = row.get('名称', 'N/A')
        stock_code = row.get('代码', 'N/A')
        close_price = row.get('收盘价', 0)
        change_pct = row.get('涨跌幅', 0)
        
        # 买入席位
        buy_seats = []
        buy_amounts = []
        for i in range(1, 6):
            seat = row.get(f'买{i}营业部', '')
            amount = row.get(f'买{i}金额', 0)
            if seat and pd.notna(seat) and str(seat).strip():
                buy_seats.append(str(seat).strip())
                buy_amounts.append(float(amount) if pd.notna(amount) else 0)
        
        # 卖出席位
        sell_seats = []
        sell_amounts = []
        for i in range(1, 6):
            seat = row.get(f'卖{i}营业部', '')
            amount = row.get(f'卖{i}金额', 0)
            if seat and pd.notna(seat) and str(seat).strip():
                sell_seats.append(str(seat).strip())
                sell_amounts.append(float(amount) if pd.notna(amount) else 0)
        
        # 计算净买入
        total_buy = sum(buy_amounts)
        total_sell = sum(sell_amounts)
        net_buy = total_buy - total_sell
        
        # 识别知名游资
        famous_buy = []
        for seat in buy_seats:
            for famous in famous_youzi:
                if famous in seat:
                    famous_buy.append(famous)
        
        # 识别机构席位
        institution_buy = 0
        institution_sell = 0
        for seat in buy_seats:
            for keyword in institution_keywords:
                if keyword in seat:
                    institution_buy += 1
        for seat in sell_seats:
            for keyword in institution_keywords:
                if keyword in seat:
                    institution_sell += 1
        
        # 判断次日溢价预期
        premium_expectation = 0
        if net_buy > 50000000:  # 净买入>5000 万
            premium_expectation = 5
        if net_buy > 100000000:  # 净买入>1 亿
            premium_expectation = 8
        if institution_buy > 0 and len(famous_buy) > 0:  # 机构 + 游资
            premium_expectation = max(premium_expectation, 8)
        if len(famous_buy) >= 2:  # 多家游资
            premium_expectation = max(premium_expectation, 5)
        if net_sell > 50000000:  # 净卖出>5000 万
            premium_expectation = -3
        
        result = {
            'stock_name': stock_name,
            'stock_code': stock_code,
            'close_price': close_price,
            'change_pct': change_pct,
            'total_buy': total_buy,
            'total_sell': total_sell,
            'net_buy': net_buy,
            'famous_buy': famous_buy,
            'institution_buy': institution_buy,
            'institution_sell': institution_sell,
            'buy_seats': buy_seats,
            'sell_seats': sell_seats,
            'premium_expectation': premium_expectation
        }
        results.append(result)
    
    # 按净买入排序
    results.sort(key=lambda x: x['net_buy'], reverse=True)
    
    return results

def generate_report(results):
    """生成分析报告"""
    if not results:
        return "无龙虎榜数据"
    
    report = []
    report.append("=" * 70)
    report.append("📊 龙虎榜分析报告")
    report.append(f"日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 70)
    report.append("")
    
    # 重点关注（净买入前 3 名）
    report.append("🎯 重点关注（净买入前 3 名）")
    report.append("-" * 70)
    
    for i, r in enumerate(results[:3], 1):
        report.append(f"\n{i}. {r['stock_name']} ({r['stock_code']})")
        report.append(f"   收盘价：¥{r['close_price']:.2f}  涨跌幅：{r['change_pct']:.2f}%")
        report.append(f"   买入总额：{r['total_buy']/10000:.2f}万  卖出总额：{r['total_sell']/10000:.2f}万")
        report.append(f"   净买入：{r['net_buy']/10000:.2f}万")
        
        if r['famous_buy']:
            report.append(f"   知名游资：{', '.join(r['famous_buy'])}")
        if r['institution_buy'] > 0:
            report.append(f"   机构席位：买入{r['institution_buy']}家")
        
        report.append(f"   次日预期：{r['premium_expectation']:+.1f}%")
        
        # 操作建议
        if r['premium_expectation'] >= 5:
            suggestion = "✅ 高开可追"
        elif r['premium_expectation'] >= 0:
            suggestion = "⚠️ 观察为主"
        else:
            suggestion = "❌ 注意风险"
        report.append(f"   操作建议：{suggestion}")
    
    report.append("")
    report.append("-" * 70)
    report.append("📊 游资动向统计")
    report.append("-" * 70)
    
    # 统计游资活跃度
    youzi_stats = {}
    for r in results:
        for yz in r['famous_buy']:
            if yz not in youzi_stats:
                youzi_stats[yz] = 0
            youzi_stats[yz] += 1
    
    if youzi_stats:
        report.append("\n活跃游资排名:")
        sorted_youzi = sorted(youzi_stats.items(), key=lambda x: x[1], reverse=True)
        for yz, count in sorted_youzi[:5]:
            report.append(f"   - {yz}: 出现 {count} 次")
    
    # 统计机构动向
    report.append("\n机构动向:")
    inst_buy = sum(1 for r in results if r['institution_buy'] > 0)
    inst_sell = sum(1 for r in results if r['institution_sell'] > 0)
    report.append(f"   - 机构买入：{inst_buy} 只股票")
    report.append(f"   - 机构卖出：{inst_sell} 只股票")
    
    report.append("")
    report.append("=" * 70)
    report.append("⚠️ 风险提示：龙虎榜数据仅供参考，不构成投资建议")
    report.append("=" * 70)
    
    return "\n".join(report)

if __name__ == "__main__":
    # 获取今日龙虎榜
    today = datetime.now().strftime("%Y%m%d")
    print(f"正在获取 {today} 龙虎榜数据...")
    
    lhb_df = get_lhb_data(today)
    
    if lhb_df is not None:
        print(f"成功获取 {len(lhb_df)} 只股票数据")
        results = analyze_lhb(lhb_df)
        report = generate_report(results)
        print(report)
        
        # 保存报告
        report_path = "/home/admin/openclaw/workspace/temp/lhb_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存至：{report_path}")
    else:
        print("获取龙虎榜数据失败")
