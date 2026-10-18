"""Generate a 7/30/90 day evidence-based growth plan."""

import streamlit as st

from api_client import APIError, create_growth_plan, list_businesses

st.title("Growth Planner")
st.caption("Turn research evidence into prioritized actions for the next 7, 30, and 90 days.")
try:
    businesses = list_businesses()
except APIError as exc:
    st.error(str(exc))
    st.stop()
if not businesses:
    st.info("Create a business profile first.")
    st.stop()
by_label = {f"{b['name']} · {b['industry']}": b for b in businesses}
business = by_label[st.selectbox("Business", list(by_label))]
research_id = st.text_input("Research run ID (optional)", value=st.session_state.get("last_research_id", ""), help="Include the latest Market Intelligence run to ground actions in its sources.")
if st.button("Generate growth plan", type="primary"):
    try:
        with st.spinner("Building your plan…"):
            plan = create_growth_plan({"business_id": business["id"], "research_run_id": research_id.strip() or None})
        st.session_state["growth_plan"] = plan
    except APIError as exc:
        st.error(str(exc))

plan = st.session_state.get("growth_plan")
if plan and plan["business_id"] == business["id"]:
    st.subheader("Plan overview")
    st.write(plan["summary"])
    for timeframe in ("7 days", "30 days", "90 days"):
        st.markdown(f"### {timeframe}")
        actions = [x for x in plan["recommendations"] if x["timeframe"] == timeframe]
        if not actions:
            st.info("No actions in this timeframe.")
        for item in actions:
            with st.container():
                st.markdown(f"**{item['title']}** · {item['priority']} priority")
                st.write(item["action"])
                st.caption(item["rationale"])
                for url in item.get("evidence_urls", []):
                    st.markdown(f"[Evidence]({url})")
