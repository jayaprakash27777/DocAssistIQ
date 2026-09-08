from app.schemas.investigation import InvestigationResponse, InvestigationSuggestion

class InvestigationProvider:
    """
    Provides clinician-facing reference intelligence for investigations based on disease (Phase 44).
    This serves strictly as reference intelligence and NOT as an automated order system.
    """

    KB = {
        "Asthma": [
            InvestigationSuggestion(
                name="Spirometry",
                priority="HIGH PRIORITY",
                rationale="To establish the diagnosis of asthma by demonstrating reversible airflow obstruction.",
                relevant_clinical_finding="Wheezing, shortness of breath",
                evidence="GINA Guidelines: Spirometry is the preferred method for diagnosing asthma.",
                limitations="Patient cooperation required; normal spirometry does not rule out asthma.",
                safety_flags=[],
                provenance="GINA 2023"
            ),
            InvestigationSuggestion(
                name="Chest X-Ray",
                priority="IF INDICATED",
                rationale="To rule out alternative diagnoses such as infection or foreign body if atypical features are present.",
                relevant_clinical_finding="Fever, asymmetric breath sounds",
                evidence="Routine CXR is not indicated for typical asthma presentations.",
                limitations="Radiation exposure; low diagnostic yield for typical asthma.",
                safety_flags=["Radiation Exposure"],
                provenance="NICE Asthma Guidelines"
            )
        ],
        "Pneumonia": [
            InvestigationSuggestion(
                name="Chest X-Ray (PA and Lateral)",
                priority="HIGH PRIORITY",
                rationale="To confirm the presence of an infiltrate confirming clinical suspicion of pneumonia.",
                relevant_clinical_finding="Fever, cough, crackles on auscultation",
                evidence="IDSA/ATS Guidelines recommend CXR for all patients with suspected pneumonia.",
                limitations="May be falsely negative early in the course of the disease or in dehydrated patients.",
                safety_flags=["Radiation Exposure"],
                provenance="IDSA/ATS 2019"
            ),
            InvestigationSuggestion(
                name="Sputum Culture and Gram Stain",
                priority="CONDITIONAL",
                rationale="To identify the causative organism and guide targeted antibiotic therapy.",
                relevant_clinical_finding="Productive cough with purulent sputum in severe inpatient settings",
                evidence="Recommended for severe inpatient CAP or if empirically treating for MRSA/Pseudomonas.",
                limitations="High rate of contamination with oral flora; frequently fails to identify a pathogen.",
                safety_flags=[],
                provenance="IDSA/ATS 2019"
            )
        ],
        "COVID-19": [
            InvestigationSuggestion(
                name="SARS-CoV-2 NAAT (PCR)",
                priority="HIGH PRIORITY",
                rationale="To confirm acute infection.",
                relevant_clinical_finding="Loss of smell, fever, fatigue",
                evidence="Gold standard for confirming diagnosis per WHO guidelines.",
                limitations="False negatives can occur depending on viral load and timing of test.",
                safety_flags=[],
                provenance="WHO 2023"
            )
        ]
    }

    def get_investigations(self, disease_name: str) -> InvestigationResponse:
        """
        Returns reference investigations for the specified disease.
        """
        # Case-insensitive matching
        key_matches = [k for k in self.KB.keys() if k.lower() == disease_name.lower()]
        suggestions = self.KB[key_matches[0]] if key_matches else []
        
        return InvestigationResponse(
            disease=disease_name,
            suggestions=suggestions
        )

investigation_provider = InvestigationProvider()
