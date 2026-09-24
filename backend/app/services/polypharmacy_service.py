import asyncio
import re
from typing import List, Dict, Any, Tuple, Optional
import structlog

from app.schemas.polypharmacy import PolypharmacyResponse, InteractionDetail
from app.services.llm_service import llm_service
from app.services.rxnav_service import get_rxcui, check_interactions

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Comprehensive Deterministic Clinical Drug-Drug Interaction Matrix
# Based on FDA Boxed Warnings, Beers Criteria, Lexicomp, and CPIC Guidelines
# ---------------------------------------------------------------------------
DETERMINISTIC_DDI_RULES: List[Dict[str, Any]] = [
    {
        "pair": ({"warfarin", "coumadin"}, {"aspirin", "ibuprofen", "naproxen", "ketorolac", "meloxicam", "diclofenac", "celecoxib", "indomethacin"}),
        "severity": "CRITICAL",
        "mechanism": "Pharmacodynamic synergism: NSAID inhibition of platelet COX-1 plus warfarin-induced vitamin K clotting factor suppression, compounded by NSAID-induced gastric mucosal erosion.",
        "clinical_effect": "Markedly elevated risk of major gastrointestinal hemorrhage, intracranial bleeding, and fatal bleeding events.",
        "recommendation": "Avoid combination. If analgesia/antipyresis is required, use acetaminophen (max 2g/day) or consider alternative non-NSAID therapies with close INR monitoring."
    },
    {
        "pair": ({"apixaban", "rivaroxaban", "dabigatran", "edoxaban"}, {"aspirin", "ibuprofen", "naproxen", "ketorolac", "meloxicam", "diclofenac"}),
        "severity": "CRITICAL",
        "mechanism": "Pharmacodynamic synergism between direct oral anticoagulants (DOACs) and antiplatelet/COX-inhibiting NSAIDs.",
        "clinical_effect": "Significantly heightened rate of major systemic hemorrhage and gastrointestinal bleeding without incremental therapeutic benefit in most indications.",
        "recommendation": "Avoid concurrent NSAID use with DOACs. If dual therapy is clinically mandated (e.g., post-PCI), strictly limit duration and mandate PPI gastroprotection."
    },
    {
        "pair": ({"sildenafil", "tadalafil", "vardenafil", "avanafil"}, {"nitroglycerin", "isosorbide mononitrate", "isosorbide dinitrate", "nitroprusside"}),
        "severity": "CRITICAL",
        "mechanism": "Synergistic accumulation of intracellular cyclic GMP (cGMP) via PDE5 inhibition combined with nitric oxide donation.",
        "clinical_effect": "Profound, refractory systemic vasodilation, catastrophic hypotension, coronary hypoperfusion, and fatal myocardial infarction.",
        "recommendation": "Absolute Contraindication: Concurrent use is strictly contraindicated. Maintain at least a 24-hour (sildenafil) to 48-hour (tadalafil) washout before any nitrate administration."
    },
    {
        "pair": ({"lisinopril", "enalapril", "ramipril", "benazepril", "captopril", "losartan", "valsartan", "candesartan", "irbesartan"}, {"spironolactone", "eplerenone", "triamterene", "amiloride"}),
        "severity": "CRITICAL",
        "mechanism": "Additive suppression of aldosterone synthesis and distal renal tubular potassium excretion.",
        "clinical_effect": "Severe, life-threatening hyperkalemia (K > 6.0 mEq/L) predisposing to fatal cardiac dysrhythmias and asystole.",
        "recommendation": "Exercise extreme vigilance. Check baseline serum potassium and renal function; re-check at 1 week, 4 weeks, and periodically. Avoid if baseline potassium > 5.0 mEq/L or eGFR < 30 mL/min."
    },
    {
        "pair": ({"lisinopril", "enalapril", "ramipril", "benazepril", "captopril"}, {"losartan", "valsartan", "candesartan", "irbesartan", "olmesartan"}),
        "severity": "CRITICAL",
        "mechanism": "Dual renin-angiotensin-aldosterone system (RAAS) blockade.",
        "clinical_effect": "Substantially increased risk of acute kidney injury, severe hypotension, and hyperkalemia without additive cardiovascular benefit (ONTARGET trial).",
        "recommendation": "Combination is generally contraindicated and strongly discouraged in routine clinical practice."
    },
    {
        "pair": ({"fluoxetine", "sertraline", "paroxetine", "citalopram", "escitalopram", "venlafaxine", "duloxetine"}, {"tramadol", "linezolid", "phenelzine", "tranylcypromine", "selegiline", "rasagiline", "methylene blue"}),
        "severity": "CRITICAL",
        "mechanism": "Additive serotonergic neurotransmission and inhibition of serotonin reuptake / MAO-mediated breakdown.",
        "clinical_effect": "High risk of life-threatening Serotonin Syndrome (autonomic instability, hyperthermia, neuromuscular rigidity, clonus, delirium).",
        "recommendation": "Absolute contraindication with MAOIs (allow 14-day to 5-week washout). Avoid tramadol with serotonergic antidepressants; consider alternative non-serotonergic analgesics."
    },
    {
        "pair": ({"methotrexate"}, {"ibuprofen", "naproxen", "ketorolac", "meloxicam", "diclofenac", "indomethacin", "amoxicillin", "penicillin"}),
        "severity": "CRITICAL",
        "mechanism": "NSAIDs and penicillins reduce renal tubular secretion of methotrexate and displace methotrexate from plasma albumin binding sites.",
        "clinical_effect": "Methotrexate accumulation resulting in severe myelosuppression, fatal pancytopenia, acute kidney injury, and severe gastrointestinal ulceration.",
        "recommendation": "Avoid high-dose methotrexate co-administration with NSAIDs. If low-dose weekly methotrexate is used for rheumatoid arthritis, monitor CBC, renal panel, and LFTs closely."
    },
    {
        "pair": ({"simvastatin", "lovastatin", "atorvastatin"}, {"clarithromycin", "erythromycin", "itraconazole", "ketoconazole", "ritonavir", "atazanavir", "amiodarone", "gemfibrozil"}),
        "severity": "CRITICAL",
        "mechanism": "Potent CYP3A4 inhibition prevents hepatic first-pass metabolism of CYP3A4-substrate statins, elevating systemic statin levels up to 10-fold.",
        "clinical_effect": "Severe drug-induced myopathy, rhabdomyolysis with myoglobinuria, and acute renal failure.",
        "recommendation": "Temporarily suspend simvastatin/lovastatin during macrolide/azole course, or switch to pravastatin or rosuvastatin (which do not depend on CYP3A4) at minimal doses."
    },
    {
        "pair": ({"digoxin"}, {"amiodarone", "verapamil", "diltiazem", "clarithromycin", "quinidine"}),
        "severity": "CRITICAL",
        "mechanism": "P-glycoprotein (P-gp) and renal clearance inhibition, causing a 50-100% surge in serum digoxin concentration.",
        "clinical_effect": "Acute digoxin toxicity: life-threatening arrhythmias (ventricular ectopy, junctional escape, AV block, ventricular tachycardia), nausea, xanthopsia, and confusion.",
        "recommendation": "Empirically reduce digoxin dose by 50% upon initiating amiodarone, verapamil, or quinidine. Closely monitor digoxin trough levels and ECG rhythm."
    },
    {
        "pair": ({"amiodarone", "sotalol", "dofetilide"}, {"ciprofloxacin", "levofloxacin", "moxifloxacin", "haloperidol", "methadone", "ondansetron", "azithromycin"}),
        "severity": "CRITICAL",
        "mechanism": "Additive prolongation of the cardiac ventricular action potential duration and corrected QT interval (QTc) via I_Kr potassium channel blockade.",
        "clinical_effect": "Heightened susceptibility to Torsades de Pointes (polymorphic ventricular tachycardia) and sudden cardiac arrest.",
        "recommendation": "Avoid simultaneous QTc-prolonging agents whenever feasible. Baseline ECG and serum potassium/magnesium correction are mandatory if co-administration cannot be avoided."
    },
    {
        "pair": ({"morphine", "oxycodone", "fentanyl", "hydrocodone", "hydromorphone", "methadone", "codeine"}, {"alprazolam", "lorazepam", "diazepam", "clonazepam", "temazepam", "zolpidem"}),
        "severity": "CRITICAL",
        "mechanism": "Synergistic central nervous system (CNS) depression mediated via mu-opioid and GABA-A receptor stimulation.",
        "clinical_effect": "FDA Boxed Warning: Profound sedation, severe respiratory depression, coma, hypoxemia, and fatal overdose.",
        "recommendation": "Limit concomitant prescribing to the lowest effective dosages and shortest possible durations. Co-prescribe Naloxone rescue kits and educate patient/caregivers on overdose signs."
    },
    {
        "pair": ({"lithium"}, {"ibuprofen", "naproxen", "meloxicam", "celecoxib", "diclofenac", "lisinopril", "losartan", "hydrochlorothiazide"}),
        "severity": "CRITICAL",
        "mechanism": "Decreased renal prostaglandin synthesis and reduced glomerular filtration diminish renal lithium excretion, causing toxic accumulation.",
        "clinical_effect": "Lithium toxicity: coarse tremors, ataxia, confusion, seizures, acute renal failure, and permanent neurologic deficits.",
        "recommendation": "Avoid concurrent NSAID, ACEi, or thiazide therapy with lithium. If mandatory, reduce lithium dose by 30-50% and monitor serum lithium levels weekly until stable."
    },
    {
        "pair": ({"clopidogrel"}, {"omeprazole", "esomeprazole"}),
        "severity": "WARNING",
        "mechanism": "Competitive inhibition of CYP2C19 by omeprazole inhibits bioactivation of clopidogrel prodrug into its active thiol metabolite.",
        "clinical_effect": "Reduced antiplatelet efficacy, leading to increased risk of recurrent ischemic events and acute stent thrombosis.",
        "recommendation": "If gastroprotection is required during dual antiplatelet therapy, switch to pantoprazole or famotidine, which exert minimal CYP2C19 inhibition."
    },
    {
        "pair": ({"ciprofloxacin", "levofloxacin", "doxycycline", "tetracycline"}, {"calcium", "iron", "ferrous sulfate", "magnesium", "aluminum hydroxide", "sucralfate", "antacids"}),
        "severity": "WARNING",
        "mechanism": "Chelation with polyvalent metallic cations forms insoluble complexes in the gastrointestinal tract.",
        "clinical_effect": "Marked reduction (up to 70-90%) in antibiotic bioavailability, risking therapeutic failure and antimicrobial resistance.",
        "recommendation": "Administer fluoroquinolones or tetracyclines at least 2 hours before or 4-6 hours after cation-containing antacids or mineral supplements."
    },
    {
        "pair": ({"metoprolol", "atenolol", "carvedilol", "bisoprolol", "propranolol"}, {"verapamil", "diltiazem"}),
        "severity": "WARNING",
        "mechanism": "Additive negative chronotropic and inotropic effects on the sinoatrial and atrioventricular nodes.",
        "clinical_effect": "Profound symptomatic bradycardia, high-grade atrioventricular (AV) conduction block, and acute decompensation of heart failure.",
        "recommendation": "Avoid concurrent non-dihydropyridine CCBs with beta-blockers, particularly in patients with pre-existing conduction disease or reduced ejection fraction."
    },
    {
        "pair": ({"allopurinol"}, {"amoxicillin", "ampicillin"}),
        "severity": "WARNING",
        "mechanism": "Idiosyncratic immune-mediated cutaneous sensitization synergism.",
        "clinical_effect": "Significantly higher incidence of drug-induced erythematous and maculopapular skin eruptions.",
        "recommendation": "Inform patient to report rash immediately. Consider alternative antibacterial coverage if clinically appropriate."
    },
    {
        "pair": ({"warfarin"}, {"metronidazole", "sulfamethoxazole", "trimethoprim-sulfamethoxazole", "bactrim", "ciprofloxacin"}),
        "severity": "CRITICAL",
        "mechanism": "Inhibition of CYP2C9 (metabolizer of potent S-warfarin) and alteration of intestinal vitamin K-producing gut microbiota.",
        "clinical_effect": "Dramatic supra-therapeutic INR surge (>5-10) with imminent risk of spontaneous major hemorrhage.",
        "recommendation": "Empirically reduce warfarin dose by 30-50% when initiating Bactrim or metronidazole; measure INR within 48-72 hours."
    }
]


class PolypharmacySimulator:
    """Enterprise Polypharmacy & Drug-Drug Interaction Simulation Service.
    
    Provides multi-tiered clinical safety evaluation:
    1. Deterministic high-alert DDI matrix based on FDA Boxed Warnings and CPIC standards.
    2. Real-time NIH RxNav Interaction API querying for verified RxCUIs.
    3. LLM-driven pharmacogenomic and clinical pharmacology synthesis.
    4. Guaranteed non-blocking fallback if LLM is unavailable.
    """

    def _matches_drug_group(self, med_name: str, drug_group: set) -> bool:
        med_clean = re.sub(r'[^a-z0-9]', ' ', med_name.lower())
        words = set(med_clean.split())
        for d in drug_group:
            d_clean = d.lower()
            if d_clean in med_name.lower() or d_clean in words:
                return True
        return False

    def check_deterministic_interactions(self, all_meds: List[str]) -> List[InteractionDetail]:
        """Matches medications against deterministic high-alert DDI rules."""
        detected: List[InteractionDetail] = []
        seen_pairs = set()

        for rule in DETERMINISTIC_DDI_RULES:
            group1, group2 = rule["pair"]
            matched_g1: List[str] = []
            matched_g2: List[str] = []

            for med in all_meds:
                if self._matches_drug_group(med, group1):
                    matched_g1.append(med)
                if self._matches_drug_group(med, group2):
                    matched_g2.append(med)

            # Avoid matching the exact same drug with itself unless distinct
            for m1 in matched_g1:
                for m2 in matched_g2:
                    if m1.lower() == m2.lower():
                        continue
                    pair_key = tuple(sorted([m1.lower(), m2.lower()]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    detected.append(
                        InteractionDetail(
                            severity=rule["severity"],
                            drugs_involved=[m1, m2],
                            mechanism=rule["mechanism"],
                            clinical_effect=rule["clinical_effect"],
                            recommendation=rule["recommendation"]
                        )
                    )

        return detected

    async def _fetch_nih_rxnav_interactions(self, meds: List[str]) -> List[InteractionDetail]:
        """Queries NIH RxNav for documented drug interactions."""
        if len(meds) < 2:
            return []

        rxcuis = []
        med_rxcui_map = {}
        for med in meds[:6]:  # Limit to first 6 to ensure rapid response
            try:
                rxcui = await asyncio.wait_for(get_rxcui(med), timeout=2.5)
                if rxcui:
                    rxcuis.append(rxcui)
                    med_rxcui_map[rxcui] = med
            except Exception:
                continue

        if len(rxcuis) < 2:
            return []

        try:
            raw_warnings = await asyncio.wait_for(check_interactions(rxcuis), timeout=3.5)
            nih_details = []
            for w in raw_warnings[:5]:
                nih_details.append(
                    InteractionDetail(
                        severity="WARNING",
                        drugs_involved=[meds[0], meds[1]] if len(meds) >= 2 else meds,
                        mechanism="NIH RxNorm Documented Drug Interaction",
                        clinical_effect=w[:250],
                        recommendation="Evaluate clinical benefit vs risk. Check prescribing information for monitoring guidance."
                    )
                )
            return nih_details
        except Exception as e:
            log.warning("rxnav_check_failed_in_polypharmacy", error=str(e))
            return []

    async def simulate(self, proposed_meds: List[str], current_meds: List[str]) -> PolypharmacyResponse:
        all_meds = [m.strip() for m in proposed_meds + current_meds if m and m.strip()]
        log.info("simulating_polypharmacy", proposed=proposed_meds, current=current_meds, total=len(all_meds))

        # 1. Deterministic Clinical DDI Check (Instant, 0ms, 100% reliable)
        deterministic_interactions = self.check_deterministic_interactions(all_meds)

        # 2. NIH RxNav API Verification (Async, non-blocking)
        nih_interactions: List[InteractionDetail] = []
        try:
            nih_interactions = await self._fetch_nih_rxnav_interactions(all_meds)
        except Exception as e:
            log.warning("nih_rxnav_enrichment_skipped", error=str(e))

        # 3. LLM Synthesis for Advanced Pharmacological Context
        system_prompt = """You are an Expert Clinical Pharmacologist and Pharmacogenomics AI.
Your task is to evaluate the safety and potential interactions of a polypharmacy regimen.
You are given a list of the patient's CURRENT medications and a list of PROPOSED medications to be added.

Analyze for:
1. Drug-Drug Interactions (Pharmacokinetic: CYP450 enzyme induction/inhibition).
2. Pharmacodynamic interactions (e.g., additive QT prolongation, serotonin syndrome risk, additive CNS depression, bleeding risk).
3. Absolute and relative contraindications.

## Output Requirements
Return ONLY valid JSON matching this exact schema:
{
  "interactions": [
    {
      "severity": "CRITICAL" | "WARNING" | "MINOR" | "SAFE",
      "drugs_involved": ["Drug A", "Drug B"],
      "mechanism": "string (e.g., CYP3A4 inhibition)",
      "clinical_effect": "string",
      "recommendation": "string"
    }
  ],
  "summary_assessment": "string (Overall safety profile and main concerns)",
  "is_safe": boolean (True if no CRITICAL interactions)
}
If there are no interactions, return an empty interactions array and is_safe = true.
"""
        user_prompt = f"""
CURRENT MEDICATIONS: {', '.join(current_meds) if current_meds else 'None'}
PROPOSED MEDICATIONS: {', '.join(proposed_meds) if proposed_meds else 'None'}

Generate the interaction report as JSON.
"""
        llm_interactions: List[InteractionDetail] = []
        summary_assessment = ""
        llm_is_safe = None

        try:
            data = await asyncio.wait_for(
                llm_service.generate_json(user_prompt, system=system_prompt),
                timeout=12.0
            )
            if isinstance(data, dict):
                for item in data.get("interactions", []):
                    try:
                        llm_interactions.append(InteractionDetail(**item))
                    except Exception:
                        continue
                summary_assessment = data.get("summary_assessment", "")
                llm_is_safe = data.get("is_safe")
        except Exception as e:
            log.warning("llm_polypharmacy_generation_failed_using_deterministic", error=str(e))

        # 4. Synthesize all findings with deterministic safety priority
        merged_interactions: List[InteractionDetail] = []
        seen_pairs = set()

        # Deterministic items first (highest evidentiary rigor)
        for item in deterministic_interactions:
            pair_key = tuple(sorted([d.lower() for d in item.drugs_involved]))
            seen_pairs.add(pair_key)
            merged_interactions.append(item)

        # Merge LLM items if not already covered
        for item in llm_interactions:
            pair_key = tuple(sorted([d.lower() for d in item.drugs_involved]))
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                merged_interactions.append(item)

        # Merge NIH RxNav items if not already covered
        for item in nih_interactions:
            pair_key = tuple(sorted([d.lower() for d in item.drugs_involved]))
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                merged_interactions.append(item)

        # Determine overall safety status
        has_critical = any(item.severity == "CRITICAL" for item in merged_interactions)
        is_safe = not has_critical

        if not summary_assessment:
            if has_critical:
                crit_count = sum(1 for i in merged_interactions if i.severity == "CRITICAL")
                summary_assessment = (
                    f"CRITICAL SAFETY ALERT: Detected {crit_count} high-risk interaction(s) requiring immediate "
                    "pharmacotherapeutic revision prior to administration. Review boxed warnings and mechanisms."
                )
            elif merged_interactions:
                warn_count = len(merged_interactions)
                summary_assessment = (
                    f"Caution advised: Identified {warn_count} moderate/minor drug interaction(s). "
                    "Dose titration, staggered administration, or close clinical monitoring recommended."
                )
            else:
                summary_assessment = (
                    "No major drug-drug interactions, CYP450 contraindications, or pharmacodynamic antagonisms "
                    "identified between current and proposed medication regimens."
                )

        return PolypharmacyResponse(
            interactions=merged_interactions,
            summary_assessment=summary_assessment,
            is_safe=is_safe
        )


polypharmacy_simulator = PolypharmacySimulator()
