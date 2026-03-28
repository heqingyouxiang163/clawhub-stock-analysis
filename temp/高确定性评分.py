#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高确定性涨停股评分脚本
从涨幅 5%-7% 股票中筛选≥75 分的股票
"""

import requests
import time
from datetime import datetime

# 涨幅 5%-7% 股票列表 (从缓存获取)
TARGET_STOCKS = [
    {'code': '688766', 'name': '普冉股份', 'change_pct': 6.9, 'current': 297.28},
    {'code': '603803', 'name': '瑞斯康达', 'change_pct': 6.8, 'current': 14.03},
    {'code': '688032', 'name': '禾迈股份', 'change_pct': 6.7, 'current': 122.78},
    {'code': '688348', 'name': '昱能科技', 'change_pct': 6.6, 'current': 60.24},
    {'code': '600032', 'name': '浙江新能', 'change_pct': 6.2, 'current': 9.58},
    {'code': '688519', 'name': '南亚新材', 'change_pct': 6.1, 'current': 139.50},
    {'code': '688619', 'name': '罗普特', 'change_pct': 6.0, 'current': 15.95},
    {'code': '603189', 'name': '网达软件', 'change_pct': 5.8, 'current': 21.25},
    {'code': '603660', 'name': '苏州科达', 'change_pct': 5.8, 'current': 10.27},
    {'code': '603393', 'name': '新天然气', 'change_pct': 5.7, 'current': 41.76},
    {'code': '601139', 'name': '深圳燃气', 'change_pct': 5.4, 'current': 7.60},
    {'code': '601330', 'name': '绿色动力', 'change_pct': 5.1, 'current': 9.86},
    {'code': '603016', 'name': '新宏泰', 'change_pct': 5.1, 'current': 36.40},
    {'code': '688063', 'name': '派能科技', 'change_pct': 5.1, 'current': 77.36},
    {'code': '688313', 'name': '仕佳光子', 'change_pct': 5.1, 'current': 81.80},
    {'code': '603843', 'name': '*ST 正平', 'change_pct': 5.0, 'current': 7.72},
    {'code': '603813', 'name': '*ST 原尚', 'change_pct': 5.0, 'current': 30.63},
]


def fetch_tencent_detail(code):
    """腾讯财经获取详细数据"""
    try:
        market = 'sh' if code.startswith('6') else 'sz'
        url = f"http://qt.gtimg.cn/q={market}{code}"
        headers = {'Referer': 'https://stockapp.finance.qq.com/'}
        
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            text = resp.content.decode('gbk')
            if '=' in text:
                data = text.split('=')[1].strip('"').split('~')
                if len(data) >= 40:
                    return {
                        'code': code,
                        'name': data[1],
                        'current': float(data[3]) if data[3] else 0,
                        'pre_close': float(data[4]) if data[4] else 0,
                        'open': float(data[5]) if data[5] else 0,
                        'high': float(data[6]) if data[6] else 0,
                        'low': float(data[7]) if data[7] else 0,
                        'volume': float(data[8]) if data[8] else 0,  # 手
                        'amount': float(data[37]) if len(data) > 37 else 0,  # 成交额 (元)
                        'turnover': float(data[39]) if len(data) > 39 else 0,  # 换手率 (%)
                        'change_pct': float(data[32]) if len(data) > 32 else 0,
                        'volume_ratio': float(data[40]) if len(data) > 40 else 0,  # 量比
                    }
    except Exception as e:
        print(f"⚠️ 获取{code}失败：{str(e)[:30]}")
    
    return None


def calculate_score(stock):
    """
    计算股票得分 (满分 100)
    
    评分标准:
    - 基础分：50 + 涨幅 * 5 (涨幅 5-7% 得 75-85 分)
    - 量比>2: +10
    - 量比>3: +15 (额外)
    - 成交额>5 亿：+10
    - 成交额>10 亿：+15 (额外)
    - 换手率 5-15%: +10 (健康换手)
    - 涨幅 6-7%: +5 (加速段)
    - 非 ST: +5
    """
    score = 50  # 基础分
    
    # 涨幅分 (5-7% 范围)
    change_pct = stock.get('change_pct', 0)
    score += change_pct * 5  # 5%→25 分，7%→35 分
    
    # 量比分
    volume_ratio = stock.get('volume_ratio', 0)
    if volume_ratio > 2:
        score += 10
    if volume_ratio > 3:
        score += 15  # 额外
    
    # 成交额分
    amount = stock.get('amount', 0)  # 元
    amount_亿 = amount / 100000000
    if amount_亿 > 5:
        score += 10
    if amount_亿 > 10:
        score += 15  # 额外
    
    # 换手率分 (健康换手 5-15%)
    turnover = stock.get('turnover', 0)
    if 5 <= turnover <= 15:
        score += 10
    elif 3 <= turnover < 5:
        score += 5
    elif turnover > 15:
        score -= 5  # 过高换手
    
    # 加速段加分
    if 6 <= change_pct <= 7:
        score += 5
    
    # 非 ST 加分
    if '*ST' not in stock.get('name', '') and 'ST' not in stock.get('name', ''):
        score += 5
    
    return min(score, 100)


def main():
    print("=" * 80)
    print("🦞 高确定性涨停股评分筛选")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    print("📊 涨幅 5%-7% 股票列表 (主升浪):")
    print("-" * 80)
    print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>7} {'现价':>10}")
    print("-" * 80)
    
    for i, s in enumerate(TARGET_STOCKS, 1):
        print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+6.1f}% ¥{s['current']:>8.2f}")
    
    print("-" * 80)
    print(f"✅ 总计：{len(TARGET_STOCKS)}只")
    print()
    
    # 获取详细数据并评分
    print("📈 获取详细数据并评分...")
    print()
    
    scored_stocks = []
    
    for s in TARGET_STOCKS:
        detail = fetch_tencent_detail(s['code'])
        
        if detail:
            # 合并数据
            stock_data = {**s, **detail}
            score = calculate_score(stock_data)
            stock_data['score'] = score
            scored_stocks.append(stock_data)
            
            print(f"  {s['code']} {s['name']}: 涨幅{detail['change_pct']:.1f}%, "
                  f"量比{detail.get('volume_ratio', 0):.2f}, "
                  f"成交{detail.get('amount', 0)/100000000:.2f}亿，"
                  f"换手{detail.get('turnover', 0):.1f}%, "
                  f"得分：{score:.0f}")
        else:
            # 使用基础数据评分
            score = calculate_score(s)
            s['score'] = score
            scored_stocks.append(s)
            print(f"  {s['code']} {s['name']}: 涨幅{s['change_pct']:.1f}%, 得分：{score:.0f} (无详细数据)")
        
        time.sleep(0.1)
    
    print()
    
    # 筛选≥75 分的股票
    high_confidence = [s for s in scored_stocks if s['score'] >= 75]
    high_confidence.sort(key=lambda x: x['score'], reverse=True)
    
    print("=" * 80)
    print(f"🎯 高确定性推荐 (≥75 分)：{len(high_confidence)}只")
    print("=" * 80)
    print()
    
    if high_confidence:
        for i, stock in enumerate(high_confidence, 1):
            change_pct = stock.get('change_pct', 0)
            amount = stock.get('amount', 0)
            volume_ratio = stock.get('volume_ratio', 0)
            turnover = stock.get('turnover', 0)
            
            print(f"{i}. {stock['code']} {stock['name']}")
            print(f"   🎯 得分：{stock['score']:.0f}/100")
            print(f"   💰 现价：¥{stock['current']} ({change_pct:+.1f}%)")
            
            if amount > 0:
                print(f"   💵 成交额：{amount/100000000:.2f}亿元")
            if volume_ratio > 0:
                print(f"   📈 量比：{volume_ratio:.2f}")
            if turnover > 0:
                print(f"   🔄 换手率：{turnover:.2f}%")
            
            # 操作建议
            if stock['score'] >= 85:
                print(f"   👉 操作：🔥 高确定性，可积极介入")
            elif stock['score'] >= 80:
                print(f"   👉 操作：🟢 确定性较高，可建仓")
            else:
                print(f"   👉 操作：🟡 符合条件，可轻仓试错")
            
            print(f"   🛑 止损：-5% | 🎯 止盈：+10%")
            print()
    else:
        print("⚠️ 无≥75 分的高确定性股票")
        print("   标准：≥75 分才推荐，宁可空仓不做弱势！")
        print()
    
    # 市场统计
    print("=" * 80)
    print("📊 市场涨幅分布统计:")
    print("=" * 80)
    print("  涨停 (≥9.5%)：  19 只")
    print("  8-9.5%:         4 只")
    print("  7-8%:           3 只")
    print("  5-7%:          17 只  ← 主升浪观察池")
    print("  3-5%:          38 只")
    print("  0-3%:          13 只")
    print("  下跌：          0 只")
    print()
    
    # 风险提示
    print("=" * 80)
    print("⚠️ 风险提示:")
    print("=" * 80)
    print("  • 仓位控制：单只≤20% | 总仓≤60%")
    print("  • 止损纪律：-5% 坚决止损")
    print("  • 标准：≥75 分才推荐，宁可空仓不做弱势！")
    print("  • 仅供参考，不构成投资建议")
    print("=" * 80)
    
    return high_confidence


if __name__ == "__main__":
    main()
