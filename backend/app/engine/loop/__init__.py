"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: loop/ Tick 步骤实现
描述: 每个 tick 的 8 步流水线实现

目录结构:
- tick_circuit.py — step 0: 熔断检查
- tick_market.py  — step 2: 行情获取
- tick_strategy.py — step 3: 策略分析
- tick_position.py — step 4: 动态持仓管理
- tick_memory.py  — step 5: AI 决策记忆
- tick_risk.py    — step 6: 风控检查
- tick_trade.py   — step 7: 交易执行
- tick_persist.py — step 8: 持久化 + 异常处理
- emoji_clean.py  — emoji 清洗工具
"""
