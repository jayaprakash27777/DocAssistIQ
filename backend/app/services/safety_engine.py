import uuid
from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Disease
from app.schemas.safety import SafetyDecision, SafetyFlag
from app.schemas.diagnosis import DifferentialDiagnosisItem
from app.schemas.representation import ClinicalRepresentationResponse
from app.services.graph_service import get_disease_knowledge_graph

class SafetyEngine:
    """
    Central deterministic Safety Engine for evaluating AI-generated clinical suggestions.
    VERSION: 1.0.0
    """
    
    VERSION = "1.0.0"

    async def evaluate_differential_item(
        self,
        db: AsyncSession,
        item: DifferentialDiagnosisItem,
        representation: ClinicalRepresentationResponse
    ) -> SafetyDecision:
        """Evaluate a single differential diagnosis candidate."""
        flags: List[SafetyFlag] = []
        
        # 1. Fetch Knowledge Graph for the suggested disease
        stmt = select(Disease).where(Disease.name.ilike(item.disease))
        res = await db.execute(stmt)
        disease = res.scalar_one_or_none()
        
        if not disease:
            # If disease isn't in KB, we have insufficient evidence to declare it safe
            flags.append(SafetyFlag(
                rule_id="SE-001",
                rule_version=self.VERSION,
                category="EVIDENCE_INSUFFICIENCY",
                severity="MEDIUM",
                message=f"Diagnosis '{item.disease}' is not present in the verified knowledge base.",
                source="SafetyEngine"
            ))
        else:
            graph = await get_disease_knowledge_graph(db, disease.id)
            
            # Check Contradictions: High number of contradictions
            if len(item.contradicting_information) > 2:
                flags.append(SafetyFlag(
                    rule_id="SE-002",
                    rule_version=self.VERSION,
                    category="CONTRADICTION",
                    severity="HIGH",
                    message=f"Diagnosis '{item.disease}' is strongly contradicted by {len(item.contradicting_information)} patient negations.",
                    source="SafetyEngine",
                    related_entity=item.disease
                ))
                
            # Check Red Flags: Certain high-risk symptoms not accounted for
            # e.g., Patient has 'severe chest pain' but the diagnosis is 'Gastroenteritis'
            high_risk_symptoms = ["chest pain", "shortness of breath", "sudden weakness", "vision loss", "severe headache"]
            patient_symptoms = [s.value.lower() for s in representation.symptoms]
            
            for hs in high_risk_symptoms:
                if any(hs in ps for ps in patient_symptoms) and not any(hs in es for es in item.supporting_findings):
                    flags.append(SafetyFlag(
                        rule_id="SE-003",
                        rule_version=self.VERSION,
                        category="RED_FLAG",
                        severity="CRITICAL",
                        message=f"High-risk symptom '{hs}' is present but not explained by diagnosis '{item.disease}'.",
                        source="SafetyEngine",
                        related_entity=item.disease
                    ))
            
            # Check Allergies and Contraindications
            patient_allergies = [a.value.lower() for a in representation.allergies]
            medicines = [n for n in graph.nodes if n.node_type == 'medicine']
            
            for med in medicines:
                # Allergy check
                if any(med.name.lower() in pa for pa in patient_allergies):
                    flags.append(SafetyFlag(
                        rule_id="SE-004",
                        rule_version=self.VERSION,
                        category="ALLERGY",
                        severity="CRITICAL",
                        message=f"Standard treatment '{med.name}' for {item.disease} conflicts with patient allergy.",
                        source="SafetyEngine",
                        related_entity=med.name
                    ))
                
                # Contraindication check (mocked by looking at patient conditions)
                patient_conditions = [c.value.lower() for c in representation.chronic_conditions]
                for edge in graph.edges:
                    if edge.relationship == 'contraindicated_for' and edge.source_id == med.id:
                        target_node = next((n for n in graph.nodes if n.id == edge.target_id), None)
                        if target_node and any(target_node.name.lower() in pc for pc in patient_conditions):
                            flags.append(SafetyFlag(
                                rule_id="SE-005",
                                rule_version=self.VERSION,
                                category="CONTRAINDICATION",
                                severity="CRITICAL",
                                message=f"Treatment '{med.name}' is contraindicated for patient condition '{target_node.name}'.",
                                source="SafetyEngine",
                                related_entity=med.name
                            ))

        # Determine overall decision
        decision = "ALLOW"
        if any(f.severity == "CRITICAL" for f in flags):
            decision = "ABSTAIN"
        elif any(f.severity in ["HIGH", "MEDIUM"] for f in flags):
            decision = "WARN"

        return SafetyDecision(decision=decision, flags=flags)

safety_engine = SafetyEngine()
