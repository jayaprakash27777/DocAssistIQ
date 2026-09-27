"""DocAssistIQ — India State-Wide & Global Outbreak Surveillance Tests.

Validates:
  1. Complete coverage of ALL 28 Indian States & 8 Union Territories with verified public health profiles
  2. Live CDC Travel Notices RSS feed integration and parsing
  3. Dynamic symptom, trigger, and geographic outbreak matching
  4. Integration into Real-Time Differential Diagnosis scoring & containment tagging
  5. State Outbreaks API endpoint responses & multi-factor filters
"""

import pytest
from app.services.india_outbreak_surveillance import (
    get_all_state_outbreaks,
    match_outbreaks_for_symptoms,
    fetch_live_cdc_outbreaks,
    ALL_INDIAN_STATES_AND_UTS,
    INDIA_STATE_OUTBREAKS,
    STATIC_GLOBAL_OUTBREAKS,
)
from app.services.realtime_prediction_service import realtime_prediction_service


def test_all_36_indian_states_and_uts_covered():
    """Verify registry includes all 28 Indian States and 8 Union Territories."""
    assert len(ALL_INDIAN_STATES_AND_UTS) == 36
    # Every state in the list must have an active surveillance profile
    registered_states = set(a["state_or_country"] for a in INDIA_STATE_OUTBREAKS)
    assert len(registered_states) >= 36


def test_every_single_state_and_ut_has_active_surveillance_data():
    """Verify that every single state/UT in ALL_INDIAN_STATES_AND_UTS returns at least one active alert."""
    for st in ALL_INDIAN_STATES_AND_UTS:
        res = get_all_state_outbreaks(state_filter=st)
        assert len(res["india_state_alerts"]) >= 1, f"State/UT '{st}' has no active surveillance alerts!"


def test_get_all_state_outbreaks_structure():
    """Verify get_all_state_outbreaks returns proper schema and counts."""
    res = get_all_state_outbreaks()
    assert res["status"] == "ok"
    assert res["total_active_alerts"] >= 40
    assert len(res["india_state_alerts"]) >= 36
    assert len(res["global_alerts"]) >= 5
    assert len(res["surveillance_sources"]) >= 5

    # Test state filter
    kerala_res = get_all_state_outbreaks(state_filter="Kerala")
    assert any(a["state_or_country"] == "Kerala" for a in kerala_res["india_state_alerts"])

    # Test query filter
    nipah_res = get_all_state_outbreaks(query_filter="Nipah")
    assert any("Nipah" in a["disease_name"] for a in nipah_res["india_state_alerts"])


def test_live_cdc_feed_parsing():
    """Verify live CDC Travel Notices are fetched and structured properly."""
    cdc_alerts = fetch_live_cdc_outbreaks()
    assert len(cdc_alerts) > 0
    first = cdc_alerts[0]
    assert first["region_type"] == "global"
    assert "US CDC Travel Health Notice" in first["status"] or "CDC" in first["reporting_agency"]
    assert len(first["immediate_actions"]) > 0


def test_match_outbreaks_kerala_nipah():
    """Symptom match for Kerala Nipah Virus Disease."""
    matches = match_outbreaks_for_symptoms(
        symptoms=["high fever", "altered mental status", "myoclonus", "acute encephalitis"],
        geographic_context="patient from Kozhikode Kerala",
    )
    assert len(matches) > 0
    top = matches[0]
    assert "Nipah" in top["disease_name"]
    assert top["state_or_country"] == "Kerala"
    assert top["alert_level"] == "CRITICAL"
    assert "NIV" in top["confirmatory_test"] or "Pune" in top["confirmatory_test"]


def test_match_outbreaks_gujarat_chandipura():
    """Symptom match for Gujarat Chandipura pediatric encephalitis."""
    matches = match_outbreaks_for_symptoms(
        symptoms=["fever", "tonic clonic seizures", "rapid altered sensorium", "vomiting"],
        geographic_context="Sabarkantha Gujarat pediatric patient",
    )
    assert len(matches) > 0
    ch_matches = [m for m in matches if "Chandipura" in m["disease_name"]]
    assert len(ch_matches) > 0
    assert ch_matches[0]["state_or_country"] == "Gujarat"


def test_match_outbreaks_karnataka_kfd():
    """Symptom match for Karnataka Kyasanur Forest Disease."""
    matches = match_outbreaks_for_symptoms(
        symptoms=["sudden high fever", "severe frontal headache", "conjunctival suffusion", "tick bite", "myalgia"],
        geographic_context="Shivamogga Karnataka forest worker",
    )
    assert len(matches) > 0
    kfd_matches = [m for m in matches if "Kyasanur" in m["disease_name"] or "KFD" in m["pathogen"]]
    assert len(kfd_matches) > 0
    assert kfd_matches[0]["state_or_country"] == "Karnataka"


def test_match_outbreaks_odisha_cerebral_malaria():
    """Symptom match for Odisha severe falciparum malaria."""
    matches = match_outbreaks_for_symptoms(
        symptoms=["tertian fever", "chills", "blackwater urine", "jaundice"],
        geographic_context="Rayagada Odisha patient",
    )
    assert len(matches) > 0
    od_matches = [m for m in matches if "Malaria" in m["disease_name"]]
    assert len(od_matches) > 0
    assert od_matches[0]["state_or_country"] == "Odisha"


def test_match_outbreaks_punjab_leptospirosis():
    """Symptom match for Punjab leptospirosis."""
    matches = match_outbreaks_for_symptoms(
        symptoms=["high fever", "conjunctival suffusion", "calf muscle tenderness", "jaundice"],
        geographic_context="Ludhiana Punjab paddy farmer",
    )
    assert len(matches) > 0
    pb_matches = [m for m in matches if "Leptospirosis" in m["disease_name"]]
    assert len(pb_matches) > 0
    assert pb_matches[0]["state_or_country"] == "Punjab"


def test_realtime_prediction_outbreak_integration():
    """Test that realtime_prediction_service tags candidates with outbreak badges and containment directives."""
    result = realtime_prediction_service.predict(
        symptoms="high fever, altered mental status, myoclonus, patient from Kozhikode Kerala with acute encephalitis"
    )
    assert result["status"] == "SUCCESS"
    assert result["outbreak_detected"] is True
    assert len(result["outbreak_matches"]) > 0
    assert result["outbreak_summary"] is not None

    # Top candidate should be Nipah Virus Disease with outbreak tagging
    top_cand = result["top_candidates"][0]
    assert "Nipah" in top_cand["disease"]
    assert top_cand.get("is_outbreak_match") is True
    assert top_cand.get("outbreak_badge") is not None
    assert "Kerala" in top_cand["outbreak_badge"]
    assert top_cand.get("outbreak_details") is not None
    assert "isolation_protocol" in top_cand["outbreak_details"]
