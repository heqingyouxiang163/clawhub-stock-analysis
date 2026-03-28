#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虎榜分析脚本
功能：
1. 获取当日龙虎榜
2. 识别游资席位
3. 分析买入/卖出
4. 判断次日溢价
5. 输出报告
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import json

# 常见游资席位 (部分知名游资)
YOUNG_CAPITAL_SEATS = {
    # 顶级游资
    '中信证券上海分公司': '作手新一',
    '国泰君安上海江苏路': '作手新一',
    '华泰证券深圳益田路荣超商务中心': '作手新一',
    '中信证券杭州延安路': '章盟主',
    '国泰君安上海四平路': '章盟主',
    '海通证券上海建国西路': '章盟主',
    '中信证券杭州四季路': '章盟主',
    '国泰君安成都北一环路': '成都系',
    '华泰证券成都南一环路第二': '成都系',
    '中国银河成都北二环路': '成都系',
    '华泰证券厦门厦禾路': '厦门系',
    '国泰君安厦门湖滨南路': '厦门系',
    '兴业证券厦门分公司': '厦门系',
    '华泰证券深圳分公司': '深圳系',
    '中信证券深圳分公司': '深圳系',
    '招商证券深圳深南东路': '深圳系',
    '东方财富证券拉萨团结路第二': '拉萨天团',
    '东方财富证券拉萨东环路第二': '拉萨天团',
    '东方财富证券拉萨团结路第一': '拉萨天团',
    '东方财富证券拉萨东环路第一': '拉萨天团',
    '中国银河北京中关村大街': '中关村',
    '国泰君安北京知春路': '北京系',
    '中信建投北京中关村东路': '北京系',
    '华泰证券武汉新华路': '武汉系',
    '长江证券武汉武珞路': '武汉系',
    '光大证券宁波解放南路': '宁波涨停板敢死队',
    '国信证券宁波百丈东路': '宁波涨停板敢死队',
    '华泰证券宁波柳汀街': '宁波涨停板敢死队',
    '中信证券宁波甬江大道': '宁波涨停板敢死队',
    '国泰君安上海银城中路': '上海系',
    '海通证券上海建国西路': '上海系',
    '申万宏源上海闵行区东川路': '上海系',
    # 机构席位
    '机构专用': '机构',
    '深股通专用': '深股通',
    '沪股通专用': '沪股通',
}

def get_today_lhb():
    """获取今日龙虎榜数据"""
    today = datetime.now().strftime('%Y%m%d')
    print(f"📊 获取 {today} 龙虎榜数据...")
    
    try:
        # 获取每日龙虎榜详情 (需要 start_date 和 end_date)
        df = ak.stock_lhb_detail_em(start_date=today, end_date=today)
        print(f"✅ 成功获取 {len(df)} 条龙虎榜记录")
        return df, today
    except Exception as e:
        print(f"❌ 获取龙虎榜失败：{e}")
        # 尝试获取最近一个交易日的数据
        for i in range(1, 10):
            prev_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            try:
                df = ak.stock_lhb_detail_em(start_date=prev_date, end_date=prev_date)
                print(f"✅ 使用 {prev_date} 数据替代，共 {len(df)} 条记录")
                return df, prev_date
            except:
                continue
        return None, None

def identify_capital_type(broker):
    """识别席位类型"""
    if not broker or pd.isna(broker):
        return '未知'
    
    broker_str = str(broker)
    
    # 机构席位
    if '机构专用' in broker_str:
        return '机构'
    if '深股通' in broker_str:
        return '深股通'
    if '沪股通' in broker_str:
        return '沪股通'
    
    # 游资席位
    for seat, name in YOUNG_CAPITAL_SEATS.items():
        if seat in broker_str:
            return f'游资-{name}'
    
    # 东方财富拉萨系（散户集中营）
    if '东方财富' in broker_str and '拉萨' in broker_str:
        return '拉萨天团'
    
    return '普通席位'

def analyze_lhb(df):
    """分析龙虎榜数据"""
    if df is None or len(df) == 0:
        return None
    
    analysis = {
        'total_stocks': 0,
        'stocks': [],
        'young_capital_activity': [],
        'institution_activity': [],
        'net_buy_top': [],
        'recommendations': []
    }
    
    # 按股票代码分组
    if '代码' not in df.columns:
        # 尝试不同的列名
        code_cols = [c for c in df.columns if '代码' in c or 'code' in c.lower()]
        if code_cols:
            df = df.rename(columns={code_cols[0]: '代码'})
    
    if '代码' not in df.columns:
        print("❌ 无法识别股票代码列")
        return analysis
    
    grouped = df.groupby('代码')
    
    for code, group in grouped:
        stock_info = {
            'code': code,
            'name': group['名称'].iloc[0] if '名称' in group.columns else '未知',
            'close_price': group['收盘价'].iloc[0] if '收盘价' in group.columns else None,
            'change_pct': group['涨跌幅'].iloc[0] if '涨跌幅' in group.columns else None,
            'turnover_rate': group['换手率'].iloc[0] if '换手率' in group.columns else None,
            'buy_total': 0,
            'sell_total': 0,
            'net_buy': 0,
            'buy_seats': [],
            'sell_seats': [],
            'young_capital_buy': 0,
            'young_capital_sell': 0,
            'institution_buy': 0,
            'institution_sell': 0,
            'score': 0,
            'next_day_premium_estimate': 0
        }
        
        # 分析买入席位
        buy_cols = [c for c in group.columns if '买' in c and '营业部' in c]
        buy_amount_cols = [c for c in group.columns if '买' in c and '金额' in c]
        
        if len(buy_cols) >= 5 and len(buy_amount_cols) >= 5:
            for i in range(5):
                if i < len(buy_cols) and i < len(buy_amount_cols):
                    broker = group[buy_cols[i]].iloc[0]
                    amount = group[buy_amount_cols[i]].iloc[0] if i < len(buy_amount_cols) else 0
                    
                    if pd.notna(broker) and broker:
                        capital_type = identify_capital_type(broker)
                        stock_info['buy_seats'].append({
                            'broker': broker,
                            'amount': amount if pd.notna(amount) else 0,
                            'type': capital_type
                        })
                        stock_info['buy_total'] += amount if pd.notna(amount) else 0
                        
                        if '游资' in capital_type:
                            stock_info['young_capital_buy'] += amount if pd.notna(amount) else 0
                        elif '机构' in capital_type:
                            stock_info['institution_buy'] += amount if pd.notna(amount) else 0
        
        # 分析卖出席位
        sell_cols = [c for c in group.columns if '卖' in c and '营业部' in c]
        sell_amount_cols = [c for c in group.columns if '卖' in c and '金额' in c]
        
        if len(sell_cols) >= 5 and len(sell_amount_cols) >= 5:
            for i in range(5):
                if i < len(sell_cols) and i < len(sell_amount_cols):
                    broker = group[sell_cols[i]].iloc[0]
                    amount = group[sell_amount_cols[i]].iloc[0] if i < len(sell_amount_cols) else 0
                    
                    if pd.notna(broker) and broker:
                        capital_type = identify_capital_type(broker)
                        stock_info['sell_seats'].append({
                            'broker': broker,
                            'amount': amount if pd.notna(amount) else 0,
                            'type': capital_type
                        })
                        stock_info['sell_total'] += amount if pd.notna(amount) else 0
                        
                        if '游资' in capital_type:
                            stock_info['young_capital_sell'] += amount if pd.notna(amount) else 0
                        elif '机构' in capital_type:
                            stock_info['institution_sell'] += amount if pd.notna(amount) else 0
        
        # 计算净买入
        stock_info['net_buy'] = stock_info['buy_total'] - stock_info['sell_total']
        
        # 评分系统 (100 分制)
        score = 50  # 基础分
        
        # 游资买入加分
        if stock_info['young_capital_buy'] > 10000000:  # >1000 万
            score += 15
        elif stock_info['young_capital_buy'] > 5000000:  # >500 万
            score += 10
        elif stock_info['young_capital_buy'] > 1000000:  # >100 万
            score += 5
        
        # 机构买入加分
        if stock_info['institution_buy'] > 20000000:  # >2000 万
            score += 20
        elif stock_info['institution_buy'] > 10000000:  # >1000 万
            score += 15
        elif stock_info['institution_buy'] > 5000000:  # >500 万
            score += 10
        
        # 净买入加分
        if stock_info['net_buy'] > 30000000:  # >3000 万
            score += 15
        elif stock_info['net_buy'] > 10000000:  # >1000 万
            score += 10
        elif stock_info['net_buy'] > 0:
            score += 5
        else:
            score -= 10
        
        # 游资卖出减分
        if stock_info['young_capital_sell'] > 20000000:
            score -= 15
        elif stock_info['young_capital_sell'] > 10000000:
            score -= 10
        
        # 换手率适中加分 (5%-15% 为佳)
        if stock_info['turnover_rate'] and pd.notna(stock_info['turnover_rate']):
            turnover = float(stock_info['turnover_rate']) if not isinstance(stock_info['turnover_rate'], str) else 0
            if 5 <= turnover <= 15:
                score += 5
            elif turnover > 20:
                score -= 5
        
        stock_info['score'] = min(100, max(0, score))
        
        # 估算次日溢价
        premium = 0
        if stock_info['score'] >= 80:
            premium = 3.5  # 高评分，预期溢价 3.5%
        elif stock_info['score'] >= 70:
            premium = 2.0
        elif stock_info['score'] >= 60:
            premium = 1.0
        elif stock_info['score'] >= 50:
            premium = 0
        else:
            premium = -2.0
        
        stock_info['next_day_premium_estimate'] = premium
        
        analysis['stocks'].append(stock_info)
        analysis['total_stocks'] += 1
        
        # 记录游资活跃股
        if stock_info['young_capital_buy'] > 5000000:
            analysis['young_capital_activity'].append(stock_info)
        
        # 记录机构活跃股
        if stock_info['institution_buy'] > 10000000:
            analysis['institution_activity'].append(stock_info)
    
    # 按评分排序
    analysis['stocks'].sort(key=lambda x: x['score'], reverse=True)
    analysis['net_buy_top'] = sorted(analysis['stocks'], key=lambda x: x['net_buy'], reverse=True)[:10]
    
    # 生成推荐
    for stock in analysis['stocks'][:5]:
        if stock['score'] >= 75:
            analysis['recommendations'].append({
                'code': stock['code'],
                'name': stock['name'],
                'score': stock['score'],
                'reason': f"评分{stock['score']}分，游资买入{stock['young_capital_buy']/10000:.1f}万，机构买入{stock['institution_buy']/10000:.1f}万，预期次日溢价{stock['next_day_premium_estimate']:.1f}%"
            })
    
    return analysis

def generate_report(analysis, date):
    """生成分析报告"""
    if not analysis:
        return "❌ 无法生成报告：分析数据为空"
    
    report = []
    report.append("=" * 60)
    report.append(f"📊 龙虎榜分析报告 - {date}")
    report.append("=" * 60)
    report.append("")
    
    # 总体概况
    report.append("📈 总体概况")
    report.append("-" * 40)
    report.append(f"上榜股票数量：{analysis['total_stocks']} 只")
    report.append(f"游资活跃股：{len(analysis['young_capital_activity'])} 只")
    report.append(f"机构活跃股：{len(analysis['institution_activity'])} 只")
    report.append("")
    
    # 高分推荐股
    if analysis['recommendations']:
        report.append("🎯 重点关注 (评分≥75)")
        report.append("-" * 40)
        for i, rec in enumerate(analysis['recommendations'], 1):
            report.append(f"{i}. {rec['code']} {rec['name']}")
            report.append(f"   评分：{rec['score']}分")
            report.append(f"   理由：{rec['reason']}")
            report.append("")
    
    # 游资活跃股
    if analysis['young_capital_activity']:
        report.append("🔥 游资活跃股")
        report.append("-" * 40)
        for stock in analysis['young_capital_activity'][:5]:
            report.append(f"{stock['code']} {stock['name']}")
            report.append(f"   游资买入：{stock['young_capital_buy']/10000:.1f}万")
            report.append(f"   游资卖出：{stock['young_capital_sell']/10000:.1f}万")
            report.append(f"   净买入：{stock['net_buy']/10000:.1f}万")
            report.append(f"   评分：{stock['score']}分 | 预期溢价：{stock['next_day_premium_estimate']:.1f}%")
            report.append("")
    
    # 机构活跃股
    if analysis['institution_activity']:
        report.append("🏦 机构活跃股")
        report.append("-" * 40)
        for stock in analysis['institution_activity'][:5]:
            report.append(f"{stock['code']} {stock['name']}")
            report.append(f"   机构买入：{stock['institution_buy']/10000:.1f}万")
            report.append(f"   机构卖出：{stock['institution_sell']/10000:.1f}万")
            report.append(f"   净买入：{stock['net_buy']/10000:.1f}万")
            report.append(f"   评分：{stock['score']}分 | 预期溢价：{stock['next_day_premium_estimate']:.1f}%")
            report.append("")
    
    # 净买入 TOP10
    report.append("💰 净买入 TOP10")
    report.append("-" * 40)
    for i, stock in enumerate(analysis['net_buy_top'], 1):
        report.append(f"{i}. {stock['code']} {stock['name']}: {stock['net_buy']/10000:.1f}万 (评分:{stock['score']})")
    report.append("")
    
    # 操作建议
    report.append("💡 操作建议")
    report.append("-" * 40)
    if analysis['recommendations']:
        report.append("✅ 可关注评分≥75 分的股票，次日溢价概率较高")
        report.append("⚠️ 注意：游资股波动大，建议快进快出")
        report.append("📉 设置止损位：-3% | 止盈位：+5%~8%")
    else:
        report.append("⚠️ 今日无高分推荐股，建议观望")
        report.append("📊 市场情绪可能较弱，等待更好机会")
    
    report.append("")
    report.append("=" * 60)
    report.append("⚠️ 免责声明：数据仅供参考，不构成投资建议")
    report.append("=" * 60)
    
    return "\n".join(report)

def main():
    """主函数"""
    print("🦞 小艺·炒股龙虾 - 龙虎榜分析系统")
    print("=" * 50)
    
    # 1. 获取龙虎榜数据
    df, date = get_today_lhb()
    if df is None:
        print("❌ 无法获取龙虎榜数据，退出")
        return
    
    # 2. 分析龙虎榜
    print("🔍 分析龙虎榜数据...")
    analysis = analyze_lhb(df)
    
    # 3. 生成报告
    print("📝 生成分析报告...")
    report = generate_report(analysis, date)
    
    # 4. 输出报告
    print("\n" + report)
    
    # 5. 保存报告到文件
    report_file = f"/home/admin/openclaw/workspace/temp/longhuban_{date}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✅ 报告已保存至：{report_file}")
    
    # 6. 保存 JSON 数据
    json_file = f"/home/admin/openclaw/workspace/temp/longhuban_{date}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"✅ 数据已保存至：{json_file}")

if __name__ == "__main__":
    main()
