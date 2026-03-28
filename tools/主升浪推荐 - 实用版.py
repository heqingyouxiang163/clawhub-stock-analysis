#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主升浪潜力股推荐 - 实用版
用途：使用扩大观察池 + 多数据源，实时筛选主升浪
"""

import time
from datetime import datetime
from 主板票筛选 import is_main_board
from 多数据源修复版 import get_realtime_data


class MainWaveRecommender:
    """主升浪推荐器 (实用版)"""
    
    def __init__(self):
        """初始化"""
        # 扩大观察池 (连板股 + 活跃股 + 热点股)
        self.watch_codes = [
            # 连板股 (优先)
            '600370',  '600227', '600683', '603929', '603248',
            '600545', '600302', '002427', '002278',
            
            # 活跃股
            '002724', '001278', '603738', '002020', '000639', '603421',
            '000620', '600519', '000858', '002594', '601318', '600036',
            '000001', '600278', '002466', '002460', '002469',
            
            # 热点股 (根据市场动态调整)
            '600569', '600643', '600396', '002256', '300042', '300461',
            '300080', '300345', '300042', '600751', '600152',
        ]
        
        self.recommendations = []
    
    def is_main_wave(self, data):
        """判断是否主升浪"""
        change_pct = data.get('change_pct', 0)
        volume_ratio = data.get('volume_ratio', 0)
        amount = data.get('amount', 0)
        
        # 条件 1: 趋势向上
        if change_pct <= 0:
            return False, "下跌/平盘"
        
        # 条件 2: 成交量放大
        volume_ok = False
        if volume_ratio and volume_ratio > 1.5:
            volume_ok = True
        elif amount > 300000000:
            volume_ok = True
        
        if not volume_ok:
            return False, "量能不足"
        
        # 条件 3: 强度足够
        if change_pct < 3:
            return False, "涨幅不足"
        
        # 条件 4: 非已涨停
        if change_pct >= 9.8:
            return False, "已涨停"
        
        return True, "主升浪"
    
    def calculate_score(self, data):
        """计算主升浪得分"""
        score = 0
        
        # 涨幅得分 (5-8% 最佳)
        change_pct = data.get('change_pct', 0)
        if 5 <= change_pct <= 8:
            score += 50
        elif 3 <= change_pct < 5:
            score += 40
        elif 8 <= change_pct < 9.5:
            score += 45
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
            amount = data.get('amount', 0)
            if amount > 500000000:
                score += 30
            elif amount > 300000000:
                score += 25
        
        # 强势加分
        if change_pct >= 7:
            score += 15
        elif change_pct >= 5:
            score += 10
        
        return min(score, 100)
    
    def recommend(self, top_n=3):
        """生成主升浪推荐"""
        print(f"🔍 扫描 {len(self.watch_codes)} 只股票...")
        print(f"📊 策略：只做主升浪 (排除下跌/震荡/无量/已涨停)")
        print()
        
        qualified_stocks = []
        stats = {
            'total': 0,
            'main_wave': 0,
            'limit_up': 0,
            'decline': 0,
            'low_volume': 0,
            'weak': 0,
        }
        
        for code in self.watch_codes:
            # 只筛选主板票
            if not is_main_board(code):
                continue
            
            stats['total'] += 1
            
            # 获取实时数据 (多数据源并行)
            result = get_realtime_data(code)
            
            if not result.get('success'):
                continue
            
            data = result['data']
            
            # 判断是否主升浪
            is_wave, reason = self.is_main_wave(data)
            
            # 统计
            if is_wave:
                stats['main_wave'] += 1
            elif reason == "已涨停":
                stats['limit_up'] += 1
            elif reason == "下跌/平盘":
                stats['decline'] += 1
            elif reason == "量能不足":
                stats['low_volume'] += 1
            elif reason == "涨幅不足":
                stats['weak'] += 1
            
            if is_wave:
                data['score'] = self.calculate_score(data)
                data['time'] = datetime.now().strftime('%H:%M:%S')
                data['source'] = result.get('source_name', 'Unknown')
                data['elapsed'] = result.get('elapsed', 0)
                qualified_stocks.append(data)
        
        # 按得分排序
        qualified_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 返回 Top N
        self.recommendations = qualified_stocks[:top_n]
        
        # 打印统计
        print(f"📊 筛选统计:")
        print(f"  总计：{stats['total']}只 (主板)")
        print(f"  ✅ 主升浪：{stats['main_wave']}只")
        print(f"  🔴 已涨停：{stats['limit_up']}只 (买不进)")
        print(f"  📉 下跌/平盘：{stats['decline']}只")
        print(f"  💧 量能不足：{stats['low_volume']}只")
        print(f"  ⚪ 涨幅不足：{stats['weak']}只")
        print()
        
        return self.recommendations
    
    def print_recommendations(self):
        """打印推荐"""
        if not self.recommendations:
            print("\n⚠️ 暂无主升浪标的")
            print("💡 建议：空仓等待或降低仓位")
            return
        
        print("\n" + "=" * 75)
        print("🦞 主升浪潜力股推荐 (实用版)")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("策略：实时筛选主升浪 (排除下跌/震荡/无量/已涨停)")
        print("=" * 75)
        
        for i, stock in enumerate(self.recommendations, 1):
            print(f"\n{i}. {stock['code']} {stock['name']} 【主升浪】")
            print(f"   得分：{stock['score']}/100")
            print(f"   现价：¥{stock['current']:.2f} ({stock['change_pct']:+.1f}%)")
            print(f"   成交额：{stock.get('amount', 0)/100000000:.2f}亿元")
            
            if stock.get('turnover'):
                print(f"   换手率：{stock['turnover']:.2f}%")
            if stock.get('volume_ratio'):
                print(f"   量比：{stock['volume_ratio']:.2f}")
            
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
        print("🦞 启动主升浪推荐 (实用版)")
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
