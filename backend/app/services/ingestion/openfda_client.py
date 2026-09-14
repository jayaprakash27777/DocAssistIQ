import httpx
import structlog
from typing import Dict, Any, List, Optional

log = structlog.get_logger(__name__)

class OpenFDAClient:
    """
    Client for interacting with the official OpenFDA API.
    Used for retrieving authoritative, live medication data.
    """
    BASE_URL = "https://api.fda.gov/drug/label.json"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # Setting a higher timeout since FDA payload can be large
        self.timeout = 30.0

    async def fetch_human_prescription_drugs(self, limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Fetches human prescription drug labels from the FDA.
        Returns a list of raw FDA JSON records.
        """
        params = {
            "search": 'openfda.product_type:"HUMAN PRESCRIPTION DRUG"',
            "limit": limit,
            "skip": skip
        }
        if self.api_key:
            params["api_key"] = self.api_key

        log.info("fetching_openfda_data", limit=limit, skip=skip)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.BASE_URL, params=params)  # type: ignore
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except httpx.HTTPStatusError as e:
                log.error("openfda_http_error", status_code=e.response.status_code, response=e.response.text)
                raise
            except Exception as e:
                log.error("openfda_connection_error", error=str(e))
                raise

openfda_client = OpenFDAClient()
