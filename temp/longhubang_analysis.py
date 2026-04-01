#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虎榜分析 (快速版)
数据源：AkShare (A 股龙虎榜数据)
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# 知名游资席位 (部分)
YOUZI_XIWEI = {
    # 一线游资
    '中信证券股份有限公司上海分公司': '上海超短帮',
    '中信证券股份有限公司上海溧阳路证券营业部': '溧阳路',
    '中信证券股份有限公司杭州延安路证券营业部': '杭州帮',
    '中信证券股份有限公司杭州婺江路证券营业部': '杭州帮',
    '国泰君安证券股份有限公司上海江苏路证券营业部': '章盟主',
    '国泰君安证券股份有限公司上海新闸路证券营业部': '章盟主',
    '海通证券股份有限公司上海建国西路证券营业部': '建国西路',
    '海通证券股份有限公司上海合肥路证券营业部': '合肥路',
    '华泰证券股份有限公司深圳益田路证券营业部': '益田路',
    '华泰证券股份有限公司厦门厦禾路证券营业部': '厦门帮',
    '华泰证券股份有限公司浙江分公司': '浙江帮',
    '中国银河证券股份有限公司绍兴证券营业部': '赵老哥',
    '中国银河证券股份有限公司北京阜成路证券营业部': '赵老哥',
    '中国中金财富证券无锡清扬路证券营业部': '清扬路',
    '光大证券股份有限公司杭州庆春路证券营业部': '庆春路',
    '东方证券股份有限公司上海浦东新区源深路证券营业部': '小鳄鱼',
    '华泰证券股份有限公司上海武定路证券营业部': '武定路',
    '中信证券股份有限公司北京总部证券营业部': '机构席位',
    '机构专用': '机构',
    '深股通专用': '北向资金',
    '沪股通专用': '北向资金',
}

def get_active_youzi():
    """获取活跃营业部数据"""
    try:
        df = ak.stock_lhb_hyyyb_em()
        return df
    except Exception as e:
        print(f"获取活跃营业部数据失败：{e}")
        return None

def get_longhubang_summary():
    """获取龙虎榜汇总数据"""
    try:
        df = ak.stock_lhb_detail_em()
        return df
    except Exception as e:
        print(f"获取龙虎榜汇总数据失败：{e}")
        return None

def analyze_longhubang(youzi_df, summary_df):
    """分析龙虎榜数据"""
    report = []
    report.append("=" * 60)
    report.append("🦞 龙虎榜分析报告")
    report.append(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 60)
    report.append("")
    
    # 1. 活跃营业部分析
    if youzi_df is not None and len(youzi_df) > 0:
        report.append("📊 今日活跃营业部 TOP10")
        report.append("-" * 60)
        for idx, row in youzi_df.head(10).iterrows():
            broker = row.get('营业部名称', '未知')
            buy_count = row.get('买入个股数', 0)
            sell_count = row.get('卖出个股数', 0)
            buy_amount = row.get('买入总金额', 0) / 10000  # 转成万
            sell_amount = row.get('卖出总金额', 0) / 10000
            net = row.get('总买卖净额', 0) / 10000
            
            # 识别游资
            youzi_name = ""
            for key, value in YOUZI_XIWEI.items():
                if key in broker:
                    youzi_name = f" [{value}]"
                    break
            
            report.append(f"{idx+1}. {broker}{youzi_name}")
            report.append(f"   买入:{buy_count}只 | 卖出:{sell_count}只 | 净买:¥{net:.0f}万")
        report.append("")
    
    # 2. 龙虎榜个股汇总分析
    if summary_df is not None and len(summary_df) > 0:
        report.append("📈 龙虎榜个股汇总 (按净买额排序)")
        report.append("-" * 60)
        
        # 按净买额排序
        summary_df_sorted = summary_df.sort_values('龙虎榜净买额', ascending=False)
        
        for idx, row in summary_df_sorted.head(15).iterrows():
            code = row.get('代码', '')
            name = row.get('名称', '')
            close_price = row.get('收盘价', 0)
            change_pct = row.get('涨跌幅', 0)
            net_buy = row.get('龙虎榜净买额', 0) / 10000  # 转成万
            total_amount = row.get('龙虎榜成交额', 0) / 10000
            turnover = row.get('换手率', 0)
            reason = row.get('上榜原因', '')
            
            # 溢价预期判断
            if net_buy > 5000:
                premium = "⭐⭐⭐ 强溢价"
            elif net_buy > 2000:
                premium = "⭐⭐ 中溢价"
            elif net_buy > 500:
                premium = "⭐ 弱溢价"
            else:
                premium = "⚠️ 无溢价"
            
            report.append(f"{name} ({code}) - {reason}")
            report.append(f"   收盘价:¥{close_price:.2f} | 涨跌幅:{change_pct:.2f}% | 换手:{turnover:.2f}%")
            report.append(f"   净买额:¥{net_buy:.0f}万 | 成交额:¥{total_amount:.0f}万")
            report.append(f"   溢价预期:{premium}")
            report.append("")
    
    # 3. 游资活跃度统计
    if youzi_df is not None and len(youzi_df) > 0:
        report.append("=" * 60)
        report.append("🔥 游资活跃度统计")
        report.append("=" * 60)
        
        youzi_count = {}
        for idx, row in youzi_df.iterrows():
            broker = row.get('营业部名称', '')
            for key, value in YOUZI_XIWEI.items():
                if key in broker:
                    youzi_count[value] = youzi_count.get(value, 0) + 1
                    break
        
        if youzi_count:
            sorted_youzi = sorted(youzi_count.items(), key=lambda x: x[1], reverse=True)
            for youzi, count in sorted_youzi[:10]:
                report.append(f"  {youzi}: {count}次上榜")
        else:
            report.append("  今日无知名游资上榜")
        report.append("")
    
    # 4. 总结
    report.append("=" * 60)
    report.append("📝 总结与策略建议")
    report.append("=" * 60)
    
    if summary_df is not None and len(summary_df) > 0:
        total_stocks = len(summary_df['代码'].unique())
        strong_premium = len(summary_df[summary_df['龙虎榜净买额'] > 5000])
        
        report.append(f"  今日上榜股票：{total_stocks}只")
        report.append(f"  强溢价预期 (>5000 万): {strong_premium}只")
        
        if strong_premium > 0:
            top_stocks = summary_df_sorted.head(3)
            report.append("  重点关注:")
            for idx, row in top_stocks.iterrows():
                report.append(f"    - {row['名称']}({row['代码']}): 净买¥{row['龙虎榜净买额']/10000:.0f}万")
        
        report.append("")
        report.append("⚠️ 风险提示:")
        report.append("  1. 龙虎榜数据仅供参考，不构成投资建议")
        report.append("  2. 游资席位可能变化，需结合盘面判断")
        report.append("  3. 次日溢价受大盘情绪影响较大")
    
    return "\n".join(report)

if __name__ == "__main__":
    print("正在获取龙虎榜数据...")
    
    # 获取活跃营业部数据
    print("1. 获取活跃营业部数据...")
    youzi_df = get_active_youzi()
    
    # 获取龙虎榜汇总数据
    print("2. 获取龙虎榜汇总数据...")
    summary_df = get_longhubang_summary()
    
    if youzi_df is not None:
        print(f"   获取到 {len(youzi_df)} 条营业部数据")
    if summary_df is not None:
        print(f"   获取到 {len(summary_df)} 条个股数据")
    
    # 生成分析报告
    report = analyze_longhubang(youzi_df, summary_df)
    print("\n" + report)
    
    # 保存报告
    with open('/home/admin/openclaw/workspace/temp/longhubang_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("\n报告已保存到：/home/admin/openclaw/workspace/temp/longhubang_report.txt")
