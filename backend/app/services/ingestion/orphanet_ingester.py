import os
import structlog
import xml.etree.ElementTree as ET
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Disease
from app.services.embedding_service import generate_and_store_embedding

log = structlog.get_logger(__name__)

class OrphanetIngester:
    """
    Ingests local XML dumps from Orphanet (Rare Diseases).
    Extracts disease definitions, saves to DB, and generates vectors.
    """

    def __init__(self, data_dir: str = "data/datasets"):
        self.data_dir = data_dir

    async def ingest_xml(self, db: AsyncSession, filename: str = "en_product1.xml") -> int:
        """
        Parses a local Orphanet XML file (e.g. en_product1.xml) and ingests it.
        """
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            log.warning("orphanet_file_not_found", filepath=filepath)
            return 0

        ingested_count = 0
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Orphanet XML typically has <DisorderList><Disorder>
            for disorder in root.findall('.//Disorder'):
                orpha_code_node = disorder.find('OrphaCode')
                name_node = disorder.find('Name')
                
                if orpha_code_node is None or name_node is None:
                    continue

                orpha_code = orpha_code_node.text
                name = name_node.text
                
                if not name or not orpha_code:
                    continue

                code = f"ORPHA_{orpha_code}"
                
                # Check if exists
                existing = await db.scalar(select(Disease).where(Disease.code == code))
                if existing:
                    continue

                # Extract Definition from TextSectionList -> TextSection
                summary = ""
                for text_section in disorder.findall('.//TextSection'):
                    text_node = text_section.find('Contents')
                    if text_node is not None and text_node.text:
                        summary += text_node.text + "\n"

                if not summary.strip():
                    # Orphanet is still valuable for name/code even without a summary,
                    # but for RAG we really want text. We'll add a generic one if missing.
                    summary = f"{name} is a rare disease cataloged by Orphanet (ORPHA:{orpha_code})."

                # Save Disease
                disease = Disease(
                    code=code,
                    name=name,
                    description=summary[:500] + "..." if len(summary) > 500 else summary,
                    status="APPROVED",
                    is_ai_generated=False,
                    credibility_tier="primary" # Orphanet is authoritative for rare diseases
                )
                db.add(disease)
                await db.commit()
                await db.refresh(disease)

                # Embed the full text for RAG
                embedding_text = f"Rare Disease: {name}\nOrphaCode: {orpha_code}\nClinical Summary: {summary}\n"
                
                # Extract synonyms
                synonym_list = disorder.find('SynonymList')
                if synonym_list is not None:
                    synonyms = [s.text for s in synonym_list.findall('Synonym') if s.text]
                    if synonyms:
                        embedding_text += f"Synonyms: {', '.join(synonyms)}\n"

                try:
                    await generate_and_store_embedding(
                        db=db,
                        source_record_id=str(disease.id),
                        source_record_type="disease",
                        content=embedding_text
                    )
                    ingested_count += 1
                    log.info("ingested_orphanet_disease", name=name, code=code)
                except Exception as e:
                    log.error("embedding_failed_orphanet", error=str(e), code=code)

        except ET.ParseError as e:
            log.error("orphanet_xml_parse_error", error=str(e))
        except Exception as e:
            log.error("orphanet_ingestion_error", error=str(e))

        return ingested_count

orphanet_ingester = OrphanetIngester()
