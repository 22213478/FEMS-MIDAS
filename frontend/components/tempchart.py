import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

def temp_chart_data(data):
    now = datetime.now()
    times = [now - timedelta(hours=23 - i) for i in range(24)]

    base_temp = data["temp_now"]

    temps = [
        base_temp - 0.8,
        base_temp - 0.7,
        base_temp - 0.6,
        base_temp - 0.5,
        base_temp - 0.4,
        base_temp - 0.3,
        base_temp - 0.2,
        base_temp - 0.1,
        base_temp,
        base_temp + 0.2,
        base_temp + 0.4,
        base_temp + 0.5,
        base_temp + 0.3,
        base_temp + 0.1,
        base_temp,
        base_temp - 0.2,
        base_temp - 0.4,
        base_temp - 0.5,
        base_temp - 0.3,
        base_temp - 0.1,
        base_temp,
        base_temp + 0.1,
        base_temp - 0.1,
        base_temp,
    ]

    return times, temps

def temp_chart(data):
    times, temps = temp_chart_data(data)

    fig = go.Figure()

    fig.add_hrect(
        y0=-16,
        y1=-10,
        fillcolor="rgba(255,107,107,0.08)",
        line_width=0,
        annotation_text="경보 구간",
        annotation_position="top right",
        annotation_font=dict(size=9, color="#ff6b6b"),
    )

    fig.add_hline(
        y=-18,
        line_dash="dot",
        line_color="#c8d9ec",
        annotation_text="-18°C 목표",
        annotation_position="bottom right",
        annotation_font=dict(size=9, color="#6b8299"),
    )

    fig.add_trace(go.Scatter(
        x=times,
        y=temps,
        mode="lines",
        line=dict(color="#0077cc", width=2.5, shape="spline"),
        fill="tonexty",
        fillcolor="rgba(0,119,204,0.08)",
        hovertemplate="%{x|%H:%M}<br><b>%{y}°C</b><extra></extra>",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=times,
        y=[-50]*len(times),
        mode="lines",
        line=dict(width=0),
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=times,
        y=temps,
        mode="lines",
        line=dict(color="#0077cc", width=2.5, shape="spline"),
        fill="tonexty",
        fillcolor="rgba(0,119,204,0.15)",  # 조금 더 진하게 추천
        hovertemplate="%{x|%H:%M}<br><b>%{y}°C</b><extra></extra>",
        showlegend=False,
))

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks="",
            tickmode="array",
            tickvals=[
                times[0],
                times[6],
                times[12],
                times[18],
            ],
            ticktext=["00시", "06시", "12시", "18시"],
            tickfont=dict(size=9, color="#6b8299"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(200,217,236,0.7)",
            zeroline=False,
            showline=False,
            ticks="",
            tickmode="array",
            tickvals=[-30, -20, -10, 0],
            ticktext=["-30°", "-20°", "-10°", "0°"],
            tickfont=dict(size=9, color="#6b8299"),
            range=[-30, 0],
        ),
    )

    with st.container(border=True, key="temp-chart-card"):
        st.markdown("""
        <div class="card-label">24시간 온도 추이</div>
        """, unsafe_allow_html=True)

        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
        )
