#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主升浪潜力股推荐 - 只做主升浪
用途：筛选主升浪股票，排除震荡和下跌趋势
"""

import time
from datetime import datetime
from 主板票筛选 import is_main_board
from 多数据源修复版 import get_realtime_data


class MainWaveRecommender:
    """主升浪推荐器"""
    
    def __init__(self):
        """初始化"""
        # 观察池 (连板股 + 强势股)
        self.watch_codes = [
            # 3 连板 (主升浪龙头)
            '600370',  # 三房巷
              
            
            # 2 连板 (主升浪初期)
            '600227',  # 赤天化
            '600683',  # 京投发展
            '603929',  # 亚翔集成
            '603248',  # 锡华科技
            
            # 昨日首板 (可能启动)
            '600302',  # 标准股份
            '002427',  # 尤夫股份
            '002278',  # 神开股份
            '002724',  # 海洋王
            '001278',  # 一彬科技
            '603738',  # 泰晶科技
            '002020',  # 深华发 A
            '000639',  # 西王食品
            '600545',  # 卓郎智能
            '603421',  # 鼎信通讯
        ]
        
        self.recommendations = []
    
    def is_main_wave(self, data, history=None):
        """
        判断是否主升浪
        
        主升浪条件:
        1. 趋势向上 (涨幅>0)
        2. 成交量放大 (量比>1.5 或 成交额>3 亿)
        3. 强度足够 (涨幅>3%)
        4. 非震荡 (不是小幅波动)
        """
        change_pct = data.get('change_pct', 0)
        volume_ratio = data.get('volume_ratio', 0)
        amount = data.get('amount', 0)
        
        # 条件 1: 趋势向上 (上涨)
        if change_pct <= 0:
            return False, "下跌/平盘"
        
        # 条件 2: 成交量放大
        volume_ok = False
        if volume_ratio and volume_ratio > 1.5:
            volume_ok = True
        elif amount > 300000000:  # 成交额>3 亿
            volume_ok = True
        
        if not volume_ok:
            return False, "量能不足"
        
        # 条件 3: 强度足够
        if change_pct < 3:
            return False, "涨幅不足"
        
        # 条件 4: 非震荡 (涨幅>3% 且不是涨停)
        if change_pct >= 9.5:
            return False, "已涨停 (买不进)"
        
        return True, "主升浪"
    
    def calculate_score(self, data):
        """
        计算主升浪得分
        
        评分标准:
        - 涨幅：5-8% 最佳 (主升浪加速段)
        - 量比：>2 最佳
        - 成交额：>5 亿最佳
        - 连板：2-3 板最佳
        """
        score = 0
        
        # 涨幅得分 (5-8% 最佳，主升浪加速段)
        change_pct = data.get('change_pct', 0)
        if 5 <= change_pct <= 8:
            score += 50  # 主升浪加速段
        elif 3 <= change_pct < 5:
            score += 40  # 启动初期
        elif 8 <= change_pct < 9.5:
            score += 45  # 接近涨停
        elif change_pct > 0:
            score += 20
        
        # 量比得分
        volume_ratio = data.get('volume_ratio', 0)
        if volume_ratio:
            if volume_ratio > 3:
                score += 30
            elif volume_ratio > 2:
                score += 25
            elif volume_ratio > 1.5:
                score += 20
        else:
            # 无量比数据，用成交额
            amount = data.get('amount', 0)
            if amount > 500000000:  # >5 亿
                score += 30
            elif amount > 300000000:  # >3 亿
                score += 25
        
        # 连板加分 (2-3 板最佳)
        # 简化：用涨幅估算连板概率
        if change_pct >= 9.5:
            score += 20  # 已涨停，强势
        elif change_pct >= 7:
            score += 15  # 可能连板
        
        # 开盘强度
        open_pct = (data.get('open', 0) - data.get('pre_close', 0)) / data.get('pre_close', 1) * 100
        if 3 <= open_pct <= 5:
            score += 10  # 强势开盘
        elif open_pct > 5:
            score += 8
        
        return min(score, 100)
    
    def recommend(self, top_n=3):
        """生成主升浪推荐"""
        print(f"🔍 扫描 {len(self.watch_codes)} 只股票...")
        print(f"📊 策略：只做主升浪 (排除下跌/震荡/已涨停)")
        print()
        
        qualified_stocks = []
        success_count = 0
        fail_count = 0
        
        for code in self.watch_codes:
            # 只筛选主板票
            if not is_main_board(code):
                continue
            
            # 获取实时数据
            result = get_realtime_data(code)
            
            if result.get('success'):
                data = result['data']
                
                # 判断是否主升浪
                is_wave, reason = self.is_main_wave(data)
                
                if is_wave:
                    data['score'] = self.calculate_score(data)
                    data['time'] = datetime.now().strftime('%H:%M:%S')
                    data['source'] = result.get('source_name', 'Unknown')
                    data['elapsed'] = result.get('elapsed', 0)
                    qualified_stocks.append(data)
                    print(f"  ✅ {code} {data.get('name', 'N/A')} - 主升浪 - ¥{data['current']:.2f} ({data['change_pct']:+.1f}%)")
                else:
                    print(f"  ⚪ {code} {data.get('name', 'N/A')} - {reason} - ¥{data['current']:.2f} ({data['change_pct']:+.1f}%)")
                
                success_count += 1
            else:
                print(f"  ❌ {code} - 获取失败")
                fail_count += 1
        
        # 按得分排序
        qualified_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 返回 Top N
        self.recommendations = qualified_stocks[:top_n]
        
        print()
        print(f"✅ 成功：{success_count}只 | 失败：{fail_count}只")
        print(f"📈 符合主升浪：{len(qualified_stocks)}只")
        
        return self.recommendations
    
    def print_recommendations(self):
        """打印推荐"""
        if not self.recommendations:
            print("\n⚠️ 暂无主升浪标的 (市场弱势或已涨停)")
            print("💡 建议：空仓等待或降低仓位")
            return
        
        print("\n" + "=" * 75)
        print("🦞 主升浪潜力股推荐")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("策略：只做主升浪 (排除下跌/震荡/已涨停)")
        print("=" * 75)
        
        for i, stock in enumerate(self.recommendations, 1):
            print(f"\n{i}. {stock['code']} {stock['name']} 【主升浪】")
            print(f"   得分：{stock['score']}/100")
            print(f"   现价：¥{stock['current']:.2f} ({stock['change_pct']:+.1f}%)")
            print(f"   开盘：¥{stock['open']:.2f}")
            print(f"   最高：¥{stock['high']:.2f}")
            print(f"   最低：¥{stock['low']:.2f}")
            
            if stock.get('turnover'):
                print(f"   换手率：{stock['turnover']:.2f}%")
            if stock.get('volume_ratio'):
                print(f"   量比：{stock['volume_ratio']:.2f}")
            
            print(f"   成交额：{stock.get('amount', 0)/100000000:.2f}亿元")
            print(f"   涨停价：¥{stock['pre_close']*1.1:.2f}")
            
            # 操作建议
            if stock['change_pct'] >= 7:
                print(f"   操作：🟡 强势，可轻仓试错")
            elif stock['change_pct'] >= 5:
                print(f"   操作：🟢 主升浪加速，可介入")
            else:
                print(f"   操作：🔵 主升浪初期，可建仓")
            
            print(f"   止损：-5% | 止盈：+10%")
        
        print("\n" + "=" * 75)
        print("⚠️ 风险提示：主升浪策略风险较高，严格止损")
        print("    仓位：单只≤20% | 总仓≤60% | 止损：-5%")
        print("=" * 75)


# 主函数
def run_recommendation():
    """运行推荐"""
    recommender = MainWaveRecommender()
    recs = recommender.recommend(top_n=3)
    recommender.print_recommendations()
    return recs


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--loop':
        # 循环模式
        print("🦞 启动主升浪推荐模式 (每 5 分钟)")
        print("=" * 75)
        
        while True:
            current_time = datetime.now()
            
            # 交易时段运行
            if current_time.hour == 9 and current_time.minute >= 30 or \
               current_time.hour == 10 or \
               current_time.hour == 11 and current_time.minute <= 30 or \
               current_time.hour == 13 or \
               current_time.hour == 14 or \
               current_time.hour == 15 and current_time.minute <= 0:
                
                run_recommendation()
                
                print(f"\n⏳ 下次推荐：5 分钟后")
                time.sleep(300)
            else:
                print("⏰ 非交易时段，等待...")
                time.sleep(60)
    else:
        # 单次运行
        run_recommendation()
