#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高确定性涨停股推荐 - 定时任务版 (实时动态观察池)
用途：每 5 分钟运行一次，实时获取市场数据，只推荐≥75 分的高确定性股票
优化：自动判断交易时间，非交易时间自动跳过
"""

import time
import requests
from datetime import datetime
from 主板票筛选 import is_main_board
from 多数据源修复版 import get_realtime_data
from 实时动态观察池 import get_realtime_watchlist


def is_trading_time():
    """判断是否在交易时间内"""
    now = datetime.now()
    
    # 周末
    if now.weekday() >= 5:
        return False
    
    # 交易时段：9:30-11:30, 13:00-15:00
    hour, minute = now.hour, now.minute
    
    if hour == 9 and minute >= 30: return True
    if hour == 10: return True
    if hour == 11 and minute <= 30: return True
    if hour == 13: return True
    if hour == 14: return True
    if hour == 15 and minute <= 5: return True
    
    return False


class HighProbRecommender:
    """高确定性涨停股推荐器"""
    
    def __init__(self):
        self.exclude_codes = [
            '601318', '600036', '000001', '601166', '600030',
            '601398', '601288', '601988', '600585', '000333',
            '601088', '601857', '600900', '600519',
        ]
    
    def fetch_realtime_watchlist(self):
        """实时获取观察池"""
        watch_codes = get_realtime_watchlist(limit=100, use_cache=True)
        
        if watch_codes:
            filtered = [code for code in watch_codes if code not in self.exclude_codes]
            print(f"✅ 实时观察池：{len(filtered)}只 (已排除大蓝筹)")
            return filtered
        
        # 备用池
        backup_pool = [
            '600370', '000890', '600227', '600683', '603929', '603248',
            '600545', '600302', '002427', '002278', '002724', '001278',
            '603738', '002020', '000639', '603421', '000620',
            '600569', '600643', '600396', '002256', '600751', '600152',
        ]
        print(f"⚠️ 使用备用池：{len(backup_pool)}只")
        return backup_pool
    
    def analyze_stock(self, code):
        """分析单只股票"""
        data = get_realtime_data(code)
        
        if not data.get('success'):
            return None
        
        d = data['data']
        change_pct = float(d.get('change_pct', 0) or 0)
        amount = float(d.get('amount', 0) or 0)
        volume_ratio = float(d.get('volume_ratio', 0) or 0)
        turnover = float(d.get('turnover', 0) or 0)
        current = float(d.get('current', 0) or 0)
        
        # 排除停牌
        if current == 0 or change_pct == 0:
            return None
        
        # 评分
        score = 0
        reasons = []
        
        # 涨幅 (5-8% 主升浪加速段)
        if 5 <= change_pct < 8:
            score += 40
            reasons.append("主升浪加速段")
        elif change_pct >= 8:
            score += 20
            reasons.append("涨幅偏高")
        elif 3 <= change_pct < 5:
            score += 20
            reasons.append("温和上涨")
        
        # 量能
        if amount > 100000:
            score += 20
            reasons.append("成交活跃")
        elif amount > 50000:
            score += 10
            reasons.append("成交尚可")
        
        # 量比
        if volume_ratio > 2:
            score += 20
            reasons.append("量比放大")
        elif volume_ratio > 1:
            score += 10
            reasons.append("量比正常")
        
        # 换手率
        if 5 <= turnover <= 15:
            score += 20
            reasons.append("换手健康")
        elif turnover > 15:
            score += 5
            reasons.append("换手偏高")
        
        return {
            'code': code,
            'name': d.get('name', '?'),
            'current': current,
            'change_pct': change_pct,
            'amount': amount,
            'volume_ratio': volume_ratio,
            'turnover': turnover,
            'score': score,
            'reasons': reasons
        }
    
    def recommend(self, min_score=75, top_n=5):
        """推荐股票 - 优化版 (并发获取)"""
        watchlist = self.fetch_realtime_watchlist()
        
        # 并发获取数据 (10 线程)
        import concurrent.futures
        candidates = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_code = {executor.submit(self.analyze_stock, code): code for code in watchlist}
            for future in concurrent.futures.as_completed(future_to_code, timeout=30):
                try:
                    result = future.result()
                    if result:
                        candidates.append(result)
                except Exception as e:
                    pass
        
        # 排序
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # 筛选 - 只输出最强的前 5 名
        self.recommendations = [s for s in candidates if s['score'] >= min_score][:top_n]
        
        return self.recommendations
    
    def print_recommendations(self, min_score=75):
        """打印推荐"""
        print("=" * 75)
        print("🦞 高确定性涨停股推荐")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"标准：≥{min_score}分才推荐 (宁可空仓，不做弱势)")
        print("=" * 75)
        print()
        
        if not self.recommendations:
            print("❌ 今日无高确定性机会")
            print()
            print("💡 建议：空仓等待，宁可空仓不做弱势")
        else:
            print(f"✅ 找到 {len(self.recommendations)} 只高确定性股票！\n")
            
            for i, s in enumerate(self.recommendations, 1):
                rating = "🟢🟢 强势" if s['score'] >= 75 else "🟡 关注"
                print(f"{i}. {s['code']} {s['name']} | 得分：{s['score']} | {s['change_pct']:+.1f}% | {rating}")
                print(f"   现价：¥{s['current']:.2f} | 成交：{s['amount']/10000:.1f}亿")
                print(f"   理由：{', '.join(s['reasons'])}")
                print(f"   建议：可建仓 | 止损：-5% | 止盈：+10%")
                print()


def run_recommendation():
    """运行推荐"""
    recommender = HighProbRecommender()
    recommender.recommend(min_score=75, top_n=3)
    recommender.print_recommendations(min_score=75)


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    import sys
    
    # 检查交易时间
    if not is_trading_time():
        print(f"⏰ 当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🛑 非交易时间，自动跳过")
        print()
        print("💤 收盘了，休息！")
        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--loop':
        print("🔄 循环模式：每 5 分钟运行一次 (交易时段)\n")
        
        while True:
            if is_trading_time():
                run_recommendation()
                print(f"\n⏳ 下次推荐：5 分钟后")
                time.sleep(300)
            else:
                print("⏰ 收盘了，停止推荐")
                break
    else:
        run_recommendation()
