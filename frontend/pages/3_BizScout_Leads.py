"""Discover and score business prospects."""

import streamlit as st

from api_client import APIError, list_businesses, list_leads, search_leads

st.title("BizScout Leads")
st.caption("Find local prospects and review their transparent 100-point fit score.")
try:
    businesses = list_businesses()
except APIError as exc:
    st.error(str(exc))
    st.stop()
if not businesses:
    st.info("Create a business profile first.")
    st.stop()
by_label = {f"{b['name']} · {b['industry']}": b for b in businesses}
label = st.selectbox("Business", list(by_label))
business = by_label[label]
with st.form("lead_search"):
    location = st.text_input("Search location", value=(business.get("target_locations") or [""])[0])
    query = st.text_input("Search phrase", value=f"{business['industry']} {business['name']}")
    limit = st.slider("Maximum prospects", 5, 50, 20)
    submitted = st.form_submit_button("Discover leads", type="primary")
if submitted:
    try:
        with st.spinner("Searching Google Maps and scoring matches…"):
            result = search_leads({"business_id": business["id"], "location": location, "query": query, "limit": limit})
        st.success(f"Saved {result['total']} prospects.")
    except APIError as exc:
        st.error(str(exc))

minimum = st.slider("Minimum fit score", 0, 100, 0)
try:
    result = list_leads(business_id=business["id"], min_score=minimum, limit=500)
    for lead in result["items"]:
        with st.expander(f"{lead['fit_score']:.0f} · {lead['name']} · {lead['category'] or 'Business'}"):
            st.write(lead["address"] or "Address not available")
            if lead["website"]:
                st.markdown(f"[Website]({lead['website']})")
            st.markdown("**Score breakdown**")
            for reason in lead["fit_reasons"]:
                st.write(f"- {reason}")
except APIError as exc:
    st.error(str(exc))
