# Legacy v1.0 — 归档代码

本目录包含 v1.0 单体架构的归档代码，仅供参考，不参与当前系统运行。

## 文件说明

| 文件 | 用途 |
|------|------|
| `deepseekok2.py` | v1.0 主交易引擎（15分钟周期，DeepSeek AI 信号） |
| `streamlit_app.py` | v1.0 Streamlit 仪表盘 |
| `data_manager.py` | v1.0 JSON 文件 IPC 层 |
| `database.py` | v1.0 SQLite 存储层 |
| `base_strategy.py` | v1.0 策略基类 |
| `technical_strategy.py` | v1.0 技术指标策略 |
| `deepseek_strategy.py` | v1.0 DeepSeek AI 策略 |
| `backtest.py` | v1.0 回测工具 |

## 注意

- 文件间相互引用（如 `from data_manager import ...`），移动后内部 import 已断开
- 如需临时运行回测：`cd legacy && PYTHONPATH=.. python backtest.py`
- 当前系统入口是项目根目录的 `run.py`（v2.0 事件驱动架构）
