"""
测试: 对话工具 — ask_X
"""


class TestDialogueTools:
    def test_ask_analyst(self):
        from app.agents.toolkits.communication.toolkit_dialogue import ask_analyst, ASK_SIGNAL
        result = ask_analyst.invoke({"question": "你怎么看当前RSI？"})
        assert ASK_SIGNAL in result
        assert "analyst" in result
        assert "RSI" in result

    def test_ask_reviewer(self):
        from app.agents.toolkits.communication.toolkit_dialogue import ask_reviewer, ASK_SIGNAL
        result = ask_reviewer.invoke({"question": "历史类似形态胜率？"})
        assert ASK_SIGNAL in result
        assert "reviewer" in result

    def test_ask_signal_detectable(self):
        from app.agents.toolkits.communication.toolkit_dialogue import ask_analyst
        from app.agents.toolkits.communication.toolkit_router import detect_ask

        result = ask_analyst.invoke({"question": "test question"})
        fake_state = {"messages": [type("Msg", (), {"content": result})()]}
        target, question = detect_ask(fake_state)
        assert target == "analyst"
        assert "test" in question
