"""
Attack Path API Routes

REST API endpoints for attack path visualization and analysis.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from analysis.attack_path import AttackPathFinder, create_mock_attack_graph
from database.models import SessionLocal

router = APIRouter(prefix="/attack-path", tags=["Attack Path"])


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AttackPathRequest(BaseModel):
    """Request to find attack paths."""

    scan_id: str = Field(..., description="Scan ID to analyze")
    entry_point: Optional[str] = Field(
        None, description="Specific entry point"
    )
    target: Optional[str] = Field(None, description="Specific target")


class AttackPathResponse(BaseModel):
    """Response with attack path data."""

    entry_point: str
    target: str
    path: List[str]
    length: int
    difficulty_score: float
    nodes: List[dict]


@router.get("/graph/{scan_id}")
def get_attack_graph(
    scan_id: str,
    db: Session = Depends(get_db),
):
    """
    Get attack graph for a scan.

    Returns nodes and edges in Cytoscape.js format for visualization.
    """
    # For demo, use mock data
    # In production, build from actual scan results
    graph = create_mock_attack_graph()

    return {
        "scan_id": scan_id,
        "graph": graph.to_cytoscape_format(),
        "statistics": {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "entry_points": len(graph.get_entry_points()),
            "crown_jewels": len(graph.get_crown_jewels()),
        },
    }


@router.post("/find-paths")
def find_attack_paths(
    request: AttackPathRequest,
    db: Session = Depends(get_db),
):
    """
    Find attack paths from entry points to targets.

    Returns all possible attack paths with difficulty scores.
    """
    graph = create_mock_attack_graph()
    finder = AttackPathFinder(graph)

    if request.target:
        # Find paths to specific target
        paths = []
        entry_points = (
            [request.entry_point]
            if request.entry_point
            else [n.id for n in graph.get_entry_points()]
        )

        for entry in entry_points:
            path = finder.find_shortest_path(entry, request.target)
            if path:
                difficulty = finder._calculate_path_difficulty(path)
                paths.append(
                    {
                        "entry_point": entry,
                        "target": request.target,
                        "path": path,
                        "length": len(path),
                        "difficulty_score": difficulty,
                        "nodes": [graph.nodes[n].to_dict() for n in path],
                    }
                )

        # Sort by difficulty
        paths.sort(key=lambda x: x["difficulty_score"])

        return {
            "scan_id": request.scan_id,
            "target": request.target,
            "paths_found": len(paths),
            "paths": paths,
        }
    else:
        # Find all paths to crown jewels
        paths = finder.find_paths_to_crown_jewels(request.entry_point)

        return {
            "scan_id": request.scan_id,
            "paths_found": len(paths),
            "paths": paths,
        }


@router.get("/critical-paths/{scan_id}")
def get_critical_paths(
    scan_id: str,
    top_n: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Get the most critical attack paths.

    Returns the easiest paths to critical assets.
    """
    graph = create_mock_attack_graph()
    finder = AttackPathFinder(graph)

    critical_paths = finder.find_critical_paths(top_n=top_n)

    return {
        "scan_id": scan_id,
        "critical_paths": critical_paths,
        "attack_surface": finder.calculate_attack_surface(),
    }


@router.get("/attack-surface/{scan_id}")
def get_attack_surface(
    scan_id: str,
    db: Session = Depends(get_db),
):
    """
    Calculate attack surface metrics.

    Returns comprehensive attack surface analysis.
    """
    graph = create_mock_attack_graph()
    finder = AttackPathFinder(graph)

    return {
        "scan_id": scan_id,
        "analysis": finder.calculate_attack_surface(),
    }


@router.get("/nodes/{scan_id}")
def get_graph_nodes(
    scan_id: str,
    node_type: Optional[str] = None,
    compromised_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    Get nodes from the attack graph.

    Supports filtering by type and compromise status.
    """
    graph = create_mock_attack_graph()

    nodes = list(graph.nodes.values())

    if node_type:
        nodes = [n for n in nodes if n.node_type.value == node_type]

    if compromised_only:
        nodes = [n for n in nodes if n.compromised]

    return {
        "scan_id": scan_id,
        "total": len(nodes),
        "nodes": [n.to_dict() for n in nodes],
    }


@router.post("/simulate")
def simulate_attack(
    scan_id: str,
    entry_point: str,
    max_steps: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Simulate an attack from an entry point.

    Shows step-by-step how an attacker could progress through the network.
    """
    graph = create_mock_attack_graph()
    finder = AttackPathFinder(graph)

    # Find paths to all crown jewels
    paths = finder.find_paths_to_crown_jewels(entry_point)

    # Select the easiest path
    if not paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attack paths found from this entry point",
        )

    easiest_path = paths[0]

    # Generate simulation steps
    steps = []
    path_nodes = easiest_path["path"]

    for i in range(len(path_nodes) - 1):
        source = graph.nodes[path_nodes[i]]
        target = graph.nodes[path_nodes[i + 1]]

        # Get edge data
        edge_data = graph.graph.get_edge_data(path_nodes[i], path_nodes[i + 1])

        steps.append(
            {
                "step": i + 1,
                "action": f"Move from {source.name} to {target.name}",
                "technique": edge_data.get("technique_name", "Unknown"),
                "technique_id": edge_data.get("technique", "T0000"),
                "description": edge_data.get("description", ""),
                "difficulty": edge_data.get("difficulty", "medium"),
                "success_probability": edge_data.get(
                    "success_probability", 0.5
                ),
            }
        )

    return {
        "scan_id": scan_id,
        "entry_point": entry_point,
        "target": easiest_path["crown_jewel"],
        "simulation": {
            "total_steps": len(steps),
            "overall_difficulty": easiest_path["difficulty_score"],
            "steps": steps,
        },
    }
