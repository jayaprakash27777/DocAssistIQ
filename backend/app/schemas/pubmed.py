from pydantic import BaseModel
from typing import List
import uuid

class PubMedArticle(BaseModel):
    title: str
    pub_date: str
    source: str
    url: str

class PubMedScannerResponse(BaseModel):
    disease: str
    controversy_found: bool
    articles: List[PubMedArticle] = []
    ai_summary: str | None = None
