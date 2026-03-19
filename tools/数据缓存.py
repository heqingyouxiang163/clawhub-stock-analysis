#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据缓存模块 - 基于 Redis
用途：缓存股票数据，减少 API 调用，提升响应速度
"""

import redis
import json
import time
from datetime import datetime

class StockDataCache:
    """股票数据缓存类"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        """初始化 Redis 连接"""
        try:
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis.ping()
            print("✅ Redis 连接成功")
        except Exception as e:
            print(f"❌ Redis 连接失败：{e}")
            print("⚠️ 降级为内存缓存")
            self.redis = None
            self.memory_cache = {}
    
    def get(self, key):
        """获取缓存数据"""
        try:
            if self.redis:
                data = self.redis.get(key)
                return json.loads(data) if data else None
            else:
                # 内存缓存降级
                if key in self.memory_cache:
                    value, expire_at = self.memory_cache[key]
                    if time.time() < expire_at:
                        return value
                    else:
                        del self.memory_cache[key]
                return None
        except Exception as e:
            print(f"❌ 获取缓存失败：{e}")
            return None
    
    def set(self, key, value, ttl=60):
        """设置缓存数据"""
        try:
            if self.redis:
                self.redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            else:
                # 内存缓存降级
                self.memory_cache[key] = (value, time.time() + ttl)
            return True
        except Exception as e:
            print(f"❌ 设置缓存失败：{e}")
            return False
    
    def delete(self, key):
        """删除缓存"""
        try:
            if self.redis:
                self.redis.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            return True
        except Exception as e:
            print(f"❌ 删除缓存失败：{e}")
            return False
    
    def clear_pattern(self, pattern):
        """批量删除匹配模式的缓存"""
        try:
            if self.redis:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    return len(keys)
            return 0
        except Exception as e:
            print(f"❌ 批量删除失败：{e}")
            return 0
    
    def get_stats(self):
        """获取缓存统计信息"""
        try:
            if self.redis:
                info = self.redis.info('stats')
                return {
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'hit_rate': self._calc_hit_rate(info)
                }
            else:
                return {'hits': 0, 'misses': 0, 'hit_rate': '0%'}
        except Exception as e:
            return {'error': str(e)}
    
    def _calc_hit_rate(self, info):
        """计算命中率"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        if total == 0:
            return '0%'
        return f"{hits/total*100:.1f}%"
    
    def test(self):
        """测试缓存功能"""
        print("🧪 测试缓存模块...")
        
        # 测试写入
        test_key = "test:stock:000001"
        test_value = {"code": "000001", "price": 10.5, "time": datetime.now().isoformat()}
        self.set(test_key, test_value, ttl=10)
        
        # 测试读取
        cached = self.get(test_key)
        if cached and cached['code'] == '000001':
            print("✅ 缓存测试通过")
            return True
        else:
            print("❌ 缓存测试失败")
            return False


# 全局缓存实例
cache = StockDataCache()


# 便捷函数
def get_stock_cache(code):
    """获取股票缓存"""
    return cache.get(f"stock:{code}")


def set_stock_cache(code, data, ttl=60):
    """设置股票缓存"""
    return cache.set(f"stock:{code}", data, ttl)


def get_cache_stats():
    """获取缓存统计"""
    return cache.get_stats()


def test_cache():
    """测试缓存"""
    return cache.test()


# 命令行测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 50)
    print("🦞 数据缓存模块测试")
    print("=" * 50)
    
    # 测试
    if test_cache():
        print("\n✅ 模块正常，可以使用")
        
        # 显示统计
        stats = get_cache_stats()
        print(f"\n📊 缓存统计：{stats}")
    else:
        print("\n❌ 模块异常，请检查 Redis 服务")

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
