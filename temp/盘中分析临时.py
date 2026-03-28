#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import akshare as ak
import time
from datetime import datetime

holdings = [
    {'code': '002828', 'name': '贝肯能源', 'cost': 14.850, 'shares': 500},
    {'code': '002342', 'name': '巨力索具', 'cost': 14.253, 'shares': 900},
]

print('='*70)
print('🔍 盘中实时监控系统')
print('监控时间：' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print('='*70)

# 尝试获取全市场数据
print('\n📊 获取市场数据...')
try:
    df = ak.stock_zh_a_spot_em()
    print(f'  成功获取 {len(df)} 只股票数据')
except Exception as e:
    print(f'  获取失败：{e}')
    df = None

if df is not None:
    for stock in holdings:
        code = stock['code']
        name = stock['name']
        cost = stock['cost']
        shares = stock['shares']
        
        print('\n' + '='*70)
        print(f'📈 {name} ({code})')
        print('='*70)
        
        try:
            stock_data = df[df['代码'] == code]
            if not stock_data.empty:
                row = stock_data.iloc[0]
                price = float(row.get('最新价', 0))
                change = float(row.get('涨跌幅', 0))
                open_p = float(row.get('今开', 0))
                high = float(row.get('最高', 0))
                low = float(row.get('最低', 0))
                volume = float(row.get('成交量', 0))
                amount = float(row.get('成交额', 0))
                
                profit = (price - cost) * shares
                profit_pct = ((price - cost) / cost) * 100
                
                print('\n【实时数据】')
                print(f'  现价：{price} 元 ({change}%)')
                print(f'  开盘：{open_p} 元 | 最高：{high} 元 | 最低：{low} 元')
                print(f'  成交量：{volume/100:.0f}手 | 成交额：{amount/10000:.1f}万')
                print(f'  持仓盈亏：{profit:+.2f} 元 ({profit_pct:+.2f}%)')
                
                # 分时图战法评分
                vwap = (open_p + high + low + price) / 4
                score = 0
                if price > vwap * 1.01: score += 30
                elif price > vwap: score += 20
                
                if change > 7: score += 25
                elif change > 5: score += 20
                elif change > 3: score += 15
                elif change > 0: score += 10
                
                if volume > 0: score += 15
                
                rating = '🟢🟢🟢 极强' if score >= 85 else '🟢🟢 强势' if score >= 70 else '🟡 中性' if score >= 55 else '🔴 弱势'
                
                print('\n【分时图战法】')
                print(f'  评分：{score}/100')
                print(f'  评级：{rating}')
                
                # 涨停潜力
                limit_up_prob = '高' if score >= 80 else '中' if score >= 60 else '低'
                print('\n【涨停潜力】')
                print(f'  潜力判断：{limit_up_prob}')
                
                # 尾盘操作建议
                print('\n【尾盘操作建议】')
                if score >= 80:
                    print('  建议：积极持有，可适度加仓')
                    print('  理由：分时强势，涨停概率高')
                elif score >= 60:
                    print('  建议：持有观望')
                    print('  理由：走势中性，等待方向明确')
                else:
                    print('  建议：逢高减仓或止损')
                    print('  理由：走势弱势，注意风险')
            else:
                print('  未找到实时数据')
        except Exception as e:
            print(f'  分析失败：{e}')

print('\n' + '='*70)
print('分析完成')
print('='*70)
