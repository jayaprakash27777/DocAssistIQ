import uuid
from typing import List, Optional
from pydantic import BaseModel

class GraphNode(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    category: Optional[str] = None
    node_type: str # 'disease', 'symptom', 'medicine', 'investigation', 'evidence'

class GraphEdge(BaseModel):
    source_id: uuid.UUID
    target_id: uuid.UUID
    relationship: str
    metadata: Optional[dict] = None

class DiseaseKnowledgeGraph(BaseModel):
    disease_id: uuid.UUID
    nodes: List[GraphNode]
    edges: List[GraphEdge]
