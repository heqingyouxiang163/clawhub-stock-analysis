#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 小龙虾·主板打板进化版

权限：仅沪深主板 | 模式：超短打板 | 能力：自我学习 + 迭代 + 升级
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import json


class XiaoLongXia:
    def __init__(self):
        self.allow_prefix = ('600', '601', '603', '605', '000', '001', '002', '003')
        self.blacklist = []
        self.best_params = {
            '封单亿': 3,
            '流通最小亿': 20,
            '时间窗': '09:30-10:00',
            '换手率最小': 5,
            '换手率最大': 20,
            '连板最小': 2
        }
        self.history_file = Path('memory/小龙虾学习记录.json')
        self.load_history()
    
    def load_history(self):
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = data.get('history', [])
                self.best_params = data.get('best_params', self.best_params)
        else:
            self.history = []
    
    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump({
                'history': self.history,
                'best_params': self.best_params,
                'last_update': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def check_main_board(self, code):
        return code[:3] in self.allow_prefix and 'ST' not in code
    
    def can_buy(self, row):
        if not self.check_main_board(row.get('代码', '')):
            return False
        if row.get('封单额亿', 0) < self.best_params['封单亿']:
            return False
        if row.get('流通市值亿', 0) < self.best_params['流通最小亿']:
            return False
        
        上板时间 = row.get('上板时间', '')
        if not 上板时间:
            return False
        
        try:
            time_str = 上板时间.replace(':', '')[:4]
            if not ('0930' <= time_str <= '1000'):
                return False
        except:
            return False
        
        if row.get('代码', '') in self.blacklist:
            return False
        
        换手率 = row.get('换手率', 0)
        if not (self.best_params['换手率最小'] <= 换手率 <= self.best_params['换手率最大']):
            return False
        
        连板数 = row.get('连板数', 1)
        if 连板数 < self.best_params['连板最小']:
            return False
        
        return True
    
    def should_sell(self, row):
        return row.get('炸板', False) or row.get('回撤', 0) <= -0.04
    
    def learn(self, history):
        if not history:
            return 0.0
        
        df = pd.DataFrame(history)
        df['盈利'] = df['盈亏'] > 0
        win_rate = df['盈利'].mean()
        total_return = df['盈亏'].sum()
        
        print(f"🦞 小龙虾学习完成 -> 胜率：{win_rate:.1%}，总收益：{total_return:.2%}")
        
        self.history.extend(history)
        self.save_history()
        
        return win_rate
    
    def evolve(self, history_data):
        if len(history_data) < 10:
            print("⚠️ 数据量太少，无法进化 (至少需要 10 条)")
            return
        
        best_win = 0
        best_p = self.best_params.copy()
        
        print("\n🔬 小龙虾开始进化...")
        
        for 封单 in [2, 3, 4, 5]:
            for 流通最小 in [15, 20, 25, 30]:
                for 换手最小 in [3, 5, 8]:
                    for 换手最大 in [15, 20, 25]:
                        self.best_params['封单亿'] = 封单
                        self.best_params['流通最小亿'] = 流通最小
                        self.best_params['换手率最小'] = 换手最小
                        self.best_params['换手率最大'] = 换手最大
                        
                        win_rate = self.backtest(history_data)
                        
                        if win_rate > best_win:
                            best_win = win_rate
                            best_p = self.best_params.copy()
                            print(f"  新记录！胜率：{win_rate:.1%}")
        
        self.best_params = best_p
        self.save_history()
        
        print(f"\n✅ 小龙虾升级完成！最新最优参数：")
        print(f"  封单额：≥{self.best_params['封单亿']}亿")
        print(f"  流通市值：≥{self.best_params['流通最小亿']}亿")
        print(f"  换手率：{self.best_params['换手率最小']}-{self.best_params['换手率最大']}%")
    
    def backtest(self, history_data):
        if not history_data:
            return 0.0
        
        wins = 0
        total = 0
        
        for record in history_data:
            if self.can_buy(record):
                total += 1
                if record.get('盈亏', 0) > 0:
                    wins += 1
        
        return wins / total if total > 0 else 0.0
    
    def scan(self, market_data):
        targets = []
        
        for row in market_data:
            if self.can_buy(row):
                targets.append({
                    '代码': row.get('代码', ''),
                    '名称': row.get('名称', ''),
                    '涨幅': row.get('涨幅', 0),
                    '封单额': row.get('封单额亿', 0),
                    '流通市值': row.get('流通市值亿', 0),
                    '换手率': row.get('换手率', 0),
                    '连板数': row.get('连板数', 1),
                    '上板时间': row.get('上板时间', ''),
                    '评分': self.calc_score(row)
                })
        
        targets.sort(key=lambda x: x['评分'], reverse=True)
        return targets[:3]
    
    def calc_score(self, row):
        score = 50
        
        封单 = row.get('封单额亿', 0)
        if 封单 >= 5:
            score += 20
        elif 封单 >= 3:
            score += 15
        elif 封单 >= 2:
            score += 10
        
        流通 = row.get('流通市值亿', 0)
        if 流通 >= 50:
            score += 15
        elif 流通 >= 30:
            score += 10
        elif 流通 >= 20:
            score += 5
        
        换手 = row.get('换手率', 0)
        if 5 <= 换手 <= 15:
            score += 15
        elif 3 <= 换手 <= 20:
            score += 10
        
        连板 = row.get('连板数', 1)
        if 连板 >= 4:
            score += 15
        elif 连板 >= 3:
            score += 10
        elif 连板 >= 2:
            score += 5
        
        时间 = row.get('上板时间', '')
        if 时间:
            try:
                time_str = 时间.replace(':', '')[:4]
                if '0930' <= time_str <= '0935':
                    score += 15
                elif '0935' < time_str <= '0945':
                    score += 10
                elif '0945' < time_str <= '1000':
                    score += 5
            except:
                pass
        
        return min(100, score)


小龙虾 = XiaoLongXia()

if __name__ == '__main__':
    print("=" * 80)
    print("🦞 小龙虾·主板打板进化版")
    print("=" * 80)
    print()
    
    print("📊 当前最优参数:")
    print(f"  封单额：≥{小龙虾.best_params['封单亿']}亿")
    print(f"  流通市值：≥{小龙虾.best_params['流通最小亿']}亿")
    print(f"  换手率：{小龙虾.best_params['换手率最小']}-{小龙虾.best_params['换手率最大']}%")
    print(f"  上板时间：{小龙虾.best_params['时间窗']}")
    print(f"  连板数：≥{小龙虾.best_params['连板最小']}板")
    print()
    
    测试数据 = [
        {'代码': '600227', '名称': '赤天化', '封单额亿': 3.5, '流通市值亿': 45, '换手率': 8.5, '连板数': 3, '上板时间': '09:35', '盈亏': 0.05},
        {'代码': '000890', '名称': '法尔胜', '封单额亿': 2.8, '流通市值亿': 35, '换手率': 12.0, '连板数': 4, '上板时间': '09:40', '盈亏': 0.08},
        {'代码': '603248', '名称': '锡华科技', '封单额亿': 1.5, '流通市值亿': 25, '换手率': 15.0, '连板数': 3, '上板时间': '09:50', '盈亏': -0.02},
        {'代码': '300001', '名称': '特锐德', '封单额亿': 4.0, '流通市值亿': 50, '换手率': 10.0, '连板数': 2, '上板时间': '09:30', '盈亏': 0.03},
    ]
    
    print("🔍 测试打板筛选:")
    for data in 测试数据:
        result = "✅" if 小龙虾.can_buy(data) else "❌"
        print(f"  {result} {data['代码']} {data['名称']}")
    
    print()
    print("🎯 扫板结果:")
    targets = 小龙虾.scan(测试数据)
    for i, stock in enumerate(targets, 1):
        print(f"  {i}. {stock['代码']} {stock['名称']} (评分：{stock['评分']})")
    
    print()
    print("📚 学习测试:")
    小龙虾.learn(测试数据)
