"""Update lead status and notes, and export selected business leads."""

import streamlit as st

from api_client import APIError, export_leads, list_businesses, list_leads, update_lead

st.title("Lead Workspace")
st.caption("Track outreach, record context, and export your lead list to CSV.")
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
try:
    leads_result = list_leads(business_id=business["id"], limit=500)
except APIError as exc:
    st.error(str(exc))
    st.stop()
leads = leads_result["items"]
if not leads:
    st.info("No leads yet. Use BizScout Leads to discover prospects.")
else:
    st.dataframe([{"Name": x["name"], "Score": x["fit_score"], "Category": x["category"], "Address": x["address"], "Status": x["status"], "Website": x["website"]} for x in leads], use_container_width=True, hide_index=True)
    options = {f"{x['name']} · {x['fit_score']:.0f} pts": x for x in leads}
    lead = options[st.selectbox("Lead to update", list(options))]
    with st.form("lead_update"):
        statuses = ["new", "contacted", "qualified", "converted", "rejected"]
        status = st.selectbox("Status", statuses, index=statuses.index(lead["status"]))
        notes = st.text_area("Notes", value=lead.get("notes", ""))
        save = st.form_submit_button("Save lead", type="primary")
    if save:
        try:
            update_lead(lead["id"], {"status": status, "notes": notes})
            st.success("Lead updated.")
            st.rerun()
        except APIError as exc:
            st.error(str(exc))

if leads:
    try:
        csv_bytes = export_leads(business["id"])
        st.download_button("Download leads.csv", data=csv_bytes, file_name="marketscout-leads.csv", mime="text/csv")
    except APIError as exc:
        st.error(str(exc))
