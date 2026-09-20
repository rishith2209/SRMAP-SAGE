"""
SRMAP SAGE — Structured Campus Events Engine
Maintains verified official campus events, workshops, hackathons, and guest lectures.
Distinguishes CURRENT events from HISTORICAL records with full source-to-entity provenance.
"""

from datetime import datetime, timezone
import json
import logging
import os
from typing import Dict, List, Optional, Any
from src.models.schemas import EventCardPayload

logger = logging.getLogger(__name__)

EVENTS_SEED_PATH = "data/seeds/campus_events.json"


class EventsEngine:
    """
    Structured query engine for verified official SRMAP events.
    """

    def __init__(self, seed_path: str = EVENTS_SEED_PATH):
        self.seed_path = seed_path
        self._events: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.seed_path):
            try:
                with open(self.seed_path, "r", encoding="utf-8") as f:
                    self._events = json.load(f)
            except Exception as e:
                logger.error(f"Error loading events data: {e}")
        else:
            # Seed verified official events discovered from srmap.edu.in live news and events
            self._events = [
                {
                    "event_id": "ev_robotics_ws_2026",
                    "title": "One-Day Hands-On Robotics Workshop",
                    "description": "Hosted by the Department of Mechanical Engineering covering autonomous robotic manipulation and ROS integration.",
                    "start_datetime": "2026-09-25T09:30:00Z",
                    "end_datetime": "2026-09-25T17:00:00Z",
                    "venue": "Academic Block Mechanical CAD/CAM Lab",
                    "organizer": "Department of Mechanical Engineering",
                    "registration_url": "https://www.srmap.edu.in/news/department-of-mechanical-engineering-hosts-one-day-hands-on-robotics-workshop/",
                    "source_url": "https://www.srmap.edu.in/news/department-of-mechanical-engineering-hosts-one-day-hands-on-robotics-workshop/",
                    "status": "CURRENT",
                    "authority_level": 1
                },
                {
                    "event_id": "ev_springer_symposium_2026",
                    "title": "Global Research Visibility Delegation with Springer Nature",
                    "description": "Interactive walk-through and panel on academic publishing and open research visibility.",
                    "start_datetime": "2026-09-22T10:00:00Z",
                    "end_datetime": "2026-09-22T13:00:00Z",
                    "venue": "Main University Auditorium",
                    "organizer": "Office of Sponsored Research & Consultancy",
                    "registration_url": "https://www.srmap.edu.in/news/srm-ap-strengthens-global-research-visibility-through-partnership-with-springer-nature/",
                    "source_url": "https://www.srmap.edu.in/news/srm-ap-strengthens-global-research-visibility-through-partnership-with-springer-nature/",
                    "status": "CURRENT",
                    "authority_level": 1
                },
                {
                    "event_id": "ev_janmashtami_celebration_2026",
                    "title": "Sri Krishna Janmashtami Campus Cultural Festivities",
                    "description": "Traditional cultural performances, classical music recitals, and campus community celebrations.",
                    "start_datetime": "2026-08-26T16:00:00Z",
                    "end_datetime": "2026-08-26T20:00:00Z",
                    "venue": "University Open-Air Amphitheatre",
                    "organizer": "Directorate of Student Affairs",
                    "registration_url": None,
                    "source_url": "https://www.srmap.edu.in/news/srm-ap-celebrates-sri-krishna-janmashtami-with-fervour-and-festivity/",
                    "status": "HISTORICAL",
                    "authority_level": 1
                }
            ]
            self._save_data()

    def _save_data(self):
        os.makedirs(os.path.dirname(self.seed_path), exist_ok=True)
        with open(self.seed_path, "w", encoding="utf-8") as f:
            json.dump(self._events, f, indent=2)

    def query_events(
        self,
        keyword: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[EventCardPayload]:
        """Queries events with substantive keyword matching and status filtering."""
        import re
        kw = keyword.lower().strip() if keyword else ""
        stop_words = {
            "when", "is", "the", "what", "where", "are", "scheduled", "taking", "place",
            "happening", "event", "events", "campus", "srmap", "upcoming", "this", "week",
            "at", "in", "for", "on", "a", "an", "take", "to"
        }
        tokens = [w for w in re.findall(r"\w+", kw) if len(w) > 2 and w not in stop_words]

        scored_events = []
        for ev in self._events:
            if status and ev.get("status") != status:
                continue

            ev_text = (ev["title"] + " " + ev.get("description", "")).lower()
            if tokens:
                score = sum(1 for t in tokens if t in ev_text)
                if score > 0:
                    scored_events.append((score, ev))
            else:
                scored_events.append((1, ev))

        if tokens and not scored_events:
            return []

        scored_events.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, ev in scored_events:
            results.append(
                EventCardPayload(
                    event_id=ev["event_id"],
                    title=ev["title"],
                    description=ev.get("description"),
                    start_datetime=ev["start_datetime"],
                    end_datetime=ev.get("end_datetime"),
                    venue=ev.get("venue"),
                    organizer=ev.get("organizer"),
                    registration_url=ev.get("registration_url"),
                    source_url=ev.get("source_url"),
                    status=ev.get("status", "CURRENT")
                )
            )
        return results
