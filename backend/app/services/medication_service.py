from app.schemas.medication import MedicationResponse, MedicationSuggestion

class MedicationProvider:
    """
    Provides clinician-facing reference intelligence for medications based on disease (Phase 45).
    This serves strictly as reference intelligence and NOT as an automated order system.
    """

    KB = {
        "Asthma": [
            MedicationSuggestion(
                generic_name="Albuterol (Salbutamol)",
                indication="Acute bronchospasm in asthma",
                formulation="Metered-dose inhaler (MDI) or nebulizer solution",
                route="Inhalation",
                standard_reference_dosing="Adults: 2 puffs every 4 to 6 hours as needed. (Reference only, not an order)",
                contraindications=["Hypersensitivity to albuterol"],
                interactions=["Beta-blockers (may antagonize effect)", "MAO inhibitors"],
                allergy_considerations="Unavailable",
                renal_considerations="No specific dosage adjustment recommended in labeling",
                hepatic_considerations="No specific dosage adjustment recommended in labeling",
                pregnancy_lactation_considerations="Pregnancy Category C; use if potential benefit justifies potential risk.",
                age_considerations="Pediatric dosing varies by age and weight.",
                monitoring_reference_information="Monitor heart rate, blood pressure, pulmonary function tests.",
                source_evidence="GINA Guidelines, FDA Label"
            ),
            MedicationSuggestion(
                generic_name="Fluticasone Propionate",
                indication="Maintenance treatment of asthma as prophylactic therapy",
                formulation="Inhalation aerosol or powder",
                route="Inhalation",
                standard_reference_dosing="Adults: 88 to 440 mcg twice daily, depending on severity. (Reference only)",
                contraindications=["Primary treatment of status asthmaticus"],
                interactions=["Strong CYP3A4 inhibitors (e.g., ritonavir, ketoconazole)"],
                allergy_considerations="Hypersensitivity to milk proteins (for powder formulation)",
                renal_considerations="Unavailable",
                hepatic_considerations="Use with caution in severe hepatic impairment",
                pregnancy_lactation_considerations="Use during pregnancy only if the potential benefit justifies the potential risk.",
                age_considerations="Approved for pediatric use depending on formulation and age.",
                monitoring_reference_information="Monitor for signs of thrush; evaluate growth in pediatric patients.",
                source_evidence="GINA Guidelines, FDA Label"
            )
        ],
        "Pneumonia": [
            MedicationSuggestion(
                generic_name="Amoxicillin",
                indication="Community-acquired pneumonia (typical, outpatient)",
                formulation="Tablet, Capsule, Oral Suspension",
                route="Oral",
                standard_reference_dosing="Adults: 1 gram 3 times a day. (Reference only, dependent on guidelines)",
                contraindications=["History of severe hypersensitivity to penicillins"],
                interactions=["Probenecid", "Oral contraceptives"],
                allergy_considerations="Cross-reactivity possible in cephalosporin-allergic patients.",
                renal_considerations="Dose adjustment required for CrCl < 30 mL/min.",
                hepatic_considerations="Unavailable",
                pregnancy_lactation_considerations="Generally considered safe in pregnancy.",
                age_considerations="Pediatric dosing is weight-based (e.g., 90 mg/kg/day).",
                monitoring_reference_information="Renal, hepatic, and hematopoietic function with prolonged use.",
                source_evidence="IDSA/ATS 2019"
            ),
            MedicationSuggestion(
                generic_name="Azithromycin",
                indication="Atypical pneumonia or in combination therapy",
                formulation="Tablet, Oral Suspension, IV",
                route="Oral, IV",
                standard_reference_dosing="Adults: 500 mg day 1, then 250 mg daily for 4 days. (Reference only)",
                contraindications=["History of cholestatic jaundice/hepatic dysfunction associated with prior use"],
                interactions=["Antacids", "Warfarin", "QT prolonging agents"],
                allergy_considerations="Macrolide allergy",
                renal_considerations="Use with caution in severe renal impairment.",
                hepatic_considerations="Use with caution in severe hepatic impairment.",
                pregnancy_lactation_considerations="Generally considered acceptable.",
                age_considerations="Weight-based for pediatrics.",
                monitoring_reference_information="ECG if at risk for prolonged QT interval.",
                source_evidence="IDSA/ATS 2019"
            )
        ],
        "COVID-19": [
            MedicationSuggestion(
                generic_name="Nirmatrelvir/Ritonavir",
                indication="Mild-to-moderate COVID-19 in patients at high risk for progression",
                formulation="Tablet co-packaged",
                route="Oral",
                standard_reference_dosing="300 mg nirmatrelvir / 100 mg ritonavir twice daily for 5 days. (Reference only)",
                contraindications=["Coadministration with highly dependent CYP3A clearance drugs", "Severe hepatic impairment"],
                interactions=["Extensive CYP3A interactions (check specific drug lists)"],
                allergy_considerations="Unavailable",
                renal_considerations="Dose reduction required for moderate renal impairment (eGFR 30 to <60 mL/min). Not recommended if eGFR <30 mL/min.",
                hepatic_considerations="Not recommended in severe hepatic impairment.",
                pregnancy_lactation_considerations="Limited data; use if benefit outweighs risk.",
                age_considerations="Authorized for patients 12 years and older weighing at least 40 kg.",
                monitoring_reference_information="Monitor for adverse drug interactions.",
                source_evidence="NIH COVID-19 Treatment Guidelines"
            )
        ]
    }

    def get_medications(self, disease_name: str) -> MedicationResponse:
        """
        Returns reference medications for the specified disease.
        """
        # Case-insensitive matching
        key_matches = [k for k in self.KB.keys() if k.lower() == disease_name.lower()]
        suggestions = self.KB[key_matches[0]] if key_matches else []
        
        return MedicationResponse(
            disease=disease_name,
            suggestions=suggestions
        )

medication_provider = MedicationProvider()
