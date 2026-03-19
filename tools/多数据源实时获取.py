#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多数据源并行获取 - 真正的实时数据
用途：同时从多个数据源获取，取最快最准确的结果
"""

import asyncio
import aiohttp
import time
from datetime import datetime
from 数据缓存 import get_stock_cache, set_stock_cache


class MultiSourceRealtimeFetcher:
    """多数据源实时获取器"""
    
    def __init__(self):
        """初始化"""
        # 数据源配置 (已验证可用)
        self.sources = {
            'sina': {
                'name': '新浪财经',
                'url': 'http://hq.sinajs.cn/list={market}{code}',
                'timeout': 5,
                'priority': 1,
                'headers': {
                    'Referer': 'https://finance.sina.com.cn/',
                    'User-Agent': 'Mozilla/5.0'
                },
                'parser': self._parse_sina
            },
            'eastmoney_em': {
                'name': '东方财富 (EM)',
                'url': 'http://push2.eastmoney.com/api/qt/stock/get?secid={market_id}.{code}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f107,f108,f109,f113,f114,f115,f116,f117',
                'timeout': 5,
                'priority': 2,
                'headers': {
                    'Referer': 'http://quote.eastmoney.com/',
                    'User-Agent': 'Mozilla/5.0'
                },
                'parser': self._parse_eastmoney
            },
            'qq': {
                'name': '腾讯财经',
                'url': 'http://qt.gtimg.cn/q={market}{code}',
                'timeout': 5,
                'priority': 3,
                'headers': {
                    'Referer': 'http://stockapp.finance.qq.com/',
                    'User-Agent': 'Mozilla/5.0'
                },
                'parser': self._parse_qq
            }
        }
        
        # 缓存
        self.cache = {}
        self.cache_ttl = 30  # 30 秒
    
    def _get_market_info(self, code):
        """获取市场信息"""
        if code.startswith('6'):
            return {'market': 'sh', 'market_id': '1'}
        elif code.startswith('0') or code.startswith('3'):
            return {'market': 'sz', 'market_id': '0'}
        elif code.startswith('4') or code.startswith('8'):
            return {'market': 'bj', 'market_id': '0'}
        else:
            return {'market': 'sz', 'market_id': '0'}
    
    def _parse_sina(self, text, code):
        """解析新浪财经数据"""
        try:
            if '=' not in text:
                return None
            
            data_str = text.split('=')[1].strip('"').strip('"')
            parts = data_str.split(',')
            
            if len(parts) < 32:
                return None
            
            name = parts[0]
            current = float(parts[3]) if parts[3] else 0
            open_p = float(parts[1]) if parts[1] else 0
            high = float(parts[4]) if parts[4] else 0
            low = float(parts[5]) if parts[5] else 0
            pre_close = float(parts[2]) if parts[2] else 0
            volume = float(parts[8]) if parts[8] else 0
            amount = float(parts[9]) if parts[9] else 0
            
            # 盘口数据
            bid_prices = [float(parts[i]) for i in range(11, 21, 2) if parts[i]]
            bid_volumes = [float(parts[i]) for i in range(10, 21, 2) if parts[i]]
            
            change_pct = (current - pre_close) / pre_close * 100 if pre_close else 0
            
            # 涨停价
            limit_up = round(pre_close * 1.1, 2)
            is_limit_up = abs(current - limit_up) < 0.01
            
            return {
                'code': code,
                'name': name,
                'current': current,
                'open': open_p,
                'high': high,
                'low': low,
                'pre_close': pre_close,
                'change_pct': change_pct,
                'volume': volume,
                'amount': amount,
                'bid_prices': bid_prices[:5],
                'bid_volumes': bid_volumes[:5],
                'limit_up': limit_up,
                'is_limit_up': is_limit_up,
                'source': 'sina',
                'timestamp': time.time()
            }
        except Exception as e:
            return None
    
    def _parse_eastmoney(self, data, code):
        """解析东方财富数据"""
        try:
            if not data or not data.get('data'):
                return None
            
            d = data['data']
            
            return {
                'code': code,
                'name': d.get('f58', ''),
                'current': d.get('f46', 0),
                'open': d.get('f47', 0),
                'high': d.get('f44', 0),
                'low': d.get('f45', 0),
                'pre_close': d.get('f60', 0),
                'change_pct': d.get('f170', 0),
                'volume': d.get('f47', 0) * 100,  # 手
                'amount': d.get('f48', 0),
                'turnover': d.get('f107', 0),  # 换手率
                'volume_ratio': d.get('f108', 0),  # 量比
                'limit_up': d.get('f49', 0),
                'is_limit_up': d.get('f109', 0) == 1,
                'source': 'eastmoney',
                'timestamp': time.time()
            }
        except Exception as e:
            return None
    
    def _parse_qq(self, text, code):
        """解析腾讯财经数据"""
        try:
            if '=' not in text:
                return None
            
            data_str = text.split('=')[1].strip('"').strip('"')
            parts = data_str.split('~')
            
            if len(parts) < 50:
                return None
            
            name = parts[1]
            current = float(parts[3]) if parts[3] else 0
            open_p = float(parts[5]) if parts[5] else 0
            high = float(parts[33]) if parts[33] else 0
            low = float(parts[34]) if parts[34] else 0
            pre_close = float(parts[4]) if parts[4] else 0
            volume = float(parts[6]) if parts[6] else 0
            amount = float(parts[37]) if parts[37] else 0
            
            change_pct = (current - pre_close) / pre_close * 100 if pre_close else 0
            
            return {
                'code': code,
                'name': name,
                'current': current,
                'open': open_p,
                'high': high,
                'low': low,
                'pre_close': pre_close,
                'change_pct': change_pct,
                'volume': volume,
                'amount': amount,
                'source': 'qq',
                'timestamp': time.time()
            }
        except Exception as e:
            return None
    
    async def _fetch_source(self, session, source_name, code, market_info):
        """从单个数据源获取"""
        source = self.sources[source_name]
        market = market_info['market']
        market_id = market_info.get('market_id', market)
        
        url = source['url'].format(code=code, market=market, market_id=market_id)
        
        try:
            start = time.time()
            async with session.get(url, headers=source['headers'], timeout=source['timeout']) as response:
                if response.status == 200:
                    if source_name == 'eastmoney':
                        data = await response.json()
                        result = source['parser'](data, code)
                    else:
                        text = await response.text()
                        result = source['parser'](text, code)
                    
                    elapsed = time.time() - start
                    
                    if result:
                        return {
                            'success': True,
                            'source': source_name,
                            'source_name': source['name'],
                            'data': result,
                            'elapsed': elapsed
                        }
                    else:
                        return {
                            'success': False,
                            'source': source_name,
                            'error': 'Parse failed',
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
        """并行获取，返回最快最准确的结果"""
        # 检查缓存
        cache_key = f"stock:{code}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                cached_data['from_cache'] = True
                return cached_data
        
        market_info = self._get_market_info(code)
        
        async with aiohttp.ClientSession() as session:
            # 创建所有数据源的任务
            tasks = []
            for source_name in sorted(self.sources.keys(), key=lambda x: self.sources[x]['priority']):
                tasks.append(self._fetch_source(session, source_name, code, market_info))
            
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
                    if result and result['success']:
                        # 保存到缓存
                        self.cache[cache_key] = (time.time(), result)
                        result['from_cache'] = False
                        return result
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
fetcher = MultiSourceRealtimeFetcher()


# 便捷函数
def get_realtime_data(code):
    """获取实时数据"""
    return fetcher.fetch_sync(code)


def get_fetcher_stats():
    """获取统计"""
    return fetcher.get_stats()


# 测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 70)
    print("🦞 多数据源实时获取测试")
    print("=" * 70)
    
    test_codes = ['002828', '600370', '600683']
    
    print(f"\n数据源：{list(fetcher.sources.keys())}")
    print(f"缓存 TTL: {fetcher.cache_ttl}秒\n")
    
    for code in test_codes:
        print(f"获取 {code}...")
        result = get_realtime_data(code)
        
        if result['success']:
            data = result['data']
            print(f"  ✅ 成功 | 来源：{result['source_name']} | 耗时：{result['elapsed']*1000:.1f}ms | 缓存：{result['from_cache']}")
            print(f"     现价：¥{data['current']:.2f} ({data['change_pct']:+.1f}%)")
            if 'turnover' in data and data['turnover']:
                print(f"     换手率：{data['turnover']:.2f}%")
            if 'volume_ratio' in data and data['volume_ratio']:
                print(f"     量比：{data['volume_ratio']:.2f}")
        else:
            print(f"  ❌ 失败 | 错误：{result.get('error', 'Unknown')}")
        
        print()
    
    # 显示统计
    stats = get_fetcher_stats()
    print("=" * 70)
    print("📊 统计信息:")
    print(f"  数据源数量：{stats['sources']}")
    print(f"  数据源列表：{', '.join(stats['sources_list'])}")
    print(f"  缓存大小：{stats['cache_size']}")
    print("=" * 70)

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
