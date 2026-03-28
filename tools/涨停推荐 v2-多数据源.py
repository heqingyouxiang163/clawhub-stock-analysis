#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
涨停潜力股推荐 v2 - 多数据源优化版
用途：使用多数据源获取准确数据，推荐涨停概率大的主板票
"""

import time
from datetime import datetime
from 主板票筛选 import is_main_board
from 多数据源修复版 import get_realtime_data


class LimitUpRecommenderV2:
    """涨停潜力股推荐器 v2 (多数据源版)"""
    
    def __init__(self):
        """初始化"""
        # 观察池 (昨日涨停股 + 热点股)
        self.watch_codes = [
            # 3 连板
            '600370',  # 三房巷
              
            
            # 2 连板
            '600227',  # 赤天化
            '600683',  # 京投发展
            '603929',  # 亚翔集成
            '603248',  # 锡华科技
            
            # 昨日首板 (可能连板)
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
            '000620',  # 盈新发展
        ]
        
        self.recommendations = []
    
    def calculate_score(self, data):
        """
        计算涨停概率得分 (优化版)
        
        评分标准:
        - 涨幅：3%-7% 最佳 (40 分)
        - 换手率：5%-15% 最佳 (30 分)
        - 量比：>2 最佳 (20 分)
        - 竞价涨幅：3%-5% 最佳 (10 分)
        """
        score = 0
        
        # 涨幅得分 (3%-7% 最佳)
        change_pct = data.get('change_pct', 0)
        if 3 <= change_pct <= 7:
            score += 40
        elif 1 <= change_pct <= 3:
            score += 30
        elif 7 <= change_pct <= 9.5:
            score += 50  # 接近涨停
        elif change_pct >= 9.8:
            score = 100  # 已涨停
        elif change_pct > 0:
            score += 10
        
        # 换手率得分 (5%-15% 最佳)
        turnover = data.get('turnover', 0)
        if turnover:  # 有真实换手率数据
            if 5 <= turnover <= 15:
                score += 30
            elif 3 <= turnover <= 20:
                score += 20
            elif turnover < 5:
                score += 15  # 缩量也可能是好事
        else:
            # 无真实数据，用成交额估算
            amount = data.get('amount', 0)
            if amount > 100000000:  # 成交额>1 亿
                score += 20
        
        # 量比得分 (>2 最佳)
        volume_ratio = data.get('volume_ratio', 0)
        if volume_ratio:
            if volume_ratio > 3:
                score += 20
            elif volume_ratio > 2:
                score += 15
            elif volume_ratio > 1.5:
                score += 10
        
        # 竞价涨幅得分 (3%-5% 最佳)
        open_pct = (data.get('open', 0) - data.get('pre_close', 0)) / data.get('pre_close', 1) * 100
        if 3 <= open_pct <= 5:
            score += 10
        elif 1 <= open_pct <= 3:
            score += 5
        elif 5 <= open_pct <= 7:
            score += 8
        
        return min(score, 100)
    
    def recommend(self, top_n=3):
        """生成推荐"""
        print(f"🔍 扫描 {len(self.watch_codes)} 只股票...")
        
        scored_stocks = []
        success_count = 0
        fail_count = 0
        
        for code in self.watch_codes:
            # 只筛选主板票
            if not is_main_board(code):
                continue
            
            # 获取实时数据 (多数据源并行)
            result = get_realtime_data(code)
            
            if result.get('success'):
                data = result['data']
                data['score'] = self.calculate_score(data)
                data['time'] = datetime.now().strftime('%H:%M:%S')
                data['source'] = result.get('source_name', 'Unknown')
                data['elapsed'] = result.get('elapsed', 0)
                scored_stocks.append(data)
                success_count += 1
            else:
                fail_count += 1
            
            # 不延迟，多数据源已经很稳定
        
        # 按得分排序
        scored_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 返回 Top N
        self.recommendations = scored_stocks[:top_n]
        
        print(f"✅ 成功：{success_count}只 | 失败：{fail_count}只")
        
        return self.recommendations
    
    def print_recommendations(self):
        """打印推荐"""
        if not self.recommendations:
            print("⚠️ 暂无推荐")
            return
        
        print("\n" + "=" * 75)
        print("🦞 涨停潜力股推荐 v2 (多数据源优化版)")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 75)
        
        for i, stock in enumerate(self.recommendations, 1):
            print(f"\n{i}. {stock['code']} {stock['name']}")
            print(f"   得分：{stock['score']}/100")
            print(f"   现价：¥{stock['current']:.2f} ({stock['change_pct']:+.1f}%)")
            print(f"   开盘：¥{stock['open']:.2f} ({(stock['open']-stock['pre_close'])/stock['pre_close']*100:+.1f}%)")
            print(f"   最高：¥{stock['high']:.2f}")
            print(f"   最低：¥{stock['low']:.2f}")
            
            if stock.get('turnover'):
                print(f"   换手率：{stock['turnover']:.2f}%")
            if stock.get('volume_ratio'):
                print(f"   量比：{stock['volume_ratio']:.2f}")
            
            print(f"   成交额：{stock.get('amount', 0)/100000000:.2f}亿元")
            print(f"   数据源：{stock.get('source', 'Unknown')} ({stock.get('elapsed', 0)*1000:.1f}ms)")
            print(f"   涨停价：¥{stock['pre_close']*1.1:.2f}")
            
            # 状态
            if stock['change_pct'] >= 9.8:
                print(f"   状态：🔴 已涨停")
            elif stock['change_pct'] >= 5:
                print(f"   状态：🟡 强势上涨")
            elif stock['change_pct'] >= 3:
                print(f"   状态：🟢 符合预期")
            else:
                print(f"   状态：⚪ 观察中")
        
        print("\n" + "=" * 75)
        print("⚠️ 风险提示：仅供参考，不构成投资建议")
        print("    止损位：-5% | 仓位：单只≤20% | 总仓≤50%")
        print("=" * 75)


# 主函数
def run_recommendation():
    """运行推荐"""
    recommender = LimitUpRecommenderV2()
    recs = recommender.recommend(top_n=3)
    recommender.print_recommendations()
    return recs


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--loop':
        # 循环模式 (每 5 分钟)
        print("🦞 启动定时推荐模式 (每 5 分钟)")
        print("=" * 75)
        
        while True:
            current_time = datetime.now()
            
            # 只在交易时段运行 (9:30-11:30, 13:00-15:00)
            if current_time.hour == 9 and current_time.minute >= 30 or \
               current_time.hour == 10 or \
               current_time.hour == 11 and current_time.minute <= 30 or \
               current_time.hour == 13 or \
               current_time.hour == 14 or \
               current_time.hour == 15 and current_time.minute <= 0:
                
                run_recommendation()
                
                # 等待 5 分钟
                print(f"\n⏳ 下次推荐：5 分钟后")
                time.sleep(300)
            else:
                print("⏰ 非交易时段，等待...")
                time.sleep(60)
    else:
        # 单次运行
        run_recommendation()
