# app/langgraph_setup.py
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

class GraphState(BaseModel):
    documents: List[Dict[str, Any]] = []
    query: str = ""
    response: str = ""

# Simple in-memory graph store for demonstration
class SimpleGraphStore:
    def __init__(self):
        self.nodes = {}
        self.edges = []
    
    def add_node(self, node_id: str, label: str, properties: Dict[str, Any]):
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "properties": properties
        }
    
    def count_nodes(self, label: str = None) -> int:
        if label:
            return sum(1 for node in self.nodes.values() if node.get("label") == label)
        return len(self.nodes)
    
    def neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        # Simple implementation - return related nodes based on edges
        related_ids = [edge["to"] for edge in self.edges if edge["from"] == node_id]
        related_ids.extend([edge["from"] for edge in self.edges if edge["to"] == node_id])
        return [self.nodes[nid] for nid in related_ids if nid in self.nodes]

# Initialize graph store
graph_store = SimpleGraphStore()

def ingest_document_as_nodes(doc):
    """Add a document as a node to the graph"""
    graph_store.add_node(
        node_id=str(doc.id),
        label="Document",
        properties={"title": doc.title, "content_length": len(doc.content)}
    )
