import os
import structlog
import xml.etree.ElementTree as ET
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Disease
from app.services.embedding_service import generate_and_store_embedding

log = structlog.get_logger(__name__)

class MedlinePlusIngester:
    """
    Ingests local XML dumps from MedlinePlus (Health Topics).
    Extracts disease summaries, saves to DB, and generates vectors.
    """

    def __init__(self, data_dir: str = "data/datasets"):
        self.data_dir = data_dir

    async def ingest_xml(self, db: AsyncSession, filename: str = "mplus_topics.xml") -> int:
        """
        Parses a local MedlinePlus XML file and ingests it.
        """
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            log.warning("medlineplus_file_not_found", filepath=filepath)
            return 0

        ingested_count = 0
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Typically MedlinePlus XML has <health-topic> elements
            for topic in root.findall('.//health-topic'):
                title = topic.get('title')
                topic_id = topic.get('id')
                
                if not title or not topic_id:
                    continue

                code = f"MEDLINEPLUS_{topic_id}"
                
                # Check if exists
                existing = await db.scalar(select(Disease).where(Disease.code == code))
                if existing:
                    continue

                # Extract Full Summary
                summary = ""
                full_summary_node = topic.find('full-summary')
                if full_summary_node is not None:
                    # Extract raw text from the summary node (which may contain HTML/XML tags)
                    summary = "".join(full_summary_node.itertext()).strip()

                if not summary:
                    continue

                # Save Disease
                disease = Disease(
                    code=code,
                    name=title,
                    description=summary[:500] + "..." if len(summary) > 500 else summary,
                    status="APPROVED",
                    is_ai_generated=False,
                    credibility_tier="primary"
                )
                db.add(disease)
                await db.commit()
                await db.refresh(disease)

                # Embed the full text for RAG
                embedding_text = f"Condition: {title}\nSummary: {summary}\n"
                
                # We can also extract synonyms or group names
                also_called = topic.findall('.//also-called')
                if also_called:
                    synonyms = [node.text for node in also_called if node.text]
                    embedding_text += f"Also known as: {', '.join(synonyms)}\n"

                try:
                    await generate_and_store_embedding(
                        db=db,
                        source_record_id=str(disease.id),
                        source_record_type="disease",
                        content=embedding_text
                    )
                    ingested_count += 1
                    log.info("ingested_medlineplus_topic", title=title, code=code)
                except Exception as e:
                    log.error("embedding_failed_medlineplus", error=str(e), code=code)

        except ET.ParseError as e:
            log.error("medlineplus_xml_parse_error", error=str(e))
        except Exception as e:
            log.error("medlineplus_ingestion_error", error=str(e))

        return ingested_count

medlineplus_ingester = MedlinePlusIngester()
