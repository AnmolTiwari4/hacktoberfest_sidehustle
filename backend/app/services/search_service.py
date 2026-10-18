"""SerpAPI Google Search and Maps integration with normalized output."""

import os
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


class SearchProviderError(RuntimeError):
    """Raised when SerpAPI is unavailable or returns an invalid response."""


def build_queries(industry: str, products: list[str], location: str, custom: str | None = None) -> list[str]:
    terms = list(dict.fromkeys([industry, *products]))[:3]
    queries = [custom.strip()] if custom and custom.strip() else []
    queries.extend(f"{term} businesses {location}" for term in terms)
    queries.append(f"{industry} market trends {location}")
    return list(dict.fromkeys(q for q in queries if q))


def _domain(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host.removeprefix("www.")


def _normalize(entry: dict, source_type: str, default_url: str = "") -> dict:
    link = entry.get("link") or entry.get("website") or entry.get("url") or default_url
    name = str(entry.get("title") or entry.get("name") or "Unknown business").strip()
    address = str(entry.get("address") or "").strip() or None
    if not link and source_type == "maps":
        link = f"https://www.google.com/maps/search/?api=1&query={quote_plus(' '.join(part for part in (name, address or '') if part))}"
    return {
        "url": str(link or ""),
        "title": str(entry.get("title") or entry.get("name") or "Untitled source").strip(),
        "source_type": source_type,
        "snippet": str(entry.get("snippet") or entry.get("description") or entry.get("address") or "").strip(),
        "name": name,
        "website": str(entry.get("website") or link or "").strip() or None,
        "address": address,
        "category": str(entry.get("type") or entry.get("category") or "").strip() or None,
        "rating": entry.get("rating"),
        "reviews": entry.get("reviews"),
        "evidence_date": entry.get("date") or entry.get("published_at") or entry.get("last_updated"),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


def _request(params: dict) -> dict:
    key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")
    if not key:
        raise SearchProviderError("SERPAPI_KEY is not configured")
    try:
        response = requests.get(SERPAPI_ENDPOINT, params={**params, "api_key": key}, timeout=(5, 25))
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise SearchProviderError(f"SerpAPI request failed: {exc}") from exc
    if payload.get("error"):
        raise SearchProviderError(str(payload["error"]))
    return payload


def search_google(query: str, limit: int = 10) -> list[dict]:
    payload = _request({"engine": "google", "q": query, "num": min(max(limit, 1), 100)})
    entries = [_normalize(item, "web") for item in payload.get("organic_results", [])]
    entries.extend(_normalize(item, "news") for item in payload.get("news_results", []))
    return deduplicate(entries)[:limit]


def search_maps(query: str, location: str, limit: int = 20) -> list[dict]:
    payload = _request({"engine": "google_maps", "q": f"{query} in {location}", "type": "search"})
    entries = [_normalize(item, "maps", item.get("gps_coordinates", {}).get("link", "")) for item in payload.get("local_results", [])]
    return deduplicate(entries)[:limit]


def deduplicate(entries: list[dict]) -> list[dict]:
    """Deduplicate by normalized website domain, falling back to normalized name."""
    result, seen = [], set()
    for entry in entries:
        domain = _domain(entry.get("website") or entry.get("url") or "")
        key = domain if domain else re.sub(r"\W+", "", entry.get("name", "").lower())
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result
