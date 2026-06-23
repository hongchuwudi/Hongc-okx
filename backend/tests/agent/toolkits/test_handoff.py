"""
测试: 移交工具 — transfer_to_X
"""

import pytest


class TestHandoffTools:
    def test_transfer_to_analyst(self):
        from app.agents.toolkits.communication.toolkit_handoff import transfer_to_analyst, HANDOFF_SIGNAL
        result = transfer_to_analyst.invoke({"reason": "需要重新分析"})
        assert HANDOFF_SIGNAL in result
        assert "analyst" in result

    def test_transfer_to_risk(self):
        from app.agents.toolkits.communication.toolkit_handoff import transfer_to_risk, HANDOFF_SIGNAL
        result = transfer_to_risk.invoke({"reason": ""})
        assert HANDOFF_SIGNAL in result
        assert "risk" in result

    def test_transfer_to_trader(self):
        from app.agents.toolkits.communication.toolkit_handoff import transfer_to_trader, HANDOFF_SIGNAL
        result = transfer_to_trader.invoke({"reason": "风控通过"})
        assert HANDOFF_SIGNAL in result
        assert "trader" in result

    def test_handoff_signal_detectable(self):
        from app.agents.toolkits.communication.toolkit_handoff import transfer_to_analyst, HANDOFF_SIGNAL
        from app.agents.toolkits.communication.toolkit_router import detect_handoff

        result = transfer_to_analyst.invoke({"reason": "test"})
        fake_state = {"messages": [type("Msg", (), {"content": result})()]}
        target = detect_handoff(fake_state)
        assert target == "analyst"
