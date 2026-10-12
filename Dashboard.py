import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import serial
import serial.tools.list_ports
from collections import deque
from datetime import datetime
import time

# PAGE CONFIG
st.set_page_config(
    page_title="Smart Building: Climate Control",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* ── Root variables (Light Theme) ───────────────── */
:root {
    --bg:        #f4f7f6;
    --surface:   #ffffff;
    --surface2:  #f8f9fc;
    --border:    #e5e9f2;
    --primary:   #c75fed;
    --accent:    #42d4d4;
    --safe:      #2ec4b6;
    --warn:      #f59e0b;
    --danger:    #ef4444;
    --purple:    #c75fed;
    --text:      #334155;
    --muted:     #94a3b8;
    --radius:    14px;
}

/* ── App background ─────────────────────────────── */
.stApp {
    background: var(--bg);
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

/* ── Hide default Streamlit chrome ──────────────── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem 2rem !important; }

/* ── Sidebar ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(195deg, #c75fed 0%, #a13ce1 100%) !important;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stRadio > label { 
    font-size: 0.78rem;
    color: rgba(255,255,255,0.7) !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin-bottom: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    border-color: rgba(255,255,255,0.4);
    background: rgba(255,255,255,0.15);
}

/* ── Page title ─────────────────────────────────── */
.page-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.02em;
    margin-bottom: 0.15rem;
}
.page-subtitle {
    font-size: 0.85rem;
    color: var(--muted);
    margin-bottom: 1.5rem;
}

/* ── Metric cards ────────────────────────────────── */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
}
.metric-card:hover { border-color: var(--primary); }
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent-color, var(--primary));
    border-radius: var(--radius) var(--radius) 0 0;
}
.metric-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 0.4rem;
}
.metric-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    font-weight: 600;
    line-height: 1;
    color: var(--text);
}
.metric-unit {
    font-size: 1rem;
    font-weight: 400;
    color: var(--muted);
    margin-left: 2px;
}
.metric-delta {
    font-size: 0.78rem;
    margin-top: 0.5rem;
    color: var(--muted);
}
.metric-delta.up   { color: var(--safe); }
.metric-delta.down { color: var(--danger); }
.metric-icon {
    position: absolute;
    right: 1.2rem; top: 1rem;
    font-size: 1.6rem;
    opacity: 0.25;
}

/* ── Section headers ─────────────────────────────── */
.section-header {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin: 1.5rem 0 0.8rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

/* ── Chart container ─────────────────────────────── */
.chart-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
}
.chart-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.2rem;
}
.chart-desc {
    font-size: 0.75rem;
    color: var(--muted);
    margin-bottom: 0.8rem;
}

/* ── Insight cards ───────────────────────────────── */
.insight-card {
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    border-left: 3px solid transparent;
    animation: slideIn 0.3s ease;
}
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-8px); }
    to   { opacity: 1; transform: translateX(0); }
}
.insight-card.safe  { background: rgba(46,196,182,0.1);  border-color: var(--safe);   }
.insight-card.warn  { background: rgba(245,158,11,0.1);  border-color: var(--warn);   }
.insight-card.alert { background: rgba(239, 68, 68,0.1); border-color: var(--danger); }
.insight-icon  { font-size: 1.3rem; flex-shrink: 0; }
.insight-msg   { font-size: 0.86rem; color: var(--text); line-height: 1.4; }

/* ── Status badge ────────────────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.status-badge.safe    { background: rgba(46,196,182,0.15);  color: var(--safe);   border: 1px solid rgba(46,196,182,0.3);  }
.status-badge.warn    { background: rgba(245,158,11,0.15);  color: var(--warn);   border: 1px solid rgba(245,158,11,0.3);  }
.status-badge.danger  { background: rgba(239,68,68,0.15);   color: var(--danger); border: 1px solid rgba(239,68,68,0.3);   }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; }
.dot.safe    { background: var(--safe);   box-shadow: 0 0 6px var(--safe);   }
.dot.warn    { background: var(--warn);   box-shadow: 0 0 6px var(--warn);   }
.dot.danger  { background: var(--danger); box-shadow: 0 0 6px var(--danger); }

/* ── Occupancy big card ──────────────────────────── */
.occ-card {
    border-radius: var(--radius);
    padding: 2rem;
    text-align: center;
    border: 1px solid var(--border);
    transition: all 0.4s ease;
}
.occ-card.occupied { background: rgba(239,68,68,0.05);  border-color: rgba(239,68,68,0.2); }
.occ-card.empty    { background: rgba(46,196,182,0.05); border-color: rgba(46,196,182,0.2);}
.occ-icon  { font-size: 3.5rem; margin-bottom: 0.5rem; }
.occ-state { font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem; font-weight: 700; margin-bottom: 0.3rem; }
.occ-state.occupied { color: var(--danger); }
.occ-state.empty    { color: var(--safe);   }
.occ-sub   { font-size: 0.8rem; color: var(--muted); }

/* ── Connection pill ─────────────────────────────── */
.conn-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    background: rgba(0,0,0,0.15);
    border: 1px solid rgba(255,255,255,0.2);
    color: #ffffff;
}
.conn-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
}
.conn-dot.connected    { background: var(--safe);  box-shadow: 0 0 8px var(--safe);    animation: pulse 2s infinite; }
.conn-dot.disconnected { background: var(--danger); }
.conn-dot.waiting      { background: var(--warn);  animation: pulse 1.5s infinite; }
@keyframes pulse {
    0%,100% { opacity:1; }
    50%      { opacity:0.4; }
}

/* ── Sidebar brand ───────────────────────────────── */
.brand-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #ffffff !important;
}
.brand-sub {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(255,255,255,0.7) !important;
}
.sidebar-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.15);
    margin: 1rem 0;
}

/* ── Debug panel ─────────────────────────────────── */
.debug-panel {
    background: rgba(0,0,0,0.15);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 0.9rem 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.7);
}
.debug-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
.debug-key { color: rgba(255,255,255,0.7); }
.debug-val { color: #ffffff; }

/* ── Plotly chart override ───────────────────────── */
.js-plotly-plot .plotly { border-radius: var(--radius); }

/* Streamlit's default element spacing */
.stPlotlyChart { border-radius: var(--radius); overflow: hidden; }
div[data-testid="stVerticalBlock"] > div { gap: 0; }

/* ── CRITICAL ALERT MODAL ───────────────────────── */
.modal-overlay {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(0, 0, 0, 0.85);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(5px);
}
.modal-content {
    background: var(--surface);
    border: 2px solid var(--danger);
    border-radius: var(--radius);
    padding: 3rem;
    text-align: center;
    max-width: 600px;
    animation: popIn 0.3s ease-out, pulseAlert 1.5s infinite;
}
.modal-title {
    color: var(--danger);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.modal-text {
    color: var(--text);
    font-size: 1.2rem;
    line-height: 1.6;
}
@keyframes popIn {
    0% { transform: scale(0.9); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}
@keyframes pulseAlert {
    0%, 100% { box-shadow: 0 0 40px rgba(239, 68, 68, 0.4); }
    50% { box-shadow: 0 0 80px rgba(239, 68, 68, 0.9); }
}
</style>
""", unsafe_allow_html=True)

# CONSTANTS
SERIAL_PORT      = "/dev/cu.usbmodem1301" 
BAUD_RATE        = 115200
HISTORY_LENGTH   = 300
REFRESH_INTERVAL = 3         
FIRE_THRESHOLD   = 60.0

# PLOTLY THEME
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#64748b", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(
        bgcolor="rgba(255,255,255,0.6)",
        bordercolor="rgba(0,0,0,0.05)",
        borderwidth=1,
        orientation="h",
        y=1.1, x=0,
    ),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.05)",
        linecolor="rgba(0,0,0,0.1)",
        tickfont=dict(size=10),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.05)",
        linecolor="rgba(0,0,0,0.1)",
        tickfont=dict(size=10),
        zeroline=False,
    ),
)

COLORS = dict(
    temp       = "#c75fed",
    humidity   = "#42d4d4",
    light      = "#3b82f6",
    occupancy  = "#10b981",
    trend      = "#f59e0b",
)

# SERIAL LAYER
def _open_serial():
    if "serial_conn" not in st.session_state:
        st.session_state["serial_conn"]  = None
        st.session_state["serial_error"] = None

    if st.session_state["serial_conn"] and st.session_state["serial_conn"].is_open:
        return

    try:
        conn = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        st.session_state["serial_conn"]  = conn
        st.session_state["serial_error"] = None
    except Exception as e:
        st.session_state["serial_conn"]  = None
        st.session_state["serial_error"] = str(e)


def read_serial_line() -> str | None:
    _open_serial()
    conn = st.session_state.get("serial_conn")
    if conn is None or not conn.is_open:
        return None
    try:
        # CRITICAL FIX: Flush the input buffer to discard stale data
        # so we only read the most recent transmission from the Arduino.
        conn.reset_input_buffer()
        
        raw = conn.readline()
        return raw.decode("utf-8", errors="replace").strip()
    except Exception as e:
        st.session_state["serial_error"] = str(e)
        st.session_state["serial_conn"]  = None
        return None


def parse_serial_line(line: str) -> dict | None:
    if not line:
        return None
    try:
        parts = line.split(",")
        if len(parts) != 4:
            return None
        return {
            "timestamp"  : datetime.now(),
            "temperature": float(parts[0]),
            "humidity"   : float(parts[1]),
            "light_level": int(parts[2]),
            "occupancy"  : int(parts[3]),
        }
    except (ValueError, IndexError):
        return None

# HISTORY STORAGE
def _init_history():
    if "history" not in st.session_state:
        st.session_state["history"]       = deque(maxlen=HISTORY_LENGTH)
        st.session_state["last_read_ok"]  = False
        st.session_state["last_raw_line"] = ""


def history_to_df() -> pd.DataFrame:
    h = list(st.session_state["history"])
    if not h:
        return pd.DataFrame(columns=["timestamp","temperature","humidity","light_level","occupancy","temp_trend"])
    df = pd.DataFrame(h)
    df["temp_trend"] = df["temperature"].rolling(10, min_periods=1).mean()
    return df



# INSIGHTS 
def evaluate_insights(temp, hum, light, occ) -> list[dict]:
    insights = []

    # Temperature
    if temp >= FIRE_THRESHOLD:
        insights.append({"level":"alert", "msg": f"FIRE RISK — Temperature critical at {temp:.1f}°C. Evacuate and alert emergency services."})
    elif temp > 28 and light > 600:
        insights.append({"level":"warn", "msg": f"High temperature ({temp:.1f}°C) with bright light. Close blinds to reduce solar gain."})
    elif temp > 28:
        insights.append({"level":"warn", "msg": f"Temperature above comfort ({temp:.1f}°C). Activate air conditioning."})
    elif temp < 16:
        insights.append({"level":"warn", "msg": f"Temperature below comfort ({temp:.1f}°C). Increase heating."})
    else:
        insights.append({"level":"safe", "msg": f"Temperature is comfortable at {temp:.1f}°C."})

    # Occupancy
    if occ == 0:
        insights.append({"level":"safe", "msg": "Room unoccupied — switching to economy HVAC mode to save energy."})
    else:
        insights.append({"level":"safe", "msg": "Room occupied — standard HVAC active."})

    # Humidity
    if hum > 70:
        insights.append({"level":"warn", "msg": f"High humidity ({hum:.0f}%). Run dehumidifier to prevent mould."})
    elif hum < 30:
        insights.append({"level":"warn", "msg": f"Low humidity ({hum:.0f}%). Activate humidifier for comfort."})
    else:
        insights.append({"level":"safe", "msg": f"Humidity is within healthy range at {hum:.0f}%."})

    # Lighting
    if light < 200 and occ == 1:
        insights.append({"level":"warn", "msg": "Low natural light with occupancy detected — turn on artificial lights."})
    elif light > 800:
        insights.append({"level":"safe", "msg": "Bright natural light — artificial lighting not required."})

    return insights


# CHART 
def _fig_temp_humidity(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["temperature"],
        name="Temperature (°C)", mode="lines",
        line=dict(color=COLORS["temp"], width=2),
        fill="tozeroy", fillcolor="rgba(199,95,237,0.1)",
        yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["humidity"],
        name="Humidity (%)", mode="lines",
        line=dict(color=COLORS["humidity"], width=2, dash="dot"),
        yaxis="y2",
    ))
    layout = {**PLOTLY_LAYOUT,
        "yaxis" : dict(**PLOTLY_LAYOUT["yaxis"], title="°C"),
        "yaxis2": dict(**PLOTLY_LAYOUT["yaxis"], title="%",
                       overlaying="y", side="right"),
        "hovermode": "x unified",
    }
    fig.update_layout(**layout)
    return fig


def _fig_light(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["light_level"],
        name="Light Level (ADC)", mode="lines",
        line=dict(color=COLORS["light"], width=2),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.1)",
    ))
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def _fig_occupancy(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["occupancy"],
        mode="lines", line=dict(color=COLORS["occupancy"], width=2, shape="hv"),
        fill="tozeroy", fillcolor="rgba(16,185,129,0.1)",
        name="Occupancy",
    ))
    fig.update_layout(**{
        **PLOTLY_LAYOUT,
        "yaxis": dict(**PLOTLY_LAYOUT["yaxis"],
                      tickvals=[0, 1], ticktext=["Empty", "Occupied"],
                      range=[-0.1, 1.3]),
    })
    return fig


def _fig_light_scatter(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df, x="temperature", y="light_level", color="humidity",
        color_continuous_scale=px.colors.sequential.Teal,
        labels={"temperature": "Temperature (°C)", "light_level": "Light (ADC)", "humidity": "Humidity (%)"},
        opacity=0.75,
    )
    fig.update_traces(marker=dict(size=6))
    fig.update_coloraxes(colorbar=dict(
        thickness=10, len=0.7, title="Humidity",
        tickfont=dict(size=9, color="#64748b"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def _fig_temp_distribution(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df["temperature"], nbinsx=25,
        marker=dict(color=COLORS["temp"], opacity=0.8,
                    line=dict(color="rgba(0,0,0,0.3)", width=0.5)),
        name="Temperature",
    ))
    fig.update_layout(**{
        **PLOTLY_LAYOUT,
        "bargap": 0.05,
        "xaxis": dict(**PLOTLY_LAYOUT["xaxis"], title="°C"),
        "yaxis": dict(**PLOTLY_LAYOUT["yaxis"], title="Count"),
    })
    return fig


def _fig_temp_prediction(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["temperature"],
        name="Actual", mode="lines",
        line=dict(color=COLORS["temp"], width=1.5, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["temp_trend"],
        name="SMA-10 Trend", mode="lines",
        line=dict(color=COLORS["trend"], width=2.5),
    ))
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def _fig_correlation(df: pd.DataFrame) -> go.Figure:
    cols = ["temperature", "humidity", "light_level", "occupancy"]
    labels = ["Temp", "Humidity", "Light", "Occ"]
    corr = df[cols].corr().values
    fig = go.Figure(go.Heatmap(
        z=corr, x=labels, y=labels,
        colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
        text=np.round(corr, 2), texttemplate="%{text}",
        textfont=dict(size=11),
        colorbar=dict(thickness=10, len=0.8, tickfont=dict(size=9, color="#64748b")),
    ))
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=20, b=0)})
    return fig


# UI COMPONENTS
def _summary_cards(df: pd.DataFrame):
    latest = df.iloc[-1] if len(df) else None
    prev   = df.iloc[-2] if len(df) > 1 else None

    def delta_html(key, fmt="{:.1f}"):
        if prev is None or latest is None:
            return ""
        d = latest[key] - prev[key]
        cls = "up" if d >= 0 else "down"
        sym = "▲" if d >= 0 else "▼"
        return f'<div class="metric-delta {cls}">{sym} {fmt.format(abs(d))} since last reading</div>'

    cols = st.columns(4, gap="small")
    cards = [
        ("temperature", "Temperature",  f"{latest['temperature']:.1f}" if latest is not None else "--",
         "°C", "", "#c75fed", delta_html("temperature")),
        ("humidity",    "Humidity",     f"{latest['humidity']:.1f}"    if latest is not None else "--",
         "%",  "", "#42d4d4", delta_html("humidity")),
        ("light_level", "Light Level",  f"{int(latest['light_level'])}" if latest is not None else "--",
         "ADC","", "#3b82f6", delta_html("light_level", fmt="{:.0f}")),
        ("occupancy",   "Occupancy",    ("Occupied" if latest["occupancy"] else "Empty") if latest is not None else "--",
         "",   "🧍", "#10b981", ""),
    ]
    for col, (key, label, val, unit, icon, color, dlt) in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="--accent-color:{color}">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}<span class="metric-unit">{unit}</span></div>
                {dlt}
            </div>""", unsafe_allow_html=True)


def _fire_badge(df: pd.DataFrame):
    if df.empty:
        return
    temp = df.iloc[-1]["temperature"]
    if temp >= FIRE_THRESHOLD:
        st.markdown('<span class="status-badge danger"><span class="dot danger"></span>FIRE RISK</span>', unsafe_allow_html=True)
    elif temp > 28:
        st.markdown('<span class="status-badge warn"><span class="dot warn"></span>HIGH TEMP WARNING</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge safe"><span class="dot safe"></span>SYSTEM NORMAL</span>', unsafe_allow_html=True)


def _insights_panel(df: pd.DataFrame):
    if df.empty:
        st.markdown('<div class="insight-card warn"><div class="insight-msg">Waiting for sensor data…</div></div>', unsafe_allow_html=True)
        return
    r = df.iloc[-1]
    for ins in evaluate_insights(r["temperature"], r["humidity"], r["light_level"], r["occupancy"]):
        st.markdown(f"""
        <div class="insight-card {ins['level']}">
            <div class="insight-msg">{ins['msg']}</div>
        </div>""", unsafe_allow_html=True)


def _occupancy_card(df: pd.DataFrame):
    if df.empty:
        occ = None
    else:
        occ = int(df.iloc[-1]["occupancy"])
    if occ == 1:
        state, cls, icon, sub = "Occupied", "occupied", "🧍", "IR Break-Beam triggered"
    elif occ == 0:
        state, cls, icon, sub = "Room Empty", "empty", "🪑", "No movement detected"
    else:
        state, cls, icon, sub = "Waiting…", "empty", "", "No data yet"

    st.markdown(f"""
    <div class="occ-card {cls}">
        <div class="occ-icon">{icon}</div>
        <div class="occ-state {cls}">{state}</div>
        <div class="occ-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


def _chart_wrap(title: str, desc: str, fig):
    st.markdown(f"""
    <div class="chart-card">
        <div class="chart-title">{title}</div>
        <div class="chart-desc">{desc}</div>
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _connection_pill():
    err   = st.session_state.get("serial_error")
    ok    = st.session_state.get("last_read_ok", False)
    if ok:
        cls, label = "connected",    "Connected"
    elif err:
        cls, label = "disconnected", "Disconnected"
    else:
        cls, label = "waiting",      "Waiting"
    return f'<span class="conn-pill"><span class="conn-dot {cls}"></span>{label}</span>'


# SIDEBAR
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("""
        <div style="padding:0.5rem 0 0.2rem 0">
            <div class="brand-title">ClimaCore</div>
            <div class="brand-sub">Smart Building IoT</div>
        </div>
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        st.markdown(f"""<div style="margin-bottom:1rem">{_connection_pill()}</div>""",
                    unsafe_allow_html=True)

        st.markdown('<div class="metric-label">Navigation</div>', unsafe_allow_html=True)
        page = st.radio(
            label="",
            options=[
                "Dashboard Overview",
                "Climate Monitoring",
                "Occupancy Monitoring",
                "Lighting Analysis",
                "Smart Analytics",
            ],
            label_visibility="collapsed",
        )

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Hardware Debugger</div>', unsafe_allow_html=True)

        last_raw = st.session_state.get("last_raw_line", "—")
        err_msg  = st.session_state.get("serial_error",  "—") or "—"
        st.markdown(f"""
        <div class="debug-panel">
            <div class="debug-row"><span class="debug-key">port</span><span class="debug-val">{SERIAL_PORT}</span></div>
            <div class="debug-row"><span class="debug-key">baud</span><span class="debug-val">{BAUD_RATE}</span></div>
            <div class="debug-row"><span class="debug-key">last_line</span><span class="debug-val">{last_raw[:20]}</span></div>
            <div class="debug-row"><span class="debug-key">error</span><span class="debug-val" style="color:#ef4444">{err_msg[:22]}</span></div>
        </div>
        """, unsafe_allow_html=True)

    return page


# PAGES
def page_overview(df: pd.DataFrame):
    st.markdown('<div class="page-title">Dashboard Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time snapshot of all building sensors</div>', unsafe_allow_html=True)

    _fire_badge(df)
    st.markdown("<br>", unsafe_allow_html=True)
    _summary_cards(df)

    st.markdown('<div class="section-header">Climate & Light</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        st.markdown('<div class="chart-card"><div class="chart-title">Temperature & Humidity</div><div class="chart-desc">Live dual-axis sensor stream</div>', unsafe_allow_html=True)
        if len(df) > 1:
            st.plotly_chart(_fig_temp_humidity(df), use_container_width=True, config={"displayModeBar": False}, key="overview_temp_hum")
        else:
            st.info("Collecting data…")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-card"><div class="chart-title">Light vs Temperature</div><div class="chart-desc">Scatter coloured by humidity</div>', unsafe_allow_html=True)
        if len(df) > 5:
            st.plotly_chart(_fig_light_scatter(df), use_container_width=True, config={"displayModeBar": False}, key="overview_scatter")
        else:
            st.info("Collecting data…")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Occupancy & Recommendations</div>', unsafe_allow_html=True)
    c3, c4 = st.columns([1, 2], gap="medium")
    with c3:
        _occupancy_card(df)
    with c4:
        _insights_panel(df)


def page_climate(df: pd.DataFrame):
    st.markdown('<div class="page-title">Climate Monitoring</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Temperature, humidity trends and HVAC recommendations</div>', unsafe_allow_html=True)

    _summary_cards(df)
    st.markdown('<div class="section-header">Temperature & Humidity Timeline</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    if len(df) > 1:
        st.plotly_chart(_fig_temp_humidity(df), use_container_width=True, config={"displayModeBar": False}, key="climate_temp_hum")
    else:
        st.info("Collecting data…")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Temperature Distribution</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    if len(df) > 5:
        st.plotly_chart(_fig_temp_distribution(df), use_container_width=True, config={"displayModeBar": False}, key="climate_temp_dist")
    else:
        st.info("Collecting data…")
    st.markdown('</div>', unsafe_allow_html=True)


def page_occupancy(df: pd.DataFrame):
    st.markdown('<div class="page-title">Occupancy Monitoring</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">IR Break-Beam detection with latching cooldown (15 s)</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2], gap="medium")
    with c1:
        st.markdown('<div class="section-header">Current State</div>', unsafe_allow_html=True)
        _occupancy_card(df)
    with c2:
        st.markdown('<div class="section-header">Occupancy Timeline</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        if len(df) > 1:
            st.plotly_chart(_fig_occupancy(df), use_container_width=True, config={"displayModeBar": False}, key="occ_timeline")
        else:
            st.info("Collecting data…")
        st.markdown('</div>', unsafe_allow_html=True)


def page_lighting(df: pd.DataFrame):
    st.markdown('<div class="page-title">Lighting Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">LDR sensor data — 10-sample moving-average smoothed</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    if len(df) > 1:
        st.plotly_chart(_fig_light(df), use_container_width=True, config={"displayModeBar": False}, key="light_timeline")
    else:
        st.info("Collecting data…")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Light vs Temperature Scatter</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    if len(df) > 5:
        st.plotly_chart(_fig_light_scatter(df), use_container_width=True, config={"displayModeBar": False}, key="light_scatter2")
    else:
        st.info("Collecting data…")
    st.markdown('</div>', unsafe_allow_html=True)


def page_analytics(df: pd.DataFrame):
    st.markdown('<div class="page-title">Smart Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Predictive modelling and cross-sensor correlation</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Temperature: Actual vs SMA-10 Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    if len(df) > 10:
        st.plotly_chart(_fig_temp_prediction(df), use_container_width=True, config={"displayModeBar": False}, key="analytics_pred")
    else:
        st.info("Need at least 10 readings for trend line…")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Sensor Correlation Matrix</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    if len(df) > 5:
        st.plotly_chart(_fig_correlation(df), use_container_width=True, config={"displayModeBar": False}, key="analytics_corr")
    else:
        st.info("Collecting data…")
    st.markdown('</div>', unsafe_allow_html=True)

# MAIN
def main():
    _init_history()
    raw_line = read_serial_line()
    if raw_line:
        st.session_state["last_raw_line"] = raw_line
        parsed = parse_serial_line(raw_line)
        if parsed:
            st.session_state["history"].append(parsed)
            st.session_state["last_read_ok"] = True
        else:
            st.session_state["last_read_ok"] = False
    else:
        st.session_state["last_read_ok"] = False

    page = render_sidebar()
    df   = history_to_df()

    if not df.empty and df.iloc[-1]["temperature"] >= FIRE_THRESHOLD:
        st.markdown(f"""
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-title">CRITICAL FIRE ALERT</div>
                <div class="modal-text">Temperature has reached {df.iloc[-1]['temperature']:.1f}°C.<br>Immediate evacuation required. Alerting emergency services...</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.get("_current_page") != page:
        st.session_state["_current_page"] = page
        st.rerun()

    if "Overview"    in page: page_overview(df)
    elif "Climate"   in page: page_climate(df)
    elif "Occupancy" in page: page_occupancy(df)
    elif "Lighting"  in page: page_lighting(df)
    elif "Analytics" in page: page_analytics(df)
    
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

if __name__ == "__main__":
    main()