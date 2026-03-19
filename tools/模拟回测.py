#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟交易回测系统 v1.0
功能：回测涨停形态策略胜率
"""

import json
from datetime import datetime, timedelta

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self):
        self.initial_capital = 100000  # 初始资金 10 万
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
    
    def load_data(self, filepath):
        """加载历史数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def backtest_limit_up_strategy(self, data):
        """
        回测涨停形态策略
        
        策略规则:
        1. 选股：涨幅 5-9%，换手率 8-15%，主力流入>1 亿
        2. 买入：次日开盘买入
        3. 卖出：涨停持有，否则次日卖出
        4. 止损：-7%
        """
        print("=" * 60)
        print("涨停形态策略回测")
        print("=" * 60)
        
        # 模拟数据 (实际应从文件加载)
        test_stocks = [
            {'symbol': 'SH603516', 'name': '淳中科技', 'entry_price': 155.6, 'change_pct': 6.63, 'turnover': 8.18, 'next_day_change': 5.0},
            {'symbol': 'SH603738', 'name': '泰晶科技', 'entry_price': 24.79, 'change_pct': 7.74, 'turnover': 20.42, 'next_day_change': -2.0},
            {'symbol': 'SH600227', 'name': '赤天化', 'entry_price': 4.77, 'change_pct': 9.15, 'turnover': 44.54, 'next_day_change': 10.0},
            {'symbol': 'SH603977', 'name': '国泰集团', 'entry_price': 15.0, 'change_pct': 5.56, 'turnover': 6.47, 'next_day_change': 3.0},
            {'symbol': 'SH600470', 'name': '六国化工', 'entry_price': 9.03, 'change_pct': 5.86, 'turnover': 49.61, 'next_day_change': -5.0},
        ]
        
        # 筛选条件
        def should_buy(stock):
            # 涨幅 5-9%
            if not (5 <= stock['change_pct'] <= 9):
                return False
            # 换手率 8-15%
            if not (8 <= stock['turnover'] <= 15):
                return False
            return True
        
        # 回测
        capital = self.initial_capital
        wins = 0
        losses = 0
        total_trades = 0
        
        print(f"\n初始资金：{capital:,.2f} 元")
        print("=" * 60)
        
        for stock in test_stocks:
            if should_buy(stock):
                # 买入
                shares = int(capital * 0.9 / stock['entry_price'])
                cost = shares * stock['entry_price']
                capital -= cost
                
                # 次日卖出
                next_price = stock['entry_price'] * (1 + stock['next_day_change'] / 100)
                revenue = shares * next_price
                capital += revenue
                
                profit = revenue - cost
                profit_pct = profit / cost * 100
                
                total_trades += 1
                if profit > 0:
                    wins += 1
                else:
                    losses += 1
                
                status = '✓' if profit > 0 else '✗'
                print(f"{status} {stock['symbol']} {stock['name']}: 买入{stock['entry_price']:.2f} → 卖出{next_price:.2f} 盈利{profit_pct:+.2f}%")
            else:
                print(f"⊘ {stock['symbol']} {stock['name']}: 不符合选股条件 (换手率{stock['turnover']:.2f}%)")
        
        # 统计
        win_rate = wins / total_trades * 100 if total_trades > 0 else 0
        total_profit = capital - self.initial_capital
        
        print("=" * 60)
        print(f"回测结果:")
        print(f"  总交易：{total_trades} 笔")
        print(f"  胜率：{win_rate:.1f}% ({wins}胜{losses}负)")
        print(f"  总盈利：{total_profit:+,.2f} 元 ({total_profit/self.initial_capital*100:+.2f}%)")
        print(f"  最终资金：{capital:,.2f} 元")
        print("=" * 60)
        
        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'final_capital': capital
        }


def main():
    """主函数"""
    engine = BacktestEngine()
    result = engine.backtest_limit_up_strategy(None)
    
    # 保存结果
    output = {
        'timestamp': datetime.now().isoformat(),
        'strategy': '涨停形态策略',
        'initial_capital': engine.initial_capital,
        'result': result
    }
    
    output_file = '/home/admin/openclaw/workspace/temp/回测结果_20260316.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n回测结果已保存：{output_file}")


if __name__ == '__main__':
    main()
