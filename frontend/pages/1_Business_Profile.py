"""Create and edit business profiles."""

import streamlit as st

from api_client import APIError, create_business, list_businesses, update_business

st.title("Business Profile")
st.caption("Describe your offer and ideal customer so research and lead scoring can be tailored to you.")

try:
    businesses = list_businesses()
except APIError as exc:
    st.error(str(exc))
    st.stop()

options = {"Create a new profile": None}
options.update({f"{b['name']} · {b['industry']}": b for b in businesses})
choice = st.selectbox("Profile", list(options))
profile = options[choice]
with st.form("business_profile"):
    name = st.text_input("Business name", value=profile["name"] if profile else "")
    industry = st.text_input("Industry", value=profile["industry"] if profile else "")
    description = st.text_area("What does your business do?", value=profile.get("description", "") if profile else "")
    products_text = st.text_input("Products or services (comma separated)", value=", ".join(profile.get("products", [])) if profile else "")
    locations_text = st.text_input("Target locations (comma separated)", value=", ".join(profile.get("target_locations", [])) if profile else "")
    ideal_customer = st.text_area("Ideal customer", value=profile.get("ideal_customer", "") if profile else "")
    submitted = st.form_submit_button("Save profile", type="primary")

if submitted:
    payload = {"name": name.strip(), "industry": industry.strip(), "description": description.strip(), "products": [v.strip() for v in products_text.split(",") if v.strip()], "target_locations": [v.strip() for v in locations_text.split(",") if v.strip()], "ideal_customer": ideal_customer.strip()}
    try:
        saved = update_business(profile["id"], payload) if profile else create_business(payload)
        st.session_state["business_id"] = saved["id"]
        st.success("Business profile saved.")
        st.rerun()
    except APIError as exc:
        st.error(str(exc))
