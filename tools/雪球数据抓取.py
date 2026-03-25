#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雪球数据抓取脚本 v1.0
功能：从雪球获取 A 股实时数据
"""

import requests
import json
import time
from datetime import datetime

class XueqiuFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://stock.xueqiu.com"
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://xueqiu.com/',
        }
        
        # 初始化 session
        self._init_session()
    
    def _init_session(self):
        """初始化 session，获取 cookie"""
        try:
            # 访问首页获取 cookie
            self.session.get('https://xueqiu.com/', headers=self.headers, timeout=10)
            print("✓ Session 初始化成功")
        except Exception as e:
            print(f"✗ Session 初始化失败：{e}")
    
    def get_stock_data(self, symbol):
        """
        获取单只股票实时数据
        
        Args:
            symbol: 股票代码 (如 SH603516 或 SZ002828)
        
        Returns:
            dict: 股票数据
        """
        url = f"{self.base_url}/v5/stock/quote.json"
        params = {
            'symbol': symbol,
            'extend': 'detail'
        }
        
        try:
            response = self.session.get(url, params=params, headers=self.headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error_code') == 0:
                quote = data['data']['quote']
                return self._parse_quote(quote, symbol)
            else:
                print(f"✗ {symbol} 数据获取失败：{data.get('error_description', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"✗ {symbol} 请求异常：{e}")
            return None
    
    def _parse_quote(self, quote, symbol):
        """解析雪球数据"""
        try:
            return {
                'symbol': symbol,
                'name': quote.get('name', ''),
                'current': quote.get('current', 0),  # 现价
                'percent': quote.get('percent', 0),  # 涨跌幅%
                'change': quote.get('change', 0),  # 涨跌额
                'open': quote.get('open', 0),  # 开盘价
                'high': quote.get('high', 0),  # 最高价
                'low': quote.get('low', 0),  # 最低价
                'last_close': quote.get('last_close', 0),  # 昨收
                'volume': quote.get('volume', 0),  # 成交量 (股)
                'amount': quote.get('amount', 0),  # 成交额 (元)
                'turnover_rate': quote.get('turnover_rate', 0),  # 换手率%
                'market_capital': quote.get('market_capital', 0),  # 总市值 (元)
                'pe_ttm': quote.get('pe_ttm', 0),  # 市盈率 TTM
                'pb': quote.get('pb', 0),  # 市净率
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"✗ {symbol} 数据解析失败：{e}")
            return None
    
    def batch_fetch(self, symbols, delay=0.2):
        """
        批量抓取股票数据
        
        Args:
            symbols: 股票代码列表
            delay: 请求间隔 (秒)
        
        Returns:
            dict: 股票数据字典
        """
        results = {}
        success = 0
        failed = 0
        
        print(f"\n开始抓取 {len(symbols)} 只股票数据...")
        print("=" * 60)
        
        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] 抓取 {symbol}...", end=" ")
            
            data = self.get_stock_data(symbol)
            if data:
                results[symbol] = data
                success += 1
                print(f"✓ 成功 (现价:{data['current']} 涨跌:{data['percent']:.2f}%)")
            else:
                failed += 1
                print("✗ 失败")
            
            # 避免频率限制
            if i < len(symbols):
                time.sleep(delay)
        
        print("=" * 60)
        print(f"抓取完成：成功 {success} 只，失败 {failed} 只，成功率 {success/len(symbols)*100:.1f}%")
        
        return results
    
    def validate_data(self, data):
        """
        数据校验
        
        Args:
            data: 股票数据
        
        Returns:
            bool: 是否通过校验
        """
        if not data:
            return False
        
        # 涨跌幅校验 (A 股±10%)
        if data['percent'] > 10 or data['percent'] < -10:
            print(f"  ⚠ 涨跌幅异常：{data['percent']:.2f}%")
            return False
        
        # 换手率校验 (0-50%)
        if data['turnover_rate'] > 50 or data['turnover_rate'] < 0:
            print(f"  ⚠ 换手率异常：{data['turnover_rate']:.2f}%")
            return False
        
        # 价格校验
        if data['high'] < data['current']:
            print(f"  ⚠ 最高价异常：{data['high']} < {data['current']}")
            return False
        if data['low'] > data['current']:
            print(f"  ⚠ 最低价异常：{data['low']} > {data['current']}")
            return False
        
        # 成交量校验
        if data['volume'] <= 0:
            print(f"  ⚠ 成交量异常：{data['volume']}")
            return False
        
        return True


def main():
    """主函数"""
    print("=" * 60)
    print("雪球数据抓取脚本 v1.0")
    print("测试时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    # 测试股票池 (10 只)
    test_symbols = [
        'SZ002828',  # 贝肯能源 (持仓)
        'SZ002342',  # 巨力索具 (持仓)
        'SH603516',  # 淳中科技
        'SH603738',  # 泰晶科技
        'SH600227',  # 赤天化 (2 连板)
        'SH603977',  # 国泰集团
        'SZ000533',  # 顺钠股份
        'SZ002426',  # 胜利精密
        'SH603005',  # 三房巷 (3 连板)
        'SZ000795',   (3 连板)
    ]
    
    # 创建抓取器
    fetcher = XueqiuFetcher()
    
    # 批量抓取
    results = fetcher.batch_fetch(test_symbols, delay=0.2)
    
    # 数据校验
    print("\n数据校验:")
    print("=" * 60)
    valid_count = 0
    for symbol, data in results.items():
        is_valid = fetcher.validate_data(data)
        if is_valid:
            valid_count += 1
            print(f"✓ {symbol} {data['name']}: 校验通过")
        else:
            print(f"✗ {symbol} {data['name']}: 校验失败")
    
    print("=" * 60)
    print(f"校验结果：通过 {valid_count}/{len(results)} 只，通过率 {valid_count/len(results)*100:.1f}%")
    
    # 保存结果
    output_file = '/home/admin/openclaw/workspace/temp/雪球数据测试_20260316.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(results),
            'valid': valid_count,
            'data': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到：{output_file}")
    
    # 输出摘要
    print("\n数据摘要:")
    print("=" * 60)
    print(f"{'代码':<10} {'名称':<10} {'现价':>8} {'涨跌%':>8} {'换手%':>8} {'成交额 (亿)':>10}")
    print("-" * 60)
    
    for symbol, data in results.items():
        name = data['name'][:10]
        current = data['current']
        percent = data['percent']
        turnover = data['turnover_rate']
        amount = data['amount'] / 100000000  # 转换为亿
        
        print(f"{symbol:<10} {name:<10} {current:>8.2f} {percent:>8.2f} {turnover:>8.2f} {amount:>10.2f}")
    
    print("=" * 60)


if __name__ == '__main__':
    main()
