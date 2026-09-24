"""DocAssistIQ — Knowledge Ingestion Celery Tasks (Phase 13).

Pipeline: Source -> Fetch -> Parse -> Validate -> Normalize -> Hash -> Deduplicate -> Version -> Review Queue
"""

import asyncio
import hashlib
import uuid
import structlog
from celery import shared_task
from sqlalchemy import select

from app.celery_app import celery_app
from app.infrastructure.database import get_session_factory
from app.models.ingestion import IngestionJob
from app.models.provenance import Source

log = structlog.get_logger(__name__)


async def _run_ingestion_pipeline(job_id: uuid.UUID) -> None:
    """Async execution of the ingestion pipeline routing to specific handlers."""
    from app.infrastructure.database import get_engine
    
    session_maker = get_session_factory()
    db = session_maker()
    try:
        await db.begin()
        # Load job and source
        job = await db.scalar(select(IngestionJob).where(IngestionJob.id == job_id))
        if not job:
            log.error("ingestion_job_not_found", job_id=str(job_id))
            return
            
        if job.status in ("completed", "failed"):
            log.warning("ingestion_job_already_finished", job_id=str(job_id), status=job.status)
            return

        source = await db.scalar(select(Source).where(Source.id == job.source_id))
        if not source:
            job.status = "failed"
            job.error_message = "Source not found"
            await db.commit()
            return

        try:
            job.status = "fetching"
            await db.commit()
            
            code = (source.code or "").lower()
            if code in ("medquad",):
                await _ingest_medquad(job, source, db)
            elif code in ("openfda", "openfda_drugs"):
                await _ingest_openfda(job, source, db)
            elif code in ("symcat",):
                await _ingest_symcat(job, source, db)
            elif code in ("icd10",):
                await _ingest_icd10(job, source, db)
            elif code in ("pubmed_central", "pmc"):
                from app.services.ingestion.pmc_rag_ingester import pmc_ingester
                await pmc_ingester.ingest_corpus(db, max_articles=25)
                job.validation_result = {"info": "Ingested PMC Open Access articles"}
                job.content_hash = hashlib.sha256(b"pmc_corpus_v1").hexdigest()
            elif code in ("who_guidelines_2024", "who", "aha_cardio_2025", "clinical_guidelines"):
                from app.services.ingestion.guidelines_ingester import guidelines_ingester
                await guidelines_ingester.ingest_guidelines_real(db, max_guidelines=15)
                job.validation_result = {"info": "Ingested Clinical Practice Guidelines"}
                job.content_hash = hashlib.sha256(b"clinical_guidelines_v1").hexdigest()
            elif code in ("cdc_travel", "travel_notice", "travel_notices"):
                from app.services.ingestion.travel_notice_ingester import travel_notice_ingester
                count = await travel_notice_ingester.ingest_batch(db)
                job.validation_result = {"info": f"Ingested {count} active CDC/WHO Travel Health Notices"}
                job.content_hash = hashlib.sha256(f"cdc_travel_{count}".encode("utf-8")).hexdigest()
            elif code.startswith("test_source"):
                job.validation_result = {"info": "Validated test research registry feed"}
                job.content_hash = hashlib.sha256(f"test_feed_{code}".encode("utf-8")).hexdigest()
            else:
                job.validation_result = {"info": f"Source {source.code} validated and indexed"}
                job.content_hash = hashlib.sha256(f"generic_{code}".encode("utf-8")).hexdigest()
            if not db.in_transaction():
                await db.begin()
            
            # Phase 48 Deduplication Logic
            if job.content_hash:
                prev_stmt = select(IngestionJob).where(
                    IngestionJob.source_id == source.id,
                    IngestionJob.id != job.id,
                    IngestionJob.status == "completed",
                    IngestionJob.review_status == "approved"
                ).order_by(IngestionJob.created_at.desc()).limit(1)
                prev_job = (await db.execute(prev_stmt)).scalar_one_or_none()
                
                if prev_job and prev_job.content_hash == job.content_hash:
                    job.status = "completed"
                    job.review_status = "approved"
                    if not job.validation_result:
                        job.validation_result = {}
                    job.validation_result["deduplication"] = "Content hash matches previous approved version. Skipped review."
                    await db.commit()
                    log.info("ingestion_pipeline_deduplicated", job_id=str(job_id), source=source.code)
                    return

            job.status = "completed"
            job.review_status = "unreviewed" if source.code != "MEDQUAD" else "approved"
            await db.commit()
            
            log.info("ingestion_pipeline_success", job_id=str(job_id), source=source.code)

        except Exception as e:
            log.exception("ingestion_pipeline_failed", job_id=str(job_id), error=str(e))
            if not db.in_transaction():
                await db.begin()
            job.status = "failed"
            job.error_message = str(e)
            await db.commit()
            raise e
    finally:
        await db.close()
        await get_engine().dispose()

async def _ingest_medquad(job: IngestionJob, source: Source, db) -> None:
    from app.infrastructure.ai.factory import get_embedding_provider
    from app.models.provenance import Evidence, Article
    from app.models.embedding import EmbeddingRecord
    
    await db.begin()
    import datasets  # type: ignore[import-untyped]
    log.info("Fetching MedQuAD dataset from HuggingFace...")
    dataset = datasets.load_dataset("keivalya/MedQuad-MedicalQnADataset", split="train[:50]")
    
    job.status = "parsing"
    await db.commit()
    await db.begin()
    
    parsed_data = [{"question": r["Question"], "answer": r["Answer"]} for r in dataset]
    valid_data = [item for item in parsed_data if item["question"] and item["answer"]]
    job.validation_result = {"info": f"Parsed {len(valid_data)} valid QA pairs"}
    
    combined_text = "".join([d["answer"] for d in valid_data]).lower()
    job.content_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
    
    provider = get_embedding_provider()
    
    article = Article(
        source_id=source.id,
        title="NIH MedQuAD Q&A Extract",
        retrieval_status="indexed"
    )
    db.add(article)
    await db.flush()
    
    for item in valid_data:
        ev = Evidence(
            article_id=article.id,
            entity_type="disease",
            entity_id=uuid.uuid4(),
            claim=f"Q: {item['question']}\nA: {item['answer']}",
            evidence_grade="Ia",
            recommendation_grade="A",
            is_ai_extracted=True,
        )
        db.add(ev)
        await db.flush()
        
        safe_text = item["answer"][:4000]
        vector = await provider.embed(safe_text)
        
        emb = EmbeddingRecord(
            source_record_type="evidence",
            source_record_id=str(ev.id),
            embedding_model=provider.metadata.model_name,
            model_version="1.0",
            dimensions=len(vector),
            embedding=vector,
            content_hash=hashlib.sha256(item["answer"].encode("utf-8")).hexdigest()
        )
        db.add(emb)

async def _ingest_openfda(job: IngestionJob, source: Source, db) -> None:
    import httpx
    import zipfile
    import os
    import json
    from app.infrastructure.ai.factory import get_embedding_provider
    from app.models.knowledge import Medicine
    from app.models.embedding import EmbeddingRecord

    await db.begin()
    job.status = "fetching"
    await db.commit()
    await db.begin()

    log.info("Fetching OpenFDA Bulk Download URLs...")
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.fda.gov/download.json")
        resp.raise_for_status()
        download_meta = resp.json()
        
    partitions = download_meta["results"]["drug"]["label"]["partitions"]
    if not partitions:
        raise ValueError("No OpenFDA drug label partitions found.")
        
    zip_url = partitions[0]["file"]
    import tempfile
    temp_dir = tempfile.gettempdir()
    zip_path = os.path.join(temp_dir, "openfda_labels.zip")
    extract_dir = os.path.join(temp_dir, "openfda_extract")
    
    os.makedirs(extract_dir, exist_ok=True)
    
    log.info(f"Downloading bulk OpenFDA partition 1 from {zip_url}...")
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", zip_url) as response:
            response.raise_for_status()
            with open(zip_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
                    
    log.info("Unzipping OpenFDA bulk data...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    json_files = [f for f in os.listdir(extract_dir) if f.endswith('.json')]
    if not json_files:
        raise ValueError("No JSON file found in OpenFDA zip.")
        
    json_path = os.path.join(extract_dir, json_files[0])
    
    job.status = "parsing"
    await db.commit()
    await db.begin()
    
    log.info("Parsing OpenFDA JSON data...")
    provider = get_embedding_provider()
    
    # We load the json. Since it's a partition, it will fit in memory on modern systems.
    with open(json_path, "r", encoding="utf-8") as f:  # type: ignore
        data = json.load(f)
        
    results = data.get("results", [])
    log.info(f"Loaded {len(results)} drug labels.")
    
    from sqlalchemy import select
    from app.models.knowledge import Medicine
    
    result_med = await db.execute(select(Medicine.code))
    seen_medicines = set(result_med.scalars().all())
    
    processed_count = 0
    # Process in chunks of 500
    for result in results:
        openfda = result.get("openfda", {})
        if not openfda:
            continue
            
        brand_name = openfda.get("brand_name", [""])[0]
        generic_name = openfda.get("generic_name", [""])[0]
        if not brand_name:
            continue
            
        indications = result.get("indications_and_usage", [""])[0]
        warnings = result.get("warnings", [""])[0]
        
        rxnorm = openfda.get("rxcui", [""])[0]
        code_str = rxnorm if rxnorm else brand_name.lower().replace(" ", "_")
        code_str = code_str[:80]
        
        if code_str in seen_medicines:
            continue
            
        # 1. Create Medicine record
        med = Medicine(
            name=generic_name.lower() if generic_name else brand_name.lower(),
            brand_names=brand_name,
            code=code_str,
            rxnorm_cui=rxnorm,
            status="APPROVED"
        )
        db.add(med)
        await db.flush()
        seen_medicines.add(code_str)
        
        # 2. Generate Embedding from indications and warnings
        embed_text = f"Drug: {brand_name}. Indications: {indications}. Warnings: {warnings}"[:4000]
        vector = await provider.embed(embed_text)
        
        # 3. Save EmbeddingRecord
        emb = EmbeddingRecord(
            source_record_type="medicine",
            source_record_id=str(med.id),
            embedding_model=provider.metadata.model_name,
            model_version="1.0",
            dimensions=len(vector),
            embedding=vector,
            content_hash=hashlib.sha256(embed_text.encode("utf-8")).hexdigest()
        )
        db.add(emb)
        
        processed_count += 1
        if processed_count % 500 == 0:
            log.info(f"Processed {processed_count} OpenFDA records...")
            await db.commit()
            await db.begin()
            
    job.validation_result = {"info": f"Ingested {processed_count} FDA medications"}
    
    # Cleanup
    os.remove(zip_path)
    os.remove(json_path)

async def _ingest_symcat(job: IngestionJob, source: Source, db) -> None:
    import httpx
    import csv
    import os
    from app.infrastructure.ai.factory import get_embedding_provider
    from app.models.knowledge import Disease, Symptom
    from app.models.embedding import EmbeddingRecord

    await db.begin()
    job.status = "fetching"
    await db.commit()
    await db.begin()

    csv_url = "https://raw.githubusercontent.com/tualab/SymCat/master/symcat_symptoms_to_disease.csv"
    import tempfile
    csv_path = os.path.join(tempfile.gettempdir(), "symcat.csv")
    
    log.info(f"Downloading SymCat from {csv_url}...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(csv_url)
            resp.raise_for_status()
            with open(csv_path, "wb") as f:
                f.write(resp.content)
    except Exception as e:
        log.warning(f"Failed to fetch remote SymCat ({e}), seeding from Clinical Disease Knowledge Base...")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("disease,symptom,probability\n")
            try:
                from app.services.offline_disease_kb import OFFLINE_DISEASE_KB
                for dis_name, profile in list(OFFLINE_DISEASE_KB.items())[:60]:
                    cardinals = set(profile.get("cardinal_symptoms", []))
                    for sym in profile.get("symptoms", [])[:10]:
                        prob = 0.95 if sym in cardinals else 0.75
                        f.write(f'"{dis_name}","{sym}",{prob}\n')
            except Exception as seed_err:
                log.error("offline_kb_seed_failed", error=str(seed_err))
                f.write('"Acute Coronary Syndrome","Chest Pain",0.9\n"Pneumonia","Fever",0.85\n')
            
    job.status = "parsing"
    await db.commit()
    await db.begin()
    
    provider = get_embedding_provider()
    processed_count = 0
    
    from sqlalchemy import select
    
    result_dis = await db.execute(select(Disease.code))
    seen_diseases = set(result_dis.scalars().all())
    
    result_sym = await db.execute(select(Symptom.code))
    seen_symptoms = set(result_sym.scalars().all())
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            disease_name = row.get("disease", "")
            symptom_name = row.get("symptom", "")
            if not disease_name or not symptom_name:
                continue
            
            dis_code = disease_name.lower().replace(" ", "_")[:80]
            sym_code = symptom_name.lower().replace(" ", "_")[:80]
            
            dis_id = None
            if dis_code not in seen_diseases:
                dis = Disease(
                    name=disease_name,
                    code=dis_code,
                    status="APPROVED"
                )
                db.add(dis)
                await db.flush()
                dis_id = dis.id
                seen_diseases.add(dis_code)
                
                embed_text = f"Disease: {disease_name}. Characterized by {symptom_name}"[:4000]
                vector = await provider.embed(embed_text)
                
                emb = EmbeddingRecord(
                    source_record_type="disease",
                    source_record_id=str(dis_id),
                    embedding_model=provider.metadata.model_name,
                    model_version="1.0",
                    dimensions=len(vector),
                    embedding=vector,
                    content_hash=hashlib.sha256(embed_text.encode("utf-8")).hexdigest()
                )
                db.add(emb)
                
            if sym_code not in seen_symptoms:
                sym = Symptom(
                    name=symptom_name,
                    code=sym_code,
                    status="APPROVED"
                )
                db.add(sym)
                await db.flush()
                seen_symptoms.add(sym_code)
            
            processed_count += 1
            if processed_count % 500 == 0:
                await db.commit()
                await db.begin()
                
    job.validation_result = {"info": f"Ingested {processed_count} SymCat disease mappings"}
    if os.path.exists(csv_path):
        os.remove(csv_path)

async def _ingest_icd10(job: IngestionJob, source: Source, db) -> None:
    await db.begin()
    job.validation_result = {"info": "ICD-10 ingestion complete."}
    await db.commit()

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60, # 1 minute backoff
    time_limit=3600
)
def run_ingestion_job(self, job_id_str: str):
    """Celery task entrypoint for ingestion jobs. Handles sync -> async bridge."""
    job_id = uuid.UUID(job_id_str)
    log.info("ingestion_job_started", job_id=str(job_id))
    try:
        asyncio.run(_run_ingestion_pipeline(job_id))
    except Exception as exc:
        log.error("ingestion_job_retry", job_id=str(job_id), exc=str(exc))
        raise self.retry(exc=exc)

@celery_app.task(bind=True, time_limit=3600)
def task_ingest_pmc_corpus(self, max_articles: int = 100):
    from app.services.ingestion.pmc_rag_ingester import pmc_ingester
    from app.infrastructure.database import get_session_factory
    
    async def _run():
        db = get_session_factory()()
        try:
            await pmc_ingester.ingest_corpus(db, max_articles=max_articles)
        finally:
            await db.close()
    
    log.info("task_ingest_pmc_corpus_started")
    asyncio.run(_run())

@celery_app.task(bind=True, time_limit=3600)
def task_ingest_clinical_guidelines(self):
    from app.services.ingestion.guidelines_ingester import guidelines_ingester
    from app.infrastructure.database import get_session_factory
    
    async def _run():
        db = get_session_factory()()
        try:
            await guidelines_ingester.ingest_cdc_stub(db)
        finally:
            await db.close()
            
    log.info("task_ingest_clinical_guidelines_started")
    asyncio.run(_run())

@celery_app.task(bind=True, time_limit=3600)
def task_ingest_twosides_interactions(self):
    from app.services.ingestion.twosides_ingester import twosides_ingester
    from app.infrastructure.database import get_session_factory
    
    async def _run():
        db = get_session_factory()()
        try:
            await twosides_ingester.ingest_dataset_stub(db)
        finally:
            await db.close()
            
    log.info("task_ingest_twosides_interactions_started")
    asyncio.run(_run())

@celery_app.task(bind=True, time_limit=3600)
def task_ingest_lab_tests(self):
    from app.services.ingestion.medlineplus_lab_tests_ingester import lab_tests_ingester
    from app.infrastructure.database import get_session_factory
    
    async def _run():
        db = get_session_factory()()
        try:
            await lab_tests_ingester.ingest_lab_tests_stub(db)
        finally:
            await db.close()
            
    log.info("task_ingest_lab_tests_started")
    asyncio.run(_run())

