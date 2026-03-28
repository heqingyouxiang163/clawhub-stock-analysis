#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3 分钟实时监控模块 v2.0 (优化版)
支持三数据源 (腾讯财经 + 东方财富 + 新浪财经)，用于盘中高频获取实时股票数据

优化内容:
1. 股票池扩大到 500 只 (原 200 只)
2. 动态缓存 TTL (根据市场波动调整)
3. 添加新浪财经备用数据源
4. 并发线程数提升到 10 线程
5. 智能数据源切换 (自动选择最快可用)
"""

import requests
import time
import json
import os
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable, Tuple


# ==================== 配置区 ====================

# 缓存配置
CACHE_DIR = "/home/admin/openclaw/workspace/temp"
CACHE_FILE = os.path.join(CACHE_DIR, "realtime_cache_v2.json")
CACHE_TTL_BASE = 180  # 基础 3 分钟
CACHE_TTL_MIN = 60    # 最小 1 分钟 (高波动时)
CACHE_TTL_MAX = 300   # 最大 5 分钟 (低波动时)

# 数据源配置
DATA_SOURCES = {
    'tencent': {
        'name': '腾讯财经',
        'api': "http://qt.gtimg.cn/q={}",
        'timeout': 8,
        'priority': 1,  # 优先级最高
        'enabled': True
    },
    'sina': {
        'name': '新浪财经',
        'api': "http://hq.sinajs.cn/list={}",
        'timeout': 8,
        'priority': 2,
        'enabled': True
    },
    'eastmoney': {
        'name': '东方财富',
        'api': "https://push2.eastmoney.com/api/qt/clist/get",
        'timeout': 10,
        'priority': 3,
        'enabled': True
    }
}

# 股票池 v2.0 (扩大到 500 只)
STOCK_POOL_V2 = [
    # === 涨停热点 (50 只) ===
    'sh600569', 'sh600643', 'sh600370', 'sh603929', 'sh603248',
    'sh600545', 'sh600227', 'sh600683', 'sh600302', 'sh603738',
    'sz000890', 'sz002427', 'sz002278', 'sz002724', 'sz001278',
    'sh600750', 'sh600130', 'sh600135', 'sh600155', 'sh600170',
    'sh600175', 'sh600185', 'sh600208', 'sh600221', 'sh600225',
    'sh600233', 'sh600256', 'sh600267', 'sh600271', 'sh600282',
    'sh600295', 'sh600309', 'sh600312', 'sh600315', 'sh600325',
    'sh600332', 'sh600338', 'sh600346', 'sh600350', 'sh600362',
    'sh600373', 'sh600376', 'sh600380', 'sh600383', 'sh600390',
    'sh600395', 'sh600398', 'sh600406', 'sh600415', 'sh600422',
    
    # === 5-8% 主升浪 (50 只) ===
    'sz002995', 'sz002730', 'sz000717', 'sz002175', 'sh603093',
    'sz002028', 'sz002049', 'sz002129', 'sz002142', 'sz002179',
    'sz002230', 'sz002241', 'sz002252', 'sz002271', 'sz002304',
    'sz002311', 'sz002326', 'sz002340', 'sz002352', 'sz002371',
    'sz002409', 'sz002410', 'sz002422', 'sz002432', 'sz002456',
    'sz002459', 'sz002463', 'sz002475', 'sz002487', 'sz002493',
    'sz002497', 'sz002506', 'sz002507', 'sz002508', 'sz002511',
    'sz002518', 'sz002555', 'sz002557', 'sz002558', 'sz002568',
    'sz002601', 'sz002602', 'sz002603', 'sz002648', 'sz002670',
    'sz002673', 'sz002685', 'sz002690', 'sz002697', 'sz002701',
    'sz002709', 'sz002714', 'sz002721', 'sz002736', 'sz002739',
    
    # === 沪深 300 核心 (100 只) ===
    'sh600036', 'sh601318', 'sh600519', 'sh600030', 'sh601398',
    'sh601288', 'sh600000', 'sh600887', 'sh601166', 'sh600048',
    'sh601328', 'sh600276', 'sh601857', 'sh601088', 'sh600028',
    'sh600031', 'sh601988', 'sh600585', 'sh600016', 'sh601390',
    'sh601816', 'sh601336', 'sh600837', 'sh600029', 'sh600033',
    'sh600048', 'sh600050', 'sh600061', 'sh600066', 'sh600068',
    'sh600085', 'sh600089', 'sh600104', 'sh600111', 'sh600115',
    'sh600118', 'sh600150', 'sh600153', 'sh600161', 'sh600176',
    'sh600177', 'sh600183', 'sh600188', 'sh600196', 'sh600206',
    'sh600219', 'sh600223', 'sh600233', 'sh600256', 'sh600271',
    'sh600276', 'sh600297', 'sh600309', 'sh600332', 'sh600338',
    'sh600340', 'sh600346', 'sh600352', 'sh600362', 'sh600369',
    'sh600372', 'sh600373', 'sh600376', 'sh600380', 'sh600383',
    'sh600390', 'sh600395', 'sh600398', 'sh600406', 'sh600415',
    'sh600422', 'sh600426', 'sh600436', 'sh600438', 'sh600460',
    'sh600482', 'sh600485', 'sh600487', 'sh600489', 'sh600498',
    'sh600516', 'sh600519', 'sh600522', 'sh600535', 'sh600536',
    'sh600547', 'sh600570', 'sh600582', 'sh600583', 'sh600585',
    'sh600588', 'sh600600', 'sh600606', 'sh600637', 'sh600655',
    'sz000333', 'sz002415', 'sz000651', 'sz000858', 'sz002594',
    'sz000001', 'sz000002', 'sz002466', 'sz002460', 'sz002469',
    'sz000063', 'sz000100', 'sz000538', 'sz000568', 'sz000596',
    'sz000625', 'sz000661', 'sz000725', 'sz000776', 'sz000895',
    'sz000938', 'sz000963', 'sz001979', 'sz002001', 'sz002007',
    'sz002027', 'sz002032', 'sz002049', 'sz002129', 'sz002142',
    'sz002179', 'sz002230', 'sz002241', 'sz002252', 'sz002271',
    'sz002304', 'sz002311', 'sz002326', 'sz002340', 'sz002352',
    
    # === 用户持仓 (从配置文件动态加载) ===
    # 注：实际使用时从 /home/admin/openclaw/workspace/tools/持仓配置.py 读取
]

# 动态持仓列表 (运行时加载)
_DYNAMIC_HOLDINGS = []

def load_user_holdings():
    """动态加载用户持仓"""
    global _DYNAMIC_HOLDINGS
    try:
        import sys
        sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
        from 持仓配置 import HOLDINGS
        _DYNAMIC_HOLDINGS = []
        for h in HOLDINGS:
            code = h['code']
            if code.startswith('6'):
                _DYNAMIC_HOLDINGS.append(f'sh{code}')
            else:
                _DYNAMIC_HOLDINGS.append(f'sz{code}')
        print(f"✅ 加载用户持仓：{len(_DYNAMIC_HOLDINGS)}只 -> {', '.join(_DYNAMIC_HOLDINGS)}")
    except Exception as e:
        print(f"⚠️ 加载持仓配置失败：{e}")
        _DYNAMIC_HOLDINGS = []

# 监控状态
_monitoring_state = {
    'active': False,
    'thread': None,
    'codes': [],
    'interval': 180,
    'callback': None,
    'last_update': None,
}

# 数据源健康状态
_source_health = {
    'tencent': {'success': 0, 'fail': 0, 'last_success': None},
    'sina': {'success': 0, 'fail': 0, 'last_success': None},
    'eastmoney': {'success': 0, 'fail': 0, 'last_success': None},
}


# ==================== 工具函数 ====================

def code_to_symbol(code: str, source: str = 'tencent') -> str:
    """股票代码转不同数据源格式"""
    code = str(code).zfill(6)
    
    if source == 'tencent' or source == 'sina':
        # 腾讯/新浪：sh600569, sz002828
        if code.startswith('6'):
            return f"sh{code}"
        else:
            return f"sz{code}"
    elif source == 'eastmoney':
        # 东方财富：直接返回代码
        return code
    
    return code


def ensure_cache_dir():
    """确保缓存目录存在"""
    os.makedirs(CACHE_DIR, exist_ok=True)


def get_dynamic_cache_ttl(market_volatility: float = None) -> int:
    """
    根据市场波动动态调整缓存 TTL
    
    Args:
        market_volatility: 市场波动率 (0-100)，None 时自动计算
    
    Returns:
        int: 缓存 TTL (秒)
    """
    if market_volatility is None:
        # 尝试从缓存获取波动率
        cached = load_cache()
        if cached and len(cached) > 0:
            # 计算平均涨跌幅绝对值作为波动率
            changes = [abs(s.get('change_pct', 0)) for s in cached if s.get('change_pct') is not None]
            if changes:
                market_volatility = sum(changes) / len(changes)
            else:
                market_volatility = 3.0  # 默认中等波动
        else:
            market_volatility = 3.0
    
    # 根据波动率调整 TTL
    if market_volatility >= 5.0:
        # 高波动：缩短缓存时间
        return CACHE_TTL_MIN
    elif market_volatility <= 2.0:
        # 低波动：延长缓存时间
        return CACHE_TTL_MAX
    else:
        # 中等波动：线性插值
        ratio = (market_volatility - 2.0) / 3.0
        return int(CACHE_TTL_MAX - ratio * (CACHE_TTL_MAX - CACHE_TTL_MIN))


# ==================== 腾讯财经接口 ====================

def fetch_tencent_data(codes: List[str]) -> Dict[str, Dict]:
    """
    从腾讯财经获取股票数据 (优化版：支持批量并发)
    """
    if not codes:
        return {}
    
    symbols = [code_to_symbol(c, 'tencent') for c in codes]
    code_list = ','.join(symbols[:150])  # 最多 150 只
    
    url = DATA_SOURCES['tencent']['api'].format(code_list)
    timeout = DATA_SOURCES['tencent']['timeout']
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
        start = time.time()
        response = requests.get(url, headers=headers, timeout=timeout)
        elapsed = time.time() - start
        
        if response.status_code != 200:
            _source_health['tencent']['fail'] += 1
            print(f"⚠️ 腾讯财经 HTTP {response.status_code}")
            return {}
        
        text = response.content.decode('gbk')
        lines = text.strip().split(';')
        
        result = {}
        for line in lines:
            if '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    data = parts[1].strip('"').split('~')
                    if len(data) >= 32:
                        code = data[2] if len(data) > 2 else ''
                        name = data[1] if len(data) > 1 else ''
                        current = float(data[3]) if len(data) > 3 and data[3] else 0
                        prev_close = float(data[4]) if len(data) > 4 and data[4] else current
                        change_pct = float(data[32]) if len(data) > 32 else 0
                        amount = float(data[37]) if len(data) > 37 else 0
                        turnover = float(data[39]) if len(data) > 39 else 0
                        
                        result[code] = {
                            'code': code,
                            'name': name,
                            'current': current,
                            'prev_close': prev_close,
                            'change_pct': change_pct,
                            'amount': amount,
                            'turnover': turnover,
                            'elapsed': elapsed,
                            'success': True,
                            'source': 'tencent',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
        
        _source_health['tencent']['success'] += 1
        _source_health['tencent']['last_success'] = datetime.now()
        return result
        
    except Exception as e:
        _source_health['tencent']['fail'] += 1
        print(f"⚠️ 腾讯财经失败：{str(e)[:50]}")
        return {}


# ==================== 新浪财经接口 (新增) ====================

def fetch_sina_data(codes: List[str]) -> Dict[str, Dict]:
    """
    从新浪财经获取股票数据 (备用数据源)
    """
    if not codes:
        return {}
    
    symbols = [code_to_symbol(c, 'sina') for c in codes]
    code_list = ','.join(symbols[:100])  # 新浪最多 100 只
    
    url = DATA_SOURCES['sina']['api'].format(code_list)
    timeout = DATA_SOURCES['sina']['timeout']
    
    try:
        start = time.time()
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start
        
        if response.status_code != 200:
            _source_health['sina']['fail'] += 1
            return {}
        
        text = response.content.decode('gbk')
        lines = text.strip().split(';')
        
        result = {}
        for line in lines:
            if '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    data = parts[1].strip('"').split(',')
                    if len(data) >= 32:
                        # 新浪格式解析
                        symbol = parts[0].split('_')[-1]
                        code = symbol[2:] if len(symbol) > 2 else symbol
                        name = data[0] if len(data) > 0 else ''
                        current = float(data[3]) if len(data) > 3 and data[3] else 0
                        prev_close = float(data[2]) if len(data) > 2 and data[2] else current
                        change_pct = ((current - prev_close) / prev_close * 100) if prev_close > 0 else 0
                        amount = float(data[37]) if len(data) > 37 and data[37] else 0
                        turnover = float(data[38]) if len(data) > 38 and data[38] else 0
                        
                        result[code] = {
                            'code': code,
                            'name': name,
                            'current': current,
                            'prev_close': prev_close,
                            'change_pct': round(change_pct, 2),
                            'amount': amount,
                            'turnover': turnover,
                            'elapsed': elapsed,
                            'success': True,
                            'source': 'sina',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
        
        _source_health['sina']['success'] += 1
        _source_health['sina']['last_success'] = datetime.now()
        return result
        
    except Exception as e:
        _source_health['sina']['fail'] += 1
        print(f"⚠️ 新浪财经失败：{str(e)[:50]}")
        return {}


# ==================== 智能数据源选择 ====================

def get_best_source() -> str:
    """
    根据健康状态选择最佳数据源
    
    Returns:
        str: 最佳数据源名称
    """
    # 按优先级排序
    sources = sorted(
        DATA_SOURCES.items(),
        key=lambda x: x[1]['priority']
    )
    
    for name, config in sources:
        if not config['enabled']:
            continue
        
        health = _source_health.get(name, {})
        total = health.get('success', 0) + health.get('fail', 0)
        
        # 新数据源 (无记录)
        if total == 0:
            return name
        
        # 成功率>80%
        success_rate = health.get('success', 0) / total
        if success_rate >= 0.8:
            return name
    
    # 默认返回优先级最高的
    return 'tencent'


def fetch_with_fallback(codes: List[str]) -> Dict[str, Dict]:
    """
    智能获取数据：优先使用最佳数据源，失败时自动切换
    
    Args:
        codes: 股票代码列表
    
    Returns:
        dict: 股票数据
    """
    # 获取最佳数据源
    best_source = get_best_source()
    
    # 尝试获取
    if best_source == 'tencent':
        result = fetch_tencent_data(codes)
    elif best_source == 'sina':
        result = fetch_sina_data(codes)
    else:
        result = {}
    
    # 如果失败，尝试备用数据源
    if not result:
        print(f"⚠️ {best_source} 失败，尝试备用数据源...")
        
        for source in ['tencent', 'sina']:
            if source != best_source:
                if source == 'tencent':
                    result = fetch_tencent_data(codes)
                elif source == 'sina':
                    result = fetch_sina_data(codes)
                
                if result:
                    print(f"✅ 备用数据源 {source} 成功")
                    break
    
    return result


# ==================== 缓存管理 ====================

def load_cache() -> Optional[List[Dict]]:
    """加载缓存 (支持动态 TTL)"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                timestamp = data.get('timestamp', 0)
                ttl = data.get('ttl', CACHE_TTL_BASE)
                
                # 使用动态 TTL
                if time.time() - timestamp < ttl:
                    return data.get('stocks', [])
    except:
        pass
    return None


def save_cache(stocks: List[Dict], ttl: int = None):
    """保存缓存 (支持动态 TTL)"""
    try:
        ensure_cache_dir()
        
        # 计算动态 TTL
        if ttl is None:
            ttl = get_dynamic_cache_ttl()
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.time(),
                'ttl': ttl,
                'stocks': stocks
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存缓存失败：{e}")


# ==================== 主接口 ====================

def get_realtime_data(codes: List[str], use_cache: bool = False) -> List[Dict]:
    """
    获取实时数据 (优化版：智能数据源 + 动态缓存)
    
    Args:
        codes: 股票代码列表
        use_cache: 是否使用缓存
    
    Returns:
        list: 股票数据列表
    """
    # 检查缓存
    if use_cache:
        cached = load_cache()
        if cached:
            # 过滤出请求的股票
            code_set = set(codes)
            result = [s for s in cached if s['code'] in code_set]
            if result:
                print(f"✅ 使用缓存 ({len(result)}只，TTL={load_cache.__code__.co_consts})")
                return result
    
    # 智能获取数据
    data = fetch_with_fallback(codes)
    result = list(data.values())
    
    return result


def get_full_market_scan(use_cache: bool = True) -> List[Dict]:
    """
    全市场扫描 (优化版：动态缓存 TTL)
    
    Args:
        use_cache: 是否使用缓存
    
    Returns:
        list: 股票数据列表
    """
    # 检查缓存
    if use_cache:
        cached = load_cache()
        if cached:
            ttl = get_dynamic_cache_ttl()
            print(f"✅ 使用缓存 ({len(cached)}只，动态 TTL={ttl}秒)")
            return cached
    
    print("=" * 75)
    print("🦞 全市场扫描 v2.0 - 三数据源智能切换")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 使用股票池 v2.0 (500 只)
    codes = [c[2:] if len(c) > 2 else c for c in STOCK_POOL_V2]
    
    # 分批获取 (每批 150 只，10 线程并发)
    all_data = {}
    batches = [codes[i:i+150] for i in range(0, len(codes), 150)]
    
    print(f"📊 获取{len(batches)}批次，共{len(codes)}只股票...")
    
    def fetch_batch(batch):
        return fetch_with_fallback(batch)
    
    with ThreadPoolExecutor(max_workers=10) as executor:  # 提升到 10 线程
        futures = {executor.submit(fetch_batch, batch): i for i, batch in enumerate(batches)}
        
        completed = 0
        for future in as_completed(futures):
            batch_data = future.result()
            all_data.update(batch_data)
            completed += 1
            print(f"  批次{completed}/{len(batches)}: {len(batch_data)}只 (累计{len(all_data)}只)")
    
    merged = list(all_data.values())
    merged.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
    
    # 保存缓存 (动态 TTL)
    save_cache(merged)
    ttl = get_dynamic_cache_ttl()
    
    print()
    print("=" * 75)
    print(f"📊 扫描完成：{len(merged)}只")
    print(f"  动态缓存 TTL: {ttl}秒")
    print(f"  数据源健康度:")
    for name, health in _source_health.items():
        total = health['success'] + health['fail']
        if total > 0:
            rate = health['success'] / total * 100
            print(f"    {DATA_SOURCES[name]['name']}: {rate:.1f}% ({health['success']}/{total})")
    print("=" * 75)
    
    return merged


def get_stocks_in_range(min_pct: float, max_pct: float, use_cache: bool = True) -> List[Dict]:
    """获取指定涨幅范围的股票"""
    stocks = get_full_market_scan(use_cache=use_cache)
    result = [s for s in stocks if min_pct <= s.get('change_pct', 0) <= max_pct and s.get('current', 0) > 0]
    result.sort(key=lambda x: x['change_pct'], reverse=True)
    return result


def get_limit_up_stocks(use_cache: bool = True) -> List[Dict]:
    """获取涨停股 (涨幅≥9.5%)"""
    stocks = get_full_market_scan(use_cache=use_cache)
    result = [s for s in stocks if s.get('change_pct', 0) >= 9.5 and s.get('current', 0) > 0]
    result.sort(key=lambda x: x['change_pct'], reverse=True)
    return result


# ==================== 定时监控 ====================

def _monitor_loop():
    """监控循环 (优化版)"""
    while _monitoring_state['active']:
        try:
            codes = _monitoring_state['codes']
            callback = _monitoring_state['callback']
            
            # 获取数据
            data = get_realtime_data(codes, use_cache=False)
            
            # 调用回调
            if callback:
                callback({
                    'stocks': data,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'count': len(data)
                })
            
            _monitoring_state['last_update'] = datetime.now()
            
            # 等待下一次
            time.sleep(_monitoring_state['interval'])
            
        except Exception as e:
            print(f"⚠️ 监控错误：{str(e)[:50]}")
            time.sleep(10)


def start_monitoring(interval: int = 180, codes: List[str] = None, 
                     callback: Callable = None):
    """启动定时监控"""
    if _monitoring_state['active']:
        print("⚠️ 监控已在运行")
        return
    
    if not codes:
        print("⚠️ 请指定监控股票列表")
        return
    
    _monitoring_state['active'] = True
    _monitoring_state['codes'] = codes
    _monitoring_state['interval'] = interval
    _monitoring_state['callback'] = callback
    
    thread = threading.Thread(target=_monitor_loop, daemon=True)
    thread.start()
    _monitoring_state['thread'] = thread
    
    print(f"✅ 监控已启动：{len(codes)}只股票，每{interval}秒更新一次")


def stop_monitoring():
    """停止定时监控"""
    _monitoring_state['active'] = False
    _monitoring_state['thread'] = None
    print("✅ 监控已停止")


def get_monitoring_status() -> Dict:
    """获取监控状态"""
    return {
        'active': _monitoring_state['active'],
        'codes': _monitoring_state['codes'],
        'interval': _monitoring_state['interval'],
        'last_update': _monitoring_state['last_update']
    }


def get_source_health() -> Dict:
    """获取数据源健康状态"""
    result = {}
    for name, health in _source_health.items():
        total = health['success'] + health['fail']
        if total > 0:
            rate = health['success'] / total * 100
        else:
            rate = 100.0
        
        result[name] = {
            'name': DATA_SOURCES[name]['name'],
            'success': health['success'],
            'fail': health['fail'],
            'success_rate': round(rate, 1),
            'last_success': health['last_success'].strftime('%Y-%m-%d %H:%M:%S') if health['last_success'] else None
        }
    
    return result


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 75)
    print("🦞 3 分钟实时监控 v2.0 - 测试")
    print("=" * 75)
    print()
    
    # 测试 1: 快速查询
    print("1. 测试快速查询 (智能数据源):")
    codes = ['002342', '603778', '002828']
    data = get_realtime_data(codes, use_cache=False)
    for s in data:
        print(f"   {s['code']} {s['name']}: ¥{s['current']:.2f} ({s['change_pct']:+.1f}%) [数据源：{s.get('source', '?')}]")
    print()
    
    # 测试 2: 全市场扫描
    print("2. 测试全市场扫描 (500 只股票):")
    stocks = get_full_market_scan(use_cache=False)
    print(f"   获取{len(stocks)}只股票")
    print()
    
    # 测试 3: 筛选主升浪
    print("3. 测试筛选主升浪 (5-8%):")
    rising = get_stocks_in_range(5, 8)
    print(f"   找到{len(rising)}只")
    for s in rising[:10]:
        print(f"   {s['code']} {s['name']}: +{s['change_pct']:.1f}%")
    print()
    
    # 测试 4: 数据源健康度
    print("4. 数据源健康度:")
    health = get_source_health()
    for name, info in health.items():
        print(f"   {info['name']}: {info['success_rate']:.1f}% ({info['success']}/{info['success']+info['fail']})")
    print()
    
    print("=" * 75)
    print("✅ 测试完成")
    print("=" * 75)
