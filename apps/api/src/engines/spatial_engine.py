"""
SRMAP SAGE — Campus Spatial & Navigation Engine
Graph representation of the SRMAP campus using NetworkX.
Supports topological shortest-path routing, building/landmark lookups, and structured step-by-step navigation.
STRICT RULE: Do not claim GPS accuracy unless officially surveyed.
If destination is unknown, refuse cleanly.
"""

from datetime import datetime, timezone
import json
import logging
import os
from typing import Optional, List, Dict, Any
import networkx as nx
from src.models.schemas import NavigationCardPayload, RouteSegment

logger = logging.getLogger(__name__)

DEFAULT_NODES_PATH = "data/seeds/campus_nodes.template.json"
DEFAULT_EDGES_PATH = "data/seeds/campus_edges.template.json"


class CampusSpatialEngine:
    """
    Topological spatial pathfinding engine for SRM University-AP campus.
    Uses NetworkX graph pathfinding across campus nodes and edges.
    """

    WALKING_SPEED_METERS_PER_SEC = 1.2  # ~4.3 km/h

    def __init__(self, nodes_path: str = DEFAULT_NODES_PATH, edges_path: str = DEFAULT_EDGES_PATH):
        self.graph = nx.DiGraph()
        self.nodes_data: Dict[str, Dict[str, Any]] = {}
        self._init_default_topology(nodes_path, edges_path)

    def _init_default_topology(self, nodes_path: str, edges_path: str):
        """Loads baseline topological nodes and edges if available."""
        if os.path.exists(nodes_path) and os.path.exists(edges_path):
            try:
                with open(nodes_path, "r", encoding="utf-8") as fn, open(edges_path, "r", encoding="utf-8") as fe:
                    nodes = json.load(fn)
                    edges = json.load(fe)
                    self.load_topology(nodes, edges)
            except Exception as e:
                logger.error(f"Error initializing default campus topology: {e}")

    def load_topology(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
        """Loads or updates campus topology graph."""
        self.graph.clear()
        self.nodes_data.clear()

        for n in nodes:
            node_id = n["id"]
            self.nodes_data[node_id] = n
            self.graph.add_node(node_id, **n)

        for e in edges:
            u, v = e["from_node"], e["to_node"]
            weight = float(e.get("distance_meters", 100.0))
            instructions = e.get("instructions", "Proceed along path")
            self.graph.add_edge(u, v, weight=weight, instructions=instructions)
            # Add bidirectional edge if walking path
            if e.get("accessibility_type", "walking") == "walking" and not self.graph.has_edge(v, u):
                self.graph.add_edge(v, u, weight=weight, instructions=f"Return along path towards {self.nodes_data.get(u, {}).get('name', u)}")

    def find_node_by_keyword(self, keyword: str) -> Optional[str]:
        """Finds closest matching node ID for an entity, landmark, or building."""
        kw = keyword.lower().strip()
        if not kw:
            return None

        # Alias dictionary for common student queries
        aliases = {
            "library": "node_academic_block",
            "central library": "node_academic_block",
            "cse": "node_academic_block",
            "cse department": "node_academic_block",
            "cse labs": "node_academic_block",
            "academic": "node_academic_block",
            "academic block": "node_academic_block",
            "block a": "node_academic_block",
            "admin": "node_admin_block",
            "admin block": "node_admin_block",
            "administrative block": "node_admin_block",
            "registrar": "node_admin_block",
            "placement office": "node_admin_block",
            "crcs": "node_admin_block",
            "crcs office": "node_admin_block",
            "hostel": "node_hostel_tower_a",
            "hostel a": "node_hostel_tower_a",
            "hostel tower a": "node_hostel_tower_a",
            "dining": "node_central_dining",
            "canteen": "node_central_dining",
            "mess": "node_central_dining",
            "food court": "node_central_dining",
            "medical": "node_health_center",
            "medical center": "node_health_center",
            "medical centre": "node_health_center",
            "health center": "node_health_center",
            "clinic": "node_health_center",
            "pharmacy": "node_health_center",
            "hospital": "node_health_center"
        }

        for alias, node_id in aliases.items():
            if alias in kw or kw in alias:
                if node_id in self.nodes_data:
                    return node_id

        for node_id, data in self.nodes_data.items():
            if kw in data["name"].lower() or kw in data.get("block_code", "").lower():
                return node_id
            for landmark in data.get("landmarks", []):
                if kw in landmark.lower():
                    return node_id
        return None

    def get_route(self, origin_identifier: str, destination_identifier: str) -> Optional[NavigationCardPayload]:
        """
        Computes shortest walking route and returns structured NavigationCardPayload.
        If either origin or destination is unverified/unknown, returns None.
        """
        origin_id = self.find_node_by_keyword(origin_identifier) or origin_identifier
        destination_id = self.find_node_by_keyword(destination_identifier) or destination_identifier

        if origin_id not in self.graph or destination_id not in self.graph:
            return None

        try:
            path = nx.shortest_path(self.graph, source=origin_id, target=destination_id, weight="weight")
            total_distance = nx.shortest_path_length(self.graph, source=origin_id, target=destination_id, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        route_segments = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.graph.get_edge_data(u, v, default={})
            target_data = self.nodes_data.get(v, {})
            instruction = edge_data.get("instructions", f"Walk towards {target_data.get('name', v)}.")
            route_segments.append(
                RouteSegment(
                    instruction=instruction,
                    distance_meters=round(edge_data.get("weight", 0.0), 1),
                    landmarks=target_data.get("landmarks", [])
                )
            )
        if not route_segments and origin_id == destination_id:
            route_segments.append(
                RouteSegment(
                    instruction=f"You are at {self.nodes_data.get(destination_id, {}).get('name', destination_id)}. Proceed inside.",
                    distance_meters=10.0,
                    landmarks=[]
                )
            )
            total_distance = 10.0

        walk_minutes = round(total_distance / (self.WALKING_SPEED_METERS_PER_SEC * 60), 1)

        return NavigationCardPayload(
            origin_name=self.nodes_data.get(origin_id, {}).get("name", origin_id),
            destination_name=self.nodes_data.get(destination_id, {}).get("name", destination_id),
            total_distance_meters=round(total_distance, 1),
            estimated_walk_minutes=walk_minutes,
            steps=route_segments,
            is_gps_verified=False,
            source_id="campus_spatial_topology_v1"
        )
