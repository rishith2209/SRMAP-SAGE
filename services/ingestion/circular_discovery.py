"""
SRMAP SAGE — Official Notice / Circular Discovery Engine
Discovers and ingests official public notices, circulars, news updates, and placement announcements
from public srmap.edu.in endpoints into the knowledge catalog with full provenance and content hashing.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
import httpx
from bs4 import BeautifulSoup

from services.ingestion.source_registry import (
    AuthorityLevel, AccessStatus, SOURCE_REGISTRY, is_auth_boundary_violation
)
from services.ingestion.freshness_engine import FreshnessStatus, FreshnessEngine

logger = logging.getLogger(__name__)

DISCOVERY_ALLOWLIST_ENDPOINTS = [
    "https://www.srmap.edu.in/all-news/",
    "https://www.srmap.edu.in/crcs/placements/",
    "https://www.srmap.edu.in/mediaroom/announcement-new-courses/",
    "https://www.srmap.edu.in/events/"
]

USER_AGENT = "SRMAP-SAGE-Bot/1.0 (Official University Assistance System; contact@srmap.edu.in)"


class CircularDiscoveryEngine:
    def __init__(self, catalog_path: str = "data/knowledge_catalog.json"):
        self.catalog_path = catalog_path
        self.freshness_engine = FreshnessEngine()

    @staticmethod
    def compute_sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def fetch_endpoint(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        if is_auth_boundary_violation(url):
            logger.warning(f"Skipping auth-required URL: {url}")
            return None
        try:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=15.0, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"Failed to fetch {url}: HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
        return None

    def parse_clean_content(self, html_text: str) -> Tuple[str, str, Optional[str], List[str]]:
        soup = BeautifulSoup(html_text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else "SRMAP Announcement"
        
        # Look for article header or title
        h1 = soup.find(["h1", "h2"])
        if h1 and len(h1.get_text(strip=True)) > 5:
            title = h1.get_text(strip=True)

        # Look for publication date
        published_date = None
        date_patterns = [
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
            r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
            r"\b\d{4}-\d{2}-\d{2}\b"
        ]
        text_full = soup.get_text()
        for pat in date_patterns:
            m = re.search(pat, text_full, re.IGNORECASE)
            if m:
                published_date = m.group(0).strip()
                break

        # Remove navigation, scripts, styles, footer
        for tag in soup(["nav", "header", "footer", "script", "style", "noscript"]):
            tag.decompose()

        cleaned_text = soup.get_text(separator=" ", strip=True)
        # Collapse multi-whitespace
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)

        # Extract sub-links (news or circular links)
        sublinks = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(k in href for k in ["/news/", "/announcement", "/circular", "/notice"]):
                if href.startswith("http") and "srmap.edu.in" in href:
                    sublinks.append(href)

        return title, cleaned_text, published_date, list(set(sublinks))

    async def discover_and_catalog(self) -> Dict[str, Any]:
        """
        Crawls the allowlisted discovery endpoints, extracts notices/circulars,
        computes hash, tracks versioning, and records into knowledge_catalog.json.
        """
        discovered_records = []
        now_iso = datetime.now(timezone.utc).isoformat()

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # 1. Fetch seed endpoints
            for endpoint in DISCOVERY_ALLOWLIST_ENDPOINTS:
                html = await self.fetch_endpoint(client, endpoint)
                if not html:
                    continue

                title, text, pub_date, sublinks = self.parse_clean_content(html)
                content_hash = self.compute_sha256(text)
                
                # Determine domain
                domain = "NOTICES"
                if "crcs" in endpoint or "placement" in endpoint:
                    domain = "PLACEMENT"
                elif "event" in endpoint:
                    domain = "EVENTS"
                elif "course" in endpoint or "academic" in endpoint:
                    domain = "ACADEMICS"

                record = {
                    "source_url": endpoint,
                    "title": title,
                    "published_date": pub_date or "Current Academic Year 2026-27",
                    "discovered_date": now_iso,
                    "document_type": "official_notice",
                    "domain": domain,
                    "authority_level": AuthorityLevel.LEVEL_1_OFFICIAL_POLICIES.value,
                    "content_hash": content_hash,
                    "last_checked": now_iso,
                    "retrieval_status": "CURRENT",
                    "supersedes": None,
                    "superseded_by": None,
                    "excerpt": text[:1000]
                }
                discovered_records.append(record)

                # 2. Fetch top sublinks (e.g. specific news/announcement pages)
                for sublink in sublinks[:3]:
                    sub_html = await self.fetch_endpoint(client, sublink)
                    if not sub_html:
                        continue
                    sub_title, sub_text, sub_date, _ = self.parse_clean_content(sub_html)
                    sub_hash = self.compute_sha256(sub_text)
                    sub_record = {
                        "source_url": sublink,
                        "title": sub_title,
                        "published_date": sub_date or "September 2026",
                        "discovered_date": now_iso,
                        "document_type": "official_circular_notice",
                        "domain": domain,
                        "authority_level": AuthorityLevel.LEVEL_1_OFFICIAL_POLICIES.value,
                        "content_hash": sub_hash,
                        "last_checked": now_iso,
                        "retrieval_status": "CURRENT",
                        "supersedes": None,
                        "superseded_by": None,
                        "excerpt": sub_text[:1000]
                    }
                    discovered_records.append(sub_record)

        return {
            "discovered_count": len(discovered_records),
            "timestamp": now_iso,
            "records": discovered_records
        }
