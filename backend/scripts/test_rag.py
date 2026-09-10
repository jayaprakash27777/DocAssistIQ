import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import get_settings
from app.schemas.rag import RAGQueryRequest
from app.services.rag_service import retrieve_evidence

# Set a fake GEMINI_API_KEY if not exists just to avoid ValueError if we don't have one right now
if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = "fake_key_for_testing"

async def test_rag():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    request = RAGQueryRequest(query="What is the active ingredient in Tylenol?")
    
    async with session_maker() as session:
        try:
            response = await retrieve_evidence(session, request)
            print(f"Query: {response.query}")
            print(f"Answer:\n{response.answer}")
            print(f"\nCitations: {len(response.citations)}")
            for cit in response.citations:
                print(f"- {cit.claim} [{cit.source_name}]")
        except Exception as e:
            print(f"Error during RAG test: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_rag())
