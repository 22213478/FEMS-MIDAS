import streamlit as st
import random
import math
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time

from pathlib import Path

st.set_page_config(
    page_title="대시보드",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def load_css(file_name):
    css_path = Path(__file__).parent.parent / "styles" / file_name
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("main.css")


# 임시 데이터
FACTORIES = [
    {
        "id": "F-01", "name": "F1 - 경산", 
        "temp": -22.4, "hum": 68, "power": 214,
        "status": "ok", "target": -22, "max_temp": -18, "min_temp": -26,
        "equip": [
            {"n": "압축기 A", "v": "가동 중", "s": "ok"},
            {"n": "압축기 B", "v": "가동 중", "s": "ok"},
            {"n": "압축기 C", "v": "대기", "s": "warn"},
            {"n": "증발기",  "v": "정상",  "s": "ok"},
            {"n": "팬모터",  "v": "정상",  "s": "ok"},
            {"n": "온도센서", "v": "정상", "s": "ok"},
        ],
        "alarms": [],
    },
    {
        "id": "F-02", "name": "F2 - 대구", 
        "temp": -18.7, "hum": 72, "power": 187,
        "status": "warn", "target": -22, "max_temp": -18, "min_temp": -26,
        "equip": [
            {"n": "압축기 A", "v": "가동 중",  "s": "ok"},
            {"n": "압축기 B", "v": "가동 중",  "s": "ok"},
            {"n": "압축기 C", "v": "정지",    "s": "err"},
            {"n": "증발기",  "v": "결빙주의", "s": "warn"},
            {"n": "팬모터",  "v": "정상",     "s": "ok"},
            {"n": "온도센서", "v": "정상",    "s": "ok"},
        ],
        "alarms": [{"msg": "내부 온도 목표 초과 (+3.3°C)", "time": "14:12"}],
    },
    {
        "id": "F-03", "name": "F3 - 구미 1", 
        "temp": -24.1, "hum": 65, "power": 231,
        "status": "ok", "target": -24, "max_temp": -20, "min_temp": -28,
        "equip": [
            {"n": "압축기 A", "v": "가동 중", "s": "ok"},
            {"n": "압축기 B", "v": "가동 중", "s": "ok"},
            {"n": "압축기 C", "v": "가동 중", "s": "ok"},
            {"n": "증발기",  "v": "정상",   "s": "ok"},
            {"n": "팬모터",  "v": "정상",   "s": "ok"},
            {"n": "온도센서", "v": "정상",  "s": "ok"},
        ],
        "alarms": [],
    },
    {
        "id": "F-04", "name": "F4 - 구미 2", 
        "temp": -15.2, "hum": 78, "power": 215,
        "status": "warn", "target": -15, "max_temp": -12, "min_temp": -20,
        "equip": [
            {"n": "압축기 A", "v": "가동 중",   "s": "ok"},
            {"n": "압축기 B", "v": "가동 중",   "s": "ok"},
            {"n": "압축기 C", "v": "미설치",   "s": "ok"},
            {"n": "증발기",  "v": "정상",      "s": "ok"},
            {"n": "팬모터",  "v": "진동감지",  "s": "warn"},
            {"n": "온도센서", "v": "정상",     "s": "ok"},
        ],
        "alarms": [{"msg": "팬모터 진동 수치 상승", "time": "13:58"}],
    },
]

SCHEDULE = {
    "냉동1": ["on","on","on","on","on","on","on","off","off","peak","peak","peak","peak","off","off","off","on","on","peak","peak","off","on","on","on"],
    "냉동2": ["off","off","off","off","on","on","on","on","off","off","peak","peak","on","on","off","on","on","on","peak","off","off","off","off","off"],
    "냉동3": ["on","on","off","off","off","on","on","on","on","on","peak","peak","off","off","on","on","on","peak","peak","off","off","on","on","on"],
    "태양광": ["off","off","off","off","off","off","solar","solar","solar","solar","solar","solar","solar","solar","solar","solar","solar","solar","off","off","off","off","off","off"],
    "요금대": ["off","off","off","off","off","off","off","off","off","peak","peak","peak","peak","peak","off","off","off","off","peak","peak","off","off","off","off"],
}

SAV_MONTHLY = {"labels": ["1월","2월","3월","4월","5월","6월"], "vals": [420,380,490,560,610,540], "max": 700}
SAV_DAILY   = {"labels": ["월","화","수","목","금","토"],       "vals": [72,85,68,91,84,76],     "max": 110}


def init_state():
    defaults = {
        "sav_tab": "monthly",
        "ctrl_log": ["14:22  시스템 자동 가동 시작", "13:45  냉동2 온도 경보 해제"],
        "emergency": False,
        "factories": [dict(f) for f in FACTORIES],
        "power_kw": 847.0,
        "solar_kw": 238.0,
        "last_tick": time.time(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


def status_color(s):
    return {"ok": "#3b6d11", "warn": "#854f0b", "err": "#a32d2d"}.get(s, "#888780")

def status_bg(s):
    return {"ok": "#eaf3de", "warn": "#faeeda", "err": "#fcebeb"}.get(s, "#f1efe8")

def status_text(s):
    return {"ok": "정상", "warn": "주의", "err": "경보"}.get(s, "-")

def bar_color(t, target):
    d = t - target
    if d < -2: return "#85b7eb"
    if d >  2: return "#e24b4a"
    return "#1d9e75"

def temp_pct(t, mn, mx):
    return max(0.0, min(100.0, (t - mn) / (mx - mn) * 100))

def badge_html(text, kind="ok"):
    return f'<span class="badge badge-{kind}">{text}</span>'

def log_action(action):
    ts = datetime.now().strftime("%H:%M")
    st.session_state.ctrl_log.insert(0, f"{ts}  {action} 실행")

def kpi_card(label, value, unit, sub, pct, accent, delta_text="", delta_kind="ok"):
    bar_html = f'<div class="kpi-bar-wrap"><div class="kpi-bar-fill" style="width:{pct:.1f}%;background:{accent}"></div></div>'
    delta_html = f'<div class="delta-{delta_kind}">{delta_text}</div>' if delta_text else ""
    return f"""
    <div class="kpi-card" style="--accent:{accent}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
      {bar_html}
      <div class="kpi-sub">{sub}</div>
      {delta_html}
    </div>
    """

def hex_to_rgba(hex_color, alpha=0.08):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def sparkline_fig(data, color, height=50):
    fig = go.Figure()

    fill_color = (
        color.replace(")", ",0.08)").replace("rgb", "rgba")
        if "rgb" in color
        else hex_to_rgba(color, 0.08)
    )

    fig.add_trace(go.Scatter(
        y=data,
        mode="lines",
        line=dict(color=color, width=1.8, shape="spline"),
        fill="tozeroy",
        fillcolor=fill_color,
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig

def schedule_fig():
    now_h = datetime.now().hour
    cell_colors = {"on": "#378add", "peak": "#e24b4a", "solar": "#639922", "off": "#f1efe8"}
    rows = list(SCHEDULE.keys())
    hours = list(range(24))

    z = []
    text = []
    for row in rows:
        pat = SCHEDULE[row]
        z.append([{"on":1,"peak":2,"solar":3,"off":0}[p] for p in pat])
        text.append([pat[h] for h in hours])

    colorscale = [
        [0.00, "#f1efe8"], [0.25, "#f1efe8"],
        [0.25, "#378add"], [0.50, "#378add"],
        [0.50, "#e24b4a"], [0.75, "#e24b4a"],
        [0.75, "#639922"], [1.00, "#639922"],
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=[f"{h}h" for h in hours],
        y=rows,
        colorscale=colorscale,
        zmin=0, zmax=3,
        showscale=False,
        xgap=1, ygap=2,
    ))
    
    fig.add_vline(x=now_h - 0.5, line_width=2, line_color="#1a1a2e", opacity=0.6)

    fig.update_layout(
        margin=dict(l=60, r=10, t=10, b=30),
        height=160,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            tickvals=[0,6,12,18,23],
            ticktext=["0h","6h","12h","18h","24h"],
            tickfont=dict(size=10, color="#888780"),
            gridcolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(tickfont=dict(size=11, color="#888780"), gridcolor="rgba(0,0,0,0)"),
    )
    return fig

def savings_fig(tab):
    d = SAV_MONTHLY if tab == "monthly" else SAV_DAILY
    fig = go.Figure(go.Bar(
        x=d["vals"], y=d["labels"],
        orientation="h",
        marker_color="#378add",
        marker_line_width=0,
        text=[f"₩{v}만" for v in d["vals"]],
        textposition="outside",
        textfont=dict(size=11, color="#444441"),
    ))
    fig.update_layout(
        margin=dict(l=10, r=60, t=10, b=10),
        height=170,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[0, d["max"] * 1.25]),
        yaxis=dict(
        tickfont=dict(size=11, color="#888780"),
        gridcolor="rgba(0,0,0,0)",
        categoryorder="array",
        categoryarray=d["labels"][::-1],
    ),
        showlegend=False,
    )
    return fig

def temp_trend_fig(f, n=20):
    base = f["temp"]
    data = [round(base + random.uniform(-0.8, 0.8), 1) for _ in range(n - 1)] + [base]
    target_line = [f["target"]] * n
    clr = bar_color(base, f["target"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=target_line, mode="lines",
        line=dict(color="#e0e3ea", width=1, dash="dash"),
        name="목표온도", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        y=data, mode="lines+markers",
        line=dict(color=clr, width=2, shape="spline"),
        marker=dict(size=4, color=clr),
        fill="tozeroy",
        fillcolor=hex_to_rgba(clr, 0.08),
        name="온도", showlegend=False,
    ))
    fig.update_layout(
        margin=dict(l=40, r=10, t=10, b=20),
        height=120,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            tickvals=[0, n-1],
            ticktext=["1시간 전", "현재"],
            tickfont=dict(size=10, color="#b4b2a9"),
            gridcolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(tickfont=dict(size=10, color="#888780"), gridcolor="#f1efe8"),
    )
    return fig


# 공장 상세 정보 모달창
@st.dialog("공장 상세 정보", width="large")
def show_factory_detail(f):
    sc     = status_color(f["status"])
    sb     = status_bg(f["status"])
    st_txt = status_text(f["status"])

    dh1, dh2 = st.columns([3, 1])
    with dh1:
        st.markdown(f"""
        <div style="margin-bottom:8px">
          <div style="font-size:17px;font-weight:500;color:#1a1a2e">
            {f['name']}
            <span style="font-size:13px;color:#888780;font-weight:400">&nbsp;{f['id']}</span>
          </div>
          <div style="font-size:12px;color:#888780;margin-top:3px">
            목표온도 {f['target']}°C &nbsp;·&nbsp; 압축기 가동 중
          </div>
        </div>
        """, unsafe_allow_html=True)
    with dh2:
        st.markdown(
            f'<div style="text-align:right;padding-top:6px">'
            f'<span class="badge" style="background:{sb};color:{sc};font-size:13px;padding:5px 14px">{st_txt}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    dm1, dm2, dm3, dm4 = st.columns(4)
    hdata  = [round(f["temp"]  + random.uniform(-0.8, 0.8), 1) for _ in range(19)] + [f["temp"]]
    phdata = [round(f["hum"]   + random.uniform(-2, 2),     1) for _ in range(19)] + [f["hum"]]
    pwdata = [round(f["power"] + random.uniform(-15, 15),   0) for _ in range(19)] + [f["power"]]

    with dm1:
        st.markdown(f"""<div class="metric-box">
          <div class="metric-box-label">현재 온도</div>
          <div class="metric-box-val">{f['temp']:.1f}<span class="metric-box-unit">°C</span></div>
          <div class="metric-box-trend" style="color:{sc}">목표 {f['target']}°C</div>
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(sparkline_fig(hdata, sc, 50), width="stretch", config={"displayModeBar": False})

    with dm2:
        st.markdown(f"""<div class="metric-box">
          <div class="metric-box-label">현재 습도</div>
          <div class="metric-box-val">{f['hum']}<span class="metric-box-unit">%RH</span></div>
          <div class="metric-box-trend" style="color:#888780">기준 60~75%</div>
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(sparkline_fig(phdata, "#1d9e75", 50), width="stretch", config={"displayModeBar": False})

    with dm3:
        st.markdown(f"""<div class="metric-box">
          <div class="metric-box-label">전력 소비</div>
          <div class="metric-box-val">{f['power']}<span class="metric-box-unit">kW</span></div>
          <div class="metric-box-trend delta-ok">전일 대비 -8%</div>
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(sparkline_fig(pwdata, "#ba7517", 50), width="stretch", config={"displayModeBar": False})

    with dm4:
        saving = round(f["power"] * 0.1)
        pct_v  = round(f["power"] / 300 * 100)
        st.markdown(f"""<div class="metric-box">
          <div class="metric-box-label">임시</div>
          <div class="metric-box-val">{saving}<span class="metric-box-unit">만원</span></div>
          <div style="height:5px;background:#f1efe8;border-radius:3px;margin-top:10px;overflow:hidden">
            <div style="width:{pct_v}%;height:5px;background:#ba7517;border-radius:3px"></div>
          </div>
          <div class="metric-box-trend" style="color:#854f0b">목표 대비 {pct_v}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    da1, da2 = st.columns([1, 1.5])
    with da1:
        st.markdown('<div class="section-label">경보 현황</div>', unsafe_allow_html=True)
        if not f["alarms"]:
            st.markdown('<div style="font-size:12px;color:#b4b2a9;padding:4px 0 10px">현재 활성 경보 없음</div>', unsafe_allow_html=True)
        else:
            for alarm in f["alarms"]:
                st.markdown(f"""
                <div class="alarm-item" style="background:#faeeda;margin-bottom:4px">
                  <div style="font-weight:500;color:#633806;font-size:12px">{alarm['msg']}</div>
                  <div style="color:#854f0b;font-size:11px;margin-top:2px">{alarm['time']}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:10px">설비 상태</div>', unsafe_allow_html=True)
        eq_cols = st.columns(3)
        for j, eq in enumerate(f["equip"]):
            with eq_cols[j % 3]:
                ec = status_color(eq["s"])
                st.markdown(f"""
                <div class="equip-item" style="margin-bottom:6px">
                  <div class="equip-name">{eq['n']}</div>
                  <div class="equip-val">{eq['v']}</div>
                  <div style="font-size:10px;color:{ec};margin-top:2px">{status_text(eq['s'])}</div>
                </div>""", unsafe_allow_html=True)

    with da2:
        st.markdown('<div class="section-label">온도 추이 (최근 1시간)</div>', unsafe_allow_html=True)
        st.plotly_chart(temp_trend_fig(f), width="stretch", config={"displayModeBar": False})


now = time.time()
if now - st.session_state.last_tick > 3:
    st.session_state.power_kw = max(700, min(1050, st.session_state.power_kw + random.uniform(-8, 8)))
    st.session_state.solar_kw = max(180, min(360,  st.session_state.solar_kw + random.uniform(-3, 3)))
    for f in st.session_state.factories:
        f["temp"] = round(f["temp"] + random.uniform(-0.2, 0.2), 1)
    st.session_state.last_tick = now


warn_count = sum(1 for f in st.session_state.factories if f["status"] in ("warn", "err"))
warn_badge = badge_html(f"주의 {warn_count}건", "warn") if (warn_count or st.session_state.emergency) else ""
emg_badge  = badge_html("비상 정지 활성화", "err") if st.session_state.emergency else ""

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:15px">
  <div style="display:flex;align-items:center;gap:12px">
    <div class="dash-logo"><span>냉동 공장</span></div>
    <span><span class="live-dot"></span><span style="font-size:12px;color:#888780">LIVE</span></span>
    {badge_html("시스템 정상", "ok")}
    {warn_badge}
    {emg_badge}
  </div>
  <div style="display:flex;align-items:center;gap:16px">
    <span style="font-size:11px;color:#b4b2a9">냉동공장 에너지 절약 시스템</span>
    <span style="font-size:12px;color:#888780;letter-spacing:.5px">{datetime.now().strftime('%H:%M:%S')}</span>
  </div>
</div>
""", unsafe_allow_html=True)


# 공장 정보
pwr  = st.session_state.power_kw
sol  = st.session_state.solar_kw

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("현재 전력 소비", f"{pwr:.0f}", "kW",
        f"계약 한도 1,200 kW", pwr / 12, "#378add",
        f"12% 하락 ", "ok"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("태양광 발전", f"{sol:.0f}", "kW",
        "이달 발전량 38,200 kWh", sol / 3.6, "#639922",
        f"자가소비율 {sol/pwr*100:.1f}%", "ok"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("절감액", "84", "만원",
        "이달 누적 1,847만원", 91.3, "#ba7517"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("임시", "4.2", "톤",
        "임시", 60, "#534ab7"), unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
st.markdown(
    '<div class="card-title" style="margin:10px 0 8px 2px">공장 상태</div>',
    unsafe_allow_html=True
)

fc_cols = st.columns(4)

for i, (col, f) in enumerate(zip(fc_cols, st.session_state.factories)):
    with col:
        pct    = temp_pct(f["temp"], f["min_temp"], f["max_temp"])
        bclr   = bar_color(f["temp"], f["target"])
        sc     = status_color(f["status"])
        sb     = status_bg(f["status"])
        st_txt = status_text(f["status"])

        with st.container(key=f"factory_card_{i}"):
            st.markdown(f"""
            <div class="factory-card-inner">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">
                <div>
                <div class="fc-name">{f['name']}</div>
                </div>
                <span class="badge" style="background:{sb};color:{sc}">{st_txt}</span>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:4px">
                <div class="fc-metric-box">
                    <div class="fc-metric-label">온도</div>
                    <div class="fc-temp-row">
                        <span class="fc-metric-val">{f['temp']:.1f}<span class="fc-metric-unit">°C</span></span>
                        <span class="fc-target-text">목표 {f['target']}°C</span>
                    </div>
                </div>
                <div class="fc-metric-box">
                <div class="fc-metric-label">습도</div>
                <div class="fc-metric-val">{f['hum']}<span class="fc-metric-unit">%</span></div>
                </div>
            </div>

            <div class="fc-bar-wrap">
                <div style="height:4px;border-radius:2px;background:{bclr};width:{pct:.1f}%"></div>
            </div>

            <div class="fc-footer">
                <span>전력 <b>{f['power']} kW</b></span>
            </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.button("상세 보기", key=f"fcbtn_{i}", width="stretch", type="secondary"):
                    show_factory_detail(st.session_state.factories[i])

            with btn_col2:
                if st.button("긴급 정지", key=f"stopbtn_{i}", width="stretch"):
                    st.session_state.emergency = True
                    log_action(f"{f['name']} 긴급 정지")
                    st.rerun()
                    

# 하단
bc1, bc2, bc3 = st.columns([1.7, 1, 1])

with bc1:
    st.markdown('<div class="card-title">가동 스케줄 (24시간)</div>', unsafe_allow_html=True)
    st.plotly_chart(schedule_fig(), width="stretch", config={"displayModeBar": False})
    st.markdown("""
    <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:-8px">
      <div style="display:flex;align-items:center;gap:5px;font-size:11px;color:#888780">
        <span style="width:12px;height:8px;background:#378add;border-radius:2px;display:inline-block"></span>가동
      </div>
      <div style="display:flex;align-items:center;gap:5px;font-size:11px;color:#888780">
        <span style="width:12px;height:8px;background:#e24b4a;border-radius:2px;display:inline-block"></span>피크요금
      </div>
      <div style="display:flex;align-items:center;gap:5px;font-size:11px;color:#888780">
        <span style="width:12px;height:8px;background:#639922;border-radius:2px;display:inline-block"></span>태양광
      </div>
      <div style="display:flex;align-items:center;gap:5px;font-size:11px;color:#888780">
        <span style="width:12px;height:8px;background:#f1efe8;border:0.5px solid #e0e3ea;border-radius:2px;display:inline-block"></span>대기
      </div>
    </div>
    """, unsafe_allow_html=True)

with bc2:
    st.markdown('<div class="card-title">누적 절감액</div>', unsafe_allow_html=True)
    tab_m, tab_d = st.tabs(["월별", "일별"])
    with tab_m:
        st.plotly_chart(savings_fig("monthly"), width="stretch", config={"displayModeBar": False})
    with tab_d:
        st.plotly_chart(savings_fig("daily"), width="stretch", config={"displayModeBar": False})
    st.markdown("""
    <div style="border-top:0.5px solid #e0e3ea;padding-top:8px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:11px;color:#888780">연간 누적</span>
      <span style="font-size:16px;font-weight:500;color:#185fa5">₩1억 2,340만</span>
    </div>
    """, unsafe_allow_html=True)

with bc3:
    st.markdown('<div class="card-title">긴급 수동 제어</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#faeeda;border:0.5px solid #fac775;border-radius:6px;
                padding:7px 10px;font-size:11px;color:#854f0b;margin-bottom:10px">
      수동 제어 시 자동 스케줄이 일시 중지됩니다
    </div>
    """, unsafe_allow_html=True)

    cb1, cb2 = st.columns(2)
    with cb1:
        if st.button("비상 정지", key="btn_stop", width="stretch"):
            st.session_state.emergency = True
            log_action("비상 정지")
            st.rerun()
        if st.button("제상 히팅", key="btn_heat", width="stretch"):
            log_action("제상 히팅")
            st.rerun()
    with cb2:
        if st.button("강제 냉각", key="btn_cool", width="stretch"):
            log_action("강제 냉각")
            st.rerun()
        if st.button("복구", key="btn_auto", width="stretch"):
            st.session_state.emergency = False
            log_action("복구")
            st.rerun()

    if st.session_state.emergency:
        st.markdown('<div class="emg-banner">비상 정지 활성화</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top:8px"><div style="font-size:11px;font-weight:500;color:#888780;margin-bottom:5px">제어 내역</div>', unsafe_allow_html=True)
    log_html = "".join(
        f'<div><span class="log-time">{line.split("  ")[0]}</span>{("  ".join(line.split("  ")[1:]) if "  " in line else line)}</div>'
        for line in st.session_state.ctrl_log[:8]
    )
    st.markdown(f'<div class="log-box">{log_html}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

#time.sleep(3)
#st.rerun()