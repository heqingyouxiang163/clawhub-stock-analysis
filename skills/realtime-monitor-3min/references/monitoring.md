# 定时监控接口

## 用途
启动后台定时监控任务，按指定间隔自动获取股票数据并回调通知。

## 使用示例

### 基础监控

```python
from realtime_monitor import start_monitoring, stop_monitoring

def on_update(data):
    """数据更新回调"""
    print(f"\n[{data['timestamp']}] 数据更新:")
    for s in data['stocks']:
        if abs(s['change_pct']) > 5:
            print(f"  {s['code']} {s['name']}: {s['change_pct']:+.1f}%")

# 启动监控 (每 3 分钟更新一次)
start_monitoring(
    interval=180,  # 3 分钟
    codes=['002342', '603778', '002828'],
    callback=on_update
)

# ... 监控自动运行 ...

# 停止监控
stop_monitoring()
```

### 高级用法

```python
from realtime_monitor import start_monitoring, get_monitoring_status

# 复杂回调逻辑
def smart_callback(data):
    # 检测异常波动
    for s in data['stocks']:
        if s['change_pct'] > 7:  # 涨幅>7%
            print(f"🚨 预警：{s['code']} {s['name']} 涨幅{s['change_pct']:.1f}%")
        elif s['change_pct'] < -5:  # 跌幅>-5%
            print(f"⚠️ 止损：{s['code']} {s['name']} 跌幅{abs(s['change_pct']):.1f}%")

# 启动监控
start_monitoring(
    interval=180,
    codes=['002342', '603778'],
    callback=smart_callback
)

# 查看监控状态
status = get_monitoring_status()
print(f"监控状态：{'运行中' if status['active'] else '已停止'}")
print(f"上次更新：{status['last_update']}")
```

## API 说明

### start_monitoring()

```python
start_monitoring(
    interval: int = 180,      # 监控间隔 (秒)
    codes: List[str] = None,  # 监控股票列表
    callback: Callable = None # 回调函数
)
```

### stop_monitoring()

```python
stop_monitoring()
```

### get_monitoring_status()

```python
status = get_monitoring_status()
# 返回：
# {
#     'active': True,
#     'codes': ['002342', '603778'],
#     'interval': 180,
#     'last_update': datetime(2026, 3, 21, 11, 55, 0)
# }
```

## 回调函数格式

```python
def on_update(data: Dict):
    """
    数据更新回调
    
    Args:
        data: {
            'stocks': List[Dict],      # 股票数据列表
            'timestamp': str,          # 时间戳
            'count': int               # 股票数量
        }
    """
    pass
```

## 注意事项

- 监控在后台线程运行，不会阻塞主程序
- 监控线程是 daemon 线程，主程序退出时自动停止
- 建议回调函数保持简单，避免耗时操作
- 监控间隔建议≥60 秒，避免请求过快
