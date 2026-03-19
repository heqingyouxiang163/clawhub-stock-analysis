#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能预判模块 - 提前获取用户可能查询的股票数据
用途：预判用户需求，提前缓存，实现秒回
"""

import json
import time
from datetime import datetime
from pathlib import Path

# 导入缓存模块
from 数据缓存 import cache, set_stock_cache, get_stock_cache


class SmartPrefetch:
    """智能预判预取类"""
    
    def __init__(self):
        """初始化"""
        self.workspace = Path.home() / "openclaw" / "workspace"
        self.memory_dir = self.workspace / "memory"
        
        # 优先级列表
        self.user_holdings = []  # 用户持仓 (最高优先级)
        self.watch_list = []     # 观察池 (中优先级)
        self.hot_stocks = []     # 热点股 (低优先级)
        
        # 加载配置
        self._load_user_holdings()
        self._load_watch_list()
    
    def _load_user_holdings(self):
        """加载用户持仓"""
        try:
            # 从 MEMORY.md 读取持仓
            memory_file = self.workspace / "MEMORY.md"
            if memory_file.exists():
                content = memory_file.read_text(encoding='utf-8')
                
                # 简单解析持仓表格
                import re
                pattern = r'\| (\w+) \| (\d+)\.\d+ 元 \| (\d+\.\d+)% \|'
                matches = re.findall(pattern, content)
                
                self.user_holdings = [code for name, code, pct in matches]
                print(f"✅ 加载用户持仓：{len(self.user_holdings)}只")
            else:
                print("⚠️ MEMORY.md 不存在，使用默认持仓")
                self.user_holdings = ["002828", "002342"]  # 贝肯能源、巨力索具
        except Exception as e:
            print(f"❌ 加载持仓失败：{e}")
            self.user_holdings = ["002828", "002342"]
    
    def _load_watch_list(self):
        """加载观察池"""
        try:
            # 从策略库读取观察池
            watch_file = self.memory_dir / "策略库" / "观察池.md"
            if watch_file.exists():
                content = watch_file.read_text(encoding='utf-8')
                
                # 解析股票代码
                import re
                codes = re.findall(r'\b(\d{6})\b', content)
                self.watch_list = list(set(codes))[:20]  # 最多 20 只
                print(f"✅ 加载观察池：{len(self.watch_list)}只")
            else:
                self.watch_list = []
        except Exception as e:
            print(f"❌ 加载观察池失败：{e}")
            self.watch_list = []
    
    def load_hot_stocks(self):
        """加载热点股"""
        try:
            # 从涨停形态库读取今日涨停股
            today = datetime.now().strftime("%Y-%m-%d")
            hot_file = self.memory_dir / "涨停形态库" / f"{today}.md"
            
            if hot_file.exists():
                content = hot_file.read_text(encoding='utf-8')
                
                # 解析股票代码
                import re
                codes = re.findall(r'\b(\d{6})\b', content)
                self.hot_stocks = list(set(codes))[:30]  # 最多 30 只
                print(f"✅ 加载热点股：{len(self.hot_stocks)}只")
            else:
                self.hot_stocks = []
        except Exception as e:
            print(f"❌ 加载热点股失败：{e}")
            self.hot_stocks = []
    
    def get_priority_codes(self):
        """获取优先级股票代码列表"""
        # 优先级：持仓 > 观察池 > 热点
        all_codes = self.user_holdings + self.watch_list + self.hot_stocks
        
        # 去重
        seen = set()
        unique_codes = []
        for code in all_codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)
        
        return unique_codes
    
    def prefetch(self, fetch_func=None):
        """预取数据"""
        print(f"🔄 开始智能预判预取...")
        start_time = time.time()
        
        codes = self.get_priority_codes()
        print(f"📋 预取股票列表：{len(codes)}只")
        
        success_count = 0
        fail_count = 0
        
        for i, code in enumerate(codes, 1):
            try:
                # 检查缓存是否已存在
                cached = get_stock_cache(code)
                if cached:
                    print(f"  [{i}/{len(codes)}] {code} ✅ 已有缓存")
                    success_count += 1
                    continue
                
                # 调用获取函数
                if fetch_func:
                    data = fetch_func(code)
                    if data:
                        set_stock_cache(code, data, ttl=60)
                        print(f"  [{i}/{len(codes)}] {code} ✅ 已缓存")
                        success_count += 1
                    else:
                        print(f"  [{i}/{len(codes)}] {code} ❌ 获取失败")
                        fail_count += 1
                else:
                    # 无获取函数，仅标记
                    print(f"  [{i}/{len(codes)}] {code} ⏳ 待获取")
                    success_count += 1
                    
            except Exception as e:
                print(f"  [{i}/{len(codes)}] {code} ❌ 异常：{e}")
                fail_count += 1
        
        elapsed = time.time() - start_time
        print(f"\n✅ 预取完成：成功{success_count}只，失败{fail_count}只，耗时{elapsed:.1f}秒")
        
        return {
            'success': success_count,
            'fail': fail_count,
            'elapsed': elapsed
        }
    
    def get_user_holdings_data(self):
        """获取用户持仓数据 (带缓存)"""
        holdings_data = []
        
        for code in self.user_holdings:
            cached = get_stock_cache(code)
            if cached:
                holdings_data.append({
                    'code': code,
                    'data': cached,
                    'from_cache': True
                })
            else:
                holdings_data.append({
                    'code': code,
                    'data': None,
                    'from_cache': False
                })
        
        return holdings_data
    
    def get_stats(self):
        """获取统计信息"""
        return {
            'user_holdings': len(self.user_holdings),
            'watch_list': len(self.watch_list),
            'hot_stocks': len(self.hot_stocks),
            'total_codes': len(self.get_priority_codes())
        }


# 全局实例
prefetcher = SmartPrefetch()


# 便捷函数
def run_prefetch(fetch_func=None):
    """运行预取"""
    return prefetcher.prefetch(fetch_func)


def get_holdings_data():
    """获取持仓数据"""
    return prefetcher.get_user_holdings_data()


def get_prefetch_stats():
    """获取预取统计"""
    return prefetcher.get_stats()


# 命令行测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 50)
    print("🦞 智能预判模块测试")
    print("=" * 50)
    
    # 加载热点股
    prefetcher.load_hot_stocks()
    
    # 显示统计
    stats = get_prefetch_stats()
    print(f"\n📊 预取统计:")
    print(f"  用户持仓：{stats['user_holdings']}只")
    print(f"  观察池：{stats['watch_list']}只")
    print(f"  热点股：{stats['hot_stocks']}只")
    print(f"  总计：{stats['total_codes']}只")
    
    # 测试预取 (不实际获取数据)
    print(f"\n🔄 测试预取...")
    run_prefetch(fetch_func=None)
