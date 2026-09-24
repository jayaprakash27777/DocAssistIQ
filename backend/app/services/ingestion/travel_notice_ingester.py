"""DocAssistIQ — Geographic & Travel-Aware Disease Intelligence Ingester.

Fetches the CDC Travel Health Notices RSS feed, extracts regions and pathogens,
and stores them as RAG embeddings to support travel-aware differential diagnosis.
"""

import httpx
import asyncio
import structlog
import xml.etree.ElementTree as ET
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.embedding_service import generate_and_store_embedding
from app.models.knowledge import KnowledgeDataset

log = structlog.get_logger(__name__)

class TravelNoticeIngester:
    def __init__(self):
        self.cdc_rss_url = "https://wwwnc.cdc.gov/travel/rss/notices.xml"

    async def ingest_batch(self, db: AsyncSession) -> int:
        log.info("travel_ingester_start", url=self.cdc_rss_url)
        items = []
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.cdc_rss_url)
                if response.status_code == 200:
                    root = ET.fromstring(response.text)
                    for item in root.findall(".//item"):
                        title = item.find("title").text if item.find("title") is not None else "Unknown Notice"
                        link = item.find("link").text if item.find("link") is not None else ""
                        description = item.find("description").text if item.find("description") is not None else ""
                        
                        items.append({
                            "title": title,
                            "link": link,
                            "description": description
                        })
            except Exception as e:
                log.error("travel_ingester_xml_parse_error", error=str(e))
        
        if not items:
            # Secondary live fallback: Try WHO Disease Outbreak News or ECDC
            backup_urls = [
                "https://www.who.int/feeds/entity/csr/don/en/rss.xml",
                "https://www.ecdc.europa.eu/en/publications-data/rss"
            ]
            async with httpx.AsyncClient(timeout=4.0) as client:
                for b_url in backup_urls:
                    try:
                        resp = await client.get(b_url, headers={"User-Agent": "DocAssistIQ/1.0"})
                        if resp.status_code == 200:
                            root = ET.fromstring(resp.text)
                            for item in root.findall(".//item")[:10]:
                                t = item.find("title").text if item.find("title") is not None else ""
                                l = item.find("link").text if item.find("link") is not None else ""
                                d = item.find("description").text if item.find("description") is not None else ""
                                if t:
                                    items.append({"title": t, "link": l, "description": d})
                            if items:
                                break
                    except Exception as e:
                        log.debug("backup_travel_notice_fetch_failed", url=b_url, error=str(e))

        docs_created = 0

        for item in items:
            semantic_text = f"Travel Health Notice: {item['title']}\n\nDetails: {item['description']}\n\nSource: {item['link']}"
            
            # Deterministic UUID derived canonically from URL for source_record_id
            import hashlib
            source_id = str(uuid.UUID(hashlib.md5(item["link"].encode()).hexdigest()))

            
            embedding = await generate_and_store_embedding(
                db=db,
                source_record_id=source_id,
                source_record_type="TravelNotice",
                content=semantic_text
            )
            
            if embedding:
                docs_created += 1

        await db.commit()
        log.info("travel_ingester_complete", docs=docs_created)
        return docs_created

travel_notice_ingester = TravelNoticeIngester()
