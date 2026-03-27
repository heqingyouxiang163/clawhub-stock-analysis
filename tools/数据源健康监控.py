#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📡 数据源健康监控系统

功能：
- 监控各数据源连接状态
- 检测数据获取失败
- 连续失败时自动通知用户
- 自动切换备用数据源

数据源列表：
1. 东方财富 API
2. 新浪财经 API
3. 腾讯财经 API

作者：炒股龙虾系统
版本：v1.0
创建：2026-03-27
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path


class DataSourceMonitor:
    """数据源健康监控器"""
    
    def __init__(self):
        self.health_file = Path("/home/admin/openclaw/workspace/temp/数据源健康状态.json")
        self.notification_file = Path("/home/admin/openclaw/workspace/temp/数据源异常通知.json")
        
        # 数据源配置（按优先级排序）
        self.sources = {
            'sina': {
                'name': '新浪财经',
                'url': 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple',
                'params': {
                    'page': '1',
                    'num': '10',
                    'sort': 'changepercent',
                    'asc': '0',
                    'node': 'hs_a'
                },
                'timeout': 5,
                'max_failures': 3,
                'priority': 1  # 最高优先级
            },
            'tencent': {
                'name': '腾讯财经',
                'url': 'http://qt.gtimg.cn/q=sh600519',
                'params': {},
                'timeout': 5,
                'max_failures': 3,
                'priority': 2  # 第二优先级
            },
            'eastmoney': {
                'name': '东方财富',
                'url': 'http://push2.eastmoney.com/api/qt/clist/get',
                'params': {
                    'pn': '1',
                    'pz': '10',
                    'fid': 'f3',
                    'fs': 'm:0 t:6,m:1 t:2',
                    'fields': 'f12,f14,f3',
                    '_': str(int(time.time() * 1000))
                },
                'timeout': 5,
                'max_failures': 2,  # 失败 2 次就降级
                'priority': 3  # 最低优先级（不稳定）
            }
        }
        
        # 加载健康状态
        self.health_status = self._load_health()
    
    def _load_health(self):
        """加载健康状态"""
        if self.health_file.exists():
            with open(self.health_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 初始化健康状态
        return {
            source_id: {
                'status': 'unknown',
                'last_check': None,
                'consecutive_failures': 0,
                'last_error': None,
                'response_time_ms': None
            }
            for source_id in self.sources
        }
    
    def _save_health(self):
        """保存健康状态"""
        self.health_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.health_file, 'w', encoding='utf-8') as f:
            json.dump(self.health_status, f, ensure_ascii=False, indent=2)
    
    def check_source(self, source_id):
        """检查单个数据源"""
        if source_id not in self.sources:
            return False
        
        source = self.sources[source_id]
        start_time = time.time()
        
        try:
            response = requests.get(
                source['url'],
                params=source['params'],
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=source['timeout']
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # 检查响应内容
                if source_id == 'eastmoney':
                    data = response.json()
                    valid = 'data' in data and 'diff' in data.get('data', {})
                elif source_id == 'sina':
                    data = response.json()
                    valid = isinstance(data, list) and len(data) > 0
                elif source_id == 'tencent':
                    valid = 'sh600519' in response.text
                
                if valid:
                    self.health_status[source_id]['status'] = 'healthy'
                    self.health_status[source_id]['consecutive_failures'] = 0
                    self.health_status[source_id]['response_time_ms'] = round(elapsed, 2)
                    print(f"✅ {source['name']}: 正常 ({elapsed:.0f}ms)")
                    return True
            
            # 响应无效
            self._record_failure(source_id, f"响应无效 (HTTP {response.status_code})")
            return False
            
        except requests.Timeout:
            self._record_failure(source_id, f"超时 ({source['timeout']}秒)")
            return False
        except Exception as e:
            self._record_failure(source_id, str(e))
            return False
    
    def _record_failure(self, source_id, error_msg):
        """记录失败"""
        source = self.sources[source_id]
        status = self.health_status[source_id]
        
        status['status'] = 'error'
        status['consecutive_failures'] += 1
        status['last_error'] = error_msg
        status['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"❌ {source['name']}: 失败 - {error_msg} (连续失败{status['consecutive_failures']}次)")
        
        # 检查是否需要通知
        if status['consecutive_failures'] >= source['max_failures']:
            self._send_notification(source_id, error_msg)
    
    def _send_notification(self, source_id, error_msg):
        """发送异常通知"""
        source = self.sources[source_id]
        
        notification = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_id': source_id,
            'source_name': source['name'],
            'error': error_msg,
            'consecutive_failures': self.health_status[source_id]['consecutive_failures'],
            'message': f"⚠️ {source['name']}数据源连续失败{self.health_status[source_id]['consecutive_failures']}次，请检查网络连接或切换备用数据源！"
        }
        
        # 保存到通知文件
        notifications = []
        if self.notification_file.exists():
            with open(self.notification_file, 'r', encoding='utf-8') as f:
                notifications = json.load(f)
        
        # 避免重复通知（1 小时内不重复通知同一数据源）
        should_notify = True
        for n in notifications[-5:]:  # 检查最近 5 条
            if n.get('source_id') == source_id:
                notify_time = datetime.strptime(n['timestamp'], '%Y-%m-%d %H:%M:%S')
                if (datetime.now() - notify_time).seconds < 3600:
                    should_notify = False
                    break
        
        if should_notify:
            notifications.append(notification)
            with open(self.notification_file, 'w', encoding='utf-8') as f:
                json.dump(notifications, f, ensure_ascii=False, indent=2)
            
            # 东方财富失败 2 次就通知，其他 3 次
            threshold = 2 if source_id == 'eastmoney' else 3
            if self.health_status[source_id]['consecutive_failures'] >= threshold:
                print(f"\n🔔 已生成异常通知：{notification['message']}")
    
    def check_all(self):
        """检查所有数据源"""
        print("=" * 60)
        print("📡 数据源健康检查")
        print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        results = {}
        for source_id in self.sources:
            results[source_id] = self.check_source(source_id)
            self.health_status[source_id]['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self._save_health()
        
        # 总结
        print("\n" + "=" * 60)
        healthy_count = sum(1 for v in results.values() if v)
        print(f"✅ 健康：{healthy_count}/{len(results)}")
        
        if healthy_count < len(results):
            print("⚠️ 有数据源异常，请查看通知！")
        else:
            print("🎉 所有数据源正常！")
        print("=" * 60)
        
        return results
    
    def get_healthy_source(self):
        """获取健康的数据源 ID"""
        for source_id, status in self.health_status.items():
            if status['status'] == 'healthy':
                return source_id
        return None


def main():
    """主函数"""
    monitor = DataSourceMonitor()
    monitor.check_all()


if __name__ == "__main__":
    main()
