import structlog
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Medicine
from app.services.ingestion.openfda_client import openfda_client
from app.services.embedding_service import generate_and_store_embedding

log = structlog.get_logger(__name__)

class MedicationIngester:
    """
    Pipeline to ingest live FDA medication data into the DocAssistIQ knowledge base
    and vectorize the clinical text for RAG.
    """

    async def ingest_batch(self, db: AsyncSession, limit: int = 10, skip: int = 0) -> int:
        """
        Fetches a batch of FDA drugs, saves to DB, and generates embeddings.
        Returns the number of successfully ingested records.
        """
        records = await openfda_client.fetch_human_prescription_drugs(limit=limit, skip=skip)
        
        ingested_count = 0
        for record in records:
            openfda_meta = record.get("openfda", {})
            if not openfda_meta:
                continue
                
            # Extract basic data
            brand_names = openfda_meta.get("brand_name", [])
            generic_names = openfda_meta.get("generic_name", [])
            product_ndc = openfda_meta.get("product_ndc", [])
            
            if not generic_names:
                continue
                
            generic_name = generic_names[0].lower()
            code = product_ndc[0] if product_ndc else generic_name.replace(" ", "_")
            
            # Check if it already exists
            existing = await db.scalar(select(Medicine).where(Medicine.code == code))
            if existing:
                log.debug("medicine_already_exists", code=code)
                continue
            
            # Extract clinical text for embeddings
            indications = record.get("indications_and_usage", [""])[0]
            contraindications = record.get("contraindications", [""])[0]
            warnings = record.get("warnings", [""])[0]
            
            if not indications and not contraindications:
                continue # Skip if there is no useful clinical text
                
            # Create the Knowledge Base record
            medicine = Medicine(
                code=code,
                name=generic_name,
                brand_names=", ".join(brand_names) if brand_names else None,
                status="APPROVED", # Assuming FDA data is approved
                is_ai_generated=False,
                credibility_tier="primary"
            )
            db.add(medicine)
            await db.commit()
            await db.refresh(medicine)
            
            # Generate Embeddings for RAG!
            embedding_text = f"Drug Name: {generic_name}.\n"
            if brand_names:
                embedding_text += f"Brand Names: {', '.join(brand_names)}.\n"
            if indications:
                embedding_text += f"Indications and Usage: {indications}\n"
            if contraindications:
                embedding_text += f"Contraindications: {contraindications}\n"
            if warnings:
                embedding_text += f"Warnings: {warnings}\n"
                
            try:
                await generate_and_store_embedding(
                    db=db,
                    source_record_id=str(medicine.id),
                    source_record_type="medicine",
                    content=embedding_text
                )
                ingested_count += 1
                log.info("ingested_medicine", name=generic_name, code=code)
            except Exception as e:
                log.error("embedding_failed_during_ingestion", error=str(e), code=code)
                # If embedding fails, we should ideally rollback or retry, but for now we just log
                
        return ingested_count

medication_ingester = MedicationIngester()
