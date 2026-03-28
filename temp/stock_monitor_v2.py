#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""持仓监控 - 贝肯能源 & 巨力索具 (备选方案)"""

import akshare as ak
from datetime import datetime

def get_stock_realtime(symbol):
    """使用 Sina 接口获取实时行情"""
    try:
        # 使用新浪实时行情接口
        realtime_df = ak.stock_zh_a_spot_em()
        stock = realtime_df[realtime_df['代码'] == symbol]
        
        if stock.empty:
            return None
        
        row = stock.iloc[0]
        return {
            'name': row.get('名称', 'N/A'),
            'price': float(row.get('最新价', 0)),
            'change_pct': float(row.get('涨跌幅', 0)),
            'change': float(row.get('涨跌额', 0)),
            'open': float(row.get('今开', 0)),
            'high': float(row.get('最高', 0)),
            'low': float(row.get('最低', 0)),
            'prev_close': float(row.get('昨收', 0)),
            'volume': int(row.get('成交量', 0)),
            'turnover': float(row.get('成交额', 0)),
            'turnover_rate': float(row.get('换手率', 0)),
            'pe_ratio': row.get('市盈率 - 动态', 'N/A'),
        }
    except Exception as e:
        return {'error': str(e)}

def get_stock_history(symbol, days=5):
    """获取最近 K 线数据"""
    try:
        from datetime import timedelta
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
        
        hist_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )
        
        if hist_df.empty:
            return None
        
        # 获取最新一条数据
        latest = hist_df.iloc[-1]
        prev = hist_df.iloc[-2] if len(hist_df) > 1 else latest
        
        return {
            'date': latest.get('日期', 'N/A'),
            'close': float(latest.get('收盘', 0)),
            'open': float(latest.get('开盘', 0)),
            'high': float(latest.get('最高', 0)),
            'low': float(latest.get('最低', 0)),
            'volume': int(latest.get('成交量', 0)),
            'prev_close': float(prev.get('收盘', latest.get('收盘', 0))),
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    stocks = [
        {'symbol': '002828', 'name': '贝肯能源'},
        {'symbol': '002342', 'name': '巨力索具'},
    ]
    
    print("=" * 60)
    print("📊 持仓监控报告")
    print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Asia/Shanghai)")
    print("=" * 60)
    
    for stock in stocks:
        symbol = stock['symbol']
        name = stock['name']
        
        print(f"\n🔹 {name} ({symbol})")
        print("-" * 40)
        
        # 尝试实时行情
        realtime = get_stock_realtime(symbol)
        if realtime and 'error' not in realtime:
            change_sign = '+' if realtime['change_pct'] >= 0 else ''
            print(f"   最新价：¥{realtime['price']:.2f}")
            print(f"   涨跌幅：{change_sign}{realtime['change_pct']:.2f}% ({change_sign}{realtime['change']:.2f})")
            print(f"   今开：¥{realtime['open']:.2f}  最高：¥{realtime['high']:.2f}  最低：¥{realtime['low']:.2f}")
            print(f"   昨收：¥{realtime['prev_close']:.2f}")
            print(f"   成交量：{realtime['volume']:,.0f} 手")
            print(f"   成交额：{realtime['turnover']:,.0f} 元")
            print(f"   换手率：{realtime['turnover_rate']:.2f}%")
            print(f"   市盈率 (动态): {realtime['pe_ratio']}")
        else:
            # 尝试历史数据
            hist = get_stock_history(symbol)
            if hist and 'error' not in hist:
                change = hist['close'] - hist['prev_close']
                change_pct = (change / hist['prev_close'] * 100) if hist['prev_close'] > 0 else 0
                change_sign = '+' if change >= 0 else ''
                print(f"   最新收盘价 ( {hist['date']} ): ¥{hist['close']:.2f}")
                print(f"   涨跌幅：{change_sign}{change_pct:.2f}% ({change_sign}{change:.2f})")
                print(f"   今开：¥{hist['open']:.2f}  最高：¥{hist['high']:.2f}  最低：¥{hist['low']:.2f}")
                print(f"   成交量：{hist['volume']:,.0f} 手")
            else:
                print(f"   ⚠️ 数据获取失败")
    
    print("\n" + "=" * 60)
    print("⚠️ 数据仅供参考，不构成投资建议")
    print("=" * 60)

if __name__ == "__main__":
    main()
