#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据获取优化集成脚本
用途：整合缓存、预判、多源获取，实现秒级响应
"""

import time
from datetime import datetime
from pathlib import Path

# 导入模块
from 数据缓存 import cache, set_stock_cache, get_stock_cache
from 智能预判 import SmartPrefetch
from 多源获取 import MultiSourceFetcher


class OptimizedDataSystem:
    """优化数据系统"""
    
    def __init__(self):
        """初始化"""
        self.prefetcher = SmartPrefetch()
        self.multi_fetcher = MultiSourceFetcher()
        
        # 统计
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_requests': 0,
            'avg_response_time': 0
        }
    
    def get_stock_data(self, code, use_cache=True):
        """获取股票数据 (优化版)"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        # 1. 检查缓存
        if use_cache:
            cached = get_stock_cache(code)
            if cached:
                self.stats['cache_hits'] += 1
                elapsed = time.time() - start_time
                self._update_avg_time(elapsed)
                
                return {
                    'success': True,
                    'code': code,
                    'data': cached,
                    'source': 'cache',
                    'elapsed': elapsed,
                    'from_cache': True
                }
        
        self.stats['cache_misses'] += 1
        
        # 2. 多源并行获取
        result = self.multi_fetcher.fetch_sync(code)
        
        elapsed = time.time() - start_time
        self._update_avg_time(elapsed)
        
        if result['success']:
            # 保存到缓存
            set_stock_cache(code, result['data'], ttl=60)
            
            return {
                'success': True,
                'code': code,
                'data': result['data'],
                'source': result['source'],
                'elapsed': elapsed,
                'from_cache': False
            }
        else:
            return {
                'success': False,
                'code': code,
                'error': result.get('error', 'Unknown'),
                'elapsed': elapsed
            }
    
    def _update_avg_time(self, elapsed):
        """更新平均响应时间"""
        total = self.stats['total_requests']
        avg = self.stats['avg_response_time']
        self.stats['avg_response_time'] = (avg * (total - 1) + elapsed) / total
    
    def prefetch_holdings(self):
        """预取持仓数据"""
        print("🔄 预取持仓数据...")
        
        codes = self.prefetcher.user_holdings
        print(f"📋 持仓股票：{len(codes)}只")
        
        for code in codes:
            # 预取但不等待
            self.multi_fetcher.fetch_sync(code)
        
        print("✅ 持仓预取完成")
    
    def get_stats(self):
        """获取系统统计"""
        cache_stats = cache.get_stats()
        fetcher_stats = self.multi_fetcher.get_stats()
        prefetch_stats = self.prefetcher.get_stats()
        
        return {
            'requests': self.stats,
            'cache': cache_stats,
            'fetcher': fetcher_stats,
            'prefetch': prefetch_stats
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        
        print("\n" + "=" * 50)
        print("📊 系统统计")
        print("=" * 50)
        
        print(f"\n📈 请求统计:")
        print(f"  总请求：{stats['requests']['total_requests']}")
        print(f"  缓存命中：{stats['requests']['cache_hits']}")
        print(f"  缓存未命中：{stats['requests']['cache_misses']}")
        print(f"  命中率：{stats['cache'].get('hit_rate', 'N/A')}")
        print(f"  平均响应：{stats['requests']['avg_response_time']*1000:.1f}ms")
        
        print(f"\n💾 缓存统计:")
        print(f"  缓存大小：{stats['fetcher']['cache_size']}")
        
        print(f"\n🎯 预取统计:")
        print(f"  用户持仓：{stats['prefetch']['user_holdings']}只")
        print(f"  观察池：{stats['prefetch']['watch_list']}只")
        print(f"  热点股：{stats['prefetch']['hot_stocks']}只")
        
        print("\n" + "=" * 50)


# 全局实例
system = OptimizedDataSystem()


# 便捷函数
def get_optimized_stock_data(code, use_cache=True):
    """获取优化股票数据"""
    return system.get_stock_data(code, use_cache)


def prefetch_now():
    """立即预取"""
    return system.prefetch_holdings()


def show_stats():
    """显示统计"""
    return system.print_stats()


# 命令行测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 50)
    print("🦞 数据优化集成系统")
    print("=" * 50)
    
    # 预取持仓
    prefetch_now()
    
    # 测试获取
    print("\n🧪 测试获取股票数据...")
    test_codes = ["002828", "002342"]
    
    for code in test_codes:
        print(f"\n获取 {code}...")
        result = get_optimized_stock_data(code)
        
        if result['success']:
            print(f"  ✅ 成功 | 来源：{result['source']} | 耗时：{result['elapsed']*1000:.1f}ms | 缓存：{result['from_cache']}")
        else:
            print(f"  ❌ 失败 | 错误：{result.get('error', 'Unknown')}")
    
    # 显示统计
    show_stats()
