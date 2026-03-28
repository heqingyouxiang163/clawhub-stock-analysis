#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主升浪潜力股推荐 v3 - 真实时数据源
用途：从东方财富获取实时涨幅榜，筛选主升浪股票
"""

import requests
import time
from datetime import datetime
from 主板票筛选 import is_main_board


class MainWaveRecommenderV3:
    """主升浪推荐器 v3 (真实时数据源)"""
    
    def __init__(self):
        """初始化"""
        self.recommendations = []
    
    def fetch_top_gainers(self, limit=100):
        """
        获取东方财富涨幅榜
        
        Returns:
            list: 涨幅前 N 只股票
        """
        try:
            # 沪深 A 股涨幅榜
            url = f"http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz={limit}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2&fields=f12,f14,f2,f3,f5,f6,f18,f107,f108"
            headers = {'Referer': 'http://quote.eastmoney.com/'}
            
            start = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    stocks = data['data']['diff']
                    
                    # 转换为统一格式
                    result = []
                    for s in stocks:
                        result.append({
                            'code': s['f12'],
                            'name': s['f14'],
                            'current': s['f2'],
                            'change_pct': s['f3'],
                            'volume': s['f5'],
                            'amount': s['f6'],
                            'turnover': s.get('f107', 0),
                            'volume_ratio': s.get('f108', 0),
                            'source': 'eastmoney',
                            'elapsed': elapsed
                        })
                    
                    return result
            return []
        except Exception as e:
            print(f"❌ 获取涨幅榜失败：{e}")
            return []
    
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
        print(f"🔍 获取东方财富涨幅榜...")
        
        # 获取涨幅前 100 名
        stocks = self.fetch_top_gainers(limit=100)
        elapsed = stocks[0].get('elapsed', 0)*1000 if stocks else 0
        print(f"📊 获取到 {len(stocks)} 只股票 (耗时：{elapsed:.1f}ms)")
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
        
        for stock in stocks:
            # 只筛选主板票
            if not is_main_board(stock['code']):
                continue
            
            stats['total'] += 1
            
            # 判断是否主升浪
            is_wave, reason = self.is_main_wave(stock)
            
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
                stock['score'] = self.calculate_score(stock)
                stock['time'] = datetime.now().strftime('%H:%M:%S')
                qualified_stocks.append(stock)
        
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
        print("🦞 主升浪潜力股推荐 v3 (真实时数据源)")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("策略：实时获取涨幅榜，筛选主升浪")
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
            
            print(f"   涨停价：¥{stock['current']*1.1:.2f}")
            
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
    recommender = MainWaveRecommenderV3()
    recs = recommender.recommend(top_n=3)
    recommender.print_recommendations()
    return recs


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--loop':
        # 循环模式
        print("🦞 启动主升浪推荐 v3 (真实时数据源)")
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
