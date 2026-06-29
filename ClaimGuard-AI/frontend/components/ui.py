from __future__ import annotations
import pandas as pd
import streamlit as st


def load_css() -> None:
    with open("assets/styles.css", encoding="utf-8") as file:
        st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='cg-title'>{title}</div><div class='cg-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
    st.write("")


def status_strip(items: list[tuple[str, str, str]]) -> None:
    badges = "".join(
        f"<div class='status-pill'><span class='status-dot status-{tone}'></span><span>{label}</span><strong>{value}</strong></div>"
        for label, value, tone in items
    )
    st.markdown(f"<div class='status-strip'>{badges}</div>", unsafe_allow_html=True)


def metric_card(label: str, value: str, tone: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <span class="badge badge-{tone}">live</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def claims_table(claims: list[dict]) -> None:
    frame = pd.DataFrame(claims)
    if frame.empty:
        st.info("No claims found.")
        return
    columns = ["case_id", "customer", "policy", "category", "claim_amount", "status", "risk_score", "adjuster"]
    st.dataframe(frame[columns], use_container_width=True, hide_index=True)


def risk_tone(score: int) -> str:
    if score >= 75:
        return "red"
    if score >= 40:
        return "amber"
    return "green"
