import logging
from typing import Optional, List, Dict, Any
import networkx as nx
from src.models.schemas import NavigationCardPayload, RouteSegment

logger = logging.getLogger(__name__)


class CampusSpatialEngine:
    """
    Topological spatial pathfinding engine for SRM University-AP campus.
    Uses NetworkX graph pathfinding across campus nodes and edges.
    """

    WALKING_SPEED_METERS_PER_SEC = 1.2  # ~4.3 km/h

    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes_data: Dict[str, Dict[str, Any]] = {}

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
            if e.get("accessibility_type") == "walking" and not self.graph.has_edge(v, u):
                self.graph.add_edge(v, u, weight=weight, instructions=f"Return along path towards {self.nodes_data.get(u, {}).get('name', u)}")

    def find_node_by_keyword(self, keyword: str) -> Optional[str]:
        """Finds closest matching node ID for an entity or building."""
        kw = keyword.lower()
        for node_id, data in self.nodes_data.items():
            if kw in data["name"].lower() or kw in data.get("block_code", "").lower():
                return node_id
            for landmark in data.get("landmarks", []):
                if kw in landmark.lower():
                    return node_id
        return None

    def get_route(self, origin_id: str, destination_id: str) -> Optional[NavigationCardPayload]:
        """Computes shortest walking route and returns structured NavigationCardPayload."""
        if origin_id not in self.graph or destination_id not in self.graph:
            return None

        try:
            path = nx.shortest_path(self.graph, source=origin_id, target=destination_id, weight="weight")
            total_distance = nx.shortest_path_length(self.graph, source=origin_id, target=destination_id, weight="weight")
        except nx.NetworkXNoPath:
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

        walk_minutes = round(total_distance / (self.WALKING_SPEED_METERS_PER_SEC * 60), 1)

        return NavigationCardPayload(
            origin_name=self.nodes_data.get(origin_id, {}).get("name", origin_id),
            destination_name=self.nodes_data.get(destination_id, {}).get("name", destination_id),
            total_distance_meters=round(total_distance, 1),
            estimated_walk_minutes=walk_minutes,
            steps=route_segments
        )
