#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多源并行获取模块 - 同时从多个数据源获取，取最快结果
用途：提升数据获取速度，自动故障转移
"""

import asyncio
import aiohttp
import time
from datetime import datetime


class MultiSourceFetcher:
    """多源数据获取类"""
    
    def __init__(self):
        """初始化"""
        # 数据源配置 (已验证可用)
        self.sources = {
            'sina': {
                'url': 'http://hq.sinajs.cn/list={market}{code}',
                'timeout': 5,
                'priority': 1,
                'headers': {
                    'Referer': 'https://finance.sina.com.cn/',
                    'User-Agent': 'Mozilla/5.0'
                }
            },
            'mcp': {
                'url': 'http://127.0.0.1:8080/stock/{code}',
                'timeout': 10,
                'priority': 2
            },
            'akshare': {
                'url': 'http://127.0.0.1:8081/stock/{code}',
                'timeout': 60,
                'priority': 3
            }
        }
        
        # 缓存
        self.cache = {}
        self.cache_ttl = 60  # 60 秒
    
    def _get_market(self, code):
        """根据股票代码获取市场标识"""
        if code.startswith('6'):
            return 'sh'
        elif code.startswith('0') or code.startswith('3'):
            return 'sz'
        elif code.startswith('HK'):
            return 'hk'
        else:
            return 'sz'  # 默认
    
    async def _fetch_source(self, session, source_name, code):
        """从单个数据源获取"""
        source = self.sources[source_name]
        market = self._get_market(code)
        
        # 替换 URL 中的变量
        url = source['url'].format(code=code, market=market)
        
        try:
            start = time.time()
            async with session.get(url, timeout=source['timeout']) as response:
                if response.status == 200:
                    data = await response.text()
                    elapsed = time.time() - start
                    
                    return {
                        'success': True,
                        'source': source_name,
                        'data': data,
                        'elapsed': elapsed
                    }
                else:
                    return {
                        'success': False,
                        'source': source_name,
                        'error': f'HTTP {response.status}',
                        'elapsed': 0
                    }
        except asyncio.TimeoutError:
            return {
                'success': False,
                'source': source_name,
                'error': 'Timeout',
                'elapsed': source['timeout']
            }
        except Exception as e:
            return {
                'success': False,
                'source': source_name,
                'error': str(e),
                'elapsed': 0
            }
    
    async def fetch_fastest(self, code):
        """并行获取，返回最快结果"""
        # 检查缓存
        cache_key = f"stock:{code}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return {
                    'success': True,
                    'source': 'cache',
                    'data': cached_data,
                    'elapsed': 0,
                    'from_cache': True
                }
        
        # 创建 HTTP 会话
        async with aiohttp.ClientSession() as session:
            # 创建所有数据源的任务
            tasks = []
            for source_name in sorted(self.sources.keys(), key=lambda x: self.sources[x]['priority']):
                tasks.append(self._fetch_source(session, source_name, code))
            
            # 等待第一个完成
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=10
            )
            
            # 取消未完成的任务
            for task in pending:
                task.cancel()
            
            # 返回第一个成功的结果
            for task in done:
                try:
                    result = task.result()
                    if result['success']:
                        # 保存到缓存
                        self.cache[cache_key] = (time.time(), result['data'])
                        
                        return {
                            'success': True,
                            'source': result['source'],
                            'data': result['data'],
                            'elapsed': result['elapsed'],
                            'from_cache': False
                        }
                except Exception as e:
                    continue
            
            # 所有任务都失败
            return {
                'success': False,
                'source': 'all',
                'error': 'All sources failed',
                'elapsed': 0
            }
    
    def fetch_sync(self, code):
        """同步接口"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.fetch_fastest(code))
        finally:
            loop.close()
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
    
    def get_stats(self):
        """获取统计"""
        return {
            'cache_size': len(self.cache),
            'sources': len(self.sources),
            'sources_list': list(self.sources.keys())
        }


# 全局实例
fetcher = MultiSourceFetcher()


# 便捷函数
def fetch_stock_fast(code):
    """快速获取股票数据"""
    return fetcher.fetch_sync(code)


def get_fetcher_stats():
    """获取统计"""
    return fetcher.get_stats()


# 命令行测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 50)
    print("🦞 多源获取模块测试")
    print("=" * 50)
    
    # 显示统计
    stats = get_fetcher_stats()
    print(f"\n📊 数据源统计:")
    print(f"  数据源数量：{stats['sources']}")
    print(f"  数据源列表：{', '.join(stats['sources_list'])}")
    print(f"  缓存大小：{stats['cache_size']}")
    
    # 测试 (需要实际 API)
    print(f"\n⚠️  测试需要实际 API 支持，跳过...")

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"
✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"
✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"
✅ **总耗时**: {total_elapsed/60:.1f}分钟")
