#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 数据缓存管理器

功能:
- 自动缓存日线数据、分时数据、涨停历史等
- 减少重复数据请求，节省 Token
- 提供统一的数据读取接口

最后更新：2026-03-28
"""

import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = None):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录，默认使用 data_cache/
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_cache')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存元数据
        self.metadata_file = self.cache_dir / 'metadata.json'
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'files': {}, 'last_update': None}
    
    def _save_metadata(self):
        """保存元数据"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def save(self, key: str, data: Any, expire_hours: int = 24) -> str:
        """保存数据到缓存
        
        Args:
            key: 缓存键 (如 'daily_quotes_20260328')
            data: 要缓存的数据
            expire_hours: 过期时间 (小时)
        
        Returns:
            缓存文件路径
        """
        cache_file = self.cache_dir / f'{key}.pkl'
        expire_time = datetime.now() + timedelta(hours=expire_hours)
        
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'data': data,
                'created_at': datetime.now().isoformat(),
                'expires_at': expire_time.isoformat()
            }, f)
        
        # 更新元数据
        self.metadata['files'][key] = {
            'file': str(cache_file),
            'created_at': datetime.now().isoformat(),
            'expires_at': expire_time.isoformat(),
            'size_bytes': cache_file.stat().st_size
        }
        self.metadata['last_update'] = datetime.now().isoformat()
        self._save_metadata()
        
        return str(cache_file)
    
    def load(self, key: str) -> Optional[Any]:
        """从缓存加载数据
        
        Args:
            key: 缓存键
        
        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        if key not in self.metadata['files']:
            return None
        
        cache_file = Path(self.metadata['files'][key]['file'])
        if not cache_file.exists():
            return None
        
        # 检查是否过期
        expires_at = datetime.fromisoformat(self.metadata['files'][key]['expires_at'])
        if datetime.now() > expires_at:
            print(f"⚠️ 缓存已过期：{key}")
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)
                print(f"✅ 缓存命中：{key}")
                return cached['data']
        except Exception as e:
            print(f"❌ 读取缓存失败：{e}")
            return None
    
    def is_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.metadata['files']:
            return False
        
        expires_at = datetime.fromisoformat(self.metadata['files'][key]['expires_at'])
        return datetime.now() <= expires_at
    
    def clear_expired(self) -> int:
        """清理过期缓存文件
        
        Returns:
            清理的文件数量
        """
        cleared = 0
        keys_to_remove = []
        
        for key, info in self.metadata['files'].items():
            expires_at = datetime.fromisoformat(info['expires_at'])
            if datetime.now() > expires_at:
                cache_file = Path(info['file'])
                if cache_file.exists():
                    cache_file.unlink()
                    cleared += 1
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.metadata['files'][key]
        
        self._save_metadata()
        return cleared
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_size = sum(info.get('size_bytes', 0) for info in self.metadata['files'].values())
        return {
            'total_files': len(self.metadata['files']),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'last_update': self.metadata.get('last_update', 'Never')
        }


# 全局缓存实例
cache = DataCache()


# ========== 便捷函数 ==========

def cache_daily_quotes(date: str = None) -> Dict:
    """获取日线数据缓存"""
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    key = f'daily_quotes_{date}'
    return cache.load(key)


def cache_intraday_data(date: str = None) -> Dict:
    """获取分时数据缓存"""
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    key = f'intraday_{date}'
    return cache.load(key)


def cache_limit_up_history() -> List:
    """获取涨停历史缓存"""
    return cache.load('limit_up_history')


def save_daily_quotes(data: Dict, date: str = None):
    """保存日线数据到缓存"""
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    key = f'daily_quotes_{date}'
    cache.save(key, data, expire_hours=48)  # 保留 48 小时
    print(f"✅ 日线数据已缓存：{date}")


def save_intraday_data(data: Dict, date: str = None):
    """保存分时数据到缓存"""
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    key = f'intraday_{date}'
    cache.save(key, data, expire_hours=12)  # 保留 12 小时 (仅交易时段有用)
    print(f"✅ 分时数据已缓存：{date}")


def save_limit_up_history(data: List):
    """保存涨停历史到缓存"""
    cache.save('limit_up_history', data, expire_hours=168)  # 保留 7 天
    print(f"✅ 涨停历史已缓存")


if __name__ == '__main__':
    # 测试缓存功能
    print("🦞 数据缓存管理器测试")
    print("=" * 50)
    
    # 显示统计
    stats = cache.get_stats()
    print(f"缓存文件数：{stats['total_files']}")
    print(f"缓存大小：{stats['total_size_mb']} MB")
    print(f"最后更新：{stats['last_update']}")
    
    # 清理过期缓存
    cleared = cache.clear_expired()
    if cleared > 0:
        print(f"清理了 {cleared} 个过期缓存文件")
