import asyncio
import uuid
from app.models.representation import ClinicalRepresentation, ClinicalItem
from app.services.epidemiology_service import epi_radar_service as epi
from app.services.pubmed_scanner_service import pubmed_scanner_service
from app.services.early_warning_service import EarlyWarningService

async def test_all():
    ews = EarlyWarningService()
    
    # 1. Test EWS Parsing logic directly
    vitals = ["Heart Rate 135 bpm", "RR 26", "Blood Pressure 85/50", "Temp 103.5F", "SpO2 90%", "confused"]
    parsed = ews.parse_vitals(vitals)
    print("Parsed Vitals:", parsed)
    mews = ews.calculate_mews(parsed)
    qsofa = ews.calculate_qsofa(parsed)
    news2 = ews.calculate_news2(parsed)
    sirs = ews.calculate_sirs(parsed)
    print(f"MEWS: {mews}, qSOFA: {qsofa}, NEWS2: {news2}, SIRS: {sirs}")
    
    if mews >= 4 and qsofa >= 2 and news2 >= 5 and sirs >= 2:
        print("EWS Math Logic: SUCCESS")
    else:
        print("EWS Math Logic: FAILED")

    # 2. Test PubMed Logic
    print("Testing PubMed Scanner...")
    res = await pubmed_scanner_service.scan_for_controversies("Sepsis")
    print(f"Controversy found: {res.controversy_found}")
    print(f"Articles: {len(res.articles)}")

if __name__ == "__main__":
    asyncio.run(test_all())
