from app.db.models import BusinessProfile, Lead


def test_lead_read_update_and_csv_export(client, test_session_factory):
    with test_session_factory() as db:
        business = BusinessProfile(name="Acme", industry="Retail", target_locations=["Boston"])
        db.add(business)
        db.flush()
        lead = Lead(business_id=business.id, name="Prospect One", fit_score=74, fit_reasons=["Industry match"], status="new")
        db.add(lead)
        db.commit()
        lead_id, business_id = lead.id, business.id

    detail = client.get(f"/api/v1/leads/{lead_id}")
    assert detail.status_code == 200
    assert detail.json()["fit_score"] == 74

    update = client.patch(f"/api/v1/leads/{lead_id}", json={"status": "contacted", "notes": "Called Monday"})
    assert update.status_code == 200
    assert update.json()["status"] == "contacted"
    assert update.json()["notes"] == "Called Monday"

    exported = client.get("/api/v1/leads/export", params={"business_id": business_id})
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]
    assert "Prospect One" in exported.text
