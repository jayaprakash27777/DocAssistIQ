import uuid
from typing import List, Literal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Disease
from app.models.patient_profile import PatientProfile
from app.schemas.safety import SafetyDecision, SafetyFlag
from app.schemas.diagnosis import DifferentialDiagnosisItem
from app.schemas.medication import MedicationSuggestion
from app.schemas.representation import ClinicalRepresentationResponse
from app.services.graph_service import get_disease_knowledge_graph
from app.services.red_flag_rules import RED_FLAG_RULES

class SafetyEngine:
    """
    Central deterministic Safety Engine for evaluating AI-generated clinical suggestions.
    VERSION: 1.0.0
    """
    
    VERSION = "1.0.0"

    async def evaluate_clinical_representation(
        self,
        representation: ClinicalRepresentationResponse
    ) -> SafetyDecision:
        """
        Evaluate the entire clinical representation against Red Flag rules.
        Does not require a database connection.
        """
        flags: List[SafetyFlag] = []
        
        for rule in RED_FLAG_RULES:
            flag = rule.evaluator(representation)
            if flag:
                flags.append(flag)
                
        decision: Literal["ALLOW", "WARN", "ABSTAIN"] = "ALLOW"
        if any(f.severity == "CRITICAL" for f in flags):
            decision = "ABSTAIN"
        elif any(f.severity in ["HIGH", "MEDIUM"] for f in flags):
            decision = "WARN"

        return SafetyDecision(decision=decision, flags=flags)

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
                
                # Graph-based contraindication traversal against patient clinical history
                patient_conditions = [c.value.lower() for c in representation.history]

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
        decision: Literal["ALLOW", "WARN", "ABSTAIN"] = "ALLOW"
        if any(f.severity == "CRITICAL" for f in flags):
            decision = "ABSTAIN"
        elif any(f.severity in ["HIGH", "MEDIUM"] for f in flags):
            decision = "WARN"

        return SafetyDecision(decision=decision, flags=flags)

    async def evaluate_medication(
        self,
        suggestion: MedicationSuggestion,
        representation: ClinicalRepresentationResponse,
        patient_profile: PatientProfile | None = None
    ) -> SafetyDecision:
        """Evaluate a medication suggestion against the patient's clinical representation and structured profile."""
        flags: List[SafetyFlag] = []
        med_name = suggestion.generic_name.lower()

        # 1. Allergy Check
        patient_allergies = [a.value.lower() for a in representation.allergies]
        if any(med_name in pa or pa in med_name for pa in patient_allergies):
            flags.append(SafetyFlag(
                rule_id="SE-MED-001",
                rule_version=self.VERSION,
                category="ALLERGY",
                severity="CRITICAL",
                message=f"Medication '{suggestion.generic_name}' directly conflicts with patient allergy.",
                source="SafetyEngine",
                related_entity=suggestion.generic_name
            ))

        # 2. Duplicate Therapy Check
        patient_meds = [m.value.lower() for m in representation.medications]
        
        # Merge structured medications from profile if available
        if patient_profile and isinstance(patient_profile.baseline_conditions, dict):
            structured_meds = patient_profile.baseline_conditions.get("current_medications", [])
            for m in structured_meds:
                if isinstance(m, str) and m.lower() not in patient_meds:
                    patient_meds.append(m.lower())
                    
        if any(med_name in pm or pm in med_name for pm in patient_meds):
            flags.append(SafetyFlag(
                rule_id="SE-MED-002",
                rule_version=self.VERSION,
                category="RED_FLAG",
                severity="MEDIUM",
                message=f"Patient is already taking '{suggestion.generic_name}' or a similar medication.",
                source="SafetyEngine",
                related_entity=suggestion.generic_name
            ))

        # 3. Drug-Drug Interaction Check (Deterministic High-Alert DDI Matrix + Panel Rules)
        try:
            from app.services.polypharmacy_service import polypharmacy_simulator
            active_ddis = polypharmacy_simulator.check_deterministic_interactions([suggestion.generic_name] + patient_meds)
            for ddi in active_ddis:
                flags.append(SafetyFlag(
                    rule_id="SE-MED-DDI-001",
                    rule_version=self.VERSION,
                    category="DRUG_INTERACTION",
                    severity="CRITICAL" if ddi.severity == "CRITICAL" else "HIGH",
                    message=f"Interaction Alert [{', '.join(ddi.drugs_involved)}]: {ddi.mechanism} - {ddi.clinical_effect}",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))
        except Exception:
            pass

        for interaction in suggestion.interactions:
            interaction_lower = interaction.lower()
            if any(pm in interaction_lower for pm in patient_meds):
                flags.append(SafetyFlag(
                    rule_id="SE-MED-003",
                    rule_version=self.VERSION,
                    category="DRUG_INTERACTION",
                    severity="HIGH",
                    message=f"Potential interaction between '{suggestion.generic_name}' and patient's current medication: {interaction}",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))

        # 4. Drug-Disease Contraindication
        patient_conditions = [c.value.lower() for c in representation.history]
        for contra in suggestion.contraindications:
            contra_lower = contra.lower()
            if any(pc in contra_lower for pc in patient_conditions):
                flags.append(SafetyFlag(
                    rule_id="SE-MED-004",
                    rule_version=self.VERSION,
                    category="CONTRAINDICATION",
                    severity="CRITICAL",
                    message=f"Medication '{suggestion.generic_name}' is contraindicated due to patient history.",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))

        # 5. Structured Context Checks (Renal, Hepatic, Pregnancy, Age)
        is_pregnant = False
        has_renal_impairment = False
        has_hepatic_impairment = False
        age_group = None

        if patient_profile and isinstance(patient_profile.baseline_conditions, dict):
            bc = patient_profile.baseline_conditions
            is_pregnant = bool(bc.get("pregnancy", False))
            has_renal_impairment = bool(bc.get("renal_impairment", False)) or bool(bc.get("ckd", False))
            has_hepatic_impairment = bool(bc.get("hepatic_impairment", False)) or bool(bc.get("liver_disease", False))
            age_group = patient_profile.age_group

        # Fallback to representation text if no structured profile
        demographics = (representation.patient_context.demographics or "").lower()
        if not is_pregnant and ("pregnant" in demographics or "pregnancy" in demographics):
            is_pregnant = True

        # Pregnancy Check
        if is_pregnant:
            if "contraindicated" in suggestion.pregnancy_lactation_considerations.lower():
                flags.append(SafetyFlag(
                    rule_id="SE-MED-005",
                    rule_version=self.VERSION,
                    category="CONTRAINDICATION",
                    severity="CRITICAL",
                    message=f"Medication '{suggestion.generic_name}' is contraindicated in pregnancy.",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))
            elif "warning" in suggestion.pregnancy_lactation_considerations.lower() or "caution" in suggestion.pregnancy_lactation_considerations.lower():
                flags.append(SafetyFlag(
                    rule_id="SE-MED-006",
                    rule_version=self.VERSION,
                    category="RED_FLAG",
                    severity="MEDIUM",
                    message=f"Pregnancy consideration: {suggestion.pregnancy_lactation_considerations}",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))

        # Renal Check
        if has_renal_impairment:
            if "contraindicated" in suggestion.renal_considerations.lower():
                flags.append(SafetyFlag(
                    rule_id="SE-MED-007",
                    rule_version=self.VERSION,
                    category="CONTRAINDICATION",
                    severity="CRITICAL",
                    message=f"Medication '{suggestion.generic_name}' is contraindicated in renal impairment.",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))
            elif "adjust" in suggestion.renal_considerations.lower() or "warning" in suggestion.renal_considerations.lower():
                flags.append(SafetyFlag(
                    rule_id="SE-MED-008",
                    rule_version=self.VERSION,
                    category="RED_FLAG",
                    severity="MEDIUM",
                    message=f"Renal adjustment may be required: {suggestion.renal_considerations}",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))

        # Hepatic Check
        if has_hepatic_impairment:
            if "contraindicated" in suggestion.hepatic_considerations.lower():
                flags.append(SafetyFlag(
                    rule_id="SE-MED-009",
                    rule_version=self.VERSION,
                    category="CONTRAINDICATION",
                    severity="CRITICAL",
                    message=f"Medication '{suggestion.generic_name}' is contraindicated in hepatic impairment.",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))
            elif "adjust" in suggestion.hepatic_considerations.lower() or "warning" in suggestion.hepatic_considerations.lower():
                flags.append(SafetyFlag(
                    rule_id="SE-MED-010",
                    rule_version=self.VERSION,
                    category="RED_FLAG",
                    severity="MEDIUM",
                    message=f"Hepatic adjustment may be required: {suggestion.hepatic_considerations}",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))

        # Age Check (Pediatric/Geriatric)
        if age_group:
            age_lower = age_group.lower()
            if ("months" in age_lower or "child" in age_lower) and "contraindicated in pediatric" in suggestion.age_considerations.lower():
                flags.append(SafetyFlag(
                    rule_id="SE-MED-011",
                    rule_version=self.VERSION,
                    category="CONTRAINDICATION",
                    severity="CRITICAL",
                    message=f"Medication '{suggestion.generic_name}' is contraindicated in pediatric patients.",
                    source="SafetyEngine",
                    related_entity=suggestion.generic_name
                ))
            elif ("65" in age_lower or "70" in age_lower or "80" in age_lower) and "geriatric" in suggestion.age_considerations.lower():
                if "contraindicated" in suggestion.age_considerations.lower():
                     flags.append(SafetyFlag(
                        rule_id="SE-MED-012",
                        rule_version=self.VERSION,
                        category="CONTRAINDICATION",
                        severity="CRITICAL",
                        message=f"Medication '{suggestion.generic_name}' is contraindicated in geriatric patients.",
                        source="SafetyEngine",
                        related_entity=suggestion.generic_name
                    ))
                else:
                    flags.append(SafetyFlag(
                        rule_id="SE-MED-013",
                        rule_version=self.VERSION,
                        category="RED_FLAG",
                        severity="MEDIUM",
                        message=f"Geriatric consideration: {suggestion.age_considerations}",
                        source="SafetyEngine",
                        related_entity=suggestion.generic_name
                    ))

        # Determine overall decision
        decision: Literal["ALLOW", "WARN", "ABSTAIN"] = "ALLOW"
        if any(f.severity == "CRITICAL" for f in flags):
            decision = "ABSTAIN"
        elif any(f.severity in ["HIGH", "MEDIUM", "WARN"] for f in flags):
            decision = "WARN"

        return SafetyDecision(decision=decision, flags=flags)

safety_engine = SafetyEngine()
