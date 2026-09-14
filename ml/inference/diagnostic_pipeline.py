"""DocAssistIQ ?" Diagnostic Inference Pipeline (Phase 64).

Loads the calibrated machine learning models and performs inference with strict
abstention thresholds to prevent unsafe diagnoses.
"""

import os
import joblib
from pathlib import Path
from pydantic import BaseModel

class DiagnosisHypothesis(BaseModel):
    condition_code: str
    condition_name: str
    probability: float
    rationale: str
    supporting_evidence: list[str]

class DiagnosticPipeline:
    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold
        
        # Load Calibrated Model
        model_path = Path("ml/experiments/baseline_calibrated_model.joblib")
        if not model_path.exists():
            raise FileNotFoundError(f"Calibrated model not found at {model_path}")
        self.model = joblib.load(model_path)

    def predict(self, text: str) -> DiagnosisHypothesis:
        """
        Predicts diagnosis for a given text.
        If the calibrated probability is below the confidence_threshold, the model abstains.
        """
        # Our base model pipeline automatically vectorizes the raw text
        probs = self.model.predict_proba([text])[0]
        
        best_idx = probs.argmax()
        best_prob = probs[best_idx]
        
        if best_prob < self.confidence_threshold:
            return DiagnosisHypothesis(
                condition_code="ABSTAIN",
                condition_name="Insufficient Clinical Confidence",
                probability=float(best_prob),
                rationale="The model's calibrated confidence is below the safety threshold. A human clinician must review this case.",
                supporting_evidence=[]
            )
            
        condition = self.model.classes_[best_idx]
        
        # In a real system, condition codes would be mapped from a database
        return DiagnosisHypothesis(
            condition_code="PREDICTED",
            condition_name=condition,
            probability=float(best_prob),
            rationale="Model prediction passed confidence thresholds based on statistical patterns in symptoms.",
            supporting_evidence=[]
        )

if __name__ == "__main__":
    print("Initializing Diagnostic Pipeline (Threshold: 0.85)...")
    pipeline = DiagnosticPipeline()
    
    print("\n--- Test Case 1: High Confidence ---")
    test_1 = "Patient presents with severe cough, high fever, chills, and shortness of breath."
    print(f"Input: {test_1}")
    result_1 = pipeline.predict(test_1)
    print(f"Prediction: {result_1.condition_name} (Prob: {result_1.probability:.2f})")
    
    print("\n--- Test Case 2: Noisy/Ambiguous (Testing Abstention) ---")
    test_2 = "Patient presents with mild fatigue, a slight headache, and a scratchy throat but no fever."
    print(f"Input: {test_2}")
    result_2 = pipeline.predict(test_2)
    print(f"Prediction: {result_2.condition_name} (Prob: {result_2.probability:.2f})")
    print(f"Rationale: {result_2.rationale}")
