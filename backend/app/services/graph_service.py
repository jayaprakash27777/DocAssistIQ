import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.knowledge import (
    Disease, Symptom, Investigation, Medicine,
    DiseaseSymptom, DiseaseInvestigation, DiseaseMedicine, DiseaseEvidence,
    MedicineContraindication, MedicineInteraction
)
from app.models.provenance import Evidence
from app.schemas.graph import GraphNode, GraphEdge, DiseaseKnowledgeGraph

logger = logging.getLogger(__name__)

async def get_disease_knowledge_graph(db: AsyncSession, disease_id: uuid.UUID) -> DiseaseKnowledgeGraph:
    """
    Traverse the PostgreSQL knowledge graph starting from a specific disease.
    Fetches connected symptoms, investigations, medicines, and evidence.
    """
    # Verify disease exists
    disease_result = await db.execute(select(Disease).where(Disease.id == disease_id))
    disease = disease_result.scalar_one_or_none()
    
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Disease not found"
        )
        
    nodes = {}
    edges = []

    # Helper to add nodes safely
    def add_node(node: GraphNode):
        if node.id not in nodes:
            nodes[node.id] = node

    # 1. Add Root Disease
    add_node(GraphNode(
        id=disease.id, 
        code=disease.code, 
        name=disease.name, 
        category=disease.category,
        node_type="disease"
    ))

    # 2. Symptoms
    ds_result = await db.execute(
        select(Symptom, DiseaseSymptom)
        .join(DiseaseSymptom, Symptom.id == DiseaseSymptom.symptom_id)
        .where(DiseaseSymptom.disease_id == disease_id)
    )
    for symptom, ds in ds_result.all():
        add_node(GraphNode(id=symptom.id, code=symptom.code, name=symptom.name, node_type="symptom"))
        edges.append(GraphEdge(
            source_id=disease_id, 
            target_id=symptom.id, 
            relationship="has_symptom",
            metadata={"frequency": ds.frequency, "specificity": ds.specificity}
        ))

    # 3. Investigations
    di_result = await db.execute(
        select(Investigation, DiseaseInvestigation)
        .join(DiseaseInvestigation, Investigation.id == DiseaseInvestigation.investigation_id)
        .where(DiseaseInvestigation.disease_id == disease_id)
    )
    for inv, di in di_result.all():
        add_node(GraphNode(id=inv.id, code=inv.code, name=inv.name, node_type="investigation"))
        edges.append(GraphEdge(
            source_id=disease_id, 
            target_id=inv.id, 
            relationship="requires_investigation",
            metadata={"indication": di.indication, "priority": di.priority}
        ))

    # 4. Medicines
    dm_result = await db.execute(
        select(Medicine, DiseaseMedicine)
        .join(DiseaseMedicine, Medicine.id == DiseaseMedicine.medicine_id)
        .where(DiseaseMedicine.disease_id == disease_id)
    )
    medicine_ids = []
    for med, dm in dm_result.all():
        medicine_ids.append(med.id)
        add_node(GraphNode(id=med.id, code=med.code, name=med.name, category=med.drug_class, node_type="medicine"))
        edges.append(GraphEdge(
            source_id=disease_id, 
            target_id=med.id, 
            relationship="treated_by",
            metadata={"treatment_role": dm.treatment_role}
        ))
        
    # 5. Evidence
    de_result = await db.execute(
        select(Evidence, DiseaseEvidence)
        .join(DiseaseEvidence, Evidence.id == DiseaseEvidence.evidence_id)
        .where(DiseaseEvidence.disease_id == disease_id)
    )
    for ev, de in de_result.all():
        add_node(GraphNode(id=ev.id, code=str(ev.id), name="Evidence Entry", node_type="evidence"))
        edges.append(GraphEdge(
            source_id=disease_id, 
            target_id=ev.id, 
            relationship="supported_by",
            metadata={"relevance_score": de.relevance_score}
        ))

    # 6. Medicine Interactions & Contraindications (only for the medicines attached to this disease)
    if medicine_ids:
        # Contraindications (Medicine -> Other Diseases)
        mc_result = await db.execute(
            select(Disease, MedicineContraindication)
            .join(MedicineContraindication, Disease.id == MedicineContraindication.disease_id)
            .where(MedicineContraindication.medicine_id.in_(medicine_ids))
        )
        for other_dis, mc in mc_result.all():
            add_node(GraphNode(
                id=other_dis.id, 
                code=other_dis.code, 
                name=other_dis.name, 
                category=other_dis.category,
                node_type="disease"
            ))
            edges.append(GraphEdge(
                source_id=mc.medicine_id, 
                target_id=other_dis.id, 
                relationship="contraindicated_for",
                metadata={"severity": mc.severity}
            ))

        # Interactions (Medicine -> Medicine)
        mi_result = await db.execute(
            select(Medicine, MedicineInteraction)
            .join(MedicineInteraction, Medicine.id == MedicineInteraction.medicine_id_2)
            .where(MedicineInteraction.medicine_id_1.in_(medicine_ids))
        )
        for other_med, mi in mi_result.all():
            add_node(GraphNode(
                id=other_med.id, 
                code=other_med.code, 
                name=other_med.name, 
                category=other_med.drug_class,
                node_type="medicine"
            ))
            edges.append(GraphEdge(
                source_id=mi.medicine_id_1, 
                target_id=other_med.id, 
                relationship="interacts_with",
                metadata={"severity": mi.severity, "description": mi.description}
            ))

    return DiseaseKnowledgeGraph(
        disease_id=disease_id,
        nodes=list(nodes.values()),
        edges=edges
    )
