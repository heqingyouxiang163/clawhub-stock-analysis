#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高确定性涨停股推荐 - 定时任务版 (实时涨幅榜)
用途：每 5 分钟运行一次，从实时涨幅榜获取数据，只推荐≥75 分的高确定性股票
优化：
1. 优先监控持仓股
2. 使用「实时 A 股涨幅榜」技能获取沪深主板数据
3. 涨停股应该高分（之前逻辑错误）
4. 只推荐沪深主板股票（排除创业板和科创板）
"""

import time
import requests
from datetime import datetime
from 主板票筛选 import is_main_board
from 多数据源修复版 import get_realtime_data
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/tencent-stock-rank')
from 持仓配置 import HOLDINGS
from tencent_stock_rank import get_realtime_rank  # 使用成熟的腾讯财经技能


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


def fetch_top_gainers(limit=150):
    """
    获取实时涨幅榜 - 使用腾讯财经技能（稳定）
    
    专为高确定性推荐设计
    """
    print("📈 使用腾讯财经技能获取沪深主板数据...")
    start_time = time.time()
    
    try:
        # 使用腾讯财经技能获取涨幅榜
        stocks = get_realtime_rank(limit=limit)
        elapsed = time.time() - start_time
        
        if stocks:
            print(f"✅ 成功获取{len(stocks)}只股票，耗时{elapsed*1000:.0f}ms")
            return stocks
        else:
            print("⚠️ 腾讯财经返回空数据，切换到备用方案...")
    except Exception as e:
        print(f"⚠️ 腾讯财经失败：{e}，切换到备用方案...")
    
    # 备用方案：使用旧的多数据源
    return _fetch_fallback(limit)


def _fetch_fallback(limit=100):
    """
    备用方案：多数据源获取涨幅榜
    当技能失败时使用
    """
    # 1. 新浪财经
    stocks = _fetch_sina(limit)
    if stocks:
        return stocks
    
    # 2. 东方财富
    print("⚠️ 新浪失败，切换到东方财富...")
    stocks = _fetch_eastmoney(limit)
    if stocks:
        return stocks
    
    # 3. 腾讯财经
    print("⚠️ 东财失败，切换到腾讯财经...")
    return _fetch_tencent(limit)


def _fetch_eastmoney(limit=100):
    """东方财富涨幅榜"""
    try:
        url = 'http://push2.eastmoney.com/api/qt/clist/get'
        params = {
            'pn': '1',
            'pz': str(limit),
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'm:1 t:2,m:1 t:23,m:0 t:6,m:0 t:80',
            'fields': 'f12,f14,f3,f2,f17',
            '_': str(int(time.time() * 1000))
        }
        
        headers = {'Referer': 'http://quote.eastmoney.com/', 'User-Agent': 'Mozilla/5.0'}
        
        start = time.time()
        response = requests.get(url, params=params, headers=headers, timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'diff' in data['data']:
                stocks = []
                for item in data['data']['diff']:
                    code = item['f12']
                    name = item['f14']
                    change_pct = item['f3']
                    current = item['f2']
                    amount = item['f17'] * 10000
                    
                    if current == 0:
                        continue
                    
                    stocks.append({
                        'code': code,
                        'name': name,
                        'current': current,
                        'change_pct': change_pct,
                        'amount': amount,
                    })
                
                print(f"✅ 东方财富涨幅榜：{len(stocks)}只 ({elapsed*1000:.0f}ms)")
                return stocks
    except Exception as e:
        pass
    
    return None


def _fetch_sina(limit=100):
    """新浪财经涨幅榜 (最终备用)"""
    try:
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple'
        params = {'page': '1', 'num': str(limit * 2), 'sort': 'changepercent', 'asc': '0', 'node': 'hs_a'}  # 多获取一些
        headers = {'Referer': 'http://vip.stock.finance.sina.com.cn/'}
        
        start = time.time()
        response = requests.get(url, params=params, headers=headers, timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            stocks = []
            
            for s in data:
                code = s.get('code', '')
                # 只保留主板 (60/00 开头，排除 688/300/301)
                if not (code.startswith('60') or code.startswith('00')):
                    continue
                
                change_pct = float(s.get('changepercent', 0) or 0)
                current = float(s.get('trade', 0) or 0)
                amount = float(s.get('turnover', 0) or 0)  # 万
                
                if current == 0:
                    continue
                
                stocks.append({
                    'code': code,
                    'name': s.get('name', '?'),
                    'current': current,
                    'change_pct': change_pct,
                    'amount': amount,
                })
            
            stocks.sort(key=lambda x: x['change_pct'], reverse=True)
            print(f"✅ 新浪财经涨幅榜：{len(stocks)}只 ({elapsed*1000:.0f}ms)")
            return stocks[:limit]
    except:
        pass
    
    return []


def _fetch_tencent(limit=100):
    """腾讯财经涨幅榜 (最后备用)"""
    try:
        sys.path.insert(0, '/home/admin/openclaw/workspace/skills/tencent-stock-rank')
        from tencent_stock_rank import get_realtime_rank
        
        start = time.time()
        stocks = get_realtime_rank(limit=limit)
        elapsed = time.time() - start
        
        print(f"✅ 腾讯涨幅榜：{len(stocks)}只 ({elapsed*1000:.0f}ms)")
        return stocks
    except:
        pass
    
    return []


class HighProbRecommender:
    """高确定性涨停股推荐器"""
    
    def __init__(self):
        self.exclude_codes = [
            '601318', '600036', '000001', '601166', '600030',
            '601398', '601288', '601988', '600585', '000333',
            '601088', '601857', '600900', '600519',
        ]
        self.holdings_codes = [h['code'] for h in HOLDINGS]
        self.watchlist_data = []  # 保存涨幅榜数据
    
    def fetch_realtime_watchlist(self):
        """实时获取观察池 = 持仓股 + 涨幅榜前 100"""
        candidates = []
        
        # 1. 优先加入持仓股
        if self.holdings_codes:
            print(f"🎯 持仓监控：{len(self.holdings_codes)}只 ({', '.join(self.holdings_codes)})")
            candidates.extend(self.holdings_codes)
        
        # 2. 从涨幅榜获取热门股
        top_gainers = fetch_top_gainers(limit=100)
        
        # 保存涨幅榜数据供 analyze_stock 使用
        self.watchlist_data = top_gainers
        
        for stock in top_gainers:
            code = stock['code']
            if code not in self.exclude_codes and code not in candidates:
                candidates.append(code)
        
        print(f"✅ 观察池：{len(candidates)}只 (持仓 + 涨幅榜)")
        return candidates
    
    def analyze_stock(self, code):
        """分析单只股票 - 潜伏主升浪策略"""
        d = None
        
        # 1. 先尝试用腾讯财经获取 (有成交额数据)
        try:
            sys.path.insert(0, '/home/admin/openclaw/workspace/skills/tencent-stock-rank')
            from tencent_stock_rank import get_single_stock
            
            d = get_single_stock(code)
        except:
            pass  # 腾讯失败，继续用新浪数据
        
        # 2. 如果腾讯没有/失败，从新浪涨幅榜数据里找
        if not d:
            for s in self.watchlist_data:
                if s.get('code') == code:
                    d = s
                    break
        
        # 3. 还是没有，跳过
        if not d:
            return None
        
        change_pct = float(d.get('change_pct', 0) or 0)
        amount = float(d.get('amount', 0) or 0)  # 单位：万
        current = float(d.get('current', 0) or 0)
        
        # 排除停牌
        if current == 0:
            return None
        
        # 只推荐沪深主板（排除创业板和科创板）
        if not is_main_board(code):
            return None
        
        # 评分 (简化版：只依赖涨幅和成交额)
        score = 0
        reasons = []
        
        # 涨幅评分 (核心指标) - 潜伏策略：主升浪优先
        if 9 <= change_pct <= 11:  # 涨停 (买不进，低分)
            score += 30
            reasons.append("⚠️ 已涨停")
        elif 7 <= change_pct < 9:  # 主升浪加速 (最佳买点！)
            score += 70
            reasons.append("🎯 主升浪")
        elif 5 <= change_pct < 7:  # 强势上涨 (次佳买点)
            score += 55
            reasons.append("强势上涨")
        elif 3 <= change_pct < 5:  # 温和上涨 (潜伏买点)
            score += 40
            reasons.append("温和上涨")
        elif change_pct > 0:
            score += 20
            reasons.append("小幅上涨")
        
        # 成交额评分 (重要指标)
        if amount > 500000:  # >50 亿
            score += 25
            reasons.append("成交爆表")
        elif amount > 100000:  # >10 亿
            score += 20
            reasons.append("成交活跃")
        elif amount > 50000:  # >5 亿
            score += 15
            reasons.append("成交尚可")
        elif amount > 20000:  # >2 亿
            score += 12
            reasons.append("成交良好")
        elif amount > 10000:  # >1 亿
            score += 10
            reasons.append("成交一般")
        elif amount > 5000:  # >5 千万
            score += 8
            reasons.append("成交偏小")
        
        # 持仓股加分
        if code in self.holdings_codes:
            score += 10
            reasons.append("🎯 持仓股")
        
        return {
            'code': code,
            'name': d.get('name', '?'),
            'current': current,
            'change_pct': change_pct,
            'amount': amount,
            'volume_ratio': 0,
            'turnover': 0,
            'score': score,
            'reasons': reasons
        }
    
    def recommend(self, min_score=60, top_n=5):
        """推荐股票"""
        watchlist = self.fetch_realtime_watchlist()
        
        # 并发获取数据 (10 线程)
        import concurrent.futures
        candidates = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_code = {executor.submit(self.analyze_stock, code): code for code in watchlist}
            for future in concurrent.futures.as_completed(future_to_code, timeout=60):
                try:
                    result = future.result()
                    if result:
                        candidates.append(result)
                except Exception as e:
                    pass
        
        # 排序
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # 筛选
        self.recommendations = [s for s in candidates if s['score'] >= min_score][:top_n]
        
        return self.recommendations
    
    def print_recommendations(self, min_score=65):
        """打印推荐"""
        print("=" * 75)
        print("🦞 高确定性涨停股推荐")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"标准：≥{min_score}分才推荐 (潜伏主升浪，涨停前介入)")
        print("=" * 75)
        print()
        
        if not self.recommendations:
            print("❌ 今日无高确定性机会")
            print()
            print("💡 建议：空仓等待，宁可空仓不做弱势")
        else:
            print(f"✅ 找到 {len(self.recommendations)} 只高确定性股票！\n")
            
            for i, s in enumerate(self.recommendations, 1):
                rating = "🟢🟢 强势" if s['score'] >= 85 else "🟢 关注" if s['score'] >= 75 else "🟡 观察"
                print(f"{i}. {s['code']} {s['name']} | 得分：{s['score']} | {s['change_pct']:+.1f}% | {rating}")
                print(f"   现价：¥{s['current']:.2f} | 成交：{s['amount']/10000:.2f}亿 | 量比：{s['volume_ratio']:.1f} | 换手：{s['turnover']:.1f}%")
                print(f"   理由：{', '.join(s['reasons'])}")
                if s['code'] in self.holdings_codes:
                    print(f"   🎯 持仓股 - 重点关注！")
                else:
                    print(f"   建议：可建仓 | 止损：-5% | 止盈：+10%")
                print()


def run_recommendation():
    """运行推荐"""
    recommender = HighProbRecommender()
    recommender.recommend(min_score=65, top_n=5)
    recommender.print_recommendations(min_score=65)


if __name__ == "__main__":
    total_start = time.time()
    
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
