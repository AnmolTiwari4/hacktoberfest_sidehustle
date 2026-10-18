from datetime import datetime, timezone

from app.services.scoring_service import score_lead


def test_score_uses_all_four_categories_and_caps_at_100():
    business = {"industry": "coffee shop", "products": ["coffee"], "target_locations": ["Queens"]}
    candidate = {
        "name": "Coffee Corner",
        "category": "coffee shop",
        "address": "Queens, NY",
        "website": "https://coffee.example",
        "rating": 4.5,
        "reviews": 120,
        "snippet": "Recent reviews mention new seasonal drinks.",
        "evidence_date": datetime.now(timezone.utc).isoformat(),
    }

    score, reasons = score_lead(business, candidate)

    assert score == 100
    assert len(reasons) == 10


def test_score_handles_missing_candidate_information():
    score, reasons = score_lead({"industry": "dentist", "products": [], "target_locations": ["Boston"]}, {"name": "Unknown"})

    assert score == 0
    assert any("uncertain" in reason for reason in reasons)
