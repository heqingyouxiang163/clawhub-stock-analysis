#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取巨力索具数据"""

import akshare as ak
from datetime import datetime, timedelta

def get_stock_data(symbol):
    """获取股票数据"""
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        # 获取历史行情
        hist_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )
        
        if hist_df.empty:
            return None
        
        latest = hist_df.iloc[-1]
        prev = hist_df.iloc[-2] if len(hist_df) > 1 else latest
        
        return {
            'date': latest.get('日期', 'N/A'),
            'close': float(latest.get('收盘', 0)),
            'open': float(latest.get('开盘', 0)),
            'high': float(latest.get('最高', 0)),
            'low': float(latest.get('最低', 0)),
            'volume': int(latest.get('成交量', 0)),
            'turnover': float(latest.get('成交额', 0)),
            'prev_close': float(prev.get('收盘', latest.get('收盘', 0))),
        }
    except Exception as e:
        return {'error': str(e)}

# 巨力索具
symbol = '002342'
print(f"巨力索具 ({symbol}):")
data = get_stock_data(symbol)
if data and 'error' not in data:
    change = data['close'] - data['prev_close']
    change_pct = (change / data['prev_close'] * 100) if data['prev_close'] > 0 else 0
    sign = '+' if change >= 0 else ''
    print(f"  日期：{data['date']}")
    print(f"  收盘价：¥{data['close']:.2f}")
    print(f"  涨跌幅：{sign}{change_pct:.2f}% ({sign}{change:.2f})")
    print(f"  开盘：¥{data['open']:.2f}")
    print(f"  最高：¥{data['high']:.2f}")
    print(f"  最低：¥{data['low']:.2f}")
    print(f"  成交量：{data['volume']:,.0f} 手")
    print(f"  成交额：{data['turnover']:,.0f} 元")
else:
    print(f"  错误：{data.get('error', '未知')}")
