from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.entities.system import SystemStatus  # noqa: E402, F401
from app.entities.trading import EquitySnapshot, Trade  # noqa: E402, F401
from app.entities.backtest import BacktestRun  # noqa: E402, F401
from app.entities.memory import TradeMemory  # noqa: E402, F401
