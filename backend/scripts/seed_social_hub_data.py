"""DocAssistIQ — Seed Social Hub with Realistic Clinical Cases & Verified Specialists.

Populates realistic, high-yield clinical cases across multiple specialties:
Cardiology, Neurology, Pediatrics, Infectious Disease, Dermatology, Critical Care.
Includes peer comments, likes, and structured diagnostic data.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.infrastructure.database import get_session_factory
from app.models.user import User
from app.models.doctor import Doctor
from app.models.social import DoctorPost, PostComment, PostLike, PostBookmark, PostAttachment
from app.services.auth_service import hash_password

DOCTORS = [
    {
        "email": "dr.chen@docassistiq.com",
        "full_name": "Dr. Sarah Chen, MD, FACC",
        "specialty": "Cardiology",
        "credential_reference": "GMC-7849102",
        "credential_body": "GMC / Board Certified",
        "bio": "Attending Interventional Cardiologist. Focus on acute coronary syndromes & structural heart interventions."
    },
    {
        "email": "dr.vance@docassistiq.com",
        "full_name": "Dr. David Vance, MD, FAAN",
        "specialty": "Neurology",
        "credential_reference": "USMLE-992140",
        "credential_body": "ABPN Board Certified",
        "bio": "Neurointensivist & Autoimmune Neurology Fellow. Specialized in encephalitis & neuro-immunology."
    },
    {
        "email": "dr.rostova@docassistiq.com",
        "full_name": "Dr. Elena Rostova, MD, PhD",
        "specialty": "Pediatrics",
        "credential_reference": "GMC-8831209",
        "credential_body": "GMC / RCPCH",
        "bio": "Consultant Pediatric Infectious Diseases. Outbreak surveillance & pediatric rheumatology."
    },
    {
        "email": "dr.thorne@docassistiq.com",
        "full_name": "Dr. Marcus Thorne, MD, FACEP",
        "specialty": "Emergency Medicine",
        "credential_reference": "ABEM-773194",
        "credential_body": "ABEM Board Certified",
        "bio": "Emergency Medicine & Resuscitation Specialist. Resuscitation science & toxicologic emergencies."
    },
    {
        "email": "dr.nair@docassistiq.com",
        "full_name": "Dr. Priya Nair, MD, DNB",
        "specialty": "Dermatology",
        "credential_reference": "NMC-6621980",
        "credential_body": "NMC / IADVL",
        "bio": "Associate Professor of Dermatology & Cutaneous Oncology. Severe drug eruptions & dermoscopy."
    }
]

CASES = [
    {
        "doc_email": "dr.chen@docassistiq.com",
        "disease_name": "Wellens' Syndrome (Type A Biphasic T-Waves in LAD Stenosis)",
        "specialty_tags": ["Cardiology", "Emergency Medicine", "Critical Care", "ECG"],
        "clinical_findings": "54M presented with episodic severe retrosternal chest tightness lasting 30 minutes, now completely pain-free upon arrival. Vitals: BP 136/82, HR 74, SpO2 98% room air. Initial Troponin I is 0.04 ng/mL (borderline). 12-lead ECG during the pain-free window reveals pathognomonic biphasic T-waves in leads V2 and V3 without ST-segment elevation and no loss of precordial R-waves.",
        "diagnosis": "Wellens' Syndrome Type A — Critical proximal Left Anterior Descending (LAD) coronary artery stenosis with high imminent risk of extensive anterior wall myocardial infarction.",
        "treatment_plan": "Patient admitted straight to CCU. Absolute contraindication to treadmill exercise testing (provokes sudden fatal anterior STEMI). Initiated DAPT (Aspirin 325 mg + Ticagrelor 180 mg loading) and therapeutic IV Unfractionated Heparin infusion. Emergent cardiac catheterization performed within 2.5 hours revealed 95% critical stenosis in proximal LAD. Successful deployment of a drug-eluting stent (DES) with TIMI 3 flow restored.",
        "drugs_used": ["Aspirin 325mg", "Ticagrelor 180mg", "Unfractionated Heparin", "Atorvastatin 80mg", "Metoprolol Succinate 25mg"],
        "comments": [
            {"doc_email": "dr.thorne@docassistiq.com", "text": "Crucial catch on the pain-free ECG. We frequently see junior residents miss the biphasic T waves when the patient says 'the pain is totally gone now'."},
            {"doc_email": "dr.vance@docassistiq.com", "text": "Classic pseudo-normalization danger if stress tested. Superb outcome with rapid catheterization."}
        ]
    },
    {
        "doc_email": "dr.vance@docassistiq.com",
        "disease_name": "Anti-NMDA Receptor Encephalitis in a Young Female",
        "specialty_tags": ["Neurology", "Immunology", "Psychiatry", "Critical Care"],
        "clinical_findings": "22F university student presenting with acute progressive neuropsychiatric decompensation: auditory hallucinations, paranoia, hyperverbal speech progressing over 10 days to severe catatonia, autonomic instability, and stereotypic orofacial dyskinesias. Lumbar puncture revealed CSF lymphocytic pleocytosis (42 cells/mcL), elevated IgG index, and positive Anti-GluN1 antibodies. Continuous EEG captured classic 'extreme delta brush' pattern.",
        "diagnosis": "Autoimmune Anti-NMDA Receptor Encephalitis secondary to an occult ovarian teratoma.",
        "treatment_plan": "Pelvic MRI confirmed 3.4 cm mature cystic ovarian teratoma. Laparoscopic cystectomy performed on hospital day 3. First-line dual immunotherapy initiated: IV Methylprednisolone 1,000 mg daily for 5 days alongside high-dose IVIG (2 g/kg total dose over 5 days). Second-line therapy with Rituximab (375 mg/m² weekly x 4) added due to refractory dyskinesias. Patient demonstrated substantial cognitive recovery by week 4.",
        "drugs_used": ["Methylprednisolone 1g IV", "Intravenous Immunoglobulin (IVIG)", "Rituximab", "Levetiracetam 1000mg BID"],
        "comments": [
            {"doc_email": "dr.rostova@docassistiq.com", "text": "Extreme delta brush is practically diagnostic when combined with orofacial dyskinesias. Excellent decision on prompt tumor resection."},
            {"doc_email": "dr.chen@docassistiq.com", "text": "How was the autonomic instability managed hemodynamically during the ICU stay? Did you require Clonidine or Dexmedetomidine?"}
        ]
    },
    {
        "doc_email": "dr.rostova@docassistiq.com",
        "disease_name": "Atypical Kawasaki Disease with Early Coronary Ectasia",
        "specialty_tags": ["Pediatrics", "Cardiology", "Rheumatology", "SpotDiagnosis"],
        "clinical_findings": "3.5-year-old boy presenting with persistent high-grade remittent fever (39.5°C) for 6 days refractory to oral cephalosporins. Examination shows non-purulent bilateral bulbar conjunctival injection, dry cracked lips with classic strawberry tongue, cervical lymphadenopathy (1.8 cm right anterior chain), and indurated palmar erythema with periungual desquamation. Transthoracic echo revealed early dilation of the proximal Right Coronary Artery (RCA Z-score +3.6).",
        "diagnosis": "Incomplete / Atypical Kawasaki Disease complicated by acute coronary arteritis.",
        "treatment_plan": "Administered single high-dose IVIG (2 g/kg infused over 12 hours) within the 10-day therapeutic window. Started high-dose oral Aspirin (80 mg/kg/day divided into 4 doses) until patient remained afebrile for 48 hours, followed by low-dose antiplatelet Aspirin (5 mg/kg/day once daily for 8 weeks). Repeat echocardiography at 2 weeks demonstrated regression of coronary lumen Z-score to +1.8.",
        "drugs_used": ["Intravenous Immunoglobulin 2g/kg", "Aspirin 80mg/kg/day", "Aspirin 5mg/kg/day"],
        "comments": [
            {"doc_email": "dr.chen@docassistiq.com", "text": "Early IVIG within the 10-day window is life-saving to prevent aneurysm thrombosis. Great echo surveillance protocol."},
            {"doc_email": "dr.nair@docassistiq.com", "text": "The palm induration and periungual peeling are such high-yield clinical dermatologic signs in fever of unknown origin in toddlers."}
        ]
    },
    {
        "doc_email": "dr.thorne@docassistiq.com",
        "disease_name": "Severe Refractory Dengue with Secondary HLH (Hemophagocytic Syndrome)",
        "specialty_tags": ["Infectious Disease", "Critical Care", "Hematology", "Surveillance"],
        "clinical_findings": "28M returned from travel 9 days prior with fever, severe retro-orbital headache, and myalgias. Transferred to ICU on Day 8 in hyperinflammatory shock. Labs: Hemoglobin 7.4 g/dL, Platelets 14,000/mcL, Absolute Neutrophil Count 380/mcL. Serum Ferritin > 42,000 ng/mL, Triglycerides 510 mg/dL, Fibrinogen 88 mg/dL. Bone marrow aspirate confirmed active hemophagocytosis of erythroblasts by activated macrophages.",
        "diagnosis": "Severe Secondary Hemophagocytic Lymphohistiocytosis (HLH / MAS) triggered by acute Dengue Virus (DENV-2 serotype).",
        "treatment_plan": "Patient managed in Medical ICU with protective ventilation and invasive arterial monitoring. Dexamethasone 10 mg/m² daily instituted immediately per HLH-2004 modified guidelines. Concomitant IVIG 1 g/kg/day for 2 days. Platelets transfused to maintain > 20k with cryoprecipitate for fibrinogen > 150 mg/dL. Requesting multidisciplinary input from Hematology on early Etoposide introduction vs Anakinra (IL-1 antagonist).",
        "drugs_used": ["Dexamethasone 10mg/m2", "IVIG 1g/kg", "Cryoprecipitate", "Platelet Apheresis", "N-Acetylcysteine"],
        "comments": [
            {"doc_email": "dr.rostova@docassistiq.com", "text": "With ferritin > 40k and cytopenias, prompt dexamethasone is imperative. In adult viral-triggered HLH, Anakinra (IL-1 blockade) has shown lower myelosuppression risk than etoposide."},
            {"doc_email": "dr.chen@docassistiq.com", "text": "Watch closely for myocardial depression and secondary dengue myocarditis in this hyperferritinemic storm."}
        ]
    },
    {
        "doc_email": "dr.nair@docassistiq.com",
        "disease_name": "Toxic Epidermal Necrolysis (TEN) Induced by Allopurinol (HLA-B*58:01)",
        "specialty_tags": ["Dermatology", "Allergy & Immunology", "Critical Care", "Pharmacology"],
        "clinical_findings": "63M with gout who initiated allopurinol 100 mg 3 weeks ago. Presented with painful coalescent dusky erythematous macules on face and trunk that rapidly evolved into extensive flaccid bullae with positive Nikolsky sign, peeling in sheet-like fashion over 40% Total Body Surface Area (TBSA). Severe stomatitis, conjunctival purulence, and genital erosions. SCORTEN score: 3 (predicted in-hospital mortality 35.3%).",
        "diagnosis": "Toxic Epidermal Necrolysis (TEN) — Severe Cutaneous Adverse Reaction (SCAR) secondary to allopurinol in HLA-B*58:01 carrier.",
        "treatment_plan": "Immediate cessation of allopurinol and all non-vital medications. Emergent transfer to specialized Burn ICU with 32°C ambient thermal control. Non-adherent silicone foam dressing applied without aggressive debridement. High-dose IVIG (1 g/kg/day x 3 days) combined with early oral Cyclosporine (3 mg/kg/day for 10 days). Daily ophthalmologic assessment with amniotic membrane transplantation consideration.",
        "drugs_used": ["IVIG 1g/kg/day", "Cyclosporine 3mg/kg/day", "Hartmann Solution Resuscitation", "Mupirocin Ointment"],
        "comments": [
            {"doc_email": "dr.thorne@docassistiq.com", "text": "Crucial reminder for primary care clinicians to screen HLA-B*58:01 prior to allopurinol initiation in high-risk ancestral populations."},
            {"doc_email": "dr.vance@docassistiq.com", "text": "Early cyclosporine has significantly improved SCORTEN-adjusted survival in multicenter registries."}
        ]
    }
]

async def seed_hub():
    session_factory = get_session_factory()
    async with session_factory() as db:
        print("1. Seeding Verified Doctor Accounts...")
        doc_map = {}

        for doc_info in DOCTORS:
            # 1. User
            user = await db.scalar(select(User).where(User.email == doc_info["email"]))
            if not user:
                user = User(
                    id=uuid.uuid4(),
                    email=doc_info["email"],
                    password_hash=hash_password("DoctorSecure2026!"),
                    full_name=doc_info["full_name"],
                    role="doctor",
                    is_active=True,
                    is_verified=True
                )
                db.add(user)
                await db.flush()
            else:
                user.full_name = doc_info["full_name"]
                user.is_verified = True
                await db.flush()

            # 2. Doctor profile
            doctor = await db.scalar(select(Doctor).where(Doctor.user_id == user.id))
            if not doctor:
                doctor = Doctor(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    specialty=doc_info["specialty"],
                    credential_reference=doc_info["credential_reference"],
                    credential_body=doc_info["credential_body"],
                    bio=doc_info["bio"],
                    verification_status="verified"
                )
                db.add(doctor)
                await db.flush()
            else:
                doctor.specialty = doc_info["specialty"]
                doctor.credential_reference = doc_info["credential_reference"]
                doctor.credential_body = doc_info["credential_body"]
                doctor.verification_status = "verified"
                await db.flush()

            doc_map[doc_info["email"]] = doctor

        # Also ensure dr.smith is verified
        smith_user = await db.scalar(select(User).where(User.email == "dr.smith@hospital.org"))
        if smith_user:
            smith_user.is_verified = True
            smith_doc = await db.scalar(select(Doctor).where(Doctor.user_id == smith_user.id))
            if smith_doc:
                smith_doc.verification_status = "verified"
                smith_doc.specialty = "Cardiology"
                smith_doc.credential_reference = "NMC-98421"
                smith_doc.credential_body = "NMC Board Certified"
                doc_map["dr.smith@hospital.org"] = smith_doc
            await db.flush()

        await db.commit()
        print(f"Verified {len(doc_map)} doctors in database.")

        print("2. Seeding Clinical Cases...")
        # Check existing cases
        for idx, case_data in enumerate(CASES):
            author_doc = doc_map.get(case_data["doc_email"])
            if not author_doc:
                continue

            existing_post = await db.scalar(select(DoctorPost).where(DoctorPost.disease_name == case_data["disease_name"]))
            if existing_post:
                print(f"Case '{case_data['disease_name']}' already exists, skipping.")
                continue

            post = DoctorPost(
                id=uuid.uuid4(),
                author_id=author_doc.id,
                disease_name=case_data["disease_name"],
                clinical_findings=case_data["clinical_findings"],
                diagnosis=case_data["diagnosis"],
                treatment_plan=case_data["treatment_plan"],
                drugs_used=case_data["drugs_used"],
                specialty_tags=case_data["specialty_tags"],
                created_at=datetime.utcnow() - timedelta(hours=idx * 4 + 1)
            )
            db.add(post)
            await db.flush()

            # Add Likes from other doctors
            for d_email, other_doc in doc_map.items():
                if other_doc.id != author_doc.id:
                    like = PostLike(
                        id=uuid.uuid4(),
                        post_id=post.id,
                        doctor_id=other_doc.id
                    )
                    db.add(like)

            # Add Bookmark from dr.smith
            if "dr.smith@hospital.org" in doc_map and idx % 2 == 0:
                bookmark = PostBookmark(
                    id=uuid.uuid4(),
                    post_id=post.id,
                    doctor_id=doc_map["dr.smith@hospital.org"].id
                )
                db.add(bookmark)

            # Add Comments
            for c in case_data.get("comments", []):
                c_author = doc_map.get(c["doc_email"])
                if c_author:
                    comment = PostComment(
                        id=uuid.uuid4(),
                        post_id=post.id,
                        author_id=c_author.id,
                        content=c["text"],
                        created_at=datetime.utcnow() - timedelta(hours=idx * 2 + 1)
                    )
                    db.add(comment)

            print(f"Seeded case: {case_data['disease_name']}")

        await db.commit()
        print("Social Hub database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_hub())
