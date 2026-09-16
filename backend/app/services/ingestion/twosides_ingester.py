import uuid
import structlog
import httpx
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.provenance import Source
from app.models.knowledge import Medicine, MedicineInteraction

log = structlog.get_logger(__name__)

class TWOSIDESIngester:
    async def ingest_dataset_stub(self, db: AsyncSession):
        """
        Fetches real drug-drug interactions using the NLM RxNav Interaction API.
        This provides live, evidence-based interactions used by the US government.
        Replaces the static TWOSIDES stub with a real-time data pipeline.
        """
        try:
            # 1. Ensure the Source exists
            stmt = select(Source).where(Source.code == "rxnav_interactions")
            result = await db.execute(stmt)
            source = result.scalar_one_or_none()

            if not source:
                source = Source(
                    code="rxnav_interactions",
                    organisation="National Library of Medicine (NLM)",
                    name="RxNav Drug Interactions API",
                    base_url="https://rxnav.nlm.nih.gov",
                    access_mechanism="api",
                    data_type="drug_database",
                    is_production_suitable=True,
                    status="active"
                )
                db.add(source)
                await db.flush()

            # For real-time ingestion, we'll fetch interactions for a set of high-alert/common medications
            # RXCUIs: 11289 (Warfarin), 5640 (Ibuprofen), 6809 (Metformin), 8640 (Oxycodone), 2551 (Cephalexin)
            rxcuis = ["11289", "5640", "6809", "8640", "2551"]
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for rxcui in rxcuis:
                    url = f"https://rxnav.nlm.nih.gov/REST/interaction/interaction.json?rxcui={rxcui}"
                    response = await client.get(url)
                    if response.status_code != 200:
                        log.warning("rxnav_interaction_fetch_failed", rxcui=rxcui, status=response.status_code)
                        continue
                        
                    data = response.json()
                    interaction_groups = data.get("interactionTypeGroup", [])
                    if not interaction_groups:
                        continue
                        
                    for group in interaction_groups:
                        for ix_type in group.get("interactionType", []):
                            for pair in ix_type.get("interactionPair", []):
                                desc = pair.get("description", "")
                                severity = pair.get("severity", "moderate")
                                concepts = pair.get("interactionConcept", [])
                                
                                if len(concepts) != 2:
                                    continue
                                    
                                min_concept1 = concepts[0].get("minConceptItem", {})
                                min_concept2 = concepts[1].get("minConceptItem", {})
                                
                                rxcui1 = min_concept1.get("rxcui")
                                name1 = min_concept1.get("name", "").lower()
                                
                                rxcui2 = min_concept2.get("rxcui")
                                name2 = min_concept2.get("name", "").lower()
                                
                                if not rxcui1 or not rxcui2:
                                    continue
                                
                                # Ensure both medicines exist in our DB
                                med1 = await self._ensure_medicine(db, rxcui1, name1)
                                med2 = await self._ensure_medicine(db, rxcui2, name2)
                                
                                if not med1 or not med2:
                                    continue
                                
                                # Check if interaction already exists
                                existing_ix = await db.execute(
                                    select(MedicineInteraction).where(
                                        ((MedicineInteraction.medicine_id_1 == med1.id) & (MedicineInteraction.medicine_id_2 == med2.id)) |
                                        ((MedicineInteraction.medicine_id_1 == med2.id) & (MedicineInteraction.medicine_id_2 == med1.id))
                                    )
                                )
                                
                                if existing_ix.scalar_one_or_none():
                                    continue
                                    
                                # Create Interaction
                                interaction = MedicineInteraction(
                                    medicine_id_1=med1.id,
                                    medicine_id_2=med2.id,
                                    severity=severity,
                                    description=desc,
                                    source_id=source.id
                                )
                                db.add(interaction)
                                
                                # Flush to avoid duplicates in the same run
                                await db.flush()

            await db.commit()
            log.info("rxnav_interactions_ingestion_complete")

        except Exception as e:
            log.error("rxnav_interactions_ingestion_error", error=str(e))
            await db.rollback()

    async def _ensure_medicine(self, db: AsyncSession, rxcui: str, name: str) -> Medicine:
        stmt = select(Medicine).where(Medicine.rxnorm_cui == rxcui).limit(1)
        med = (await db.execute(stmt)).scalar_one_or_none()
        if not med:
            # If not found by rxcui, try by name
            stmt2 = select(Medicine).where(Medicine.name.ilike(name)).limit(1)
            med = (await db.execute(stmt2)).scalar_one_or_none()
            if not med:
                med = Medicine(
                    code=f"rxnorm_{rxcui}",
                    name=name,
                    rxnorm_cui=rxcui,
                    status="APPROVED"
                )
                db.add(med)
                await db.flush()
        return med

twosides_ingester = TWOSIDESIngester()
