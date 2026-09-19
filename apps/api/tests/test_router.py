import pytest
from src.engines.router_engine import IntentRouter
from src.providers.mock_provider import MockLLMProvider
from src.engines.spatial_engine import CampusSpatialEngine


def test_intent_router_classification():
    provider = MockLLMProvider()
    router = IntentRouter(provider)

    assert router.classify_fast("How do I apply for medical leave?") == "PROCEDURE_FORM"
    assert router.classify_fast("Where is Professor John's office?") == "FACULTY_LOOKUP"
    assert router.classify_fast("How do I go from Hostel A to the library?") == "CAMPUS_DIRECTIONS"
    assert router.classify_fast("What was the placement package for TCS last year?") == "PLACEMENT_QUERY"
    assert router.classify_fast("What is the minimum attendance required for semester exams?") == "ACADEMIC_POLICY"


def test_campus_spatial_engine_pathfinding():
    engine = CampusSpatialEngine()
    nodes = [
        {"id": "node_a", "name": "Hostel Alpha", "category": "hostel"},
        {"id": "node_b", "name": "Dining Hall", "category": "dining"},
        {"id": "node_c", "name": "Academic Library", "category": "building"}
    ]
    edges = [
        {"from_node": "node_a", "to_node": "node_b", "distance_meters": 100.0, "accessibility_type": "walking", "instructions": "Walk straight from Hostel Alpha to Dining Hall"},
        {"from_node": "node_b", "to_node": "node_c", "distance_meters": 150.0, "accessibility_type": "walking", "instructions": "Proceed from Dining Hall to Academic Library"}
    ]
    engine.load_topology(nodes, edges)

    route = engine.get_route("node_a", "node_c")
    assert route is not None
    assert route.total_distance_meters == 250.0
    assert len(route.steps) == 2
    assert route.origin_name == "Hostel Alpha"
    assert route.destination_name == "Academic Library"


@pytest.mark.asyncio
async def test_mock_provider_fallback():
    provider = MockLLMProvider()
    embedding = await provider.generate_embedding("SRMAP Attendance Policy")
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)
