#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
涨停潜力股定时推荐 - 每 5 分钟自动推荐
用途：盘中实时监控，推荐涨停概率大的主板票
"""

import requests
import time
from datetime import datetime
from 主板票筛选 import is_main_board
from 数据缓存 import get_stock_cache, set_stock_cache


class LimitUpRecommender:
    """涨停潜力股推荐器"""
    
    def __init__(self):
        """初始化"""
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
        ]
        
        self.recommendations = []
    
    def get_realtime_data(self, code):
        """获取实时数据"""
        try:
            market = 'sh' if code.startswith('6') else 'sz'
            url = f"http://hq.sinajs.cn/list={market}{code}"
            headers = {
                'Referer': 'https://finance.sina.com.cn/',
                'User-Agent': 'Mozilla/5.0'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200 and response.text:
                text = response.text
                if '=' in text:
                    data_str = text.split('=')[1].strip('"').strip('"')
                    parts = data_str.split(',')
                    
                    if len(parts) >= 32:
                        name = parts[0]
                        current = float(parts[3]) if parts[3] else 0
                        open_p = float(parts[1]) if parts[1] else 0
                        high = float(parts[4]) if parts[4] else 0
                        low = float(parts[5]) if parts[5] else 0
                        pre_close = float(parts[2]) if parts[2] else 0
                        volume = float(parts[8]) if parts[8] else 0
                        amount = float(parts[9]) if parts[9] else 0
                        
                        # 计算涨幅
                        change_pct = (current - pre_close) / pre_close * 100 if pre_close else 0
                        
                        # 估算换手率 (简化)
                        turnover = amount / (current * 1000000) * 100 if current else 0
                        
                        return {
                            'code': code,
                            'name': name,
                            'current': current,
                            'open': open_p,
                            'high': high,
                            'low': low,
                            'pre_close': pre_close,
                            'change_pct': change_pct,
                            'turnover': turnover,
                            'volume': volume,
                            'amount': amount
                        }
            return None
        except Exception as e:
            return None
    
    def calculate_score(self, data):
        """计算涨停概率得分"""
        score = 0
        
        # 涨幅得分 (3%-7% 最佳)
        change = data.get('change_pct', 0)
        if 3 <= change <= 7:
            score += 40
        elif 1 <= change <= 3:
            score += 30
        elif 7 <= change <= 9.5:
            score += 50  # 接近涨停
        elif change > 0:
            score += 10
        
        # 换手率得分 (5%-15% 最佳)
        turnover = data.get('turnover', 0)
        if 5 <= turnover <= 15:
            score += 30
        elif 3 <= turnover <= 20:
            score += 20
        elif turnover < 5:
            score += 15  # 缩量也可能是好事
        
        # 开盘价得分 (高开 3%-5% 最佳)
        open_change = (data['open'] - data['pre_close']) / data['pre_close'] * 100 if data['pre_close'] else 0
        if 3 <= open_change <= 5:
            score += 30
        elif 1 <= open_change <= 3:
            score += 20
        elif 5 <= open_change <= 7:
            score += 25
        
        return min(score, 100)
    
    def recommend(self, top_n=3):
        """生成推荐"""
        print(f"🔍 扫描 {len(self.watch_codes)} 只股票...")
        
        scored_stocks = []
        for code in self.watch_codes:
            # 只筛选主板票
            if not is_main_board(code):
                continue
            
            data = self.get_realtime_data(code)
            if data:
                data['score'] = self.calculate_score(data)
                data['time'] = datetime.now().strftime('%H:%M:%S')
                scored_stocks.append(data)
                
                # 缓存
                set_stock_cache(code, data, ttl=300)
            
            time.sleep(0.1)  # 避免请求过快
        
        # 按得分排序
        scored_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 返回 Top N
        self.recommendations = scored_stocks[:top_n]
        return self.recommendations
    
    def print_recommendations(self):
        """打印推荐"""
        if not self.recommendations:
            print("⚠️ 暂无推荐")
            return
        
        print("\n" + "=" * 70)
        print("🦞 涨停潜力股推荐")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        for i, stock in enumerate(self.recommendations, 1):
            print(f"\n{i}. {stock['code']} {stock['name']}")
            print(f"   得分：{stock['score']}/100")
            print(f"   现价：¥{stock['current']:.2f} ({stock['change_pct']:+.1f}%)")
            print(f"   开盘：¥{stock['open']:.2f} ({(stock['open']-stock['pre_close'])/stock['pre_close']*100:+.1f}%)")
            print(f"   最高：¥{stock['high']:.2f}")
            print(f"   换手：{stock['turnover']:.2f}%")
            print(f"   涨停价：¥{stock['pre_close']*1.1:.2f}")
            
            # 操作建议
            if stock['change_pct'] >= 9.5:
                print(f"   状态：🔴 已涨停/接近涨停")
            elif stock['change_pct'] >= 5:
                print(f"   状态：🟡 强势上涨")
            elif stock['change_pct'] >= 3:
                print(f"   状态：🟢 符合预期")
            else:
                print(f"   状态：⚪ 观察中")
        
        print("\n" + "=" * 70)
        print("⚠️ 风险提示：仅供参考，不构成投资建议")
        print("    止损位：-5% | 仓位：单只≤20% | 总仓≤50%")
        print("=" * 70)


# 主函数
def run_recommendation():
    """运行推荐"""
    recommender = LimitUpRecommender()
    recs = recommender.recommend(top_n=3)
    recommender.print_recommendations()
    return recs


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--loop':
        # 循环模式 (每 5 分钟)
        print("🦞 启动定时推荐模式 (每 5 分钟)")
        print("=" * 70)
        
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
