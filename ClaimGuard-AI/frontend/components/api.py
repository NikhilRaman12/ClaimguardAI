import os
from typing import Any
import requests
import streamlit as st
from components import local_agent


API_URL = os.getenv("CLAIMGUARD_API_URL", "http://localhost:8000/api")
API_TOKEN = os.getenv("CLAIMGUARD_API_TOKEN", "")


def runtime_label() -> str:
    return st.session_state.get("runtime_label", f"API: {API_URL}")


def login(email: str, password: str) -> dict[str, Any] | None:
    try:
        response = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password}, timeout=10)
        if response.ok:
            return response.json()
        st.error("Invalid credentials")
    except requests.RequestException as exc:
        st.error(f"API unavailable: {exc}")
    return None


def headers() -> dict[str, str]:
    token = st.session_state.get("token") or API_TOKEN
    return {"Authorization": f"Bearer {token}"} if token else {}


def get(path: str) -> Any:
    try:
        response = requests.get(f"{API_URL}{path}", headers=headers(), timeout=5)
        response.raise_for_status()
        st.session_state.runtime_label = f"API: {API_URL}"
        return response.json()
    except requests.RequestException as exc:
        fallback = local_agent.handle_get(path)
        if fallback is not None:
            st.session_state.runtime_label = "Embedded agent runtime"
            return fallback
        st.error(f"API request failed: GET {path} ({exc})")
        return None


def post(path: str, payload: dict[str, Any] | None = None) -> Any:
    try:
        response = requests.post(f"{API_URL}{path}", headers=headers(), json=payload or {}, timeout=10)
        response.raise_for_status()
        st.session_state.runtime_label = f"API: {API_URL}"
        return response.json()
    except requests.RequestException as exc:
        fallback = local_agent.handle_post(path, payload)
        if fallback is not None:
            st.session_state.runtime_label = "Embedded agent runtime"
            return fallback
        st.error(f"API request failed: POST {path} ({exc})")
        return None
