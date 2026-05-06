from __future__ import annotations

import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env", override=False)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Dynamic Scheduling Demo", layout="centered")
st.title("동적 스케줄링 데모")
st.caption("입고량(quantity)을 바꾸고 Job A를 즉시 1회 실행해 목표 온도 변화를 확인합니다.")

factory_id = st.number_input("공장 ID", min_value=1, max_value=99, value=1, step=1)
quantity = st.number_input("입고량 (quantity)", min_value=0, max_value=100000, value=30, step=1)

if st.button("동적 스케줄링 데모 실행", type="primary", use_container_width=True):
    payload = {"factory_id": int(factory_id), "quantity": int(quantity)}
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/demo/dynamic-schedule/run",
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        body = resp.json()
        data = body.get("data", {})
    except Exception as exc:
        st.error("데모 실행 실패")
        st.caption(str(exc))
    else:
        st.success(body.get("message", "demo recompute completed"))
        col1, col2 = st.columns(2)
        col1.metric("입고량", f"{data.get('quantity', '-')}")
        rec_temp = data.get("recommended_temp_c")
        db_temp = data.get("schedule_target_temp_c")
        col2.metric("권장 온도(이번 실행)", "-" if rec_temp is None else f"{float(rec_temp):.2f} C")

        st.caption(
            "DB 저장 확인: "
            + ("-" if db_temp is None else f"{float(db_temp):.2f} C")
            + f" / 저장 시각(DB): {data.get('schedule_created_at', '-')}"
        )

        st.write(f"- 모드: `{data.get('mode', '-')}`")
        st.write(f"- 입고량 소스: `{data.get('inbound_source', '-')}`")
        st.write(f"- 계산 시각: `{data.get('computed_at', '-')}`")
        st.write(f"- 저장 시각(DB): `{data.get('schedule_created_at', '-')}`")

        with st.expander("응답 원본 보기", expanded=False):
            st.json(body)
