import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

st.set_page_config(
    page_title="BTC 量化交易机器人",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CDN 注入：DaisyUI + Tailwind + ByteDance IconPark ─────────────────────────
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css" rel="stylesheet" type="text/css" />
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/@icon-park/web@latest/lib/index.js"></script>
<style>
  /* ── 隐藏 Streamlit 默认 UI ── */
  #MainMenu, footer, header { visibility: hidden; }
  .stDeployButton { display: none; }

  /* ── 全局背景 ── */
  .stApp {
    background: linear-gradient(135deg, #0d0b1e 0%, #1a1535 45%, #0e1626 100%) !important;
    min-height: 100vh;
  }
  .main .block-container {
    padding: 1.5rem 2.5rem !important;
    max-width: 100% !important;
  }

  /* ── 设计变量 ── */
  :root {
    --brand:   #667eea;
    --brand2:  #764ba2;
    --green:   #38ef7d;
    --red:     #f5576c;
    --gold:    #ffd93d;
    --orange:  #ff9a3d;
    --card:    rgba(18, 18, 34, 0.88);
    --card2:   rgba(33, 33, 56, 0.88);
    --border:  rgba(102, 126, 234, 0.18);
    --text:    #ddddf0;
    --muted:   #7878a0;
  }

  /* ── 玻璃卡片基础 ── */
  .g-card {
    background: linear-gradient(135deg, var(--card) 0%, var(--card2) 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 22px;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
    transition: transform .2s ease, box-shadow .2s ease;
  }
  .g-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 44px rgba(102, 126, 234, 0.18);
  }

  /* ── KPI 指标卡片 ── */
  .kpi {
    background: linear-gradient(135deg, var(--card) 0%, var(--card2) 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 22px 24px;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    height: 100%;
    box-sizing: border-box;
    transition: transform .2s ease, box-shadow .2s ease;
  }
  .kpi:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 48px rgba(102, 126, 234, 0.24);
  }
  .kpi-icon {
    width: 44px; height: 44px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 21px;
    margin-bottom: 14px;
  }
  .kpi-icon.brand  { background: rgba(102, 126, 234, 0.18); }
  .kpi-icon.green  { background: rgba(56, 239, 125, 0.15); }
  .kpi-icon.gold   { background: rgba(255, 217, 61,  0.15); }
  .kpi-icon.purple { background: rgba(118, 75,  162, 0.18); }
  .kpi-icon.red    { background: rgba(245, 87,  108, 0.15); }

  .kpi-label {
    font-size: 11px; font-weight: 600;
    color: var(--muted);
    letter-spacing: .08em; text-transform: uppercase;
    margin-bottom: 6px;
  }
  .kpi-value {
    font-size: 26px; font-weight: 800;
    color: var(--text); line-height: 1.1;
  }
  .kpi-delta { font-size: 13px; font-weight: 600; margin-top: 6px; }
  .kpi-delta.up      { color: var(--green); }
  .kpi-delta.down    { color: var(--red); }
  .kpi-delta.neutral { color: var(--muted); }

  /* ── 状态横幅 ── */
  .status-banner {
    border-radius: 16px;
    padding: 14px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 22px;
  }
  .status-banner.running {
    background: linear-gradient(135deg, rgba(102,126,234,.10), rgba(118,75,162,.10));
    border: 1px solid rgba(102, 126, 234, .30);
  }
  .status-banner.stopped {
    background: linear-gradient(135deg, rgba(245,87,108,.08), rgba(240,147,251,.08));
    border: 1px solid rgba(245, 87, 108, .30);
  }
  .status-banner.warning {
    background: linear-gradient(135deg, rgba(255,217,61,.08), rgba(255,154,61,.10));
    border: 1px solid rgba(255, 217, 61, .30);
  }
  .s-dot {
    display: inline-block; width: 9px; height: 9px;
    border-radius: 50%; margin-right: 8px;
    animation: dot-pulse 2s ease-in-out infinite;
  }
  .s-dot.running { background: var(--green); box-shadow: 0 0 8px var(--green); }
  .s-dot.stopped { background: var(--red);   box-shadow: 0 0 8px var(--red); animation: none; }
  .s-dot.warning { background: var(--gold);  box-shadow: 0 0 8px var(--gold); }
  .s-badge {
    padding: 4px 13px; border-radius: 20px;
    font-size: 11px; font-weight: 700;
    letter-spacing: .1em; text-transform: uppercase;
  }
  .s-badge.running { background: rgba(56,239,125,.14); color: var(--green); border: 1px solid rgba(56,239,125,.30); }
  .s-badge.stopped { background: rgba(245,87,108,.14); color: var(--red);   border: 1px solid rgba(245,87,108,.30); }
  .s-badge.warning { background: rgba(255,217,61,.14); color: var(--gold);  border: 1px solid rgba(255,217,61,.30); }

  /* ── AI 信号大卡片 ── */
  .ai-card {
    border-radius: 20px;
    padding: 30px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .ai-card::before {
    content: "";
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at center 30%, rgba(255,255,255,.04) 0%, transparent 70%);
    pointer-events: none;
  }
  .ai-card.buy  {
    background: linear-gradient(135deg, rgba(17,153,142,.18), rgba(56,239,125,.12));
    border: 2px solid rgba(56,239,125,.35);
    animation: glow-g 2.5s ease-in-out infinite alternate;
  }
  .ai-card.sell {
    background: linear-gradient(135deg, rgba(240,147,251,.12), rgba(245,87,108,.18));
    border: 2px solid rgba(245,87,108,.35);
    animation: glow-r 2.5s ease-in-out infinite alternate;
  }
  .ai-card.hold {
    background: linear-gradient(135deg, rgba(255,217,61,.10), rgba(255,154,61,.12));
    border: 2px solid rgba(255,217,61,.28);
  }
  .ai-sig { font-size: 64px; font-weight: 900; letter-spacing: .06em; line-height: 1; margin: 0; }
  .ai-card.buy  .ai-sig { color: var(--green); text-shadow: 0 0 40px rgba(56,239,125,.5); }
  .ai-card.sell .ai-sig { color: var(--red);   text-shadow: 0 0 40px rgba(245,87,108,.5); }
  .ai-card.hold .ai-sig { color: var(--gold);  text-shadow: 0 0 40px rgba(255,217,61,.4); }

  /* ── 信心徽章 ── */
  .conf {
    display: inline-block;
    padding: 5px 16px; border-radius: 20px;
    font-size: 12px; font-weight: 700;
    margin: 12px 0;
  }
  .conf.high   { background: rgba(56,239,125,.14); color: var(--green); border: 1px solid rgba(56,239,125,.30); }
  .conf.medium { background: rgba(255,217,61,.14); color: var(--gold);  border: 1px solid rgba(255,217,61,.30); }
  .conf.low    { background: rgba(245,87,108,.14); color: var(--red);   border: 1px solid rgba(245,87,108,.30); }
  .conf.na     { background: rgba(120,120,160,.10); color: var(--muted); border: 1px solid rgba(120,120,160,.22); }

  /* ── 止损 / 止盈 ── */
  .tpsl { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
  .tpsl-item { border-radius: 12px; padding: 14px; text-align: center; }
  .tpsl-item.sl { background: rgba(245,87,108,.07); border: 1px solid rgba(245,87,108,.20); }
  .tpsl-item.tp { background: rgba(56,239,125,.07);  border: 1px solid rgba(56,239,125,.20); }
  .tpsl-label { font-size: 10px; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 6px; }
  .tpsl-item.sl .tpsl-val { font-size: 19px; font-weight: 800; color: var(--red); }
  .tpsl-item.tp .tpsl-val { font-size: 19px; font-weight: 800; color: var(--green); }

  /* ── 区块标题 ── */
  .sec-head {
    display: flex; align-items: center; gap: 9px;
    margin-bottom: 14px; padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }
  .sec-head .sh-icon { font-size: 16px; }
  .sec-head span {
    font-size: 13px; font-weight: 700;
    color: var(--text); letter-spacing: .05em; text-transform: uppercase;
  }

  /* ── 绩效卡片 ── */
  .perf-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
  .perf-item {
    text-align: center; padding: 16px 10px;
    border-radius: 14px;
    background: rgba(102,126,234,.06);
    border: 1px solid var(--border);
  }
  .perf-item .p-label { font-size: 10px; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: .07em; margin-bottom: 6px; }
  .perf-item .p-val   { font-size: 22px; font-weight: 800; }

  /* ── 持仓方向标签 ── */
  .dir-long  { color: var(--green); font-weight: 800; background: rgba(56,239,125,.12); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(56,239,125,.28); }
  .dir-short { color: var(--red);   font-weight: 800; background: rgba(245,87,108,.12); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(245,87,108,.28); }

  /* ── 交易记录表格 ── */
  .t-table { width: 100%; border-collapse: collapse; font-size: 13px; color: var(--text); }
  .t-table th {
    color: var(--muted); font-size: 10px; font-weight: 700;
    letter-spacing: .08em; text-transform: uppercase;
    padding: 9px 14px; border-bottom: 1px solid var(--border);
    text-align: left; background: transparent;
  }
  .t-table td { padding: 9px 14px; border-bottom: 1px solid rgba(102,126,234,.06); }
  .t-table tr:hover td { background: rgba(102,126,234,.06); }
  .t-sig-buy  { color: var(--green); font-weight: 700; }
  .t-sig-sell { color: var(--red);   font-weight: 700; }
  .t-sig-hold { color: var(--gold);  font-weight: 700; }

  /* ── 按钮 ── */
  .stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; padding: 8px 18px !important;
    font-weight: 600 !important; font-size: 13px !important;
    box-shadow: 0 4px 14px rgba(102,126,234,.28) !important;
    transition: all .2s ease !important;
  }
  .stButton > button:hover {
    box-shadow: 0 8px 22px rgba(102,126,234,.5) !important;
    transform: translateY(-1px) !important;
  }
  .stCheckbox label { color: var(--muted) !important; font-size: 13px !important; }

  /* ── 页面标题 ── */
  .page-title {
    font-size: 26px; font-weight: 900;
    background: linear-gradient(135deg, #667eea 0%, #a78bfa 50%, #764ba2 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0;
  }
  .page-subtitle { font-size: 12px; color: var(--muted); margin: 3px 0 0 0; }

  /* ── 动画 ── */
  @keyframes glow-g { from { box-shadow: 0 8px 32px rgba(56,239,125,.15); } to { box-shadow: 0 8px 40px rgba(56,239,125,.42); } }
  @keyframes glow-r { from { box-shadow: 0 8px 32px rgba(245,87,108,.15); } to { box-shadow: 0 8px 40px rgba(245,87,108,.42); } }
  @keyframes dot-pulse { 0%,100% { opacity:1; } 50% { opacity:.4; } }

  /* ── 滚动条 ── */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: rgba(18,18,34,.5); }
  ::-webkit-scrollbar-thumb { background: linear-gradient(#667eea, #764ba2); border-radius: 3px; }

  /* ── Streamlit 内置组件微调 ── */
  .stAlert { border-radius: 12px !important; }
  [data-testid="column"] { overflow: visible !important; }
</style>
""", unsafe_allow_html=True)

# ── 数据文件路径 ───────────────────────────────────────────────────────────────
DATA_FILE   = "trading_data.json"
TRADES_FILE = "trades_history.json"


# ── 数据加载函数 ───────────────────────────────────────────────────────────────
def load_trading_data():
    """从 DB 加载系统状态，fallback 到 JSON"""
    try:
        from data_manager import load_trading_data_from_db
        data = load_trading_data_from_db()
        if data is not None and data.get("account", {}).get("equity", 0) > 0:
            # 检查数据是否过期
            if "last_update" in data:
                try:
                    last_update = datetime.strptime(data["last_update"], "%Y-%m-%d %H:%M:%S")
                    if (datetime.now() - last_update).total_seconds() > 1800:
                        data["status"] = "warning"
                except Exception:
                    pass
            return data
        # DB 为空，fallback 到 JSON
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "last_update" in data:
                try:
                    last_update = datetime.strptime(data["last_update"], "%Y-%m-%d %H:%M:%S")
                    if (datetime.now() - last_update).total_seconds() > 1800:
                        data["status"] = "warning"
                except Exception:
                    pass
            return data
    except Exception:
        pass

    # 兜底：返回默认空数据
    return {
        "status": "stopped", "last_update": "N/A",
        "account": {"balance": 0, "equity": 0, "leverage": 0},
        "btc": {"price": 0, "change": 0, "timeframe": "1h", "mode": "全仓-单向"},
        "position": None,
        "performance": {"total_pnl": 0, "win_rate": 0, "total_trades": 0},
        "ai_signal": {
            "signal": "HOLD", "confidence": "N/A",
            "reason": "等待交易程序启动...",
            "stop_loss": 0, "take_profit": 0, "timestamp": "N/A"
        },
        "file_not_found": True,
    }


def load_trades_history():
    """从 DB 加载交易历史，fallback 到 JSON"""
    try:
        from data_manager import load_trades_history_from_db
        trades = load_trades_history_from_db()
        if trades:
            return trades
    except Exception:
        pass
    try:
        if os.path.exists(TRADES_FILE):
            with open(TRADES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


# ── 图表函数 ──────────────────────────────────────────────────────────────────
def create_equity_chart():
    try:
        from data_manager import load_equity_history_from_db
        equity_history = load_equity_history_from_db()
        if not equity_history:
            from data_manager import load_equity_history
            equity_history = load_equity_history()

        _empty_layout = dict(
            height=420,
            plot_bgcolor="rgba(18,18,34,.6)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
        )

        if not equity_history:
            fig = go.Figure()
            fig.add_annotation(text="暂无权益数据", xref="paper", yref="paper",
                               x=.5, y=.5, showarrow=False,
                               font=dict(size=18, color="#667eea"))
            fig.update_layout(**_empty_layout)
            return fig

        df = pd.DataFrame(equity_history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        init_eq    = df["equity"].iloc[0]
        curr_eq    = df["equity"].iloc[-1]
        eq_delta   = curr_eq - init_eq
        eq_pct     = (eq_delta / init_eq * 100) if init_eq > 0 else 0

        line_col = "#38ef7d" if eq_delta >= 0 else "#f5576c"
        fill_col = "rgba(56,239,125,.18)" if eq_delta >= 0 else "rgba(245,87,108,.18)"

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"], y=df["equity"],
            mode="lines",
            name="账户总权益",
            line=dict(color=line_col, width=2.5, shape="spline"),
            fill="tozeroy", fillcolor=fill_col,
            hovertemplate="<b>%{x}</b><br>总权益: %{y:.2f} USDT<extra></extra>",
        ))
        fig.add_hline(
            y=init_eq,
            line_dash="dot", line_color="rgba(255,255,255,.25)", line_width=1.5,
            annotation_text=f"初始 {init_eq:.2f}", annotation_font_color="#9090b0",
            annotation_position="right",
        )
        fig.update_layout(
            title=dict(
                text=f"账户总权益  <span style='font-size:14px; color:{'#38ef7d' if eq_delta>=0 else '#f5576c'}'>"
                     f"{eq_delta:+.2f} USDT ({eq_pct:+.2f}%)</span>",
                font=dict(size=17, color="#ddddf0"), x=0.02, xanchor="left",
            ),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,.06)", color="#7878a0",
                       title_font=dict(size=12, color="#7878a0")),
            yaxis=dict(title="USDT", showgrid=True, gridcolor="rgba(255,255,255,.06)",
                       color="#7878a0", title_font=dict(size=12, color="#7878a0")),
            height=420, hovermode="x unified", showlegend=False,
            plot_bgcolor="rgba(18,18,34,.6)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ddddf0", family="Inter, sans-serif"),
            margin=dict(l=60, r=40, t=50, b=50),
        )
        return fig

    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"加载失败: {e}", xref="paper", yref="paper",
                           x=.5, y=.5, showarrow=False, font=dict(size=14, color="#f5576c"))
        fig.update_layout(height=420, plot_bgcolor="rgba(18,18,34,.6)", paper_bgcolor="rgba(0,0,0,0)")
        return fig


def create_signal_distribution_chart(trades_history):
    _empty = dict(
        height=320, plot_bgcolor="rgba(18,18,34,.6)", paper_bgcolor="rgba(0,0,0,0)"
    )
    if not trades_history:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", xref="paper", yref="paper",
                           x=.5, y=.5, showarrow=False, font=dict(size=16, color="#667eea"))
        fig.update_layout(**_empty)
        return fig

    df    = pd.DataFrame(trades_history)
    cnts  = df["signal"].value_counts()
    clrs  = {"BUY": "#38ef7d", "SELL": "#f5576c", "HOLD": "#ffd93d"}

    fig = go.Figure(data=[go.Pie(
        labels=cnts.index, values=cnts.values,
        marker=dict(
            colors=[clrs.get(s, "#667eea") for s in cnts.index],
            line=dict(color="rgba(18,18,34,.8)", width=3),
        ),
        hole=.55,
        textinfo="label+percent",
        textfont=dict(size=13, color="white"),
        hovertemplate="<b>%{label}</b><br>数量: %{value}<br>%{percent}<extra></extra>",
    )])
    fig.update_layout(
        title=dict(text="信号分布", font=dict(size=15, color="#ddddf0"), x=.5, xanchor="center"),
        height=320, showlegend=True,
        legend=dict(font=dict(color="#ddddf0", size=11),
                    bgcolor="rgba(18,18,34,.5)",
                    bordercolor="rgba(102,126,234,.2)", borderwidth=1),
        plot_bgcolor="rgba(18,18,34,.6)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=44, b=10),
    )
    return fig


# ── HTML 组件构建函数 ──────────────────────────────────────────────────────────
def kpi_card(icon, icon_cls, label, value, delta=None, delta_cls="neutral"):
    delta_html = f'<div class="kpi-delta {delta_cls}">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi">
      <div class="kpi-icon {icon_cls}">{icon}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {delta_html}
    </div>
    """


def section_head(icon, title):
    return f"""
    <div class="sec-head">
      <span class="sh-icon">{icon}</span>
      <span>{title}</span>
    </div>
    """


# ── 主应用 ────────────────────────────────────────────────────────────────────
def main():
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()

    # ── 页面标题 ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; gap:14px; margin-bottom:22px;">
      <div style="width:48px;height:48px;border-radius:14px;
                  background:linear-gradient(135deg,#667eea,#764ba2);
                  display:flex;align-items:center;justify-content:center;
                  font-size:26px;box-shadow:0 6px 20px rgba(102,126,234,.4);">
        🤖
      </div>
      <div>
        <div class="page-title">BTC 自动交易机器人</div>
        <div class="page-subtitle">AI 量化交易平台 · 实时监控仪表盘</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 控制栏 ────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1, 1.5, 5])
    with c1:
        if st.button("↻  刷新数据", use_container_width=True):
            st.session_state.last_refresh = time.time()
            st.rerun()
    with c2:
        auto = st.checkbox("⏱ 自动刷新 (10s)", value=st.session_state.auto_refresh, key="arc")
        if auto != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto
            st.session_state.last_refresh = time.time()

    # ── 数据加载 ──────────────────────────────────────────────────────────────
    data           = load_trading_data()
    trades_history = load_trades_history()

    if data is None:
        st.error("无法加载数据，请检查交易程序是否运行。")
        return

    if data.get("file_not_found"):
        st.warning("""
**⚠️ 未检测到交易数据文件**

1. 确保已启动交易程序 `deepseekok2.py`
2. 启动后会自动创建数据文件
3. 刷新此页面即可查看实时数据

```
python deepseekok2.py
```
""")

    # ── 运行状态横幅 ──────────────────────────────────────────────────────────
    status = data.get("status", "stopped")
    s_cls  = "running" if status == "running" else ("warning" if status == "warning" else "stopped")
    s_icon = "🟢" if s_cls == "running" else ("🟡" if s_cls == "warning" else "🔴")
    s_text = "RUNNING" if s_cls == "running" else ("WARNING" if s_cls == "warning" else "STOPPED"  )
    s_desc = "交易机器人运行正常" if s_cls == "running" else \
             ("数据超过30分钟未更新" if s_cls == "warning" else "交易机器人已停止")

    st.markdown(f"""
    <div class="status-banner {s_cls}">
      <div style="display:flex;align-items:center;gap:8px;">
        <span class="s-dot {s_cls}"></span>
        <span style="color:var(--text);font-size:15px;font-weight:700;">{s_desc}</span>
        <span style="color:var(--muted);font-size:13px;margin-left:6px;">
          最后更新: {data.get('last_update','N/A')}
        </span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="color:var(--muted);font-size:12px;">
          {data.get('btc',{}).get('timeframe','1h')} · {data.get('btc',{}).get('mode','全仓-单向')}
        </span>
        <span class="s-badge {s_cls}">{s_icon} {s_text}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 第一行：4 个 KPI 指标卡片 ─────────────────────────────────────────────
    st.markdown('<div style="margin-bottom:6px;"></div>', unsafe_allow_html=True)
    kc1, kc2, kc3, kc4 = st.columns(4)

    btc_change = data["btc"]["change"]
    delta_cls  = "up" if btc_change > 0 else ("down" if btc_change < 0 else "neutral")
    delta_sym  = "▲" if btc_change > 0 else ("▼" if btc_change < 0 else "—")

    with kc1:
        st.markdown(kpi_card(
            "💰", "brand",
            "可用余额",
            f"{data['account']['balance']:,.2f} USDT",
        ), unsafe_allow_html=True)

    with kc2:
        st.markdown(kpi_card(
            "📊", "green",
            "账户总权益",
            f"{data['account']['equity']:,.2f} USDT",
        ), unsafe_allow_html=True)

    with kc3:
        st.markdown(kpi_card(
            "⚡", "gold",
            "杠杆倍数",
            f"{data['account']['leverage']}x",
        ), unsafe_allow_html=True)

    with kc4:
        st.markdown(kpi_card(
            "₿", "purple",
            "BTC / USDT",
            f"${data['btc']['price']:,.2f}",
            delta=f"{delta_sym} {abs(btc_change):.2f}%",
            delta_cls=delta_cls,
        ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 第二行：权益曲线 ──────────────────────────────────────────────────────
    st.markdown(section_head("📈", "账户总权益曲线"), unsafe_allow_html=True)
    st.plotly_chart(
        create_equity_chart(),
        use_container_width=True,
        config={"displayModeBar": True, "displaylogo": False,
                "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 第三行：持仓 + 绩效 ───────────────────────────────────────────────────
    pc1, pc2 = st.columns(2)

    with pc1:
        st.markdown(section_head("📦", "当前持仓"), unsafe_allow_html=True)
        if data["position"]:
            pos      = data["position"]
            is_long  = pos["side"].lower() == "long"
            dir_cls  = "dir-long" if is_long else "dir-short"
            dir_txt  = "LONG  ↑" if is_long else "SHORT ↓"
            pnl      = pos["unrealized_pnl"]
            pnl_col  = "var(--green)" if pnl >= 0 else "var(--red)"
            pnl_sym  = "▲" if pnl >= 0 else "▼"
            border_c = "rgba(56,239,125,.35)" if is_long else "rgba(245,87,108,.35)"
            st.markdown(f"""
            <div class="g-card" style="border-left:3px solid {border_c};">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
                <span class="{dir_cls}">{dir_txt}</span>
                <span style="color:var(--muted);font-size:12px;">
                  数量: <b style="color:var(--text);">{pos['size']:.2f} 张</b>
                </span>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <div style="background:rgba(102,126,234,.07);border-radius:12px;padding:14px;">
                  <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">入场价格</div>
                  <div style="font-size:20px;font-weight:800;color:var(--gold);">${pos['entry_price']:,.2f}</div>
                </div>
                <div style="background:rgba(102,126,234,.07);border-radius:12px;padding:14px;">
                  <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">未实现盈亏</div>
                  <div style="font-size:20px;font-weight:800;color:{pnl_col};">{pnl_sym} {abs(pnl):.2f} USDT</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="g-card" style="text-align:center;padding:40px 24px;">
              <div style="font-size:36px;margin-bottom:10px;opacity:.4;">📭</div>
              <div style="color:var(--muted);font-size:14px;">当前无持仓</div>
            </div>
            """, unsafe_allow_html=True)

    with pc2:
        st.markdown(section_head("🏆", "绩效统计"), unsafe_allow_html=True)
        perf     = data["performance"]
        pnl_tot  = perf["total_pnl"]
        wr       = perf["win_rate"]
        pnl_col  = "var(--green)" if pnl_tot >= 0 else "var(--red)"
        pnl_sym  = "▲" if pnl_tot >= 0 else "▼"
        wr_col   = "var(--green)" if wr >= 50 else "var(--red)"
        st.markdown(f"""
        <div class="g-card">
          <div class="perf-grid">
            <div class="perf-item">
              <div class="p-label">总盈亏</div>
              <div class="p-val" style="color:{pnl_col};">{pnl_sym}{abs(pnl_tot):.2f}</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">USDT</div>
            </div>
            <div class="perf-item">
              <div class="p-label">胜率</div>
              <div class="p-val" style="color:{wr_col};">{wr:.1f}<span style="font-size:16px;">%</span></div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">Win Rate</div>
            </div>
            <div class="perf-item">
              <div class="p-label">总交易</div>
              <div class="p-val" style="color:var(--brand);">{perf['total_trades']}</div>
              <div style="font-size:11px;color:var(--muted);margin-top:3px;">次</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 第四行：AI 信号 + 信号分布 ────────────────────────────────────────────
    ac1, ac2 = st.columns([2, 1])

    with ac1:
        st.markdown(section_head("🤖", "AI 实时决策"), unsafe_allow_html=True)
        ai      = data["ai_signal"]
        sig     = ai["signal"]
        sig_cls = {"BUY": "buy", "SELL": "sell", "HOLD": "hold"}.get(sig, "hold")
        sig_ico = {"BUY": "📈", "SELL": "📉", "HOLD": "⏸"}.get(sig, "⏸")

        conf_raw = ai["confidence"]
        conf_cls = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(conf_raw, "na")
        conf_txt = {"HIGH": "🔥 高信心", "MEDIUM": "⚡ 中信心", "LOW": "⚠️ 低信心"}.get(conf_raw, "⏳ 待分析")

        st.markdown(f"""
        <div class="ai-card {sig_cls}">
          <div style="font-size:22px;margin-bottom:4px;">{sig_ico}</div>
          <div class="ai-sig">{sig}</div>
          <div><span class="conf {conf_cls}">{conf_txt}</span></div>
          <div style="font-size:12px;color:rgba(255,255,255,.5);margin-top:4px;">
            ⏰ {ai.get('timestamp','N/A')}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 分析理由 + TP/SL
        sl_price = ai.get("stop_loss", 0)
        tp_price = ai.get("take_profit", 0)
        st.markdown(f"""
        <div class="g-card" style="margin-top:12px;">
          <div style="font-size:13px;color:var(--text);line-height:1.7;margin-bottom:16px;">
            <span style="color:var(--muted);font-size:11px;font-weight:700;
                         text-transform:uppercase;letter-spacing:.07em;">分析理由</span><br>
            {ai.get('reason','—')}
          </div>
          <div class="tpsl">
            <div class="tpsl-item sl">
              <div class="tpsl-label">🛑 止损价</div>
              <div class="tpsl-val">${sl_price:,.2f}</div>
            </div>
            <div class="tpsl-item tp">
              <div class="tpsl-label">✅ 止盈价</div>
              <div class="tpsl-val">${tp_price:,.2f}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with ac2:
        st.markdown(section_head("🎯", "信号分布"), unsafe_allow_html=True)
        st.plotly_chart(
            create_signal_distribution_chart(trades_history),
            use_container_width=True,
            config={"displayModeBar": False, "displaylogo": False},
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 第五行：交易记录 ──────────────────────────────────────────────────────
    st.markdown(section_head("📝", "近期交易记录"), unsafe_allow_html=True)
    if trades_history:
        df_t = pd.DataFrame(trades_history).tail(20).iloc[::-1].reset_index(drop=True)

        def _sig_cls(s):
            return {"BUY": "t-sig-buy", "SELL": "t-sig-sell"}.get(s, "t-sig-hold")

        rows_html = ""
        for _, row in df_t.iterrows():
            ts    = pd.to_datetime(row.get("timestamp", "")).strftime("%m-%d %H:%M") if row.get("timestamp") else "—"
            sig   = row.get("signal", "—")
            price = f"${float(row.get('price', 0)):,.2f}"
            amt   = f"{float(row.get('amount', 0)):.3f}"
            conf  = row.get("confidence", "—")
            pnl   = row.get("pnl", 0)
            pnl_html = (
                f'<span style="color:var(--green);">+{pnl:.2f}</span>' if pnl > 0
                else (f'<span style="color:var(--red);">{pnl:.2f}</span>' if pnl < 0
                      else '<span style="color:var(--muted);">—</span>')
            )
            reason_short = str(row.get("reason", ""))[:40] + ("…" if len(str(row.get("reason", ""))) > 40 else "")
            rows_html += f"""
            <tr>
              <td style="color:var(--muted);">{ts}</td>
              <td><span class="{_sig_cls(sig)}">{sig}</span></td>
              <td style="color:var(--gold);">{price}</td>
              <td>{amt}</td>
              <td>{pnl_html}</td>
              <td style="color:var(--muted);">{conf}</td>
              <td style="color:var(--muted);max-width:200px;overflow:hidden;">{reason_short}</td>
            </tr>
            """

        st.markdown(f"""
        <div class="g-card" style="padding:0;overflow:hidden;">
          <div style="overflow-x:auto;max-height:420px;overflow-y:auto;">
            <table class="t-table">
              <thead>
                <tr>
                  <th>时间</th><th>信号</th><th>价格</th>
                  <th>数量</th><th>盈亏</th><th>信心</th><th>理由</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="g-card" style="text-align:center;padding:40px 24px;">
          <div style="font-size:32px;margin-bottom:10px;opacity:.35;">📭</div>
          <div style="color:var(--muted);font-size:14px;">暂无交易记录</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 页脚 ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:16px 0 4px;
                border-top:1px solid rgba(102,126,234,.12);
                color:rgba(120,120,160,.5);font-size:11px;letter-spacing:.06em;">
      BTC 量化交易机器人 · Powered by AI · 数据仅供参考，不构成投资建议
    </div>
    """, unsafe_allow_html=True)

    # ── 自动刷新逻辑 ──────────────────────────────────────────────────────────
    if st.session_state.auto_refresh:
        elapsed = time.time() - st.session_state.last_refresh
        if elapsed >= 10:
            st.session_state.last_refresh = time.time()
            time.sleep(0.05)
            st.rerun()
        else:
            remaining = int(10 - elapsed)
            st.markdown(f"""
            <div style="text-align:center;padding:8px;
                        color:var(--muted);font-size:12px;">
              ⏳ 下次自动刷新 <b style="color:var(--brand);">{remaining}s</b> 后
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1)
            st.rerun()


if __name__ == "__main__":
    main()
