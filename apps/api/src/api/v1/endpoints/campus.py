from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_async_db
from src.models.db_models import CampusNode, CampusEdge
from src.models.schemas import NavigationCardPayload
from src.engines.spatial_engine import CampusSpatialEngine

router = APIRouter(prefix="/campus", tags=["Campus"])
spatial_engine = CampusSpatialEngine()


@router.get("/nodes")
async def list_campus_nodes(db: AsyncSession = Depends(get_async_db)):
    stmt = select(CampusNode)
    res = await db.execute(stmt)
    nodes = res.scalars().all()
    return [
        {
            "id": n.id,
            "name": n.name,
            "category": n.category,
            "block_code": n.block_code,
            "floor": n.floor,
            "landmarks": n.landmarks
        }
        for n in nodes
    ]


@router.get("/navigate", response_model=NavigationCardPayload)
async def navigate_route(
    origin: str = Query(..., description="Origin node ID or building name"),
    destination: str = Query(..., description="Destination node ID or building name"),
    db: AsyncSession = Depends(get_async_db)
):
    # Ensure topology is initialized from DB if empty
    if not spatial_engine.graph.nodes:
        nodes_res = await db.execute(select(CampusNode))
        edges_res = await db.execute(select(CampusEdge))
        nodes = [
            {
                "id": n.id,
                "name": n.name,
                "category": n.category,
                "block_code": n.block_code,
                "floor": n.floor,
                "landmarks": n.landmarks
            }
            for n in nodes_res.scalars().all()
        ]
        edges = [
            {
                "from_node": e.from_node,
                "to_node": e.to_node,
                "distance_meters": float(e.distance_meters),
                "accessibility_type": e.accessibility_type,
                "instructions": e.instructions
            }
            for e in edges_res.scalars().all()
        ]
        spatial_engine.load_topology(nodes, edges)

    origin_id = spatial_engine.find_node_by_keyword(origin) or origin
    destination_id = spatial_engine.find_node_by_keyword(destination) or destination

    route = spatial_engine.get_route(origin_id, destination_id)
    if not route:
        raise HTTPException(
            status_code=404,
            detail=f"Could not calculate walking path between '{origin}' and '{destination}'"
        )
    return route
