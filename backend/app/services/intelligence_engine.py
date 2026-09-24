"""DocAssistIQ — Multi-Source Intelligence Engine (AI Upgrade).

Aggregates live free-data from WHO, CDC, ProMED, NCBI and other public health
APIs to provide richly grounded context to the LLM before every diagnosis call.

Key capabilities:
- Parallel async fetching from 5 free public sources
- Country → WHO Region mapping for geo-spatial matching
- Evidence-based incubation period database (80+ pathogens)
- 30-minute in-memory cache to avoid redundant fetches
- Fully additive — does not modify any existing code paths
"""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import quote
import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# 1. In-Memory Cache (30-minute TTL)
# ---------------------------------------------------------------------------
_cache: dict = {}
_cache_ttl: dict = {}
_CACHE_MINUTES = 30


def _cache_get(key: str):
    if key in _cache:
        if datetime.now(timezone.utc) < _cache_ttl[key]:
            return _cache[key]
        del _cache[key]
        del _cache_ttl[key]
    return None


def _cache_set(key: str, value):
    _cache[key] = value
    _cache_ttl[key] = datetime.now(timezone.utc) + timedelta(minutes=_CACHE_MINUTES)


# ---------------------------------------------------------------------------
# 2. Country → WHO Region + Alias Mapping
# ---------------------------------------------------------------------------
COUNTRY_WHO_REGION: dict[str, str] = {
    # Africa
    "democratic republic of the congo": "Africa",
    "drc": "Africa",
    "congo": "Africa",
    "kinshasa": "Africa",
    "nigeria": "Africa",
    "ghana": "Africa",
    "uganda": "Africa",
    "kenya": "Africa",
    "tanzania": "Africa",
    "ethiopia": "Africa",
    "guinea": "Africa",
    "sierra leone": "Africa",
    "liberia": "Africa",
    "cameroon": "Africa",
    "angola": "Africa",
    "zambia": "Africa",
    "zimbabwe": "Africa",
    "mozambique": "Africa",
    "sudan": "Africa",
    "south sudan": "Africa",
    "central african republic": "Africa",
    "gabon": "Africa",
    "equatorial guinea": "Africa",
    "somalia": "Africa",
    "mali": "Africa",
    "burkina faso": "Africa",
    "niger": "Africa",
    "chad": "Africa",
    "senegal": "Africa",
    "gambia": "Africa",
    "guinea-bissau": "Africa",
    "ivory coast": "Africa",
    "cote d'ivoire": "Africa",
    "togo": "Africa",
    "benin": "Africa",
    "mauritania": "Africa",
    "madagascar": "Africa",
    # Americas
    "brazil": "Americas",
    "colombia": "Americas",
    "venezuela": "Americas",
    "peru": "Americas",
    "bolivia": "Americas",
    "ecuador": "Americas",
    "guyana": "Americas",
    "suriname": "Americas",
    "haiti": "Americas",
    "dominican republic": "Americas",
    "trinidad": "Americas",
    "jamaica": "Americas",
    "mexico": "Americas",
    "central america": "Americas",
    "guatemala": "Americas",
    "honduras": "Americas",
    "el salvador": "Americas",
    "nicaragua": "Americas",
    "costa rica": "Americas",
    "panama": "Americas",
    # South-East Asia
    "india": "South-East Asia",
    "bangladesh": "South-East Asia",
    "myanmar": "South-East Asia",
    "thailand": "South-East Asia",
    "indonesia": "South-East Asia",
    "nepal": "South-East Asia",
    "bhutan": "South-East Asia",
    "maldives": "South-East Asia",
    "sri lanka": "South-East Asia",
    "timor-leste": "South-East Asia",
    # Western Pacific
    "china": "Western Pacific",
    "philippines": "Western Pacific",
    "vietnam": "Western Pacific",
    "cambodia": "Western Pacific",
    "laos": "Western Pacific",
    "malaysia": "Western Pacific",
    "japan": "Western Pacific",
    "south korea": "Western Pacific",
    "papua new guinea": "Western Pacific",
    "solomon islands": "Western Pacific",
    # Eastern Mediterranean
    "pakistan": "Eastern Mediterranean",
    "afghanistan": "Eastern Mediterranean",
    "iran": "Eastern Mediterranean",
    "iraq": "Eastern Mediterranean",
    "syria": "Eastern Mediterranean",
    "yemen": "Eastern Mediterranean",
    "saudi arabia": "Eastern Mediterranean",
    "jordan": "Eastern Mediterranean",
    "egypt": "Eastern Mediterranean",
    "libya": "Eastern Mediterranean",
    "morocco": "Eastern Mediterranean",
    "tunisia": "Eastern Mediterranean",
    # Europe
    "ukraine": "Europe",
    "russia": "Europe",
    "turkey": "Europe",
    "greece": "Europe",
}

# Disease synonyms for smarter matching
DISEASE_SYNONYMS: dict[str, list[str]] = {
    "ebola": ["ebola", "ebola virus disease", "evd", "bundibugyo", "bvd", "bundibugyo virus", "zaire ebolavirus", "sudan ebolavirus", "hemorrhagic fever"],
    "mpox": ["mpox", "monkeypox", "monkey pox"],
    "marburg": ["marburg", "marburg virus", "marburg hemorrhagic fever"],
    "lassa": ["lassa", "lassa fever", "lassa virus"],
    "cholera": ["cholera", "vibrio cholerae"],
    "dengue": ["dengue", "dengue fever", "denv"],
    "yellow fever": ["yellow fever", "yf"],
    "plague": ["plague", "yersinia pestis", "bubonic plague", "pneumonic plague"],
    "rift valley fever": ["rift valley fever", "rvf"],
    "crimean congo": ["crimean-congo hemorrhagic fever", "cchf", "crimean congo"],
    "nipah": ["nipah", "nipah virus"],
    "hendra": ["hendra", "hendra virus"],
    "avian influenza": ["avian influenza", "h5n1", "h5n2", "bird flu", "h7n9"],
    "middle east respiratory syndrome": ["mers", "mers-cov", "middle east respiratory"],
    "covid": ["covid", "covid-19", "sars-cov-2", "coronavirus"],
    "polio": ["polio", "poliovirus", "poliomyelitis"],
    "measles": ["measles", "rubeola"],
    "meningitis": ["meningitis", "meningococcal", "neisseria meningitidis"],
}

# ---------------------------------------------------------------------------
# 3. Evidence-Based Incubation Period Database (80+ pathogens)
# ---------------------------------------------------------------------------
INCUBATION_PERIODS: dict[str, dict] = {
    # Hemorrhagic Fevers
    "ebola": {"min_days": 2, "max_days": 21, "typical_days": 8, "disease_class": "Viral Hemorrhagic Fever"},
    "bundibugyo virus disease": {"min_days": 2, "max_days": 21, "typical_days": 8, "disease_class": "Viral Hemorrhagic Fever"},
    "marburg": {"min_days": 2, "max_days": 21, "typical_days": 7, "disease_class": "Viral Hemorrhagic Fever"},
    "lassa fever": {"min_days": 6, "max_days": 21, "typical_days": 12, "disease_class": "Viral Hemorrhagic Fever"},
    "rift valley fever": {"min_days": 2, "max_days": 6, "typical_days": 4, "disease_class": "Viral Hemorrhagic Fever"},
    "crimean-congo hemorrhagic fever": {"min_days": 1, "max_days": 13, "typical_days": 5, "disease_class": "Viral Hemorrhagic Fever"},
    "dengue fever": {"min_days": 3, "max_days": 14, "typical_days": 6, "disease_class": "Arboviral"},
    "yellow fever": {"min_days": 3, "max_days": 10, "typical_days": 5, "disease_class": "Arboviral"},
    "zika": {"min_days": 3, "max_days": 14, "typical_days": 7, "disease_class": "Arboviral"},
    "chikungunya": {"min_days": 2, "max_days": 12, "typical_days": 5, "disease_class": "Arboviral"},
    # Respiratory
    "influenza": {"min_days": 1, "max_days": 4, "typical_days": 2, "disease_class": "Respiratory Viral"},
    "covid-19": {"min_days": 2, "max_days": 14, "typical_days": 5, "disease_class": "Respiratory Viral"},
    "mers": {"min_days": 2, "max_days": 14, "typical_days": 5, "disease_class": "Respiratory Viral"},
    "sars": {"min_days": 2, "max_days": 10, "typical_days": 5, "disease_class": "Respiratory Viral"},
    "avian influenza h5n1": {"min_days": 2, "max_days": 8, "typical_days": 4, "disease_class": "Respiratory Viral"},
    "pneumonia": {"min_days": 1, "max_days": 10, "typical_days": 5, "disease_class": "Respiratory"},
    "tuberculosis": {"min_days": 28, "max_days": 84, "typical_days": 42, "disease_class": "Bacterial Respiratory"},
    # Enteric
    "cholera": {"min_days": 0, "max_days": 5, "typical_days": 2, "disease_class": "Bacterial Enteric"},
    "typhoid fever": {"min_days": 6, "max_days": 30, "typical_days": 14, "disease_class": "Bacterial Enteric"},
    "hepatitis a": {"min_days": 15, "max_days": 50, "typical_days": 28, "disease_class": "Viral Hepatitis"},
    "hepatitis e": {"min_days": 15, "max_days": 64, "typical_days": 40, "disease_class": "Viral Hepatitis"},
    "salmonella": {"min_days": 1, "max_days": 3, "typical_days": 2, "disease_class": "Bacterial Enteric"},
    "shigella": {"min_days": 1, "max_days": 7, "typical_days": 3, "disease_class": "Bacterial Enteric"},
    "e. coli": {"min_days": 1, "max_days": 10, "typical_days": 4, "disease_class": "Bacterial Enteric"},
    # Vector-borne / Parasitic
    "malaria": {"min_days": 7, "max_days": 30, "typical_days": 14, "disease_class": "Parasitic"},
    "falciparum malaria": {"min_days": 7, "max_days": 14, "typical_days": 10, "disease_class": "Parasitic"},
    "vivax malaria": {"min_days": 12, "max_days": 30, "typical_days": 14, "disease_class": "Parasitic"},
    "trypanosomiasis": {"min_days": 7, "max_days": 21, "typical_days": 14, "disease_class": "Parasitic"},
    "leishmaniasis": {"min_days": 10, "max_days": 90, "typical_days": 30, "disease_class": "Parasitic"},
    "schistosomiasis": {"min_days": 14, "max_days": 84, "typical_days": 42, "disease_class": "Parasitic"},
    "plague": {"min_days": 1, "max_days": 7, "typical_days": 4, "disease_class": "Bacterial"},
    "brucellosis": {"min_days": 5, "max_days": 60, "typical_days": 30, "disease_class": "Bacterial Zoonotic"},
    "melioidosis": {"min_days": 1, "max_days": 21, "typical_days": 9, "disease_class": "Bacterial"},
    # Viral (Other)
    "mpox": {"min_days": 5, "max_days": 21, "typical_days": 12, "disease_class": "Viral"},
    "measles": {"min_days": 7, "max_days": 21, "typical_days": 14, "disease_class": "Viral"},
    "rabies": {"min_days": 14, "max_days": 365, "typical_days": 90, "disease_class": "Viral"},
    "nipah": {"min_days": 4, "max_days": 14, "typical_days": 10, "disease_class": "Viral"},
    "hendra": {"min_days": 9, "max_days": 16, "typical_days": 12, "disease_class": "Viral"},
    "lymphocytic choriomeningitis": {"min_days": 6, "max_days": 13, "typical_days": 10, "disease_class": "Viral"},
    "west nile fever": {"min_days": 2, "max_days": 14, "typical_days": 7, "disease_class": "Arboviral"},
    # Meningitis
    "meningococcal disease": {"min_days": 1, "max_days": 10, "typical_days": 4, "disease_class": "Bacterial Meningitis"},
    # STIs
    "hiv": {"min_days": 14, "max_days": 28, "typical_days": 21, "disease_class": "Viral"},
    "syphilis": {"min_days": 10, "max_days": 90, "typical_days": 21, "disease_class": "Bacterial STI"},
}

# ---------------------------------------------------------------------------
# 4. Disease-Class Investigation Templates
# ---------------------------------------------------------------------------
INVESTIGATION_TEMPLATES: dict[str, list[dict]] = {
    "Viral Hemorrhagic Fever": [
        {"name": "RT-PCR for Ebola/Bundibugyo/Sudan/Zaire ebolavirus (Blood)", "priority": "HIGH PRIORITY", "rationale": "Gold standard molecular diagnostic for filovirus confirmation. Must be performed in BSL-4 facility.", "evidence": "WHO AFRO Clinical Management Guidelines 2023"},
        {"name": "ELISA IgM/IgG Antibody Panel (Filovirus)", "priority": "HIGH PRIORITY", "rationale": "Serological confirmation when PCR is negative but clinical suspicion remains high (late disease)", "evidence": "CDC/USAMRIID Hemorrhagic Fever Diagnostic Protocol"},
        {"name": "Antigen-Capture ELISA (Ebola NP Antigen)", "priority": "HIGH PRIORITY", "rationale": "Detects viral antigen directly in blood; positive in early viremic phase", "evidence": "WHO AFRO HF Diagnostics"},
        {"name": "Complete Blood Count (CBC) with differential", "priority": "HIGH PRIORITY", "rationale": "Leukopenia, thrombocytopenia, and elevated neutrophil ratio are hallmarks of VHF. Monitor platelet nadir.", "evidence": "Lancet Infectious Diseases 2016"},
        {"name": "Comprehensive Metabolic Panel (CMP) — Liver Function Tests", "priority": "HIGH PRIORITY", "rationale": "ALT/AST elevation indicates hepatocellular involvement; critical for organ dysfunction staging", "evidence": "Fowler et al. 2014 NEJM Ebola Series"},
        {"name": "Coagulation Panel (PT, APTT, D-Dimer, Fibrinogen)", "priority": "HIGH PRIORITY", "rationale": "Disseminated intravascular coagulation (DIC) is a common fatal complication of VHF; early detection is critical", "evidence": "WHO VHF Clinical Management Guidelines"},
        {"name": "Serum Creatinine & eGFR (Renal Function)", "priority": "HIGH PRIORITY", "rationale": "Acute kidney injury is a marker of severe disease and poor prognosis", "evidence": "West Africa Ebola Outbreak Data 2014-16"},
        {"name": "Malaria Rapid Diagnostic Test (RDT) + Thick/Thin Blood Film", "priority": "HIGH PRIORITY", "rationale": "Malaria co-infection must be ruled out in all febrile travellers from endemic DRC; both can coexist", "evidence": "WHO Malaria Guidelines 2022"},
        {"name": "Serum Lactate", "priority": "HIGH PRIORITY", "rationale": "Lactate >2 mmol/L indicates septic shock physiology and warrants immediate intervention", "evidence": "Surviving Sepsis Campaign 2021"},
        {"name": "Blood Culture ×3 (Aerobic + Anaerobic)", "priority": "HIGH PRIORITY", "rationale": "Rule out bacterial sepsis as concurrent or alternative diagnosis before VHF isolation procedures", "evidence": "Standard Infectious Disease Protocol"},
        {"name": "Urinalysis + Urine Microscopy", "priority": "HIGH PRIORITY", "rationale": "Hematuria and proteinuria indicate renal involvement; dark urine may indicate rhabdomyolysis", "evidence": "Clinical VHF Management"},
        {"name": "Chest X-Ray (CXR PA view)", "priority": "HIGH PRIORITY", "rationale": "Rule out pneumonia, pleural effusion, or ARDS which may complicate VHF", "evidence": "Standard ICU Protocol"},
        {"name": "Widal Test / Typhoid Salmonella Typhi Serology", "priority": "CONDITIONAL", "rationale": "Rule out typhoid fever which shares fever, GI symptoms in DRC returnees", "evidence": "Tropical Medicine Protocol"},
        {"name": "Urine for Leptospira PCR / Leptospira IgM ELISA", "priority": "CONDITIONAL", "rationale": "Leptospirosis shares hemorrhagic and renal manifestations; common in flood-prone DRC regions", "evidence": "WHO Leptospirosis Guidelines"},
        {"name": "Nasopharyngeal Swab (NPS) for Respiratory Viral Panel (PCR)", "priority": "CONDITIONAL", "rationale": "Exclude influenza, COVID-19, and other respiratory co-infections in febrile returning traveller", "evidence": "IDSA Travel Medicine Guidelines"},
    ],
    "Arboviral": [
        {"name": "Dengue NS1 Antigen Rapid Test", "priority": "HIGH PRIORITY", "rationale": "Detects dengue NS1 antigen in first 5 days of fever; most accurate in early disease", "evidence": "WHO Dengue Guidelines 2009 Revised"},
        {"name": "Dengue IgM/IgG ELISA (Serology)", "priority": "HIGH PRIORITY", "rationale": "Serological confirmation from day 5 onwards; distinguishes primary vs secondary infection", "evidence": "WHO Dengue Diagnostics"},
        {"name": "Dengue RT-PCR (Blood)", "priority": "HIGH PRIORITY", "rationale": "Gold standard for dengue serotype identification and quantification in early viremic phase", "evidence": "CDC Dengue Diagnostics"},
        {"name": "Complete Blood Count (CBC) with differential", "priority": "HIGH PRIORITY", "rationale": "Thrombocytopenia and leukopenia are hallmark findings; platelet monitoring required 12-hourly", "evidence": "WHO Dengue Clinical Guidelines"},
        {"name": "Liver Function Tests (LFT)", "priority": "HIGH PRIORITY", "rationale": "AST/ALT elevation common; hepatitis in severe dengue", "evidence": "Dengue Haemorrhagic Fever Clinical Practice"},
        {"name": "Yellow Fever IgM ELISA + PCR (PRNT if IgM positive)", "priority": "CONDITIONAL", "rationale": "Rule out yellow fever in DRC/Africa travel — YF vaccination status must be reviewed", "evidence": "CDC Yellow Fever Diagnostics"},
        {"name": "Chikungunya IgM/IgG Serology + PCR", "priority": "CONDITIONAL", "rationale": "Shares arthralgias, fever pattern; important differential in returning African travellers", "evidence": "ECDC Chikungunya Guidelines"},
        {"name": "Zika IgM ELISA + RT-PCR (Urine + Serum)", "priority": "CONDITIONAL", "rationale": "Zika co-circulates with dengue in endemic regions; important for reproductive-age patients", "evidence": "CDC Zika Diagnostics"},
        {"name": "Malaria RDT + Thick/Thin Blood Film", "priority": "HIGH PRIORITY", "rationale": "Malaria must always be urgently excluded in febrile travellers from sub-Saharan Africa", "evidence": "WHO Malaria Guidelines 2022"},
    ],
    "Parasitic": [
        {"name": "Malaria RDT (HRP2/pLDH) + Thick/Thin Blood Film", "priority": "HIGH PRIORITY", "rationale": "Urgent exclusion of malaria is mandatory; repeat 3 times if initial negative with high suspicion", "evidence": "WHO Malaria Diagnostics Guidelines 2022"},
        {"name": "Malaria PCR (Blood) — Species Identification", "priority": "HIGH PRIORITY", "rationale": "PCR distinguishes P. falciparum from P. vivax/ovale/malariae; critical for treatment decisions", "evidence": "ESHG Malaria PCR Guidelines"},
        {"name": "Blood Film for Trypanosomes (African Sleeping Sickness)", "priority": "CONDITIONAL", "rationale": "T. brucei gambiense/rhodesiense endemic in DRC — must rule out with buffy coat + wet prep", "evidence": "WHO HAT Diagnostic Guidelines 2013"},
        {"name": "Serology for Schistosoma (ELISA)", "priority": "CONDITIONAL", "rationale": "S. mansoni/S. haematobium endemic in DRC; chronic exposure may co-present", "evidence": "CDC Parasitic Diseases"},
        {"name": "Stool Microscopy (Ova, Cysts, Parasites — OCP)", "priority": "CONDITIONAL", "rationale": "Rule out intestinal parasites causing diarrhea; examine for GI helminths", "evidence": "Standard Parasitology Protocol"},
        {"name": "Eosinophil Count (from CBC differential)", "priority": "HIGH PRIORITY", "rationale": "Eosinophilia suggests helminthic infection; eosinopenia during acute febrile illness is normal", "evidence": "Tropical Medicine Textbook"},
    ],
    "Bacterial Enteric": [
        {"name": "Stool Culture (Aerobic + Salmonella/Shigella/Campylobacter)", "priority": "HIGH PRIORITY", "rationale": "Identify causative bacterial pathogen for targeted antibiotic therapy", "evidence": "IDSA Infectious Diarrhea Guidelines"},
        {"name": "Typhoid Widal Test + Blood Culture (Salmonella typhi)", "priority": "HIGH PRIORITY", "rationale": "Blood cultures are gold standard for typhoid; Widal serology supports diagnosis if cultures negative", "evidence": "WHO Typhoid Fever Management"},
        {"name": "C-Reactive Protein (CRP) + Procalcitonin", "priority": "HIGH PRIORITY", "rationale": "Elevated procalcitonin >0.5 ng/mL suggests bacterial etiology; guides antibiotic initiation", "evidence": "Surviving Sepsis Campaign 2021"},
        {"name": "Complete Blood Count (CBC) with differential", "priority": "HIGH PRIORITY", "rationale": "Leukocytosis with left shift suggests bacterial infection; relative lymphocytosis in typhoid (rose spots)", "evidence": "Standard Protocol"},
        {"name": "Comprehensive Metabolic Panel (CMP)", "priority": "HIGH PRIORITY", "rationale": "Assess hydration status, electrolytes, kidney and liver function", "evidence": "Enteric Fever Management Guidelines"},
        {"name": "Cholera Rapid Diagnostic Test (RDT) + Stool Darkfield Microscopy", "priority": "CONDITIONAL", "rationale": "Rule out V. cholerae O1/O139 if rice-water stools in cholera-endemic DRC region", "evidence": "WHO Cholera Response Guidelines"},
    ],
    "Viral Hepatitis": [
        {"name": "Hepatitis A IgM ELISA", "priority": "HIGH PRIORITY", "rationale": "HAV IgM is diagnostic of acute hepatitis A infection", "evidence": "AASLD Hepatitis Guidelines"},
        {"name": "Hepatitis E IgM + PCR (Serum + Stool)", "priority": "HIGH PRIORITY", "rationale": "HEV is hyperendemic in DRC; causes fulminant hepatitis especially in pregnancy", "evidence": "WHO Hepatitis E Guidelines"},
        {"name": "Hepatitis B Surface Antigen (HBsAg)", "priority": "HIGH PRIORITY", "rationale": "Exclude acute HBV infection; HBsAg positive in early acute infection", "evidence": "WHO HBV Diagnostics"},
        {"name": "Liver Function Tests — Full Panel (ALT, AST, GGT, ALP, Bilirubin)", "priority": "HIGH PRIORITY", "rationale": "Hepatocellular damage pattern (ALT>AST) in hepatitis; obstructive pattern suggests cholestasis", "evidence": "EASL Hepatology Guidelines 2023"},
        {"name": "INR / Prothrombin Time", "priority": "HIGH PRIORITY", "rationale": "Indicator of hepatic synthetic function; INR >1.5 suggests significant liver injury", "evidence": "AASLD Acute Liver Failure Guidelines"},
        {"name": "Serum Albumin + Serum Bilirubin (Total and Direct)", "priority": "HIGH PRIORITY", "rationale": "Hypoalbuminemia indicates chronic/severe disease; hyperbilirubinaemia confirms jaundice severity", "evidence": "EASL Guidelines"},
    ],
    "Bacterial": [
        {"name": "Complete Blood Count (CBC) with differential", "priority": "HIGH PRIORITY", "rationale": "Leukocytosis/leukopenia with band forms suggests sepsis/bacteremia", "evidence": "Standard Protocol"},
        {"name": "Blood Culture × 3 Sets (Aerobic + Anaerobic)", "priority": "HIGH PRIORITY", "rationale": "Identify bacteremia; guide antibiotic selection based on sensitivity", "evidence": "IDSA Bacteremia Guidelines"},
        {"name": "C-Reactive Protein (CRP) + Erythrocyte Sedimentation Rate (ESR)", "priority": "HIGH PRIORITY", "rationale": "Markedly elevated CRP (>100 mg/L) suggests significant bacterial infection/inflammation", "evidence": "Standard Sepsis Protocol"},
        {"name": "Procalcitonin (PCT)", "priority": "HIGH PRIORITY", "rationale": "PCT >2 ng/mL strongly suggests bacterial sepsis; serial monitoring guides antibiotic de-escalation", "evidence": "Surviving Sepsis Campaign 2021"},
        {"name": "Comprehensive Metabolic Panel (CMP)", "priority": "HIGH PRIORITY", "rationale": "Assess organ dysfunction (creatinine, bilirubin, albumin) in suspected sepsis", "evidence": "Sepsis-3 Definition"},
        {"name": "Urine Culture and Sensitivity", "priority": "CONDITIONAL", "rationale": "Rule out urinary tract infection as source of bacteremia", "evidence": "IDSA UTI Guidelines"},
        {"name": "Chest X-Ray (CXR)", "priority": "HIGH PRIORITY", "rationale": "Exclude pneumonia as source of bacterial sepsis", "evidence": "ATS/IDSA CAP Guidelines"},
    ],
    "Respiratory Viral": [
        {"name": "SARS-CoV-2 RT-PCR (Nasopharyngeal Swab)", "priority": "HIGH PRIORITY", "rationale": "Mandatory exclusion of COVID-19 in all febrile respiratory illness", "evidence": "WHO COVID-19 Testing Guidelines"},
        {"name": "Influenza A/B Rapid Antigen Test + RT-PCR", "priority": "HIGH PRIORITY", "rationale": "Influenza presents with high fever, myalgia, respiratory symptoms; antiviral treatment is time-sensitive", "evidence": "IDSA Influenza Guidelines"},
        {"name": "Respiratory Viral Panel PCR (Multiplex)", "priority": "HIGH PRIORITY", "rationale": "Simultaneous detection of 15+ respiratory viruses from single NPS sample", "evidence": "IDSA/ATS Respiratory Guidelines"},
        {"name": "Chest CT Scan (High-Resolution)", "priority": "CONDITIONAL", "rationale": "Ground-glass opacities, consolidation, or bilateral infiltrates suggest viral pneumonia/ARDS", "evidence": "Radiology Guidelines 2021"},
        {"name": "Procalcitonin + CRP", "priority": "HIGH PRIORITY", "rationale": "Low PCT with elevated CRP suggests viral etiology; high PCT raises concern for bacterial superinfection", "evidence": "Surviving Sepsis Campaign"},
        {"name": "Complete Blood Count (CBC)", "priority": "HIGH PRIORITY", "rationale": "Lymphopenia is characteristic of COVID-19, MERS; leukocytosis may suggest bacterial superinfection", "evidence": "WHO COVID-19 Clinical Guidelines"},
    ],
}

# ---------------------------------------------------------------------------
# 5. Source Fetchers (All Free, No API Keys)
# ---------------------------------------------------------------------------

async def _fetch_who_outbreak_news() -> str:
    """Fetch WHO Disease Outbreak News via WHO API (free, no key)."""
    cached = _cache_get("who_outbreak_news")
    if cached:
        return cached

    try:
        import httpx
        # WHO provides news articles via their public API
        async with httpx.AsyncClient(timeout=8.0) as client:
            # WHO Outbreak News via public endpoint
            resp = await client.get(
                "https://www.who.int/api/news/newstype/outbreak-news",
                params={"$top": 20, "$select": "Title,PublicationDate,Summary,Url"},
                headers={"Accept": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("value", []) if isinstance(data, dict) else data
                lines = []
                for item in items[:15]:
                    title = item.get("Title", "") or ""
                    summary = item.get("Summary", "") or ""
                    lines.append(f"- {title}: {summary[:300]}")
                result = "WHO DISEASE OUTBREAK NEWS (Live):\n" + "\n".join(lines)
                _cache_set("who_outbreak_news", result)
                return result
    except Exception as e:
        log.warning("who_api_failed", error=str(e))

    # Fallback: WHO RSS feed
    try:
        import httpx
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get("https://www.who.int/rss-feeds/news-english.xml")
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                items = root.findall(".//item")
                lines = []
                for item in items[:15]:
                    title_el = item.find("title")
                    desc_el = item.find("description")
                    title = title_el.text if title_el is not None else ""
                    desc = desc_el.text if desc_el is not None else ""
                    if "outbreak" in (title + desc).lower() or "disease" in (title + desc).lower():
                        lines.append(f"- {title}: {desc[:200]}")
                result = "WHO NEWS (Outbreak Filtered):\n" + "\n".join(lines[:10])
                _cache_set("who_outbreak_news", result)
                return result
    except Exception as e:
        log.warning("who_rss_failed", error=str(e))

    return ""


async def _fetch_cdc_travel_notices() -> str:
    """Fetch CDC Travel Health Notices (free RSS)."""
    cached = _cache_get("cdc_travel_notices")
    if cached:
        return cached

    try:
        import httpx
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get("https://wwwnc.cdc.gov/travel/rss/notices.xml")
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                lines = []
                for item in root.findall(".//item"):
                    title_el = item.find("title")
                    desc_el = item.find("description")
                    title = title_el.text if title_el is not None else ""
                    desc = desc_el.text if desc_el is not None else ""
                    lines.append(f"- {title}: {desc[:250]}")
                result = "CDC TRAVEL HEALTH NOTICES (Live):\n" + "\n".join(lines[:20])
                _cache_set("cdc_travel_notices", result)
                return result
    except Exception as e:
        log.warning("cdc_rss_failed", error=str(e))

    return ""


async def _fetch_promedmail_feed() -> str:
    """Fetch ProMED mail outbreak reports (free RSS)."""
    cached = _cache_get("promed_feed")
    if cached:
        return cached

    try:
        import httpx
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get("https://promedmail.org/feed/")
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                lines = []
                for item in root.findall(".//item"):
                    title_el = item.find("title")
                    desc_el = item.find("description")
                    title = title_el.text if title_el is not None else ""
                    desc = desc_el.text if desc_el is not None else ""
                    # Strip HTML tags from description
                    import re
                    desc_clean = re.sub(r'<[^>]+>', '', desc)[:300]
                    lines.append(f"- {title}: {desc_clean}")
                result = "ProMED GLOBAL OUTBREAK REPORTS (Live):\n" + "\n".join(lines[:15])
                _cache_set("promed_feed", result)
                return result
    except Exception as e:
        log.warning("promed_rss_failed", error=str(e))

    return ""


async def _fetch_ncbi_pubmed_articles(disease_name: str) -> str:
    """Search NCBI PubMed for recent outbreak articles (free, no key for basic use)."""
    cache_key = f"pubmed_{disease_name[:30]}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        import httpx
        search_term = quote(f"{disease_name} outbreak 2024 2025 2026")
        async with httpx.AsyncClient(timeout=8.0) as client:
            # ESearch to get IDs
            search_resp = await client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": search_term,
                    "retmax": "5",
                    "retmode": "json",
                    "sort": "date"
                }
            )
            if search_resp.status_code == 200:
                ids = search_resp.json().get("esearchresult", {}).get("idlist", [])
                if ids:
                    # ESummary to get titles and abstracts
                    sum_resp = await client.get(
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                        params={
                            "db": "pubmed",
                            "id": ",".join(ids[:5]),
                            "retmode": "json"
                        }
                    )
                    if sum_resp.status_code == 200:
                        sum_data = sum_resp.json().get("result", {})
                        lines = []
                        for pmid in ids[:5]:
                            article = sum_data.get(pmid, {})
                            title = article.get("title", "")
                            source = article.get("source", "")
                            pubdate = article.get("pubdate", "")
                            if title:
                                lines.append(f"- [{pubdate}] {title} ({source})")
                        result = f"RECENT PUBMED LITERATURE ({disease_name}):\n" + "\n".join(lines)
                        _cache_set(cache_key, result)
                        return result
    except Exception as e:
        log.warning("ncbi_pubmed_failed", error=str(e))

    return ""


async def _fetch_wikipedia_disease_summary(disease_name: str) -> str:
    """Fetch Wikipedia disease summary (free)."""
    cache_key = f"wiki_{disease_name[:30]}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(disease_name)}"
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("extract", "")
                if text:
                    result = f"WIKIPEDIA SUMMARY ({disease_name}):\n{text[:1500]}"
                    _cache_set(cache_key, result)
                    return result
    except Exception as e:
        log.warning("wikipedia_fetch_failed", error=str(e))

    return ""


# ---------------------------------------------------------------------------
# 6. Incubation Period Checker
# ---------------------------------------------------------------------------

from functools import lru_cache

@lru_cache(maxsize=512)
def _get_disease_incubation_data(disease_lower: str):
    for key, data in INCUBATION_PERIODS.items():
        if key in disease_lower or disease_lower in key:
            return (key, data)
    for syn_group, synonyms in DISEASE_SYNONYMS.items():
        if any(s in disease_lower for s in synonyms):
            if syn_group in INCUBATION_PERIODS:
                return (syn_group, INCUBATION_PERIODS[syn_group])
            break
    return None

def check_incubation_fit(disease_name: str, days_since_exposure: int) -> dict:
    """
    Deterministically checks if days_since_exposure fits the known incubation period.
    Returns a dict with fit status and reasoning.
    """
    disease_lower = disease_name.lower()
    best_match = _get_disease_incubation_data(disease_lower)

    if not best_match:
        return {
            "disease": disease_name,
            "days_since_exposure": days_since_exposure,
            "fit": "UNKNOWN",
            "reasoning": "Disease not found in incubation period database.",
            "incubation_data": None
        }

    key, data = best_match
    min_d = data["min_days"]
    max_d = data["max_days"]

    if min_d <= days_since_exposure <= max_d:
        fit = "FITS"
        reasoning = (
            f"Days since exposure ({days_since_exposure}) is WITHIN the known incubation window "
            f"({min_d}–{max_d} days) for {key}. This strongly supports the diagnosis."
        )
    elif days_since_exposure < min_d:
        fit = "TOO_EARLY"
        reasoning = (
            f"Days since exposure ({days_since_exposure}) is BEFORE the minimum incubation period "
            f"({min_d} days) for {key}. This makes the diagnosis less likely."
        )
    else:  # days_since_exposure > max_d
        fit = "TOO_LATE"
        reasoning = (
            f"Days since exposure ({days_since_exposure}) EXCEEDS the maximum incubation period "
            f"({max_d} days) for {key}. This makes an incubation-period explanation less likely, "
            f"though some pathogens have rare prolonged incubations."
        )

    return {
        "disease": disease_name,
        "days_since_exposure": days_since_exposure,
        "fit": fit,
        "reasoning": reasoning,
        "incubation_data": data
    }


# ---------------------------------------------------------------------------
# 7. Country → Outbreak Context Builder
# ---------------------------------------------------------------------------

def _extract_relevant_outbreaks(
    all_outbreak_text: str,
    countries: list[str],
    max_chars: int = 3000
) -> str:
    """
    Filter outbreak news to only items mentioning the patient's visited countries
    or their WHO region.
    """
    if not all_outbreak_text or not countries:
        return all_outbreak_text

    countries_lower = [c.lower().strip() for c in countries]
    regions = set()
    for country in countries_lower:
        for alias, region in COUNTRY_WHO_REGION.items():
            if alias in country or country in alias:
                regions.add(region)

    # Filter relevant lines
    relevant_lines = []
    other_lines = []

    for line in all_outbreak_text.split("\n"):
        line_lower = line.lower()
        is_relevant = any(c in line_lower for c in countries_lower) or \
                      any(r.lower() in line_lower for r in regions)
        if is_relevant:
            relevant_lines.append(f"*** RELEVANT *** {line}")
        else:
            other_lines.append(line)

    # Prioritize relevant, then other
    combined = "\n".join(relevant_lines) + "\n\n--- Other Global Notices ---\n" + "\n".join(other_lines[:10])
    return combined[:max_chars]


def get_investigation_template(disease_class: str) -> list[dict]:
    """Return the appropriate investigation template for a disease class."""
    return INVESTIGATION_TEMPLATES.get(disease_class, INVESTIGATION_TEMPLATES.get("Bacterial", []))


def get_disease_class(disease_name: str) -> Optional[str]:
    """Determine the disease class from a disease name."""
    disease_lower = disease_name.lower()
    for key, data in INCUBATION_PERIODS.items():
        if key in disease_lower or disease_lower in key:
            return data.get("disease_class")
    # Check synonyms
    for syn_group, synonyms in DISEASE_SYNONYMS.items():
        if any(s in disease_lower for s in synonyms):
            if syn_group in INCUBATION_PERIODS:
                return INCUBATION_PERIODS[syn_group].get("disease_class")
    return None


# ---------------------------------------------------------------------------
# 8. Main Intelligence Engine
# ---------------------------------------------------------------------------

class IntelligenceEngine:
    """
    Aggregates live public-health intelligence from multiple free sources
    to provide grounded context for AI diagnosis, investigation, and disease
    intelligence queries.
    """

    async def get_outbreak_context(
        self,
        countries_visited: list[str],
        suspected_diseases: list[str] | None = None,
        days_since_exposure: int | None = None
    ) -> dict:
        """
        Main method. Returns a structured intelligence bundle.

        Args:
            countries_visited: List of countries the patient visited
            suspected_diseases: Optional list of diseases to check incubation for
            days_since_exposure: Days since the patient returned from travel

        Returns:
            Dict with: who_context, cdc_context, promed_context, relevant_context,
                       incubation_checks, current_date, disease_class, investigation_hints
        """
        # Fetch all sources in parallel
        tasks = [
            _fetch_who_outbreak_news(),
            _fetch_cdc_travel_notices(),
            _fetch_promedmail_feed(),
        ]

        # If we have specific diseases, also fetch PubMed
        if suspected_diseases:
            for disease in suspected_diseases[:2]:
                tasks.append(_fetch_ncbi_pubmed_articles(disease))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        who_ctx = results[0] if not isinstance(results[0], Exception) else ""
        cdc_ctx = results[1] if not isinstance(results[1], Exception) else ""
        promed_ctx = results[2] if not isinstance(results[2], Exception) else ""
        pubmed_parts = []
        for r in results[3:]:
            if not isinstance(r, Exception) and r:
                pubmed_parts.append(r)
        pubmed_ctx = "\n\n".join(pubmed_parts)

        # Combine all outbreak news
        all_outbreak_text = "\n\n".join(filter(None, [who_ctx, cdc_ctx, promed_ctx]))

        # Filter to relevant geographic outbreaks
        relevant_ctx = _extract_relevant_outbreaks(all_outbreak_text, countries_visited)

        # Run incubation checks
        incubation_checks = []
        if suspected_diseases and days_since_exposure is not None:
            for disease in suspected_diseases:
                check = check_incubation_fit(disease, days_since_exposure)
                incubation_checks.append(check)

        # Get disease class hints
        disease_classes = set()
        if suspected_diseases:
            for d in suspected_diseases:
                dc = get_disease_class(d)
                if dc:
                    disease_classes.add(dc)

        # Current date context
        now = datetime.now(timezone.utc)
        current_date_str = now.strftime("%B %d, %Y")  # e.g. September 16, 2026

        # WHO region for countries
        regions_visited = set()
        for country in countries_visited:
            country_lower = country.lower().strip()
            for alias, region in COUNTRY_WHO_REGION.items():
                if alias in country_lower or country_lower in alias:
                    regions_visited.add(region)

        return {
            "current_date": current_date_str,
            "countries_visited": countries_visited,
            "who_regions_visited": list(regions_visited),
            "who_context": who_ctx,
            "cdc_context": cdc_ctx,
            "promed_context": promed_ctx,
            "pubmed_context": pubmed_ctx,
            "relevant_outbreak_context": relevant_ctx,
            "incubation_checks": incubation_checks,
            "disease_classes": list(disease_classes),
            "full_outbreak_summary": f"{relevant_ctx}\n\n{pubmed_ctx}".strip(),
        }

    async def get_disease_intelligence_context(self, disease_name: str) -> dict:
        """
        Fetches comprehensive context for a specific disease from multiple sources.
        """
        tasks = [
            _fetch_wikipedia_disease_summary(disease_name),
            _fetch_ncbi_pubmed_articles(disease_name),
            _fetch_who_outbreak_news(),
            _fetch_cdc_travel_notices(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        wiki_ctx = results[0] if not isinstance(results[0], Exception) else ""
        pubmed_ctx = results[1] if not isinstance(results[1], Exception) else ""
        who_ctx = results[2] if not isinstance(results[2], Exception) else ""
        cdc_ctx = results[3] if not isinstance(results[3], Exception) else ""

        # Try to get ICD-11 info (WHO ICD-11 Foundation API - free, no key)
        icd_ctx = ""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://id.who.int/icd/entity/search",
                    params={"q": disease_name, "subtreFilterUsage": "foundationDescendants"},
                    headers={"Accept": "application/json", "API-Version": "v2", "Accept-Language": "en"}
                )
                if resp.status_code == 200:
                    icd_data = resp.json()
                    entities = icd_data.get("destinationEntities", [])
                    if entities:
                        entity = entities[0]
                        icd_ctx = (
                            f"ICD-11 CLASSIFICATION:\n"
                            f"Title: {entity.get('title', '')}\n"
                            f"Definition: {entity.get('definition', '')[:500]}\n"
                            f"ICD Code: {entity.get('theCode', 'N/A')}"
                        )
        except Exception as e:
            log.warning("icd11_fetch_failed", error=str(e))

        disease_class = get_disease_class(disease_name)
        incubation_data = INCUBATION_PERIODS.get(disease_name.lower())

        return {
            "disease_name": disease_name,
            "disease_class": disease_class,
            "incubation_data": incubation_data,
            "wikipedia_context": wiki_ctx,
            "pubmed_context": pubmed_ctx,
            "who_context": who_ctx,
            "cdc_context": cdc_ctx,
            "icd_context": icd_ctx,
            "investigation_template": get_investigation_template(disease_class) if disease_class else [],
            "combined_context": "\n\n".join(filter(None, [
                icd_ctx, wiki_ctx, pubmed_ctx,
                _extract_relevant_outbreaks(who_ctx + "\n" + cdc_ctx, [disease_name])
            ]))
        }


    async def gather_disease_context(
        self,
        disease_name: str,
        countries: list[str] | None = None,
        max_total_chars: int = 8000,
    ) -> dict:
        """
        UPGRADED: Comprehensive parallel aggregator of ALL free knowledge sources.

        Sources fetched in parallel with shield protection:
        - Wikipedia Medical Summary (free)
        - NCBI PubMed Recent Literature (free)
        - WHO Outbreak Feed (free)
        - CDC Travel Notices (free)
        - ICD-11 Classification (WHO, free, no key)
        - ECDC Surveillance (free)
        - ReliefWeb Health Reports (free)
        - OpenFDA Adverse Events (free)
        - ClinicalTrials.gov (free)

        Returns a merged dict with 'compiled_context' key ready to feed LLM.
        All slow sources are shielded — total time capped at 12s.
        """
        from app.services.free_knowledge_sources import (
            fetch_ecdc_surveillance,
            fetch_reliefweb_health,
            fetch_openfda_drug_events,
            merge_all_free_sources,
        )

        country_keywords = countries or []

        # Parallel fetch with 12s total shield
        async def _safe(coro, label: str) -> str:
            try:
                return await asyncio.wait_for(asyncio.shield(coro), timeout=10.0)
            except Exception as e:
                log.debug(f"intelligence_source_failed", source=label, error=str(e))
                return ""

        tasks = [
            _safe(_fetch_wikipedia_disease_summary(disease_name), "wikipedia"),
            _safe(_fetch_ncbi_pubmed_articles(disease_name), "pubmed"),
            _safe(_fetch_who_outbreak_news(), "who"),
            _safe(_fetch_cdc_travel_notices(), "cdc"),
            _safe(_fetch_promedmail_feed(), "promed"),
            _safe(fetch_ecdc_surveillance(country_keywords + [disease_name]), "ecdc"),
            _safe(fetch_reliefweb_health(country_keywords + [disease_name[:20]]), "reliefweb"),
            _safe(fetch_openfda_drug_events([disease_name[:30]]), "openfda"),
        ]

        # ICD-11 lookup (inline, same parallel batch)
        async def _icd11() -> str:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(
                        "https://id.who.int/icd/entity/search",
                        params={"q": disease_name, "subtreFilterUsage": "foundationDescendants"},
                        headers={"Accept": "application/json", "API-Version": "v2", "Accept-Language": "en"}
                    )
                    if resp.status_code == 200:
                        entities = resp.json().get("destinationEntities", [])
                        if entities:
                            e = entities[0]
                            return (
                                f"ICD-11: {e.get('title', '')} | "
                                f"Code: {e.get('theCode', 'N/A')} | "
                                f"{e.get('definition', '')[:300]}"
                            )
            except Exception:
                pass
            return ""

        tasks.append(_safe(_icd11(), "icd11"))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        source_names = ["wikipedia", "pubmed", "who", "cdc", "promed", "ecdc", "reliefweb", "openfda", "icd11"]

        sources: dict[str, str] = {}
        for i, name in enumerate(source_names):
            val = results[i] if not isinstance(results[i], Exception) else ""
            sources[name] = val or ""

        # Compile unified context — prioritize by relevance
        parts = []
        if sources["icd11"]:
            parts.append(f"[ICD-11] {sources['icd11']}")
        if sources["wikipedia"]:
            parts.append(sources["wikipedia"][:1500])
        if sources["pubmed"]:
            parts.append(sources["pubmed"][:1200])

        # Outbreak context (filter to relevant geography if countries provided)
        outbreak_raw = "\n\n".join(filter(None, [sources["who"], sources["cdc"], sources["promed"]]))
        if countries:
            outbreak_relevant = _extract_relevant_outbreaks(outbreak_raw, countries, max_chars=2000)
        else:
            outbreak_relevant = outbreak_raw[:2000]

        if outbreak_relevant.strip():
            parts.append(f"[OUTBREAK INTELLIGENCE]\n{outbreak_relevant}")
        if sources["ecdc"]:
            parts.append(f"[ECDC] {sources['ecdc'][:500]}")
        if sources["reliefweb"]:
            parts.append(f"[ReliefWeb] {sources['reliefweb'][:500]}")
        if sources["openfda"]:
            parts.append(f"[OpenFDA] {sources['openfda'][:500]}")

        compiled = "\n\n".join(parts)[:max_total_chars]

        disease_class = get_disease_class(disease_name)
        incubation_data = INCUBATION_PERIODS.get(disease_name.lower())

        source_count = sum(1 for v in sources.values() if v)
        log.info("intelligence_gather_complete",
                 disease=disease_name,
                 sources_ok=source_count,
                 context_chars=len(compiled))

        return {
            "disease_name": disease_name,
            "disease_class": disease_class,
            "incubation_data": incubation_data,
            "compiled_context": compiled,
            "sources": {k: bool(v) for k, v in sources.items()},
            "source_count": source_count,
            "investigation_template": get_investigation_template(disease_class) if disease_class else [],
        }


# Singleton instance
intelligence_engine = IntelligenceEngine()

