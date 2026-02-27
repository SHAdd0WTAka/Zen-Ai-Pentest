"""
Attack Path Analysis

Graph-based attack path modeling and analysis.
Uses NetworkX for graph operations and path finding.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx


class NodeType(str, Enum):
    """Types of nodes in the attack graph."""
    ENTRY_POINT = "entry_point"  # Internet-facing asset
    WORKSTATION = "workstation"  # User machine
    SERVER = "server"  # Internal server
    DATABASE = "database"  # Data store
    DOMAIN_CONTROLLER = "domain_controller"  # AD DC
    WEB_APPLICATION = "web_application"
    API_ENDPOINT = "api_endpoint"
    CLOUD_RESOURCE = "cloud_resource"
    CONTAINER = "container"
    CROWN_JEWEL = "crown_jewel"  # Critical asset


class EdgeType(str, Enum):
    """Types of edges (attack vectors) in the graph."""
    NETWORK_ACCESS = "network_access"
    CREDENTIAL_REUSE = "credential_reuse"
    VULNERABILITY_EXPLOIT = "vulnerability_exploit"
    LATERAL_MOVEMENT = "lateral_movement"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    TRUST_RELATIONSHIP = "trust_relationship"
    DATA_FLOW = "data_flow"


@dataclass
class AttackNode:
    """A node in the attack graph representing an asset."""
    id: str
    name: str
    node_type: NodeType
    ip: Optional[str] = None
    domain: Optional[str] = None
    
    # Security properties
    vulnerabilities: List[Dict] = field(default_factory=list)
    open_ports: List[int] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    
    # Compromise status
    compromised: bool = False
    compromise_method: Optional[str] = None
    
    # Value/Impact
    criticality: str = "medium"  # low, medium, high, critical
    data_sensitivity: str = "none"  # none, internal, confidential, restricted
    
    # Position for visualization
    x: Optional[float] = None
    y: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type.value,
            "ip": self.ip,
            "domain": self.domain,
            "vulnerabilities": self.vulnerabilities,
            "open_ports": self.open_ports,
            "services": self.services,
            "compromised": self.compromised,
            "compromise_method": self.compromise_method,
            "criticality": self.criticality,
            "data_sensitivity": self.data_sensitivity,
        }


@dataclass
class AttackEdge:
    """An edge in the attack graph representing a potential attack vector."""
    source: str
    target: str
    edge_type: EdgeType
    
    # Attack properties
    technique: str  # MITRE ATT&CK technique ID
    technique_name: str
    description: str
    
    # Difficulty/Success probability
    difficulty: str = "medium"  # easy, medium, hard
    success_probability: float = 0.5  # 0.0 to 1.0
    
    # Requirements
    prerequisites: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    
    # Status
    exploited: bool = False
    detected: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type.value,
            "technique": self.technique,
            "technique_name": self.technique_name,
            "description": self.description,
            "difficulty": self.difficulty,
            "success_probability": self.success_probability,
            "prerequisites": self.prerequisites,
            "required_tools": self.required_tools,
            "exploited": self.exploited,
        }


class AttackGraph:
    """
    Attack Graph representing the network topology and attack vectors.
    
    Uses NetworkX for efficient graph operations.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, AttackNode] = {}
        self.edges: List[AttackEdge] = []
    
    def add_node(self, node: AttackNode) -> None:
        """Add a node to the attack graph."""
        self.nodes[node.id] = node
        self.graph.add_node(
            node.id,
            **node.to_dict()
        )
    
    def add_edge(self, edge: AttackEdge) -> None:
        """Add an edge (attack vector) to the graph."""
        self.edges.append(edge)
        self.graph.add_edge(
            edge.source,
            edge.target,
            **edge.to_dict()
        )
    
    def get_node(self, node_id: str) -> Optional[AttackNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_entry_points(self) -> List[AttackNode]:
        """Get all entry points (nodes with no incoming edges)."""
        entry_point_ids = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        return [self.nodes[nid] for nid in entry_point_ids]
    
    def get_crown_jewels(self) -> List[AttackNode]:
        """Get all crown jewel nodes (critical assets)."""
        return [
            node for node in self.nodes.values()
            if node.node_type == NodeType.CROWN_JEWEL or node.criticality == "critical"
        ]
    
    def get_neighbors(self, node_id: str) -> List[AttackNode]:
        """Get all neighbors of a node."""
        neighbor_ids = list(self.graph.neighbors(node_id))
        return [self.nodes[nid] for nid in neighbor_ids]
    
    def to_cytoscape_format(self) -> Dict:
        """
        Convert to Cytoscape.js format for visualization.
        
        Returns:
            Dict with 'nodes' and 'edges' arrays
        """
        nodes = []
        for node_id, node in self.nodes.items():
            nodes.append({
                "data": {
                    "id": node.id,
                    "label": node.name,
                    **node.to_dict()
                },
                "position": {"x": node.x or 0, "y": node.y or 0} if node.x and node.y else None,
            })
        
        edges = []
        for edge in self.edges:
            edges.append({
                "data": {
                    "id": f"{edge.source}-{edge.target}",
                    "source": edge.source,
                    "target": edge.target,
                    **edge.to_dict()
                }
            })
        
        return {"nodes": nodes, "edges": edges}
    
    def to_dict(self) -> Dict:
        """Convert entire graph to dictionary."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "entry_points": len(self.get_entry_points()),
                "crown_jewels": len(self.get_crown_jewels()),
            }
        }
    
    @classmethod
    def from_scan_results(cls, scan_data: Dict) -> "AttackGraph":
        """
        Build attack graph from scan results.
        
        Args:
            scan_data: Dictionary with hosts, vulnerabilities, etc.
            
        Returns:
            AttackGraph instance
        """
        graph = cls()
        
        # Add nodes from scan results
        for host in scan_data.get("hosts", []):
            node = AttackNode(
                id=host["id"],
                name=host.get("name", host["ip"]),
                node_type=NodeType(host.get("type", "server")),
                ip=host.get("ip"),
                domain=host.get("domain"),
                open_ports=host.get("open_ports", []),
                services=host.get("services", []),
                criticality=host.get("criticality", "medium"),
            )
            graph.add_node(node)
        
        # Add edges based on network connectivity and vulnerabilities
        # This is simplified - real implementation would be more sophisticated
        for vuln in scan_data.get("vulnerabilities", []):
            if vuln.get("allows_access_to"):
                edge = AttackEdge(
                    source=vuln["host_id"],
                    target=vuln["allows_access_to"],
                    edge_type=EdgeType.VULNERABILITY_EXPLOIT,
                    technique=vuln.get("mitre_technique", "T1190"),
                    technique_name=vuln.get("technique_name", "Exploit Public-Facing Application"),
                    description=vuln.get("description", ""),
                    difficulty=vuln.get("difficulty", "medium"),
                )
                graph.add_edge(edge)
        
        return graph


class AttackPathFinder:
    """
    Find and analyze attack paths through the network.
    
    Uses graph algorithms to find optimal paths for attackers.
    """
    
    def __init__(self, graph: AttackGraph):
        self.graph = graph
    
    def find_shortest_path(
        self,
        source: str,
        target: str,
        weight: str = "difficulty"
    ) -> Optional[List[str]]:
        """
        Find the shortest attack path from source to target.
        
        Args:
            source: Starting node ID
            target: Target node ID
            weight: Edge attribute to use as weight
            
        Returns:
            List of node IDs representing the path, or None if no path exists
        """
        try:
            # Map difficulty to numeric weights
            if weight == "difficulty":
                weight_map = {"easy": 1, "medium": 2, "hard": 3}
                
                # Create weighted graph
                weighted_graph = nx.DiGraph()
                for node_id, data in self.graph.graph.nodes(data=True):
                    weighted_graph.add_node(node_id, **data)
                
                for u, v, data in self.graph.graph.edges(data=True):
                    diff = data.get("difficulty", "medium")
                    w = weight_map.get(diff, 2)
                    weighted_graph.add_edge(u, v, weight=w, **data)
                
                path = nx.shortest_path(
                    weighted_graph,
                    source,
                    target,
                    weight="weight"
                )
            else:
                path = nx.shortest_path(
                    self.graph.graph,
                    source,
                    target
                )
            
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def find_all_paths(
        self,
        source: str,
        target: str,
        cutoff: int = 10
    ) -> List[List[str]]:
        """
        Find all simple paths from source to target.
        
        Args:
            source: Starting node ID
            target: Target node ID
            cutoff: Maximum path length
            
        Returns:
            List of paths (each path is a list of node IDs)
        """
        try:
            paths = list(nx.all_simple_paths(
                self.graph.graph,
                source,
                target,
                cutoff=cutoff
            ))
            return paths
        except nx.NodeNotFound:
            return []
    
    def find_paths_to_crown_jewels(
        self,
        entry_point: Optional[str] = None
    ) -> List[Dict]:
        """
        Find all attack paths from entry points to crown jewels.
        
        Args:
            entry_point: Specific entry point (or None for all entry points)
            
        Returns:
            List of path dictionaries with metadata
        """
        results = []
        
        entry_points = [entry_point] if entry_point else [
            n.id for n in self.graph.get_entry_points()
        ]
        
        crown_jewels = [n.id for n in self.graph.get_crown_jewels()]
        
        for entry in entry_points:
            for jewel in crown_jewels:
                paths = self.find_all_paths(entry, jewel, cutoff=8)
                
                for path in paths:
                    # Calculate path metrics
                    difficulty_score = self._calculate_path_difficulty(path)
                    
                    results.append({
                        "entry_point": entry,
                        "crown_jewel": jewel,
                        "path": path,
                        "length": len(path),
                        "difficulty_score": difficulty_score,
                        "nodes": [self.graph.nodes[n].to_dict() for n in path],
                    })
        
        # Sort by difficulty (easiest first)
        results.sort(key=lambda x: x["difficulty_score"])
        
        return results
    
    def find_critical_paths(self, top_n: int = 5) -> List[Dict]:
        """
        Find the most critical attack paths (easiest to critical assets).
        
        Args:
            top_n: Number of top paths to return
            
        Returns:
            List of critical path dictionaries
        """
        all_paths = self.find_paths_to_crown_jewels()
        
        # Filter for high/critical criticality targets
        critical_paths = [
            p for p in all_paths
            if self.graph.nodes[p["crown_jewel"]].criticality in ["high", "critical"]
        ]
        
        return critical_paths[:top_n]
    
    def calculate_attack_surface(self) -> Dict:
        """
        Calculate network attack surface metrics.
        
        Returns:
            Dictionary with attack surface statistics
        """
        entry_points = self.graph.get_entry_points()
        crown_jewels = self.graph.get_crown_jewels()
        
        # Calculate reachable assets from each entry point
        reachability = {}
        for entry in entry_points:
            reachable = nx.descendants(self.graph.graph, entry.id)
            reachability[entry.id] = {
                "name": entry.name,
                "reachable_count": len(reachable),
                "includes_crown_jewel": any(
                    cj.id in reachable for cj in crown_jewels
                ),
            }
        
        # Count vulnerabilities by severity
        vuln_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for node in self.graph.nodes.values():
            for vuln in node.vulnerabilities:
                sev = vuln.get("severity", "medium")
                if sev in vuln_counts:
                    vuln_counts[sev] += 1
        
        return {
            "entry_points": len(entry_points),
            "crown_jewels": len(crown_jewels),
            "total_assets": len(self.graph.nodes),
            "total_attack_vectors": len(self.graph.edges),
            "reachability": reachability,
            "vulnerability_distribution": vuln_counts,
            "attack_surface_score": self._calculate_surface_score(
                entry_points, crown_jewels, vuln_counts
            ),
        }
    
    def _calculate_path_difficulty(self, path: List[str]) -> float:
        """Calculate overall difficulty score for a path."""
        total_difficulty = 0
        
        for i in range(len(path) - 1):
            edge_data = self.graph.graph.get_edge_data(path[i], path[i + 1])
            if edge_data:
                diff = edge_data.get("difficulty", "medium")
                total_difficulty += {"easy": 1, "medium": 2, "hard": 3}.get(diff, 2)
        
        return total_difficulty / len(path) if path else float('inf')
    
    def _calculate_surface_score(
        self,
        entry_points: List[AttackNode],
        crown_jewels: List[AttackNode],
        vuln_counts: Dict
    ) -> str:
        """Calculate overall attack surface rating."""
        score = 0
        
        # Points for entry points
        score += len(entry_points) * 2
        
        # Points for crown jewels (more = worse)
        score += len(crown_jewels) * 3
        
        # Points for vulnerabilities
        score += vuln_counts["critical"] * 10
        score += vuln_counts["high"] * 5
        score += vuln_counts["medium"] * 2
        score += vuln_counts["low"] * 1
        
        # Normalize to rating
        if score > 100:
            return "CRITICAL"
        elif score > 50:
            return "HIGH"
        elif score > 25:
            return "MEDIUM"
        else:
            return "LOW"


# Example usage / Mock data generator
def create_mock_attack_graph() -> AttackGraph:
    """Create a sample attack graph for testing."""
    graph = AttackGraph()
    
    # Entry points
    graph.add_node(AttackNode(
        id="web-server",
        name="Web Server",
        node_type=NodeType.ENTRY_POINT,
        ip="203.0.113.10",
        open_ports=[80, 443],
        services=["nginx", "php"],
        vulnerabilities=[
            {"id": "CVE-2021-44228", "name": "Log4j", "severity": "critical"}
        ]
    ))
    
    # Internal systems
    graph.add_node(AttackNode(
        id="app-server",
        name="Application Server",
        node_type=NodeType.SERVER,
        ip="10.0.1.20",
        open_ports=[8080, 22],
        services=["tomcat", "ssh"],
        criticality="high"
    ))
    
    graph.add_node(AttackNode(
        id="db-server",
        name="Database Server",
        node_type=NodeType.DATABASE,
        ip="10.0.1.30",
        open_ports=[5432],
        services=["postgresql"],
        criticality="critical",
        data_sensitivity="restricted"
    ))
    
    graph.add_node(AttackNode(
        id="dc",
        name="Domain Controller",
        node_type=NodeType.DOMAIN_CONTROLLER,
        ip="10.0.1.5",
        open_ports=[389, 636, 88],
        services=["ldap", "kerberos"],
        criticality="critical"
    ))
    
    graph.add_node(AttackNode(
        id="file-server",
        name="File Server",
        node_type=NodeType.CROWN_JEWEL,
        ip="10.0.1.40",
        open_ports=[445, 139],
        services=["smb"],
        criticality="critical",
        data_sensitivity="confidential"
    ))
    
    # Attack edges
    graph.add_edge(AttackEdge(
        source="web-server",
        target="app-server",
        edge_type=EdgeType.VULNERABILITY_EXPLOIT,
        technique="T1190",
        technique_name="Exploit Public-Facing Application",
        description="SQL Injection allows command execution",
        difficulty="easy",
        success_probability=0.9
    ))
    
    graph.add_edge(AttackEdge(
        source="app-server",
        target="db-server",
        edge_type=EdgeType.CREDENTIAL_REUSE,
        technique="T1552",
        technique_name="Unsecured Credentials",
        description="Database credentials stored in config file",
        difficulty="easy",
        success_probability=0.8
    ))
    
    graph.add_edge(AttackEdge(
        source="app-server",
        target="dc",
        edge_type=EdgeType.LATERAL_MOVEMENT,
        technique="T1021",
        technique_name="Remote Services",
        description="Pass-the-hash attack using cached credentials",
        difficulty="medium",
        success_probability=0.6
    ))
    
    graph.add_edge(AttackEdge(
        source="dc",
        target="file-server",
        edge_type=EdgeType.TRUST_RELATIONSHIP,
        technique="T1484",
        technique_name="Domain Policy Modification",
        description="Domain admin access to all domain resources",
        difficulty="easy",
        success_probability=0.95
    ))
    
    return graph
