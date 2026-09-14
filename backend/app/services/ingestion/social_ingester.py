import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social import DoctorPost
from app.services.embedding_service import generate_and_store_embedding
from app.services.concept_normalizer import ConceptNormalizer
# Temporarily mocked out graph functions for social ingester
async def get_or_create_disease(db, name):
    pass
async def get_or_create_medicine(db, name):
    pass
async def add_disease_medicine_relation(db, disease_id, medicine_id):
    pass

log = structlog.get_logger(__name__)
normalizer = ConceptNormalizer()

async def ingest_doctor_post(db: AsyncSession, post: DoctorPost) -> None:
    """
    Ingest a DoctorPost into the AI knowledge base.
    
    1. Generates semantic text representations and stores them in the vector database.
    2. Attempts to extract strict node relationships (Disease -> Medicine) into the Knowledge Graph.
    """
    try:
        # 1. Format Semantic Text for RAG / Vector Database
        # We synthesize a clean clinical report from the structured fields.
        semantic_text = (
            f"Clinical Case Report: {post.disease_name}\n"
            f"Specialties: {', '.join(post.specialty_tags) if post.specialty_tags else 'General'}\n"
            f"Clinical Findings: {post.clinical_findings}\n"
            f"Diagnosis Rationale: {post.diagnosis}\n"
            f"Treatment Plan: {post.treatment_plan}\n"
            f"Pharmacological Interventions: {', '.join(post.drugs_used) if post.drugs_used else 'None'}\n"
        )
        
        # We use the DoctorPost ID as the source record ID
        embedding = await generate_and_store_embedding(
            db=db,
            source_record_id=str(post.id),
            source_record_type="DoctorPost",
            content=semantic_text
        )
        
        if embedding:
            log.info("social_ingestion_embedding_success", post_id=str(post.id))
        else:
            log.warning("social_ingestion_embedding_skipped_or_failed", post_id=str(post.id))
            
        # 2. Extract Graph Relationships (Disease -> Medicine)
        # For phase 48, we unconditionally map exact matches.
        
        # Attempt to normalize disease
        disease_concept = normalizer.normalize(post.disease_name)
        if not disease_concept:
            log.info("social_ingestion_graph_skip_disease", post_id=str(post.id), raw=post.disease_name)
            return
            
        disease_node = await get_or_create_disease(db, disease_concept.standard_name)  # type: ignore
        
        # Attempt to normalize drugs
        mapped_drugs = []
        for raw_drug in post.drugs_used:
            drug_concept = normalizer.normalize(raw_drug)
            if drug_concept:
                drug_node = await get_or_create_medicine(db, drug_concept.standard_name)  # type: ignore
                await add_disease_medicine_relation(db, disease_node.id, drug_node.id)
                mapped_drugs.append(drug_concept.standard_name)  # type: ignore
                
        if mapped_drugs:
            log.info("social_ingestion_graph_success", post_id=str(post.id), disease=disease_node.name, drugs=mapped_drugs)

    except Exception as e:
        log.error("social_ingestion_failed", post_id=str(post.id), error=str(e))
