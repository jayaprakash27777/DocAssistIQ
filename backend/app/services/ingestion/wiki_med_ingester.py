import httpx
import structlog
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Disease
from app.services.embedding_service import generate_and_store_embedding

log = structlog.get_logger(__name__)

class WikiMedIngester:
    """
    Fetches high-quality medical articles from Wikipedia (WikiProject Medicine)
    via the MediaWiki API, parses the plaintext summaries, and generates vectors.
    """
    
    BASE_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self):
        self.headers = {
            "User-Agent": "DocAssistIQ/1.0 (Clinical AI Knowledge Ingestion Pipeline)"
        }

    async def fetch_category_members(self, category: str, limit: int = 50) -> List[str]:
        """Fetches article titles belonging to a specific Wikipedia category."""
        async with httpx.AsyncClient() as client:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": str(limit),
                "cmtype": "page",
                "format": "json"
            }
            try:
                response = await client.get(self.BASE_URL, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                members = data.get("query", {}).get("categorymembers", [])
                return [m["title"] for m in members]
            except Exception as e:
                log.error("wiki_category_fetch_failed", error=str(e), category=category)
                return []

    async def fetch_article_summary(self, title: str) -> Optional[str]:
        """Fetches the plaintext extract (summary) of a Wikipedia article."""
        async with httpx.AsyncClient() as client:
            params = {
                "action": "query",
                "prop": "extracts",
                "exintro": "true", # Only the introduction summary
                "explaintext": "true", # Plain text instead of HTML
                "titles": title,
                "format": "json"
            }
            try:
                response = await client.get(self.BASE_URL, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_data in pages.items():
                    return page_data.get("extract")
            except Exception as e:
                log.error("wiki_article_fetch_failed", error=str(e), title=title)
                
            return None
                
    async def ingest_articles(self, db: AsyncSession, titles: List[str]) -> int:
        """Ingests a list of Wikipedia article titles into the Knowledge Base."""
        ingested_count = 0
        for title in titles:
            code = f"WIKI_{title.replace(' ', '_').upper()}"
            
            # Check if exists
            existing = await db.scalar(select(Disease).where(Disease.code == code))
            if existing:
                continue
                
            summary = await self.fetch_article_summary(title)
            if not summary or len(summary) < 100:
                continue # Skip very short or missing articles
                
            # Create DB Record
            disease = Disease(
                code=code,
                name=title,
                description=summary[:500] + "..." if len(summary) > 500 else summary,
                status="APPROVED",
                is_ai_generated=False,
                credibility_tier="secondary" # Wikipedia is secondary to MedlinePlus/FDA
            )
            db.add(disease)
            await db.commit()
            await db.refresh(disease)
            
            # Embed for RAG
            embedding_text = f"Condition: {title}\nWikipedia Clinical Summary: {summary}\n"
            try:
                await generate_and_store_embedding(
                    db=db,
                    source_record_id=str(disease.id),
                    source_record_type="disease",
                    content=embedding_text
                )
                ingested_count += 1
                log.info("ingested_wiki_article", title=title)
            except Exception as e:
                log.error("embedding_failed_wiki", error=str(e), title=title)
                
        return ingested_count

wiki_med_ingester = WikiMedIngester()
