#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涨幅 5%-7% 股票评分 - 高确定性推荐
基于缓存数据，对涨幅 5%-7% 的股票进行评分
"""

import json
import requests
from datetime import datetime

CACHE_FILE = "/home/admin/openclaw/workspace/temp/全市场涨幅榜缓存.json"

def load_stocks_in_range(min_pct, max_pct):
    """从缓存加载指定涨幅范围的股票"""
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    result = [s for s in stocks if min_pct <= s['change_pct'] <= max_pct and s['current'] > 0]
    result.sort(key=lambda x: x['change_pct'], reverse=True)
    return result


def fetch_tencent_detail(code):
    """腾讯财经获取详细数据（量比、换手等）"""
    prefix = "sh" if code.startswith('6') else "sz"
    url = f"http://qt.gtimg.cn/q={prefix}{code}"
    
    try:
        resp = requests.get(url, timeout=5, headers={'Referer': 'https://stockapp.finance.qq.com/'})
        if resp.status_code == 200:
            text = resp.content.decode('gbk')
            if '=' in text:
                data = text.split('=')[1].strip('"').split('~')
                if len(data) >= 45:
                    return {
                        'volume_ratio': float(data[45]) if data[45] else 0,  # 量比
                        'turnover': float(data[39]) if data[39] else 0,  # 换手率
                        'amount': float(data[37]) if data[37] else 0,  # 成交额
                        'pe': float(data[40]) if data[40] else 0,  # 市盈率
                    }
    except:
        pass
    
    return None


def calculate_score(stock):
    """计算股票评分 (100 分制)"""
    code = stock['code']
    name = stock['name']
    change_pct = stock['change_pct']
    current = stock['current']
    amount = stock.get('amount', 0)
    turnover = stock.get('turnover', 0)
    open_pct = ((stock.get('open', 0) or 0) - (stock.get('prev_close', 1) or 1)) / (stock.get('prev_close', 1) or 1) * 100
    
    # 获取腾讯详细数据
    detail = fetch_tencent_detail(code)
    if detail:
        volume_ratio = detail.get('volume_ratio', 0)
        turnover = detail.get('turnover', turnover)
        amount = detail.get('amount', amount)
    else:
        volume_ratio = 0
    
    score = 0
    details = {}
    
    # 1. 涨幅得分 (15 分) - 5.5%-7% 最佳
    if 6 <= change_pct <= 7:
        score += 15
        details['change'] = '15/15 (最佳区间)'
    elif 5.5 <= change_pct < 6:
        score += 13
        details['change'] = '13/15 (强势)'
    elif 5 <= change_pct < 5.5:
        score += 11
        details['change'] = '11/15 (合格)'
    else:
        score += 8
        details['change'] = '8/15 (偏弱)'
    
    # 2. 量比得分 (25 分) - >2 最佳
    if volume_ratio > 3:
        score += 25
        details['volume_ratio'] = '25/25 (极强)'
    elif volume_ratio > 2:
        score += 20
        details['volume_ratio'] = '20/25 (强势)'
    elif volume_ratio > 1.5:
        score += 15
        details['volume_ratio'] = '15/25 (温和)'
    elif volume_ratio > 1:
        score += 10
        details['volume_ratio'] = '10/25 (偏弱)'
    else:
        # 无量比数据，用成交额估算
        if amount > 500000000:
            score += 18
            details['volume_ratio'] = '18/25 (大成交)'
        elif amount > 200000000:
            score += 15
            details['volume_ratio'] = '15/25 (中成交)'
        elif amount > 100000000:
            score += 12
            details['volume_ratio'] = '12/25 (小成交)'
        else:
            score += 8
            details['volume_ratio'] = '8/25 (无量)'
    
    # 3. 成交得分 (20 分) - >3 亿最佳
    if amount > 500000000:
        score += 20
        details['amount'] = '20/20 (超活跃)'
    elif amount > 300000000:
        score += 18
        details['amount'] = '18/20 (很活跃)'
    elif amount > 150000000:
        score += 15
        details['amount'] = '15/20 (活跃)'
    elif amount > 100000000:
        score += 12
        details['amount'] = '12/20 (尚可)'
    elif amount > 50000000:
        score += 10
        details['amount'] = '10/20 (偏小)'
    else:
        score += 6
        details['amount'] = '6/20 (太小)'
    
    # 4. 换手得分 (15 分) - 3-15% 最佳
    if turnover and 3 <= turnover <= 15:
        score += 15
        details['turnover'] = '15/15 (健康)'
    elif turnover and 2 <= turnover <= 20:
        score += 12
        details['turnover'] = '12/15 (可接受)'
    elif turnover and turnover > 20:
        score += 8
        details['turnover'] = '8/15 (过高)'
    elif turnover and 0 < turnover < 2:
        score += 10
        details['turnover'] = '10/15 (偏低)'
    else:
        score += 5
        details['turnover'] = '5/15 (无数据)'
    
    # 5. 开盘得分 (15 分) - 高开 1-4% 最佳
    if 1 <= open_pct <= 4:
        score += 15
        details['open'] = '15/15 (完美高开)'
    elif 4 < open_pct <= 6:
        score += 12
        details['open'] = '12/15 (高开较多)'
    elif 0 <= open_pct < 1:
        score += 10
        details['open'] = '10/15 (平开)'
    elif -2 <= open_pct < 0:
        score += 7
        details['open'] = '7/15 (小幅低开)'
    else:
        score += 4
        details['open'] = '4/15 (大幅低开)'
    
    # 6. 股价合理性 (10 分) - 排除*ST 和异常高价
    if '*ST' in name or 'ST' in name:
        score += 0
        details['risk'] = '0/10 (*ST 风险股)'
    elif current > 500:
        score += 5
        details['risk'] = '5/10 (股价过高)'
    elif 10 <= current <= 200:
        score += 10
        details['risk'] = '10/10 (合理区间)'
    elif current < 5:
        score += 6
        details['risk'] = '6/10 (低价股)'
    else:
        score += 8
        details['risk'] = '8/10 (可接受)'
    
    return min(score, 100), details, volume_ratio, turnover, amount, open_pct


def main():
    print("=" * 80)
    print("🦞 涨幅 5%-7% 股票评分 - 高确定性推荐")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("标准：≥75 分才推荐，宁可空仓不做弱势！")
    print("=" * 80)
    print()
    
    # 获取涨幅 5%-7% 的股票
    stocks = load_stocks_in_range(5, 7)
    print(f"📊 涨幅 5%-7% 股票：{len(stocks)}只")
    print()
    
    # 评分
    results = []
    for i, stock in enumerate(stocks, 1):
        score, details, volume_ratio, turnover, amount, open_pct = calculate_score(stock)
        results.append({
            **stock,
            'score': score,
            'details': details,
            'volume_ratio': volume_ratio,
            'turnover': turnover,
            'amount': amount,
            'open_pct': open_pct
        })
        print(f"{i:2}. {stock['code']} {stock['name']:<10} 涨幅:{stock['change_pct']:>+5.1f}% 评分:{score:3}/100")
    
    print()
    
    # 排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 筛选≥75 分的
    recommended = [r for r in results if r['score'] >= 75]
    
    print("=" * 80)
    print("🎯 高确定性推荐 (≥75 分)")
    print("=" * 80)
    print()
    
    if recommended:
        for i, r in enumerate(recommended, 1):
            # 评级
            if r['score'] >= 85:
                rating = "🟢🟢🟢 极强"
                action = "积极建仓"
            elif r['score'] >= 80:
                rating = "🟢🟢 强势"
                action = "可建仓"
            else:
                rating = "🟢 较强"
                action = "轻仓试错"
            
            print(f"{i}. {r['code']} {r['name']}")
            print(f"   评分：{r['score']}/100 [{rating}]")
            print(f"   现价：¥{r['current']:.2f} ({r['change_pct']:+.1f}%)")
            print(f"   成交：{r['amount']/100000000:.2f}亿  量比:{r['volume_ratio']:.2f}  换手:{r['turnover']:.1f}%")
            print(f"   开盘：{r['open_pct']:+.1f}%")
            print(f"   👉 操作：{action}")
            print()
    else:
        print("⚠️ 无≥75 分的股票，今日市场偏弱，建议观望！")
        print()
    
    # 70-74 分观察区
    watch = [r for r in results if 70 <= r['score'] < 75]
    if watch:
        print("=" * 80)
        print("👀 观察区 (70-74 分)")
        print("=" * 80)
        print()
        for r in watch:
            print(f"   {r['code']} {r['name']}  {r['score']}分  涨幅:{r['change_pct']:+.1f}%  成交:{r['amount']/100000000:.2f}亿")
        print()
    
    # 风险提示
    print("=" * 80)
    print("⚠️ 风险提示")
    print("=" * 80)
    print("""
  • 仓位控制：≤20%/只，总仓≤60%
  • 止损位：-5% 坚决止损
  • 止盈位：+10% 分批止盈
  • 不追高：涨幅>8% 不追
  • 不抄底：下跌趋势不接飞刀
  
  标准：≥75 分才推荐，宁可空仓不做弱势！
""")
    print("=" * 80)
    
    return recommended


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    main()
