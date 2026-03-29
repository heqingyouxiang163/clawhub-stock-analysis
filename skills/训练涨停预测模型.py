#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 训练涨停预测模型 (使用模拟数据演示)
"""

from skills.涨停分时图训练 import LimitUpTrainer
import random


def generate_simulated_data():
    """生成模拟涨停股数据"""
    stocks = []
    
    # 模拟 50 只涨停股
    for i in range(50):
        code = f"600{i+1:03d}" if i < 25 else f"000{i-24:03d}"
        
        # 涨停股典型特征
        base_price = random.uniform(5, 50)
        
        # 生成 240 个分时点 (每分钟一个)
        intraday_data = []
        price = base_price * 0.98  # 开盘价
        
        for minute in range(240):
            # 模拟价格上涨趋势
            progress = minute / 240
            target_price = base_price * (1 + progress * 0.10)  # 最终涨停 10%
            
            # 添加随机波动
            price = target_price + random.uniform(-0.02, 0.02) * base_price
            
            # 成交量模拟 (早盘和涨停时放量)
            if minute < 30 or minute > 200:
                volume = random.randint(1000, 5000)
            else:
                volume = random.randint(500, 2000)
            
            # 均线模拟
            avg_price = base_price * (1 + progress * 0.05)
            
            intraday_data.append({
                'time': f"{9+minute//60:02d}{minute%60:02d}00",
                'price': round(price, 2),
                'volume': volume,
                'avg_price': round(avg_price, 2)
            })
        
        stocks.append({
            '代码': code,
            '名称': f'模拟股票{i+1}',
            '连板数': random.choice([2, 3, 4, 2, 3, 2]),  # 2-4 连板
            '封单额亿': random.uniform(2, 5),
            'intraday_data': intraday_data
        })
    
    return stocks


if __name__ == '__main__':
    print("=" * 80)
    print("🦞 训练涨停预测模型")
    print("=" * 80)
    print()
    
    # 生成模拟数据
    print("📊 生成模拟涨停股数据...")
    simulated_data = generate_simulated_data()
    print(f"生成 {len(simulated_data)} 只涨停股")
    print()
    
    # 训练模型
    trainer = LimitUpTrainer()
    trainer.train(simulated_data)
    
    print()
    print("=" * 80)
    print("✅ 模型训练完成！")
    print("=" * 80)
    print()
    
    # 测试预测
    print("🧪 测试预测功能...")
    print()
    
    test_stock = simulated_data[0]
    score = trainer.predict_score(test_stock)
    print(f"测试股票：{test_stock['代码']} {test_stock['名称']}")
    print(f"涨停概率评分：{score}")
    print()
    
    if score >= 80:
        print("✅ 重点推荐 (≥80 分)")
    elif score >= 70:
        print("⚠️ 可关注 (70-79 分)")
    else:
        print("❌ 观望 (<70 分)")
    
    print()
    print("📁 模型已保存到：memory/涨停预测模型.json")
