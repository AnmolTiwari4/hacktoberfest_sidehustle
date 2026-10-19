"""HTTP client for the MarketScout FastAPI service."""

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def _configured_api_url() -> str:
    value = os.getenv("API_BASE_URL")
    if not value:
        try:
            import streamlit as st

            value = st.secrets.get("API_BASE_URL")
        except Exception:
            value = None
    return (value or "https://hacktoberfest-sidehustle.onrender.com").rstrip("/")


API_BASE_URL = _configured_api_url()
API_PREFIX = "/api/v1"


class APIError(RuntimeError):
    """Readable error returned to the Streamlit interface."""


def request(method: str, path: str, *, params: dict | None = None, json: dict | None = None) -> Any:
    try:
        response = requests.request(method, f"{API_BASE_URL}{path}", params=params, json=json, timeout=(5, 60))
    except requests.RequestException as exc:
        raise APIError(f"Could not reach the API at {API_BASE_URL}. Check that the backend is running and API_BASE_URL is correct.") from exc
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise APIError(f"API error ({response.status_code}): {detail}")
    if "application/json" in response.headers.get("content-type", ""):
        return response.json()
    return response.content


def get_health() -> dict:
    return request("GET", "/health")


def list_businesses() -> list[dict]:
    return request("GET", f"{API_PREFIX}/businesses")


def create_business(payload: dict) -> dict:
    return request("POST", f"{API_PREFIX}/businesses", json=payload)


def update_business(business_id: str, payload: dict) -> dict:
    return request("PATCH", f"{API_PREFIX}/businesses/{business_id}", json=payload)


def create_research(payload: dict) -> dict:
    return request("POST", f"{API_PREFIX}/research", json=payload)


def get_research_report(research_id: str) -> dict:
    return request("GET", f"{API_PREFIX}/research/{research_id}/report")


def search_leads(payload: dict) -> dict:
    return request("POST", f"{API_PREFIX}/leads/search", json=payload)


def list_leads(**params: Any) -> dict:
    return request("GET", f"{API_PREFIX}/leads", params=params)


def update_lead(lead_id: str, payload: dict) -> dict:
    return request("PATCH", f"{API_PREFIX}/leads/{lead_id}", json=payload)


def export_leads(business_id: str | None = None) -> bytes:
    params = {"business_id": business_id} if business_id else None
    return request("GET", f"{API_PREFIX}/leads/export", params=params)


def create_growth_plan(payload: dict) -> dict:
    return request("POST", f"{API_PREFIX}/growth-plans", json=payload)
