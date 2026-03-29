#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 涨停分时图 + 成交量训练系统

功能:
- 分析历史涨停股的分时图特征
- 分析成交量特征
- 训练涨停预测模型
- 优化盘中推荐评分
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


class LimitUpTrainer:
    """涨停分时图 + 成交量训练器"""
    
    def __init__(self):
        self.data_dir = Path('data_cache/limit_up_intraday')
        self.model_file = Path('memory/涨停预测模型.json')
        self.load_model()
    
    def load_model(self):
        """加载训练好的模型"""
        if self.model_file.exists():
            with open(self.model_file, 'r', encoding='utf-8') as f:
                self.model = json.load(f)
        else:
            self.model = {
                '分时特征': {},
                '成交量特征': {},
                '综合评分权重': {}
            }
    
    def save_model(self):
        """保存训练好的模型"""
        self.model['last_update'] = datetime.now().isoformat()
        with open(self.model_file, 'w', encoding='utf-8') as f:
            json.dump(self.model, f, ensure_ascii=False, indent=2)
    
    def analyze_intraday_pattern(self, data_points: list) -> dict:
        """
        分析分时图形态特征
        
        Args:
            data_points: 分时数据列表
        
        Returns:
            分时特征字典
        """
        if not data_points or len(data_points) < 10:
            return {}
        
        prices = [d.get('price', 0) for d in data_points]
        avg_prices = [d.get('avg_price', 0) for d in data_points if d.get('avg_price', 0) > 0]
        volumes = [d.get('volume', 0) for d in data_points]
        
        # 1. 均线上方运行时间占比
        above_avg_ratio = sum(1 for p in prices if p > avg_prices[0]) / len(prices) * 100 if avg_prices else 0
        
        # 2. 价格波动率
        price_volatility = np.std(prices) / np.mean(prices) * 100 if prices else 0
        
        # 3. 上涨斜率
        if len(prices) >= 2:
            slope = (prices[-1] - prices[0]) / len(prices)
        else:
            slope = 0
        
        # 4. 均线支撑次数
        support_count = 0
        for i in range(10, len(prices)):
            if prices[i-1] < avg_prices[0] and prices[i] > avg_prices[0]:
                support_count += 1
        
        # 5. 量价配合
        price_up_volume_up = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1] and volumes[i] > volumes[i-1]:
                price_up_volume_up += 1
        volume_price_coop = price_up_volume_up / len(prices) * 100 if prices else 0
        
        return {
            '均线上方占比': round(above_avg_ratio, 2),
            '价格波动率': round(price_volatility, 2),
            '上涨斜率': round(slope, 4),
            '均线支撑次数': support_count,
            '量价配合度': round(volume_price_coop, 2)
        }
    
    def analyze_volume_pattern(self, data_points: list) -> dict:
        """
        分析成交量特征
        
        Args:
            data_points: 分时数据列表
        
        Returns:
            成交量特征字典
        """
        if not data_points or len(data_points) < 10:
            return {}
        
        volumes = [d.get('volume', 0) for d in data_points]
        
        # 1. 平均成交量
        avg_volume = np.mean(volumes)
        
        # 2. 成交量波动率
        volume_volatility = np.std(volumes) / avg_volume * 100 if avg_volume > 0 else 0
        
        # 3. 放量倍数 (最大量/平均量)
        volume_ratio = max(volumes) / avg_volume if avg_volume > 0 else 0
        
        # 4. 缩量涨停特征 (涨停后成交量萎缩)
        # 假设后 1/3 数据是涨停后
        limit_up_start = len(volumes) * 2 // 3
        pre_limit_volume = np.mean(volumes[:limit_up_start]) if limit_up_start > 0 else 0
        post_limit_volume = np.mean(volumes[limit_up_start:]) if limit_up_start < len(volumes) else 0
        volume_shrink = post_limit_volume / pre_limit_volume if pre_limit_volume > 0 else 1
        
        # 5. 堆量特征 (连续放量)
        continuous_volume_up = 0
        for i in range(2, len(volumes)):
            if volumes[i] > volumes[i-1] > volumes[i-2]:
                continuous_volume_up += 1
        volume_stack = continuous_volume_up / len(volumes) * 100 if volumes else 0
        
        return {
            '平均成交量': round(avg_volume, 2),
            '成交量波动率': round(volume_volatility, 2),
            '放量倍数': round(volume_ratio, 2),
            '缩量比': round(volume_shrink, 2),
            '堆量特征': round(volume_stack, 2)
        }
    
    def train(self, history_data: list):
        """
        训练涨停预测模型
        
        Args:
            history_data: 历史涨停股数据列表
        """
        print("🔬 开始训练涨停预测模型...")
        print(f"训练数据：{len(history_data)}只涨停股")
        print()
        
        all_intraday_features = []
        all_volume_features = []
        
        for stock in history_data:
            data_points = stock.get('intraday_data', [])
            
            if data_points:
                # 分析分时特征
                intraday_feat = self.analyze_intraday_pattern(data_points)
                if intraday_feat:
                    all_intraday_features.append(intraday_feat)
                
                # 分析成交量特征
                volume_feat = self.analyze_volume_pattern(data_points)
                if volume_feat:
                    all_volume_features.append(volume_feat)
        
        if not all_intraday_features:
            print("⚠️ 数据不足，无法训练")
            return
        
        # 计算平均特征 (作为标准模板)
        avg_intraday = {}
        for key in all_intraday_features[0].keys():
            values = [f[key] for f in all_intraday_features if key in f]
            avg_intraday[key] = np.mean(values)
        
        avg_volume = {}
        for key in all_volume_features[0].keys():
            values = [f[key] for f in all_volume_features if key in f]
            avg_volume[key] = np.mean(values)
        
        # 计算特征权重 (根据与涨停的相关性)
        # 简化版：使用平均值作为基准，偏离越小评分越高
        self.model['分时特征'] = avg_intraday
        self.model['成交量特征'] = avg_volume
        
        # 计算综合评分权重
        self.model['综合评分权重'] = {
            '分时均线': 0.35,
            '成交量': 0.25,
            '连板数': 0.20,
            '封单额': 0.10,
            '板块效应': 0.10
        }
        
        self.save_model()
        
        print("✅ 训练完成！")
        print()
        print("📊 涨停股分时特征均值:")
        for k, v in avg_intraday.items():
            print(f"  {k}: {v}")
        print()
        print("📊 涨停股成交量特征均值:")
        for k, v in avg_volume.items():
            print(f"  {k}: {v}")
        print()
        print("📊 综合评分权重:")
        for k, v in self.model['综合评分权重'].items():
            print(f"  {k}: {v*100:.0f}%")
    
    def predict_score(self, stock_data: dict) -> float:
        """
        预测涨停概率评分
        
        Args:
            stock_data: 股票数据 (包含 intraday_data)
        
        Returns:
            涨停概率评分 (0-100)
        """
        if not self.model or not stock_data:
            return 50.0
        
        data_points = stock_data.get('intraday_data', [])
        if not data_points:
            return 50.0
        
        # 分析当前股票特征
        intraday_feat = self.analyze_intraday_pattern(data_points)
        volume_feat = self.analyze_volume_pattern(data_points)
        
        if not intraday_feat or not volume_feat:
            return 50.0
        
        # 计算与标准模板的相似度
        score = 50.0
        
        # 分时特征评分 (40 分)
        intraday_score = 0
        for key in self.model['分时特征']:
            if key in intraday_feat:
                target = self.model['分时特征'][key]
                actual = intraday_feat[key]
                # 偏离越小分数越高
                diff = abs(actual - target) / (target if target != 0 else 1)
                intraday_score += max(0, (1 - diff) * 10)
        intraday_score = min(40, intraday_score)
        
        # 成交量特征评分 (30 分)
        volume_score = 0
        for key in self.model['成交量特征']:
            if key in volume_feat:
                target = self.model['成交量特征'][key]
                actual = volume_feat[key]
                diff = abs(actual - target) / (target if target != 0 else 1)
                volume_score += max(0, (1 - diff) * 8)
        volume_score = min(30, volume_score)
        
        # 其他特征评分 (30 分)
        other_score = 0
        
        # 连板数
        limit_count = stock_data.get('连板数', 1)
        if limit_count >= 4:
            other_score += 15
        elif limit_count >= 3:
            other_score += 12
        elif limit_count >= 2:
            other_score += 8
        
        # 封单额
        fengdan = stock_data.get('封单额亿', 0)
        if fengdan >= 5:
            other_score += 10
        elif fengdan >= 3:
            other_score += 7
        elif fengdan >= 2:
            other_score += 4
        
        total_score = intraday_score + volume_score + other_score
        return min(100, total_score)


# ======================================
# 使用示例
# ======================================

if __name__ == '__main__':
    trainer = LimitUpTrainer()
    
    # 模拟训练数据
    训练数据 = [
        {
            '代码': '600227',
            '名称': '赤天化',
            '连板数': 3,
            '封单额亿': 3.5,
            'intraday_data': [
                {'time': '093000', 'price': 4.00, 'volume': 1000, 'avg_price': 4.00},
                {'time': '093100', 'price': 4.10, 'volume': 1200, 'avg_price': 4.05},
                {'time': '093200', 'price': 4.20, 'volume': 1500, 'avg_price': 4.10},
                # ... 更多数据
            ]
        }
    ]
    
    # 训练
    # trainer.train(训练数据)
    
    # 预测
    # score = trainer.predict_score(训练数据 [0])
    # print(f"涨停概率评分：{score}")
    
    print("🦞 涨停分时图 + 成交量训练系统已就绪")
    print()
    print("使用方法:")
    print("1. 收集历史涨停股分时数据")
    print("2. trainer.train(历史数据)")
    print("3. score = trainer.predict_score(股票数据)")
    print("4. 根据评分推荐 (≥80 分重点推荐)")
