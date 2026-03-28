#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 小龙虾·主板打板进化版

权限：仅沪深主板 | 模式：超短打板 | 能力：自我学习 + 迭代 + 升级

功能:
- 只关注沪深主板 (600/601/603/605/000/001)
- 自动筛选打板目标
- 自我学习复盘胜率
- 自动进化优化参数
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


class XiaoLongXia:
    """小龙虾·主板打板进化版"""
    
    def __init__(self):
        # 只认沪深主板，别的一律不碰
        self.allow_prefix = ('600', '601', '603', '605', '000', '001', '002', '003')
        self.blacklist = []
        
        # 最优参数 (初始值)
        self.best_params = {
            '封单亿': 3,
            '流通最小亿': 20,
            '时间窗': '09:30-10:00',
            '换手率最小': 5,
            '换手率最大': 20,
            '连板最小': 2
        }
        
        # 学习记录
        self.history_file = Path('memory/小龙虾学习记录.json')
        self.load_history()
    
    def load_history(self):
        """加载历史学习记录"""
        if self.history_file.exists():
            import json
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = data.get('history', [])
                self.best_params = data.get('best_params', self.best_params)
        else:
            self.history = []
    
    def save_history(self):
        """保存历史学习记录"""
        import json
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump({
                'history': self.history,
                'best_params': self.best_params,
                'last_update': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def 只看主板(self, code: str) -> bool:
        """筛选：只做正经主板票"""
        return code[:3] in self.allow_prefix and 'ST' not in code
    
    def 能打板吗(self, row: dict) -> bool:
        """打板条件判断"""
        # 1. 必须是主板
        if not self.只看主板(row.get('代码', '')):
            return False
        
        # 2. 封单额要求
        if row.get('封单额亿', 0) < self.best_params['封单亿']:
            return False
        
        # 3. 流通市值要求
        if row.get('流通市值亿', 0) < self.best_params['流通最小亿']:
            return False
        
        # 4. 上板时间要求
        上板时间 = row.get('上板时间', '')
        if not 上板时间:
            return False
        
        try:
            time_str = 上板时间.split(':')[0] + 上板时间.split(':')[1][:2]
            if not ('0930' <= time_str <= '1000'):
                return False
        except:
            return False
        
        # 5. 黑名单检查
        if row.get('代码', '') in self.blacklist:
            return False
        
        # 6. 换手率要求
        换手率 = row.get('换手率', 0)
        if not (self.best_params['换手率最小'] <= 换手率 <= self.best_params['换手率最大']):
            return False
        
        # 7. 连板数要求
        连板数 = row.get('连板数', 1)
        if 连板数 < self.best_params['连板最小']:
            return False
        
        return True
    
    def 该卖吗(self, row: dict) -> bool:
        """卖出纪律"""
        # 炸板必须卖
        if row.get('炸板', False):
            return True
        
        # 回撤超过 4% 必须卖
        if row.get('回撤', 0) <= -0.04:
            return True
        
        return False
    
    def 学习(self, 历史记录：list) -> float:
        """自我学习：复盘胜率"""
        if not 历史记录:
            return 0.0
        
        df = pd.DataFrame(历史记录)
        df['盈利'] = df['盈亏'] > 0
        
        胜率 = df['盈利'].mean()
        总收益 = df['盈亏'].sum()
        
        print(f"🦞 小龙虾学习完成 → 胜率：{胜率:.1%}，总收益：{总收益:.2%}")
        
        # 保存到历史记录
        self.history.extend(历史记录)
        self.save_history()
        
        return 胜率
    
    def 进化 (self, 历史数据：list):
        """自我迭代：自动优化参数"""
        if len(历史数据) < 10:
            print("⚠️ 数据量太少，无法进化 (至少需要 10 条)")
            return
        
        best_win = 0
        best_p = self.best_params.copy()
        
        print("\n🔬 小龙虾开始进化...")
        
        # 网格搜索最优参数
        for 封单 in [2, 3, 4, 5]:
            for 流通最小 in [15, 20, 25, 30]:
                for 换手最小 in [3, 5, 8]:
                    for 换手最大 in [15, 20, 25]:
                        # 临时修改参数
                        self.best_params['封单亿'] = 封单
                        self.best_params['流通最小亿'] = 流通最小
                        self.best_params['换手率最小'] = 换手最小
                        self.best_params['换手率最大'] = 换手最大
                        
                        # 回测胜率
                        胜率 = self.回测 (历史数据)
                        
                        if 胜率 > best_win:
                            best_win = 胜率
                            best_p = self.best_params.copy()
                            print(f"  新记录！胜率：{胜率:.1%} | 参数：封单={封单}亿，流通={流通最小}亿，换手={换手最小}-{换手最大}%")
        
        # 恢复最优参数
        self.best_params = best_p
        self.save_history()
        
        print(f"\n✅ 小龙虾升级完成！最新最优参数：")
        print(f"  封单额：≥{self.best_params['封单亿']}亿")
        print(f"  流通市值：≥{self.best_params['流通最小亿']}亿")
        print(f"  换手率：{self.best_params['换手率最小']}-{self.best_params['换手率最大']}%")
        print(f"  上板时间：{self.best_params['时间窗']}")
        print(f"  连板数：≥{self.best_params['连板最小']}板")
    
    def 回测 (self, 历史数据：list) -> float:
        """回测当前参数"""
        if not 历史数据:
            return 0.0
        
        盈利次数 = 0
        总次数 = 0
        
        for record in 历史数据:
            if self.能打板吗 (record):
                总次数 += 1
                if record.get('盈亏', 0) > 0:
                    盈利次数 += 1
        
        return 盈利次数 / 总次数 if 总次数 > 0 else 0.0
    
    def 扫板 (self, 实时行情：list) -> list:
        """实盘扫板：筛选目标"""
        目标 = []
        
        for row in 实时行情:
            if self.能打板吗 (row):
                目标.append({
                    '代码': row.get('代码', ''),
                    '名称': row.get('名称', ''),
                    '涨幅': row.get('涨幅', 0),
                    '封单额': row.get('封单额亿', 0),
                    '流通市值': row.get('流通市值亿', 0),
                    '换手率': row.get('换手率', 0),
                    '连板数': row.get('连板数', 1),
                    '上板时间': row.get('上板时间', ''),
                    '评分': self.计算评分 (row)
                })
        
        # 按评分排序，只选前 3 强
        目标.sort(key=lambda x: x['评分'], reverse=True)
        return 目标[:3]
    
    def 计算评分 (self, row: dict) -> float:
        """计算个股评分 (100 分制)"""
        评分 = 50  # 基础分
        
        # 封单额加分
        封单 = row.get('封单额亿', 0)
        if 封单 >= 5:
            评分 += 20
        elif 封单 >= 3:
            评分 += 15
        elif 封单 >= 2:
            评分 += 10
        
        # 流通市值加分
        流通 = row.get('流通市值亿', 0)
        if 流通 >= 50:
            评分 += 15
        elif 流通 >= 30:
            评分 += 10
        elif 流通 >= 20:
            评分 += 5
        
        # 换手率加分
        换手 = row.get('换手率', 0)
        if 5 <= 换手 <= 15:
            评分 += 15
        elif 3 <= 换手 <= 20:
            评分 += 10
        
        # 连板数加分
        连板 = row.get('连板数', 1)
        if 连板 >= 4:
            评分 += 15
        elif 连板 >= 3:
            评分 += 10
        elif 连板 >= 2:
            评分 += 5
        
        # 上板时间加分
        时间 = row.get('上板时间', '')
        if 时间:
            try:
                time_str = 时间.split(':')[0] + 时间.split(':')[1][:2]
                if '0930' <= time_str <= '0935':
                    评分 += 15
                elif '0935' < time_str <= '0945':
                    评分 += 10
                elif '0945' < time_str <= '1000':
                    评分 += 5
            except:
                pass
        
        return min(100, 评分)


# ======================================
# 激活你的小龙虾
# ======================================

小龙虾 = XiaoLongXia()

# 用法示例：
# 今日目标 = 小龙虾。扫板 (实时行情)
# 小龙虾。学习 (今日交易记录)
# 小龙虾。进化 (一周历史数据)


if __name__ == '__main__':
    # 测试示例
    print("=" * 80)
    print("🦞 小龙虾·主板打板进化版")
    print("=" * 80)
    print()
    
    # 显示当前最优参数
    print("📊 当前最优参数:")
    print(f"  封单额：≥{小龙虾.best_params['封单亿']}亿")
    print(f"  流通市值：≥{小龙虾.best_params['流通最小亿']}亿")
    print(f"  换手率：{小龙虾.best_params['换手率最小']}-{小龙虾.best_params['换手率最大']}%")
    print(f"  上板时间：{小龙虾.best_params['时间窗']}")
    print(f"  连板数：≥{小龙虾.best_params['连板最小']}板")
    print()
    
    # 模拟测试
    测试数据 = [
        {'代码': '600227', '名称': '赤天化', '封单额亿': 3.5, '流通市值亿': 45, '换手率': 8.5, '连板数': 3, '上板时间': '09:35', '盈亏': 0.05},
        {'代码': '000890', '名称': '法尔胜', '封单额亿': 2.8, '流通市值亿': 35, '换手率': 12.0, '连板数': 4, '上板时间': '09:40', '盈亏': 0.08},
        {'代码': '603248', '名称': '锡华科技', '封单额亿': 1.5, '流通市值亿': 25, '换手率': 15.0, '连板数': 3, '上板时间': '09:50', '盈亏': -0.02},
        {'代码': '300001', '名称': '特锐德', '封单额亿': 4.0, '流通市值亿': 50, '换手率': 10.0, '连板数': 2, '上板时间': '09:30', '盈亏': 0.03},  # 创业板，应该被过滤
    ]
    
    print("🔍 测试打板筛选:")
    for 数据 in 测试数据:
        结果 = "✅" if 小龙虾。能打板吗 (数据) else "❌"
        print(f"  {结果} {数据 ['代码']} {数据 ['名称']}")
    
    print()
    print("🎯 扫板结果:")
    目标 = 小龙虾。扫板 (测试数据)
    for i, 股票 in enumerate(目标，1):
        print(f"  {i}. {股票 ['代码']} {股票 ['名称']} (评分：{股票 ['评分']})")
    
    print()
    print("📚 学习测试:")
    小龙虾。学习 (测试数据)
    
    print()
    print("🔬 进化测试 (简化版):")
    小龙虾。进化 (测试数据 * 5)  # 复制 5 份以增加数据量
