#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
涨停潜力股推荐 v3 - 动态观察池版
用途：自动更新观察池，避免重复推荐
"""

import time
from datetime import datetime
from 主板票筛选 import is_main_board
from 多数据源修复版 import get_realtime_data


class LimitUpRecommenderV3:
    """涨停潜力股推荐器 v3 (动态观察池版)"""
    
    def __init__(self):
        """初始化"""
        # 基础观察池 (昨日涨停股)
        self.base_watch_codes = [
            # 3 连板
            '600370',  # 三房巷
            '000890',  # 法尔胜
            
            # 2 连板
            '600227',  # 赤天化
            '600683',  # 京投发展
            '603929',  # 亚翔集成
            '603248',  # 锡华科技
            
            # 昨日首板
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
        
        # 动态观察池 (会更新)
        self.dynamic_watch_codes = list(self.base_watch_codes)
        
        # 已推荐记录 (避免重复)
        self.recommended_history = []
        
        # 已涨停股票 (不再推荐)
        self.limit_up_stocks = []
        
        self.recommendations = []
    
    def calculate_score(self, data):
        """计算涨停概率得分"""
        score = 0
        
        # 涨幅得分
        change_pct = data.get('change_pct', 0)
        if 3 <= change_pct <= 7:
            score += 40
        elif 1 <= change_pct <= 3:
            score += 30
        elif 7 <= change_pct <= 9.5:
            score += 50
        elif change_pct >= 9.8:
            score = 100  # 已涨停
        elif change_pct > 0:
            score += 10
        
        # 换手率得分
        turnover = data.get('turnover', 0)
        if turnover:
            if 5 <= turnover <= 15:
                score += 30
            elif 3 <= turnover <= 20:
                score += 20
            elif turnover < 5:
                score += 15
        else:
            amount = data.get('amount', 0)
            if amount > 100000000:
                score += 20
        
        # 量比得分
        volume_ratio = data.get('volume_ratio', 0)
        if volume_ratio:
            if volume_ratio > 3:
                score += 20
            elif volume_ratio > 2:
                score += 15
            elif volume_ratio > 1.5:
                score += 10
        
        # 竞价涨幅得分
        open_pct = (data.get('open', 0) - data.get('pre_close', 0)) / data.get('pre_close', 1) * 100
        if 3 <= open_pct <= 5:
            score += 10
        elif 1 <= open_pct <= 3:
            score += 5
        elif 5 <= open_pct <= 7:
            score += 8
        
        return min(score, 100)
    
    def update_watch_pool(self):
        """更新观察池"""
        # 移除已涨停的股票 (避免重复推荐)
        new_pool = []
        for code in self.dynamic_watch_codes:
            if code not in self.limit_up_stocks:
                new_pool.append(code)
        
        self.dynamic_watch_codes = new_pool
        
        # 如果观察池股票太少，补充基础池
        if len(self.dynamic_watch_codes) < 10:
            self.dynamic_watch_codes = list(self.base_watch_codes)
            print(f"🔄 观察池已重置 (剩余股票太少)")
    
    def recommend(self, top_n=3, force_refresh=False):
        """生成推荐"""
        # 更新观察池
        self.update_watch_pool()
        
        print(f"🔍 扫描 {len(self.dynamic_watch_codes)} 只股票...")
        
        scored_stocks = []
        success_count = 0
        fail_count = 0
        
        for code in self.dynamic_watch_codes:
            # 只筛选主板票
            if not is_main_board(code):
                continue
            
            # 获取实时数据
            result = get_realtime_data(code)
            
            if result.get('success'):
                data = result['data']
                
                # 检查是否已涨停 (记录但不推荐)
                if data.get('change_pct', 0) >= 9.8:
                    if code not in self.limit_up_stocks:
                        self.limit_up_stocks.append(code)
                        print(f"  📌 {code} 已涨停，加入观察列表")
                
                # 计算得分
                data['score'] = self.calculate_score(data)
                data['time'] = datetime.now().strftime('%H:%M:%S')
                data['source'] = result.get('source_name', 'Unknown')
                data['elapsed'] = result.get('elapsed', 0)
                scored_stocks.append(data)
                success_count += 1
            else:
                fail_count += 1
        
        # 按得分排序
        scored_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 排除已涨停股票 (盘中买不进去)
        non_limit_up_stocks = []
        for stock in scored_stocks:
            if stock.get('change_pct', 0) < 9.5:  # 涨幅<9.5% 才有买入机会
                non_limit_up_stocks.append(stock)
            else:
                print(f"  📌 {stock['code']} 已涨停/接近涨停，排除")
        
        # 过滤已推荐的股票 (除非强制刷新)
        if not force_refresh:
            filtered_stocks = []
            for stock in non_limit_up_stocks:
                if stock['code'] not in self.recommended_history[-10:]:  # 最近 10 次不重复
                    filtered_stocks.append(stock)
            non_limit_up_stocks = filtered_stocks
        
        # 返回 Top N
        self.recommendations = non_limit_up_stocks[:top_n]
        
        # 记录推荐历史
        for stock in self.recommendations:
            self.recommended_history.append(stock['code'])
        
        print(f"✅ 成功：{success_count}只 | 失败：{fail_count}只")
        print(f"📌 已涨停：{len(self.limit_up_stocks)}只")
        
        return self.recommendations
    
    def print_recommendations(self):
        """打印推荐"""
        if not self.recommendations:
            print("⚠️ 暂无推荐 (可能都已涨停)")
            return
        
        print("\n" + "=" * 75)
        print("🦞 涨停潜力股推荐 v3 (动态观察池)")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 75)
        
        for i, stock in enumerate(self.recommendations, 1):
            print(f"\n{i}. {stock['code']} {stock['name']}")
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
    recommender = LimitUpRecommenderV3()
    recs = recommender.recommend(top_n=3, force_refresh=False)
    recommender.print_recommendations()
    return recs


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--loop':
        # 循环模式
        print("🦞 启动定时推荐模式 (每 5 分钟)")
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
