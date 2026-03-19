#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虎榜分析脚本
获取当日龙虎榜数据，识别游资席位，分析买卖情况，判断次日溢价
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# 知名游资席位映射（常见活跃游资）
YOUSI_MAPPING = {
    # 顶级游资
    "东方财富证券股份有限公司拉萨团结路第二证券营业部": "拉萨天团",
    "东方财富证券股份有限公司拉萨东环路第二证券营业部": "拉萨天团",
    "东方财富证券股份有限公司拉萨东环路第一证券营业部": "拉萨天团",
    "东方财富证券股份有限公司拉萨团结路第一证券营业部": "拉萨天团",
    "东方财富证券股份有限公司山南香曲东路证券营业部": "拉萨天团",
    "东方财富证券股份有限公司昌都两江大道证券营业部": "拉萨天团",
    
    # 知名游资
    "中国银河证券股份有限公司北京中关村大街证券营业部": "中关村",
    "中国银河证券股份有限公司北京阜成路证券营业部": "银河阜成路",
    "国泰君安证券股份有限公司上海江苏路证券营业部": "上海超短",
    "华泰证券股份有限公司深圳益田路荣超商务中心证券营业部": "深圳荣超",
    "中信证券股份有限公司上海溧阳路证券营业部": "溧阳路",
    "中信证券股份有限公司上海分公司": "中信上海",
    "中信证券股份有限公司北京总部证券营业部": "中信北京",
    "中信证券股份有限公司苏州苏州大道东证券营业部": "中信苏州",
    "中信证券股份有限公司上海浦东新区东方路证券营业部": "中信浦东",
    "中信建投证券股份有限公司上海五莲路证券营业部": "五莲路",
    "华泰证券股份有限公司浙江分公司": "浙江游资",
    "华泰证券股份有限公司无锡金融一街证券营业部": "无锡金融",
    "国泰君安证券股份有限公司深圳深南大道京基一百证券营业部": "京基一百",
    "招商证券股份有限公司深圳深南东路证券营业部": "招商深南东",
    "光大证券股份有限公司宁波中山西路证券营业部": "宁波中山西",
    "海通证券股份有限公司深圳分公司华富路证券营业部": "深圳华富路",
    "安信证券股份有限公司上海黄浦区跨龙路证券营业部": "跨龙路",
    "华鑫证券有限责任公司上海分公司": "量化基金",
    "华鑫证券有限责任公司上海宛平南路证券营业部": "量化宛平路",
    "华鑫证券有限责任公司上海红宝石路证券营业部": "量化红宝石",
    "中国国际金融股份有限公司上海分公司": "中金上海",
    "机构专用": "机构",
    "深股通专用": "深股通",
    "沪股通专用": "沪股通",
    "开源证券股份有限公司西安太华路证券营业部": "西安游资",
    "联储证券股份有限公司深圳分公司": "深圳游资",
    "西南证券股份有限公司重庆总部证券营业部": "重庆游资",
}

def identify_yousi(broker_name):
    """识别游资席位"""
    if pd.isna(broker_name):
        return "未知"
    
    broker_str = str(broker_name)
    
    for key, value in YOUSI_MAPPING.items():
        if key in broker_str:
            return value
    
    # 检查是否包含常见游资关键词
    if "东方财富" in broker_str and "拉萨" in broker_str:
        return "拉萨天团"
    elif "机构" in broker_str:
        return "机构"
    elif "股通" in broker_str:
        return "股通"
    elif "华鑫" in broker_str:
        return "量化基金"
    elif "中信" in broker_str:
        return "中信系"
    elif "银河" in broker_str:
        return "银河系"
    elif "国泰君安" in broker_str:
        return "国君系"
    elif "华泰" in broker_str:
        return "华泰系"
    elif "招商" in broker_str:
        return "招商系"
    elif "光大" in broker_str:
        return "光大系"
    elif "海通" in broker_str:
        return "海通系"
    
    return "其他游资"

def get_today_lhb_summary():
    """获取今日龙虎榜汇总数据"""
    today = datetime.now().strftime("%Y%m%d")
    print(f"📊 获取 {today} 龙虎榜汇总数据...")
    
    try:
        # 获取每日龙虎榜详情（汇总数据）
        df = ak.stock_lhb_detail_em(start_date=today, end_date=today)
        print(f"✅ 获取到 {len(df)} 条龙虎榜记录")
        return df, today
    except Exception as e:
        print(f"❌ 获取龙虎榜失败：{e}")
        return None, today

def get_stock_detail(symbol, date):
    """获取单只股票的详细龙虎榜数据"""
    try:
        # 获取买入席位
        buyers = ak.stock_lhb_stock_detail_em(symbol=symbol, date=date, flag='买入')
        # 卖出席位
        sellers = ak.stock_lhb_stock_detail_em(symbol=symbol, date=date, flag='卖出')
        return buyers, sellers
    except Exception as e:
        return None, None

def analyze_lhb(summary_df, date):
    """分析龙虎榜数据"""
    if summary_df is None or len(summary_df) == 0:
        return None
    
    analysis_results = []
    
    # 去重（同一股票可能有多条记录）
    summary_df = summary_df.drop_duplicates(subset=['代码'], keep='first')
    
    for idx, row in summary_df.iterrows():
        code = str(row['代码']).zfill(6)
        stock_name = row['名称']
        close_price = float(row['收盘价']) if pd.notna(row['收盘价']) else 0
        change_pct = float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else 0
        turnover_rate = float(row['换手率']) if pd.notna(row['换手率']) else 0
        
        # 获取汇总数据
        total_buy = float(row['龙虎榜买入额']) if pd.notna(row['龙虎榜买入额']) else 0
        total_sell = float(row['龙虎榜卖出额']) if pd.notna(row['龙虎榜卖出额']) else 0
        net_buy = float(row['龙虎榜净买额']) if pd.notna(row['龙虎榜净买额']) else 0
        
        # 获取详细席位
        buyers, sellers = get_stock_detail(code, date)
        
        buyer_details = []
        seller_details = []
        buyer_yousi = []
        seller_yousi = []
        
        if buyers is not None and len(buyers) > 0:
            for _, b in buyers.head(5).iterrows():
                broker = b['交易营业部名称']
                amount = float(b['买入金额']) if pd.notna(b['买入金额']) else 0
                yousi = identify_yousi(broker)
                buyer_details.append({'营业部': broker, '金额': amount, '游资': yousi})
                buyer_yousi.append(yousi)
        
        if sellers is not None and len(sellers) > 0:
            for _, s in sellers.head(5).iterrows():
                broker = s['交易营业部名称']
                amount = float(s['卖出金额']) if pd.notna(s['卖出金额']) else 0
                yousi = identify_yousi(broker)
                seller_details.append({'营业部': broker, '金额': amount, '游资': yousi})
                seller_yousi.append(yousi)
        
        # 判断次日溢价概率
        premium_prob = assess_premium_probability(net_buy, change_pct, turnover_rate, buyer_yousi, seller_yousi)
        
        result = {
            '代码': code,
            '名称': stock_name,
            '收盘价': close_price,
            '涨跌幅': change_pct,
            '换手率': turnover_rate,
            '总买入': total_buy,
            '总卖出': total_sell,
            '净买入': net_buy,
            '买方游资': buyer_yousi,
            '卖方游资': seller_yousi,
            '溢价概率': premium_prob,
            '上榜原因': row.get('上榜原因', ''),
            '详情': {
                'buyers': buyer_details,
                'sellers': seller_details,
            }
        }
        analysis_results.append(result)
    
    # 按净买入排序
    analysis_results.sort(key=lambda x: x['净买入'], reverse=True)
    
    return analysis_results

def assess_premium_probability(net_buy, change_pct, turnover_rate, buyer_yousi, seller_yousi):
    """评估次日溢价概率"""
    score = 50  # 基础分
    
    # 净买入加分
    if net_buy > 50000000:  # 净买入>5000 万
        score += 25
    elif net_buy > 20000000:  # 净买入>2000 万
        score += 15
    elif net_buy > 10000000:  # 净买入>1000 万
        score += 10
    elif net_buy < -20000000:  # 净卖出>2000 万
        score -= 20
    elif net_buy < -10000000:  # 净卖出>1000 万
        score -= 10
    
    # 涨停加分
    if change_pct >= 9.5:
        score += 15
    elif change_pct >= 5:
        score += 5
    elif change_pct <= -5:
        score -= 10
    
    # 换手率适中加分（5%-15% 最佳）
    if 5 <= turnover_rate <= 15:
        score += 10
    elif turnover_rate > 20:
        score -= 5  # 换手过高
    
    # 机构买入加分
    if '机构' in buyer_yousi:
        score += 15
    
    # 知名游资买入加分
    yousi_list = ['拉萨天团', '中信系', '银河系', '上海超短', '深圳荣超', '溧阳路']
    for yousi in yousi_list:
        if yousi in buyer_yousi:
            score += 5
            break
    
    # 量化基金卖出减分
    if '量化基金' in seller_yousi:
        score -= 5
    
    # 限制在 0-100 之间
    score = max(0, min(100, score))
    
    if score >= 75:
        return {'score': score, 'level': '高', 'recommend': '值得关注'}
    elif score >= 60:
        return {'score': score, 'level': '中高', 'recommend': '可观察'}
    elif score >= 45:
        return {'score': score, 'level': '中', 'recommend': '谨慎'}
    else:
        return {'score': score, 'level': '低', 'recommend': '回避'}

def format_currency(amount):
    """格式化金额"""
    if pd.isna(amount):
        return "0 万"
    amount = float(amount)
    if amount >= 100000000:
        return f"{amount/100000000:.2f}亿"
    elif amount >= 10000:
        return f"{amount/10000:.2f}万"
    else:
        return f"{amount:.0f}"

def generate_report(results, date):
    """生成分析报告"""
    report = []
    report.append("=" * 80)
    report.append(f"🐉 龙虎榜分析报告 - {date}")
    report.append("=" * 80)
    report.append("")
    
    if not results or len(results) == 0:
        report.append("⚠️ 今日无龙虎榜数据或获取失败")
        report.append("可能原因：休市、数据接口暂时不可用")
        return "\n".join(report)
    
    report.append(f"📈 共分析 {len(results)} 只上榜股票")
    report.append("")
    
    # 按净买入排序的前 10 只
    top10 = results[:10]
    
    report.append("-" * 80)
    report.append("🔥 净买入 TOP10")
    report.append("-" * 80)
    
    for i, stock in enumerate(top10, 1):
        report.append("")
        report.append(f"{i}. 【{stock['代码']}】{stock['名称']}")
        report.append(f"   收盘价：¥{stock['收盘价']:.2f} | 涨跌幅：{stock['涨跌幅']:.2f}% | 换手率：{stock['换手率']:.2f}%")
        report.append(f"   上榜原因：{stock['上榜原因']}")
        report.append(f"   总买入：{format_currency(stock['总买入'])} | 总卖出：{format_currency(stock['总卖出'])}")
        net_sign = "🟢" if stock['净买入'] > 0 else "🔴"
        report.append(f"   净买入：{format_currency(stock['净买入'])} {net_sign}")
        report.append(f"   买方游资：{', '.join(stock['买方游资']) if stock['买方游资'] else '无知名游资'}")
        report.append(f"   卖方游资：{', '.join(stock['卖方游资']) if stock['卖方游资'] else '无知名游资'}")
        report.append(f"   次日溢价概率：{stock['溢价概率']['score']}% ({stock['溢价概率']['level']}) - {stock['溢价概率']['recommend']}")
        
        # 显示详细买卖席位
        if stock['详情']['buyers']:
            report.append("   买入席位:")
            for b in stock['详情']['buyers'][:3]:
                report.append(f"     • {b['营业部']} - {format_currency(b['金额'])} [{b['游资']}]")
        
        if stock['详情']['sellers']:
            report.append("   卖出席位:")
            for s in stock['详情']['sellers'][:3]:
                report.append(f"     • {s['营业部']} - {format_currency(s['金额'])} [{s['游资']}]")
    
    report.append("")
    report.append("-" * 80)
    report.append("📊 统计摘要")
    report.append("-" * 80)
    
    # 统计
    positive_net = [s for s in results if s['净买入'] > 0]
    negative_net = [s for s in results if s['净买入'] <= 0]
    high_premium = [s for s in results if s['溢价概率']['score'] >= 75]
    
    report.append(f"净买入为正：{len(positive_net)} 只 | 净卖出为主：{len(negative_net)} 只")
    report.append(f"高溢价概率 (≥75%)：{len(high_premium)} 只")
    
    if high_premium:
        report.append("")
        report.append("🎯 重点关注（高溢价概率）:")
        for s in high_premium[:5]:
            report.append(f"   • {s['代码']} {s['名称']} - 溢价概率 {s['溢价概率']['score']}%")
    
    report.append("")
    report.append("=" * 80)
    report.append("⚠️ 风险提示：本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """主函数"""
    print("🚀 开始龙虎榜分析...")
    print("")
    
    # 获取数据
    summary_df, date = get_today_lhb_summary()
    
    if summary_df is None or len(summary_df) == 0:
        print("❌ 数据获取失败，尝试获取最近一个交易日...")
        # 尝试获取昨天的数据
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        try:
            summary_df = ak.stock_lhb_detail_em(start_date=yesterday, end_date=yesterday)
            date = yesterday
            print(f"✅ 获取到 {len(summary_df)} 条龙虎榜记录（{yesterday}）")
        except Exception as e:
            print(f"❌ 获取龙虎榜失败：{e}")
            report = f"❌ 龙虎榜数据获取失败\n日期：{date}\n请检查网络连接或稍后重试"
            print(report)
            return report
    
    if summary_df is None or len(summary_df) == 0:
        report = f"❌ 龙虎榜数据获取失败\n日期：{date}\n请检查网络连接或稍后重试"
        print(report)
        return report
    
    # 分析数据
    print("🔍 分析龙虎榜数据（获取详细席位信息）...")
    results = analyze_lhb(summary_df, date)
    
    # 生成报告
    print("📝 生成分析报告...")
    report = generate_report(results, date)
    
    print("")
    print(report)
    
    # 保存报告
    report_path = f"/home/admin/openclaw/workspace/temp/lhb_report_{date}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("")
    print(f"✅ 报告已保存至：{report_path}")
    
    return report

if __name__ == "__main__":
    main()
