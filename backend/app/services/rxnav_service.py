import httpx
import structlog
from typing import List, Optional

log = structlog.get_logger(__name__)

async def get_rxcui(generic_name: str) -> Optional[str]:
    """
    Resolve a generic medication name to its NIH RxNorm Concept Unique Identifier (RxCUI).
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={generic_name}")
            if resp.status_code == 200:
                data = resp.json()
                id_group = data.get("idGroup", {})
                rxnorm_id = id_group.get("rxnormId")
                if rxnorm_id and len(rxnorm_id) > 0:
                    return rxnorm_id[0]
            return None
    except Exception as e:
        log.error("rxnav_get_rxcui_failed", error=str(e), generic_name=generic_name)
        return None

async def check_interactions(rxcuis: List[str]) -> List[str]:
    """
    Given a list of RxCUIs, ping the NIH Interaction API to find severe interactions.
    Returns a list of overarching high-priority interaction warning descriptions.
    """
    if len(rxcuis) < 2:
        return []

    rxcui_str = "+".join(rxcuis)
    warnings = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={rxcui_str}")
            if resp.status_code == 200:
                data = resp.json()
                
                # Parse interaction data
                if "fullInteractionTypeGroup" in data:
                    for group in data["fullInteractionTypeGroup"]:
                        for interaction_type in group.get("fullInteractionType", []):
                            for interaction_pair in interaction_type.get("interactionPair", []):
                                description = interaction_pair.get("description")
                                if description:
                                    warnings.append(description)
                                    
            return warnings
    except Exception as e:
        log.error("rxnav_check_interactions_failed", error=str(e), rxcuis=rxcuis)
        # We don't want to fail the whole system if the API is down, just return empty or a generic warning
        return []
