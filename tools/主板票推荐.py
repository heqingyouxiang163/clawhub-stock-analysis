#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主板票推荐模块 - 只推荐沪深主板涨停概率大的股票
用途：过滤创业板/科创板，只推荐主板票
"""

from 主板票筛选 import is_main_board, filter_main_board
from 数据缓存 import get_stock_cache, set_stock_cache
from 快速使用示例 import get_stock_price_sina
import time


class MainBoardRecommender:
    """主板票推荐器"""
    
    def __init__(self):
        """初始化"""
        self.watch_list = []  # 观察池
        self.hot_stocks = []  # 热点股
        self.recommendations = []  # 推荐列表
    
    def load_watch_list(self, file_path=None):
        """加载观察池"""
        # 从文件加载或手动添加
        default_watch = [
            "600519",  # 贵州茅台
            "000858",  # 五粮液
            "601318",  # 中国平安
        ]
        
        self.watch_list = default_watch
        print(f"✅ 加载观察池：{len(self.watch_list)}只主板票")
    
    def filter_limit_up_stocks(self, limit_up_list):
        """
        从涨停股列表中筛选主板票
        
        Args:
            limit_up_list: 涨停股列表
        
        Returns:
            list: 主板涨停股
        """
        return filter_main_board(limit_up_list)
    
    def calculate_score(self, stock_data):
        """
        计算涨停概率得分
        
        Args:
            stock_data: 股票数据 dict
        
        Returns:
            float: 得分 (0-100)
        """
        score = 0
        
        # 换手率得分 (5-15% 最佳)
        turnover = stock_data.get('turnover', 0)
        if 5 <= turnover <= 15:
            score += 30
        elif 3 <= turnover <= 20:
            score += 20
        else:
            score += 10
        
        # 量比得分 (>2 最佳)
        volume_ratio = stock_data.get('volume_ratio', 0)
        if volume_ratio > 3:
            score += 30
        elif volume_ratio > 2:
            score += 20
        elif volume_ratio > 1.5:
            score += 10
        
        # 封板时间得分 (越早越好)
        close_time = stock_data.get('close_time', '150000')
        if close_time < '100000':
            score += 30
        elif close_time < '113000':
            score += 20
        elif close_time < '140000':
            score += 10
        
        # 板块效应得分
        block_effect = stock_data.get('block_effect', 0)
        if block_effect >= 3:
            score += 10
        elif block_effect >= 2:
            score += 5
        
        return min(score, 100)
    
    def recommend(self, limit_up_stocks, top_n=5):
        """
        推荐主板票
        
        Args:
            limit_up_stocks: 涨停股列表
            top_n: 推荐数量
        
        Returns:
            list: 推荐股票 (按得分排序)
        """
        print(f"🔍 从 {len(limit_up_stocks)} 只涨停股中筛选主板票...")
        
        # 1. 筛选主板票
        main_board_stocks = self.filter_limit_up_stocks(limit_up_stocks)
        print(f"✅ 筛选出 {len(main_board_stocks)} 只主板票")
        
        # 2. 计算得分
        scored_stocks = []
        for stock in main_board_stocks:
            score = self.calculate_score(stock)
            stock['score'] = score
            scored_stocks.append(stock)
        
        # 3. 按得分排序
        scored_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 4. 返回 Top N
        self.recommendations = scored_stocks[:top_n]
        
        return self.recommendations
    
    def print_recommendations(self):
        """打印推荐列表"""
        if not self.recommendations:
            print("⚠️ 暂无推荐")
            return
        
        print("\n" + "=" * 60)
        print("🦞 主板票推荐 (涨停概率大)")
        print("=" * 60)
        
        for i, stock in enumerate(self.recommendations, 1):
            code = stock.get('code', 'N/A')
            name = stock.get('name', 'N/A')
            score = stock.get('score', 0)
            turnover = stock.get('turnover', 0)
            close_time = stock.get('close_time', 'N/A')
            
            print(f"\n{i}. {code} {name}")
            print(f"   得分：{score}/100")
            print(f"   换手率：{turnover}%")
            print(f"   封板时间：{close_time}")
        
        print("\n" + "=" * 60)
        print("⚠️ 风险提示：仅供参考，不构成投资建议")
        print("=" * 60)


# 全局实例
recommender = MainBoardRecommender()


# 便捷函数
def get_main_board_recommendations(limit_up_stocks, top_n=5):
    """获取主板票推荐"""
    return recommender.recommend(limit_up_stocks, top_n)


def print_recommendations():
    """打印推荐"""
    recommender.print_recommendations()


# 测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 50)
    print("🦞 主板票推荐测试")
    print("=" * 50)
    
    # 模拟涨停股数据
    test_stocks = [
        {'code': '600519', 'name': '贵州茅台', 'turnover': 8.5, 'close_time': '093500', 'block_effect': 3},
        {'code': '300750', 'name': '宁德时代', 'turnover': 12.3, 'close_time': '094000', 'block_effect': 5},
        {'code': '000858', 'name': '五粮液', 'turnover': 6.8, 'close_time': '095000', 'block_effect': 2},
        {'code': '688981', 'name': '中芯国际', 'turnover': 15.2, 'close_time': '100000', 'block_effect': 4},
        {'code': '002594', 'name': '比亚迪', 'turnover': 9.5, 'close_time': '101500', 'block_effect': 3},
        {'code': '601318', 'name': '中国平安', 'turnover': 7.2, 'close_time': '103000', 'block_effect': 2},
    ]
    
    # 获取推荐
    recs = get_main_board_recommendations(test_stocks, top_n=3)
    
    # 打印推荐
    print_recommendations()
