"""
Attack Graph Visualization Utilities

Helper functions for visualizing attack graphs.
"""

from typing import Dict, List


class AttackGraphVisualizer:
    """
    Utilities for visualizing attack graphs.
    
    Converts graph data to various visualization formats.
    """
    
    @staticmethod
    def to_d3_format(graph_data: Dict) -> Dict:
        """Convert to D3.js force-directed graph format."""
        nodes = []
        links = []
        
        for node in graph_data.get("nodes", []):
            nodes.append({
                "id": node["id"],
                "name": node["name"],
                "type": node["type"],
                "group": node.get("criticality", "medium"),
            })
        
        for edge in graph_data.get("edges", []):
            links.append({
                "source": edge["source"],
                "target": edge["target"],
                "type": edge.get("type", "unknown"),
            })
        
        return {"nodes": nodes, "links": links}
    
    @staticmethod
    def to_visjs_format(graph_data: Dict) -> Dict:
        """Convert to Vis.js network format."""
        nodes = []
        edges = []
        
        for node in graph_data.get("nodes", []):
            nodes.append({
                "id": node["id"],
                "label": node["name"],
                "group": node["type"],
                "title": f"Type: {node['type']}<br>Criticality: {node.get('criticality', 'unknown')}",
            })
        
        for edge in graph_data.get("edges", []):
            edges.append({
                "from": edge["source"],
                "to": edge["target"],
                "label": edge.get("technique_name", ""),
                "title": edge.get("description", ""),
            })
        
        return {"nodes": nodes, "edges": edges}
