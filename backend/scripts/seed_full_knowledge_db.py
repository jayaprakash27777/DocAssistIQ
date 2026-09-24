"""DocAssistIQ — Seed Full Knowledge Database from Offline KB.

Synchronizes all 96+ disease profiles from offline_disease_kb.py into PostgreSQL:
- diseases table (code, name, category, status='APPROVED', etc.)
- symptoms table (code, name, description)
- disease_symptoms join table (disease_id, symptom_id, frequency, specificity)
"""

import sys
import os
import re
import uuid
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, text
from app.infrastructure.database import get_session_factory
from app.models.knowledge import Disease, Symptom, DiseaseSymptom
from app.services.offline_disease_kb import DISEASE_KB


def slugify(text_val: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text_val.strip().lower()).strip("-")
    return cleaned[:50]


async def seed_knowledge():
    print(f"[*] Starting knowledge seeding from {len(DISEASE_KB)} disease profiles...")
    factory = get_session_factory()

    async with factory() as session:
        # Collect all unique symptoms
        all_symptom_names = set()
        for disease_name, profile in DISEASE_KB.items():
            for s in profile.get("symptoms", []):
                all_symptom_names.add(s.strip().lower())
            for s in profile.get("cardinal_symptoms", []):
                all_symptom_names.add(s.strip().lower())

        print(f"[*] Discovered {len(all_symptom_names)} unique symptoms.")

        # Cache existing symptoms
        result = await session.execute(select(Symptom))
        existing_symptoms = {s.name.lower(): s for s in result.scalars().all()}
        existing_symptom_codes = {s.code for s in existing_symptoms.values()}

        new_symptoms = 0
        for sym_name in all_symptom_names:
            if sym_name not in existing_symptoms:
                code_cand = f"sym-{slugify(sym_name)}"
                # ensure unique code
                counter = 1
                base_code = code_cand
                while code_cand in existing_symptom_codes:
                    code_cand = f"{base_code}-{counter}"
                    counter += 1

                sym_obj = Symptom(
                    id=uuid.uuid4(),
                    code=code_cand,
                    name=sym_name.capitalize(),
                    description=f"Clinical finding or symptom: {sym_name}",
                    is_ai_generated=False,
                )
                session.add(sym_obj)
                existing_symptoms[sym_name] = sym_obj
                existing_symptom_codes.add(code_cand)
                new_symptoms += 1

        if new_symptoms > 0:
            await session.commit()
            print(f"[+] Added {new_symptoms} new symptoms.")

        # Cache existing diseases
        res_d = await session.execute(select(Disease))
        existing_diseases = {d.name.lower(): d for d in res_d.scalars().all()}
        existing_disease_codes = {d.code for d in existing_diseases.values()}

        new_diseases = 0
        updated_diseases = 0

        for disease_name, profile in DISEASE_KB.items():
            clusters = profile.get("clusters", [])
            category = clusters[0] if clusters else "infectious"
            description = (
                f"Clinical entity with incubation range {profile.get('incubation_min', '?')}-"
                f"{profile.get('incubation_max', '?')} days. "
                f"Endemic/risk regions: {', '.join(profile.get('geographic_zones', ['Global']))}."
            )

            d_obj = existing_diseases.get(disease_name.lower())
            if not d_obj:
                code_cand = f"dis-{slugify(disease_name)}"
                counter = 1
                base_code = code_cand
                while code_cand in existing_disease_codes:
                    code_cand = f"{base_code}-{counter}"
                    counter += 1

                d_obj = Disease(
                    id=uuid.uuid4(),
                    code=code_cand,
                    name=disease_name,
                    description=description,
                    category=category,
                    status="APPROVED",
                    is_ai_generated=False,
                )
                session.add(d_obj)
                existing_diseases[disease_name.lower()] = d_obj
                existing_disease_codes.add(code_cand)
                new_diseases += 1
            else:
                d_obj.status = "APPROVED"
                updated_diseases += 1

        await session.commit()
        print(f"[+] Added {new_diseases} diseases, updated {updated_diseases} diseases.")

        # Now link disease_symptoms
        # Cache existing disease_symptom pairs
        res_ds = await session.execute(select(DiseaseSymptom.disease_id, DiseaseSymptom.symptom_id))
        existing_links = set(res_ds.all())

        new_links = 0
        for disease_name, profile in DISEASE_KB.items():
            d_obj = existing_diseases.get(disease_name.lower())
            if not d_obj:
                continue

            cardinal = set(s.strip().lower() for s in profile.get("cardinal_symptoms", []))
            all_syms = set(s.strip().lower() for s in profile.get("symptoms", [])) | cardinal

            for sym_name in all_syms:
                s_obj = existing_symptoms.get(sym_name)
                if not s_obj:
                    continue

                if (d_obj.id, s_obj.id) not in existing_links:
                    freq = "very_common" if sym_name in cardinal else "common"
                    spec = 0.95 if sym_name in cardinal else 0.70
                    link = DiseaseSymptom(
                        disease_id=d_obj.id,
                        symptom_id=s_obj.id,
                        frequency=freq,
                        specificity=spec,
                    )
                    session.add(link)
                    existing_links.add((d_obj.id, s_obj.id))
                    new_links += 1

        if new_links > 0:
            await session.commit()
            print(f"[+] Linked {new_links} disease-symptom associations.")

        # Final verification
        final_d = (await session.execute(text("SELECT count(*) FROM diseases"))).scalar()
        final_s = (await session.execute(text("SELECT count(*) FROM symptoms"))).scalar()
        final_ds = (await session.execute(text("SELECT count(*) FROM disease_symptoms"))).scalar()
        print(f"\n[SUCCESS] Knowledge DB Seed Complete:")
        print(f"  - Diseases: {final_d}")
        print(f"  - Symptoms: {final_s}")
        print(f"  - Disease-Symptom Links: {final_ds}")


if __name__ == "__main__":
    asyncio.run(seed_knowledge())
