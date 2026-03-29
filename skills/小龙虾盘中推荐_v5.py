#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 小龙虾盘中推荐 v5.0 - 集成涨停预测模型

功能:
- 实时扫描主板股票
- 涨停概率预测 (基于训练模型)
- 综合评分推荐 (≥80 分重点推荐)
- 自动推送反馈
"""

import sys
sys.path.insert(0, 'skills')

from 小龙虾_main_board import XiaoLongXia
from 涨停分时图训练 import LimitUpTrainer
import requests
import time
from datetime import datetime


class XiaoLongXiaV5(XiaoLongXia):
    """小龙虾 v5.0 - 集成涨停预测模型"""
    
    def __init__(self):
        super().__init__()
        self.trainer = LimitUpTrainer()
        self.trainer.load_model()  # 加载训练好的模型
        print("🦞 小龙虾 v5.0 启动 - 集成涨停预测模型")
    
    def scan_with_prediction(self, market_data: list) -> list:
        """
        扫板 + 涨停概率预测
        
        Args:
            market_data: 实时行情数据
        
        Returns:
            推荐股票列表 (按涨停概率排序)
        """
        print(f"🔍 扫描市场，获取到 {len(market_data)} 只股票...")
        
        targets = []
        
        for row in market_data:
            # 1. 基础筛选 (主板 + 打板条件)
            if not self.can_buy(row):
                continue
            
            # 2. 计算基础评分
            base_score = self.calc_score(row)
            
            # 3. 涨停概率预测
            predict_score = self.trainer.predict_score(row)
            
            # 4. 综合评分 (基础评分 40% + 预测评分 60%)
            final_score = base_score * 0.4 + predict_score * 0.6
            
            targets.append({
                '代码': row.get('代码', ''),
                '名称': row.get('名称', ''),
                '涨幅': row.get('涨幅', 0),
                '封单额': row.get('封单额亿', 0),
                '流通市值': row.get('流通市值亿', 0),
                '换手率': row.get('换手率', 0),
                '连板数': row.get('连板数', 1),
                '上板时间': row.get('上板时间', ''),
                '基础评分': round(base_score, 1),
                '涨停概率': round(predict_score, 1),
                '综合评分': round(final_score, 1),
                '推荐等级': self.get_recommend_level(final_score)
            })
        
        # 按综合评分排序
        targets.sort(key=lambda x: x['综合评分'], reverse=True)
        
        return targets[:5]  # 返回前 5 强
    
    def get_recommend_level(self, score: float) -> str:
        """获取推荐等级"""
        if score >= 85:
            return "🔥 重点推荐"
        elif score >= 75:
            return "✅ 推荐"
        elif score >= 65:
            return "⚠️ 关注"
        else:
            return "❌ 观望"
    
    def feedback(self, targets: list):
        """推送推荐反馈"""
        now = datetime.now().strftime("%m-%d %H:%M")
        
        print(f"\n{'='*80}")
        print(f"【小龙虾推荐 · {now}】")
        print(f"{'='*80}")
        
        if not targets:
            print("⚠️ 暂无符合要求的标的")
        else:
            for i, t in enumerate(targets, 1):
                print(f"\n{i}. {t['代码']} {t['名称']}")
                print(f"   涨幅：{t['涨幅']:+.2f}% | 连板：{t['连板数']}板 | 封单：{t['封单额']}亿")
                print(f"   基础评分：{t['基础评分']} | 涨停概率：{t['涨停概率']} | 综合评分：{t['综合评分']}")
                print(f"   推荐等级：{t['推荐等级']}")
        
        print(f"\n{'='*80}\n")


def get_realtime_market():
    """获取实时行情数据"""
    all_stocks = []
    
    # 获取沪深 A 股实时数据
    for prefix_list, market in [(['600', '601', '603', '605'], 'sh'),
                                  (['000', '001', '002', '003'], 'sz')]:
        for prefix in prefix_list:
            for i in range(0, 100, 10):  # 每批 10 只
                batch = [f'{market}{prefix}{j:03d}' for j in range(i, min(i+10, 100))]
                code_list = ','.join(batch)
                url = f"http://qt.gtimg.cn/q={code_list}"
                
                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        text = resp.content.decode('gbk')
                        for line in text.strip().split(';'):
                            if '=' in line:
                                data = line.split('=')[1].strip('"').split('~')
                                if len(data) >= 50:
                                    code = data[2]
                                    change_pct = float(data[32]) if data[32] else 0
                                    
                                    # 只获取涨幅>3% 的股票
                                    if change_pct > 3:
                                        all_stocks.append({
                                            '代码': code,
                                            '名称': data[1],
                                            '涨幅': change_pct,
                                            '封单额亿': float(data[48]) / 100000000 if len(data) > 48 and data[48] else 0,
                                            '流通市值亿': float(data[45]) / 100000000 if len(data) > 45 and data[45] else 0,
                                            '换手率': float(data[40]) if len(data) > 40 and data[40] else 0,
                                            '连板数': 1,  # 需要额外获取
                                            '上板时间': '',  # 需要额外获取
                                        })
                except:
                    pass
                
                time.sleep(0.05)
    
    return all_stocks


if __name__ == '__main__':
    print("=" * 80)
    print("🦞 小龙虾 v5.0 - 盘中推荐 (集成涨停预测模型)")
    print("=" * 80)
    print()
    
    # 初始化
    lxl = XiaoLongXiaV5()
    
    # 获取实时行情
    market_data = get_realtime_market()
    
    # 扫板 + 预测
    targets = lxl.scan_with_prediction(market_data)
    
    # 推送反馈
    lxl.feedback(targets)
    
    # 保存推荐记录
    import json
    from pathlib import Path
    
    record_file = Path('temp/小龙虾推荐记录.json')
    record_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(record_file, 'a', encoding='utf-8') as f:
        json.dump({
            '时间': datetime.now().isoformat(),
            '推荐股票': targets
        }, f, ensure_ascii=False, indent=2)
        f.write('\n')
    
    print("✅ 推荐记录已保存")
