"""MarketScout AI Streamlit dashboard."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

try:
    configured_api_url = st.secrets.get("API_BASE_URL")
except Exception:
    configured_api_url = None

API_BASE_URL = (
    configured_api_url
    or os.getenv("API_BASE_URL", "https://hacktoberfest-sidehustle.onrender.com")
).rstrip("/")
os.environ["API_BASE_URL"] = API_BASE_URL

from api_client import APIError, get_health, list_businesses, list_leads

st.set_page_config(page_title="MarketScout AI", page_icon="🧭", layout="wide")
st.title("🧭 MarketScout AI")
st.caption("Turn a business profile into market evidence, scored prospects, and practical growth actions.")

try:
    health = get_health()
    st.sidebar.success(f"API connected · {health.get('service', 'FastAPI')}")
except APIError as exc:
    st.sidebar.error(str(exc))

try:
    businesses = list_businesses()
    if businesses:
        labels = {f"{b['name']} · {b['industry']}": b for b in businesses}
        selected = st.sidebar.selectbox("Active business", list(labels))
        st.session_state["business_id"] = labels[selected]["id"]
    else:
        st.session_state.pop("business_id", None)
except APIError as exc:
    businesses = []
    st.error(str(exc))

if not businesses:
    st.info("Create your first business profile from **Business Profile** in the sidebar to get started.")
else:
    business = next(b for b in businesses if b["id"] == st.session_state.get("business_id"))
    st.subheader(f"Overview · {business['name']}")
    cols = st.columns(3)
    try:
        lead_result = list_leads(business_id=business["id"], limit=500)
        leads = lead_result["items"]
        cols[0].metric("Saved leads", lead_result["total"])
        cols[1].metric("High fit (70+)", sum(lead["fit_score"] >= 70 for lead in leads))
        cols[2].metric("Awaiting outreach", sum(lead["status"] == "new" for lead in leads))
        if leads:
            st.markdown("#### Top prospects")
            st.dataframe([{"Business": x["name"], "Score": x["fit_score"], "Category": x["category"], "Location": x["address"], "Status": x["status"]} for x in leads[:8]], use_container_width=True, hide_index=True)
    except APIError as exc:
        st.error(str(exc))
    st.markdown("#### Your profile")
    st.write(business.get("description") or "Add a description from Business Profile to help focus research.")
    st.caption(f"Industry: {business['industry']} · Target areas: {', '.join(business.get('target_locations') or []) or 'not set'}")
    st.markdown("Use the pages in the sidebar to launch market research, discover leads, and build a 7/30/90 day plan.")
