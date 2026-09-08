from abc import ABC, abstractmethod
from typing import List

from app.schemas.representation import ClinicalRepresentationResponse
from app.schemas.diagnosis import DifferentialDiagnosisResponse, DifferentialDiagnosisItem

class DiagnosisProvider(ABC):
    """Stable interface for diagnosis providers (Phase 34)."""
    @abstractmethod
    async def generate_differential(self, representation: ClinicalRepresentationResponse) -> DifferentialDiagnosisResponse:
        pass


class BaselineDiagnosisProvider(DiagnosisProvider):
    """
    Transparent, baseline differential diagnosis engine (Phase 33).
    Uses a simple weighted overlap algorithm against an internal Knowledge Matrix.
    """
    
    KB = {
        "Asthma": ["cough", "shortness of breath", "wheezing", "chest tightness"],
        "Hypertension": ["headache", "shortness of breath", "nosebleed", "dizziness"],
        "Diabetes Type 2": ["increased thirst", "frequent urination", "increased hunger", "fatigue", "blurred vision"],
        "COPD": ["shortness of breath", "wheezing", "chest tightness", "chronic cough"],
        "Pneumonia": ["cough", "fever", "chills", "shortness of breath", "chest pain"],
        "COVID-19": ["fever", "cough", "fatigue", "loss of taste", "loss of smell", "shortness of breath"],
        "Pulmonary Embolism": ["shortness of breath", "chest pain", "cough", "rapid heart rate"],
        "Migraine": ["headache", "nausea", "sensitivity to light", "sensitivity to sound"],
        "Gastroenteritis": ["nausea", "vomiting", "diarrhea", "abdominal pain", "fever"],
        "Influenza": ["fever", "chills", "muscle aches", "cough", "congestion", "runny nose", "headache", "fatigue"]
    }

    async def generate_differential(self, representation: ClinicalRepresentationResponse) -> DifferentialDiagnosisResponse:
        missing_critical_info = []
        
        if not representation.symptoms:
            missing_critical_info.append("At least one reported symptom is required.")
            
        if not representation.duration:
            missing_critical_info.append("Duration of symptoms is missing.")
            
        if not representation.severity:
            missing_critical_info.append("Severity of symptoms is missing.")
            
        if not representation.symptoms:
            # We absolutely cannot proceed without symptoms
            return DifferentialDiagnosisResponse(
                consultation_id=str(representation.consultation_id),
                status="INSUFFICIENT_INFO",
                message="Insufficient clinical information to generate a safe and meaningful differential diagnosis.",
                missing_critical_info=missing_critical_info,
                provider_metadata={
                    "provider": "BaselineDiagnosisProvider",
                    "version": "1.0"
                },
                top_candidates=[]
            )

        rep_symptoms = set(item.value.lower() for item in representation.symptoms)
        rep_negations = set(item.value.lower() for item in representation.negations)
        
        candidates = []
        
        for disease, expected_symptoms in self.KB.items():
            expected_set = set(s.lower() for s in expected_symptoms)
            
            supporting = list(expected_set.intersection(rep_symptoms))
            missing = list(expected_set - rep_symptoms - rep_negations)
            contradictions = list(expected_set.intersection(rep_negations))
            
            union_len = len(expected_set.union(rep_symptoms))
            if union_len == 0:
                score = 0.0
            else:
                score = len(supporting) / union_len
            
            score -= (len(contradictions) * 0.2)
            
            if score > 0 or len(supporting) > 0:
                explanation = f"Matched {len(supporting)} findings. "
                if contradictions:
                    explanation += f"Penalized for {len(contradictions)} contradictions. "
                
                # Apply uncertainty penalty for missing severity or duration
                uncertainty = "High" if len(supporting) <= 1 else "Moderate" if score < 0.5 else "Low"
                if missing_critical_info:
                    score *= 0.8  # Penalty for missing core info
                    uncertainty = "High"
                    explanation += " Confidence reduced due to missing clinical context (duration/severity)."
                
                candidates.append(DifferentialDiagnosisItem(
                    disease=disease,
                    score=round(score, 3),
                    supporting_findings=supporting,
                    missing_expected_findings=missing,
                    contradicting_information=contradictions,
                    uncertainty=uncertainty,
                    explanation_reference=explanation.strip()
                ))
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        top_5 = candidates[:5]
        
        return DifferentialDiagnosisResponse(
            consultation_id=str(representation.consultation_id),
            status="SUCCESS",
            message=None,
            missing_critical_info=missing_critical_info,
            provider_metadata={
                "provider": "BaselineDiagnosisProvider",
                "version": "1.0",
                "algorithm": "Jaccard-like overlap with contradiction penalty",
                "kb_size": len(self.KB)
            },
            top_candidates=top_5
        )
