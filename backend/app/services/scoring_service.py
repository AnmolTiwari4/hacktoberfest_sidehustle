"""Deterministic 100-point lead-fit score."""

from datetime import datetime, timedelta, timezone
import re
from urllib.parse import urlparse


def score_lead(business: dict, candidate: dict) -> tuple[float, list[str]]:
    """Score industry (40), geography (25), activity (20), completeness/freshness (15)."""
    reasons: list[str] = []
    industry_terms = [business.get("industry", "")] + list(business.get("products", []))
    candidate_text = " ".join(str(candidate.get(k) or "") for k in ("name", "category", "snippet")).lower()
    matches = [term for term in industry_terms if term and str(term).lower() in candidate_text]
    industry = min(40, round(40 * len(matches) / max(1, len([x for x in industry_terms if x])), 1))
    if matches:
        reasons.append(f"Industry/product relevance: {', '.join(map(str, matches[:3]))} (+{industry:g}/40)")
    else:
        reasons.append(f"Industry relevance is uncertain (+{industry:g}/40)")

    locations = business.get("target_locations", [])
    address = str(candidate.get("address") or "").lower()
    location_matches = [loc for loc in locations if loc and str(loc).lower() in address]
    geo = 25.0 if location_matches else (10.0 if address and not locations else (5.0 if address else 0.0))
    if location_matches:
        reasons.append(f"Located in target area: {location_matches[0]} (+{geo:g}/25)")
    elif geo:
        reasons.append(f"Address is available, but target-area match is unconfirmed (+{geo:g}/25)")

    activity = 0.0
    reviews = candidate.get("reviews")
    rating = candidate.get("rating")
    if isinstance(reviews, (int, float)) and reviews > 0:
        activity += 12
        reasons.append("Public review activity is visible (+12/20)")
    if isinstance(rating, (int, float)) and 0 < rating <= 5:
        activity += 4
        reasons.append("Public rating is available (+4/20)")
    if candidate.get("snippet"):
        activity += 4
        reasons.append("Recent/public listing evidence is available (+4/20)")
    if activity == 0:
        reasons.append("No activity evidence found (+0/20)")

    # Source age receives up to 5 points; the remaining 10 measure source completeness.
    freshness = 0.0
    raw_retrieved = candidate.get("evidence_date")
    try:
        if isinstance(raw_retrieved, datetime):
            evidence_at = raw_retrieved
        elif isinstance(raw_retrieved, str):
            relative = re.fullmatch(r"\s*(\d+)\s+(day|week|month|year)s?\s+ago\s*", raw_retrieved, re.I)
            if relative:
                amount = int(relative.group(1))
                unit = relative.group(2).lower()
                age_days = amount * {"day": 1, "week": 7, "month": 30, "year": 365}[unit]
                evidence_at = datetime.now(timezone.utc) - timedelta(days=age_days)
            else:
                parsed = raw_retrieved.replace("Z", "+00:00")
                try:
                    evidence_at = datetime.fromisoformat(parsed)
                except ValueError:
                    evidence_at = datetime.strptime(raw_retrieved.strip(), "%b %d, %Y").replace(tzinfo=timezone.utc)
        else:
            evidence_at = None
        if isinstance(evidence_at, datetime):
            if evidence_at.tzinfo is None:
                evidence_at = evidence_at.replace(tzinfo=timezone.utc)
            age_days = max(0.0, (datetime.now(timezone.utc) - evidence_at.astimezone(timezone.utc)).total_seconds() / 86400)
            freshness = 5.0 if age_days <= 30 else (3.0 if age_days <= 90 else (1.0 if age_days <= 365 else 0.0))
    except (ValueError, TypeError, OverflowError):
        freshness = 0.0
    if freshness:
        reasons.append(f"Source evidence is within the last year (+{freshness:g}/5 freshness)")
    else:
        reasons.append("Source age is unavailable or older than one year (+0/5 freshness)")

    completeness = 0.0
    if candidate.get("website") and urlparse(str(candidate["website"])).scheme in ("http", "https"):
        completeness += 4
        reasons.append("Website is available (+4/10 completeness)")
    if candidate.get("address"):
        completeness += 3
        reasons.append("Address is available (+3/10 completeness)")
    if candidate.get("category"):
        completeness += 2
        reasons.append("Business category is available (+2/10 completeness)")
    if candidate.get("snippet"):
        completeness += 1
        reasons.append("Source snippet provides context (+1/10 completeness)")

    total = min(100.0, industry + geo + activity + freshness + completeness)
    return round(total, 1), reasons
