#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""持仓监控 - 贝肯能源 & 巨力索具"""

import akshare as ak
import pandas as pd
from datetime import datetime

def get_stock_info(symbol):
    """获取个股实时行情"""
    try:
        # 获取实时行情
        spot_df = ak.stock_zh_a_spot_em()
        stock_data = spot_df[spot_df['代码'] == symbol]
        
        if stock_data.empty:
            return None
        
        stock = stock_data.iloc[0]
        return {
            '代码': symbol,
            '名称': stock.get('名称', 'N/A'),
            '最新价': stock.get('最新价', 0),
            '涨跌幅': stock.get('涨跌幅', 0),
            '涨跌额': stock.get('涨跌额', 0),
            '成交量': stock.get('成交量', 0),
            '成交额': stock.get('成交额', 0),
            '最高': stock.get('最高', 0),
            '最低': stock.get('最低', 0),
            '今开': stock.get('今开', 0),
            '昨收': stock.get('昨收', 0),
            '换手率': stock.get('换手率', 0),
            '市盈率-动态': stock.get('市盈率-动态', 0),
            '市净率': stock.get('市净率', 0),
        }
    except Exception as e:
        return {'error': str(e)}

def get_stock_flow(symbol):
    """获取资金流向"""
    try:
        # 确定市场
        market = "sz" if symbol.startswith(('0', '3')) else "sh"
        flow_df = ak.stock_individual_fund_flow(stock=symbol, market=market)
        
        if flow_df.empty:
            return None
        
        # 获取最新一期数据
        latest = flow_df.iloc[0] if len(flow_df) > 0 else None
        if latest is None:
            return None
            
        return {
            '日期': latest.get('日期', 'N/A'),
            '主力净流入': latest.get('主力净流入-净额', 0),
            '大单净流入': latest.get('大单净流入-净额', 0),
            '中单净流入': latest.get('中单净流入-净额', 0),
            '小单净流入': latest.get('小单净流入-净额', 0),
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
        
        # 获取实时行情
        info = get_stock_info(symbol)
        if info and 'error' not in info:
            print(f"   最新价：¥{info['最新价']}")
            print(f"   涨跌幅：{info['涨跌幅']:+.2f}% ({info['涨跌额']:+.2f})")
            print(f"   今开：¥{info['今开']}  最高：¥{info['最高']}  最低：¥{info['最低']}")
            print(f"   昨收：¥{info['昨收']}")
            print(f"   成交量：{info['成交量']:,.0f} 手")
            print(f"   成交额：{info['成交额']:,.0f} 元")
            print(f"   换手率：{info['换手率']:.2f}%")
            print(f"   市盈率 (动态): {info['市盈率 - 动态']}")
            print(f"   市净率：{info['市净率']}")
        else:
            error_msg = info.get('error', '未知错误') if info else '无数据'
            print(f"   ⚠️ 行情数据获取失败：{error_msg}")
        
        # 获取资金流向
        flow = get_stock_flow(symbol)
        if flow and 'error' not in flow:
            print(f"\n   💰 资金流向 ({flow['日期']}):")
            print(f"      主力净流入：{flow['主力净流入']:,.0f} 元")
            print(f"      大单净流入：{flow['大单净流入']:,.0f} 元")
            print(f"      中单净流入：{flow['中单净流入']:,.0f} 元")
            print(f"      小单净流入：{flow['小单净流入']:,.0f} 元")
        else:
            error_msg = flow.get('error', '未知错误') if flow else '无数据'
            print(f"\n   ⚠️ 资金流向数据获取失败：{error_msg}")
    
    print("\n" + "=" * 60)
    print("⚠️ 数据仅供参考，不构成投资建议")
    print("=" * 60)

if __name__ == "__main__":
    main()
