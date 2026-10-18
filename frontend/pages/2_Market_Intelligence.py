"""Launch market research and inspect its sources and findings."""

import streamlit as st

from api_client import APIError, create_research, get_research_report, list_businesses

st.title("Market Intelligence")
st.caption("Search public web and Maps evidence, then summarize it into a sourced market snapshot.")
try:
    businesses = list_businesses()
except APIError as exc:
    st.error(str(exc))
    st.stop()
if not businesses:
    st.info("Create a business profile first.")
    st.stop()
by_label = {f"{b['name']} · {b['industry']}": b for b in businesses}
label = st.selectbox("Business", list(by_label), index=next((i for i, b in enumerate(by_label.values()) if b["id"] == st.session_state.get("business_id")), 0))
business = by_label[label]
with st.form("market_research"):
    location = st.text_input("Market or location", value=(business.get("target_locations") or [""])[0])
    query = st.text_input("Optional focus query", placeholder="e.g. competitors, demand, pricing, local trends")
    limit = st.slider("Results per search", 3, 20, 8)
    launch = st.form_submit_button("Run research", type="primary")
if launch:
    try:
        with st.spinner("Searching and preparing report…"):
            run = create_research({"business_id": business["id"], "run_type": "market", "location": location, "query": query or None, "limit": limit})
            report = get_research_report(run["id"])
        st.session_state["last_research_id"] = run["id"]
        st.session_state["last_research_business_id"] = business["id"]
        st.session_state["market_report"] = report
        st.success(f"Research complete · {run['id']}")
    except APIError as exc:
        st.error(str(exc))

report = st.session_state.get("market_report")
if report and report["research"]["business_id"] == business["id"]:
    st.subheader("Research summary")
    st.write(report["summary"])
    for finding in report["findings"]:
        with st.expander(finding["title"]):
            st.write(finding["insight"])
            for url in finding.get("evidence_urls", []):
                st.markdown(f"[Source]({url})")
    st.subheader(f"Sources · {len(report['sources'])}")
    st.dataframe([{"Title": s["title"], "Type": s["source_type"], "Snippet": s["snippet"], "URL": s["url"]} for s in report["sources"]], use_container_width=True, hide_index=True)
