import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from services.ingestion.hasher import compute_text_hash

logger = logging.getLogger(__name__)

OFFICIAL_WEB_REGISTRY = [
    {
        "url": "https://www.srmap.edu.in/",
        "title": "SRM University-AP Official Portal",
        "authority_level": 1,
        "source_type": "official_website",
        "domain_category": "GENERAL_UNIVERSITY_INFORMATION"
    },
    {
        "url": "https://student.srmap.edu.in/srmapstudentcorner/HRDSystem",
        "title": "SRMAP Student Portal HRD System",
        "authority_level": 2,
        "source_type": "authenticated_portal",
        "domain_category": "STUDENT_AFFAIRS"
    },
    {
        "url": "https://placements.haveloc.com/student-home",
        "title": "Haveloc Placement Portal (SRMAP)",
        "authority_level": 3,
        "source_type": "operational_platform",
        "domain_category": "PLACEMENTS"
    },
    {
        "url": "https://intranet.srmap.edu.in/wp-login.php?redirect_to=%2Fdocument-manager%2F%3Ffid%3DMTA3",
        "title": "SRMAP Intranet Document Manager",
        "authority_level": 2,
        "source_type": "authenticated_intranet",
        "domain_category": "ACADEMICS"
    },
    {
        "url": "https://www.instagram.com/srmuap/?hl=en",
        "title": "SRM University-AP Official Instagram",
        "authority_level": 4,
        "source_type": "social_media",
        "domain_category": "EVENTS"
    },
    {
        "url": "https://en.wikipedia.org/wiki/SRM_University,_Andhra_Pradesh",
        "title": "SRM University, Andhra Pradesh (Wikipedia Overview)",
        "authority_level": 5,
        "source_type": "background_context",
        "domain_category": "GENERAL_UNIVERSITY_INFORMATION"
    }
]


class WebCrawler:
    def __init__(self, user_agent: str = "SRMAP-SAGE-Bot/1.0 (Academic Guidance Engine; contact@srmap.edu.in)"):
        self.headers = {"User-Agent": user_agent}

    def fetch_source(self, source_info: Dict[str, Any]) -> Dict[str, Any]:
        url = source_info["url"]
        result = {
            "url": url,
            "title": source_info["title"],
            "authority_level": source_info["authority_level"],
            "source_type": source_info["source_type"],
            "domain_category": source_info["domain_category"],
            "status": "pending",
            "http_status": None,
            "content_hash": None,
            "text": "",
            "crawled_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }

        try:
            with httpx.Client(headers=self.headers, follow_redirects=True, timeout=12.0) as client:
                resp = client.get(url)
                result["http_status"] = resp.status_code

                if resp.status_code in [401, 403]:
                    result["status"] = "AUTHENTICATION_REQUIRED"
                    result["metadata"]["reason"] = f"HTTP {resp.status_code} Access Denied / Auth Required"
                    return result

                html = resp.text
                lower_html = html.lower()

                # Detect login / authentication requirements
                is_auth = (
                    "wp-login.php" in str(resp.url).lower()
                    or "login" in str(resp.url).lower()
                    or "signin" in str(resp.url).lower()
                    or "password" in lower_html and ("username" in lower_html or "user id" in lower_html or "log in" in lower_html)
                )

                if is_auth and source_info["authority_level"] in [2, 3]:
                    result["status"] = "AUTHENTICATION_REQUIRED"
                    result["metadata"]["auth_endpoint"] = str(resp.url)
                    result["metadata"]["reason"] = "Authentication form or redirect detected. In accordance with SAGE safety rules, no credential bypass is attempted."
                    return result

                # Parse public HTML
                soup = BeautifulSoup(html, "html.parser")
                # Remove scripts and styles
                for s in soup(["script", "style", "nav", "footer"]):
                    s.extract()

                page_title = soup.title.string.strip() if soup.title and soup.title.string else source_info["title"]
                result["title"] = page_title
                clean_text = " ".join(soup.get_text().split())
                result["text"] = clean_text[:15000]  # Store first 15k chars of clean text
                result["content_hash"] = compute_text_hash(result["text"])
                result["status"] = "SUCCESS"

        except Exception as e:
            result["status"] = "FAILED"
            result["metadata"]["error"] = str(e)
            logger.error(f"Failed to crawl {url}: {e}")

        return result
