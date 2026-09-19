"""
SRMAP SAGE — Source Registry
Defines the controlled source registry, hierarchy, authority levels, and safety boundaries.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, HttpUrl, Field


class AuthorityLevel(int, Enum):
    LEVEL_1_OFFICIAL_POLICIES = 1       # Official SRMAP policies, regulations, signed circulars, official notices
    LEVEL_2_AUTHENTICATED_PORTALS = 2   # Official authenticated university systems (HRD, Intranet)
    LEVEL_3_OPERATIONAL_PLATFORMS = 3   # Associated operational platforms (e.g. placements.haveloc.com)
    LEVEL_4_SOCIAL_MEDIA = 4            # Official institutional social media
    LEVEL_5_BACKGROUND_SOURCES = 5      # External background sources (e.g. Wikipedia)


class AccessStatus(str, Enum):
    PUBLIC = "PUBLIC"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    AUTHENTICATED_OPERATIONAL_PLATFORM = "AUTHENTICATED_OPERATIONAL_PLATFORM"
    PUBLIC_SUPPLEMENTARY = "PUBLIC_SUPPLEMENTARY"
    BACKGROUND_ONLY = "BACKGROUND_ONLY"
    CONTENT_NOT_RETRIEVED = "CONTENT_NOT_RETRIEVED"
    CRAWL_ERROR = "CRAWL_ERROR"


class ControlledSource(BaseModel):
    id: str
    name: str
    url: str
    authority_level: AuthorityLevel
    access_status: AccessStatus
    crawl_interval_hours: int = 24
    respect_robots_txt: bool = True
    bypass_allowed: bool = False
    requires_auth: bool = False
    notes: Optional[str] = None


# Official Initial Registry
SOURCE_REGISTRY: Dict[str, ControlledSource] = {
    "src_srmap_main": ControlledSource(
        id="src_srmap_main",
        name="SRMAP Official Website",
        url="https://www.srmap.edu.in/",
        authority_level=AuthorityLevel.LEVEL_1_OFFICIAL_POLICIES,
        access_status=AccessStatus.PUBLIC,
        crawl_interval_hours=24,
        respect_robots_txt=True,
        bypass_allowed=False,
        requires_auth=False,
        notes="Primary public portal for university announcements, press releases, events, and circulars."
    ),
    "src_srmap_hrd": ControlledSource(
        id="src_srmap_hrd",
        name="SRMAP Student Portal HRD System",
        url="https://student.srmap.edu.in/srmapstudentcorner/HRDSystem",
        authority_level=AuthorityLevel.LEVEL_2_AUTHENTICATED_PORTALS,
        access_status=AccessStatus.AUTHENTICATION_REQUIRED,
        crawl_interval_hours=168,  # Check status weekly without hammering
        respect_robots_txt=True,
        bypass_allowed=False,
        requires_auth=True,
        notes="Official student corner. Requires student login. SAGE will NEVER bypass credentials."
    ),
    "src_srmap_intranet": ControlledSource(
        id="src_srmap_intranet",
        name="SRMAP Intranet Document Manager",
        url="https://intranet.srmap.edu.in/",
        authority_level=AuthorityLevel.LEVEL_2_AUTHENTICATED_PORTALS,
        access_status=AccessStatus.AUTHENTICATION_REQUIRED,
        crawl_interval_hours=168,
        respect_robots_txt=True,
        bypass_allowed=False,
        requires_auth=True,
        notes="Internal staff/student intranet. Requires university authentication. Never bypassed."
    ),
    "src_haveloc_placement": ControlledSource(
        id="src_haveloc_placement",
        name="Haveloc Student Placement Portal",
        url="https://placements.haveloc.com/student-home",
        authority_level=AuthorityLevel.LEVEL_3_OPERATIONAL_PLATFORMS,
        access_status=AccessStatus.AUTHENTICATED_OPERATIONAL_PLATFORM,
        crawl_interval_hours=72,
        respect_robots_txt=True,
        bypass_allowed=False,
        requires_auth=True,
        notes="Operational placement partner platform. Client-side authenticated web app."
    ),
    "src_srmuap_instagram": ControlledSource(
        id="src_srmuap_instagram",
        name="SRMAP Official Instagram",
        url="https://www.instagram.com/srmuap/",
        authority_level=AuthorityLevel.LEVEL_4_SOCIAL_MEDIA,
        access_status=AccessStatus.PUBLIC_SUPPLEMENTARY,
        crawl_interval_hours=24,
        respect_robots_txt=True,
        bypass_allowed=False,
        requires_auth=False,
        notes="Supplementary campus life and event updates. Cannot override official policy."
    ),
    "src_wikipedia_srmap": ControlledSource(
        id="src_wikipedia_srmap",
        name="Wikipedia SRM AP Page",
        url="https://en.wikipedia.org/wiki/SRM_University,_AP",
        authority_level=AuthorityLevel.LEVEL_5_BACKGROUND_SOURCES,
        access_status=AccessStatus.BACKGROUND_ONLY,
        crawl_interval_hours=168,
        respect_robots_txt=True,
        bypass_allowed=False,
        requires_auth=False,
        notes="External background context only. Never allowed to override official university sources."
    ),
}


def get_source_by_url(url: str) -> Optional[ControlledSource]:
    for src in SOURCE_REGISTRY.values():
        if url.startswith(src.url.rstrip("/")) or src.url.startswith(url.rstrip("/")):
            return src
    return None


def get_all_sources() -> List[ControlledSource]:
    return list(SOURCE_REGISTRY.values())


def is_auth_boundary_violation(url: str) -> bool:
    """Verifies that an incoming retrieval request will not attempt to bypass login boundaries."""
    src = get_source_by_url(url)
    if src and src.requires_auth:
        return True
    return False
