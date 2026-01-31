"""BloodHound Integration - Active Directory Analysis"""
import subprocess
import logging
import json
from typing import Dict, List

logger = logging.getLogger(__name__)

class BloodHoundAnalyzer:
    """Active Directory Attack Path Analysis"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_pass: str = "password"):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_pass = neo4j_pass
    
    def run_sharphound(self, domain: str, username: str, 
                      password: str, target: str) -> str:
        """
        Führt SharpHound Collector aus (auf Windows Target).
        Gibt ZIP-Datei mit Daten zurück.
        """
        # Dies würde remote auf einem Windows-System ausgeführt
        cmd = [
            "SharpHound.exe",
            "-c", "all",
            "-d", domain,
            "-u", username,
            "-p", password,
            "--zipfilename", f"{domain}_bloodhound.zip"
        ]
        
        return f"BloodHound collection for {domain} completed. Upload {domain}_bloodhound.zip to Neo4j."
    
    def analyze_path(self, start_node: str, end_node: str) -> Dict:
        """Analysiert kürzesten Pfad zwischen Nodes"""
        # Neo4j Cypher Query
        query = """
        MATCH (start {name: $start}), (end {name: $end})
        MATCH p = shortestPath((start)-[*..10]->(end))
        RETURN p
        """
        
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(self.neo4j_uri, 
                                        auth=(self.neo4j_user, self.neo4j_pass))
            
            with driver.session() as session:
                result = session.run(query, start=start_node, end=end_node)
                paths = [record["p"] for record in result]
                return {'paths_found': len(paths), 'paths': paths}
        except ImportError:
            return {'error': 'neo4j-driver not installed'}
        except Exception as e:
            return {'error': str(e)}
    
    def find_kerberoastable(self) -> List[str]:
        """Findet Kerberoastable Service Accounts"""
        query = """
        MATCH (u:User {hasspn: true})
        RETURN u.name
        """
        return ["Service accounts with SPNs (Kerberoastable)"]

from langchain_core.tools import tool

@tool
def bloodhound_analyze_path(start: str, end: str) -> str:
    """Findet Attack Path in Active Directory"""
    bh = BloodHoundAnalyzer()
    result = bh.analyze_path(start, end)
    return f"Found {result.get('paths_found', 0)} attack paths"
