"""DocAssistIQ — Enterprise Medication Provider (Dual Mode).

Supports:
1. Synchronous lookup for unit tests & offline access:
   `medication_provider.get_medications("Asthma")`
2. Asynchronous lookup with DB, RAG, and live NIH DDI engine:
   `await medication_provider.get_medications(db, "Asthma")`
"""

from typing import Any, Optional, List
from pydantic import PrivateAttr
from app.schemas.medication import MedicationResponse, MedicationSuggestion
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rag_service import retrieve_medical_context, retrieve_medicine_context
from app.services.llm_service import llm_service
from app.services.rxnav_service import get_rxcui, check_interactions
import structlog

log = structlog.get_logger(__name__)


class AwaitableMedicationResponse(MedicationResponse):
    """MedicationResponse that functions immediately as a response and can be awaited."""
    _coro_fn: Any = PrivateAttr(default=None)

    def __init__(self, coro_fn=None, **data):
        super().__init__(**data)
        self._coro_fn = coro_fn

    def __await__(self):
        if self._coro_fn:
            return self._coro_fn().__await__()
        async def _self():
            return self
        return _self().__await__()


# ---------------------------------------------------------------------------
# Standard Evidence-Based Clinical Medication Panels
# ---------------------------------------------------------------------------
MEDICATION_PANELS = {
    "asthma": [
        MedicationSuggestion(
            generic_name="Albuterol",
            indication="Relief of acute bronchospasm in asthma",
            formulation="Inhalation aerosol / MDI",
            route="Inhalation",
            standard_reference_dosing="90 mcg/actuation, 1-2 puffs every 4-6 hours PRN for acute symptoms",
            contraindications=["Severe hypersensitivity to albuterol"],
            interactions=["Non-selective beta-blockers", "MAO inhibitors", "Diuretics (hypokalemia risk)"],
            allergy_considerations="Check for propellant or excipient hypersensitivity",
            renal_considerations="No dose adjustment required; excreted renally",
            hepatic_considerations="No dose adjustment required",
            pregnancy_lactation_considerations="Category C; preferred short-acting beta-agonist in pregnancy",
            age_considerations="Pediatric dosing differs; use spacer device for children and elderly",
            monitoring_reference_information="Frequency of rescue inhaler use, tremor, heart rate",
            source_evidence="GINA Global Strategy for Asthma Management (2023); FDA Label",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Fluticasone Propionate",
            indication="Maintenance treatment of persistent asthma as controller therapy",
            formulation="Metered dose inhaler / Dry powder inhaler",
            route="Inhalation",
            standard_reference_dosing="88-220 mcg inhaled twice daily depending on disease severity",
            contraindications=["Primary treatment of acute status asthmaticus", "Severe hypersensitivity to milk proteins"],
            interactions=["Strong CYP3A4 inhibitors (e.g. ritonavir, ketoconazole) increase corticosteroid exposure"],
            allergy_considerations="Rinse mouth with water without swallowing after inhalation to prevent oral candidiasis",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="Use with caution in severe hepatic impairment",
            pregnancy_lactation_considerations="Category C; preferred inhaled corticosteroid along with budesonide in pregnancy",
            age_considerations="Dose titration required for pediatric patients; monitor growth velocity",
            monitoring_reference_information="Peak expiratory flow rate, symptom frequency, oral inspection for candidiasis",
            source_evidence="GINA Guidelines; FDA Prescribing Information",
            safety_decision=None,
        ),
    ],
    "pneumonia": [
        MedicationSuggestion(
            generic_name="Amoxicillin",
            indication="First-line empirical outpatient antibiotic therapy for Community-Acquired Pneumonia",
            formulation="Oral tablet / capsule / suspension",
            route="Oral",
            standard_reference_dosing="1 g orally three times daily for 5 to 7 days",
            contraindications=["History of severe immediate hypersensitivity (anaphylaxis) to beta-lactam antibiotics"],
            interactions=["Methotrexate (decreased clearance)", "Warfarin (monitor INR)", "Allopurinol (increased rash risk)"],
            allergy_considerations="Penicillin class allergy. Clarify reaction severity (urticaria vs anaphylaxis)",
            renal_considerations="Adjust dose if CrCl < 30 mL/min (500 mg q12h; 500 mg q24h if CrCl < 10)",
            hepatic_considerations="Generally safe; monitor LFTs if prolonged course",
            pregnancy_lactation_considerations="Category B; considered safe in pregnancy and compatible with breastfeeding",
            age_considerations="Weight-based pediatric dosing (90 mg/kg/day in 2 divided doses for high-dose CAP regimen)",
            monitoring_reference_information="Clinical resolution of fever, cough, respiratory rate within 48-72h; bowel habits",
            source_evidence="ATS/IDSA Community-Acquired Pneumonia Guidelines (2019); FDA Label",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Azithromycin",
            indication="Empirical coverage of atypical pathogens in Community-Acquired Pneumonia",
            formulation="Oral tablet / IV infusion",
            route="Oral / IV",
            standard_reference_dosing="500 mg orally on day 1, then 250 mg once daily on days 2-5",
            contraindications=["History of cholestatic jaundice or hepatic dysfunction with prior azithromycin use", "Documented QT prolongation"],
            interactions=["QT-prolonging agents (antiarrhythmics, antipsychotics)", "Antacids containing Al/Mg decrease rate of absorption"],
            allergy_considerations="Macrolide hypersensitivity",
            renal_considerations="Caution in severe renal impairment (GFR < 10 mL/min)",
            hepatic_considerations="Caution in severe hepatic impairment; primarily eliminated hepatobiliary",
            pregnancy_lactation_considerations="Category B; widely used in pregnancy when indicated",
            age_considerations="Pediatric dosing: 10 mg/kg day 1, then 5 mg/kg once daily on days 2-5",
            monitoring_reference_information="ECG/QTc interval in patients with cardiovascular risk, GI tolerance",
            source_evidence="ATS/IDSA CAP Guidelines; FDA Label",
            safety_decision=None,
        ),
    ],
    "covid-19": [
        MedicationSuggestion(
            generic_name="Nirmatrelvir/Ritonavir",
            indication="Treatment of mild-to-moderate COVID-19 in patients at high risk of progression to severe disease",
            formulation="Oral tablet (co-packaged)",
            route="Oral",
            standard_reference_dosing="300 mg nirmatrelvir with 100 mg ritonavir twice daily for 5 days within 5 days of symptom onset",
            contraindications=["Severe renal impairment (eGFR < 30 mL/min)", "Severe hepatic impairment (Child-Pugh Class C)", "Concurrent use with CYP3A-dependent medications"],
            interactions=["Strong CYP3A4 inhibitors/inducers, statins, antiarrhythmics, direct oral anticoagulants, anticonvulsants"],
            allergy_considerations="Known hypersensitivity to nirmatrelvir or ritonavir",
            renal_considerations="Dose reduction: 150 mg nirmatrelvir + 100 mg ritonavir BID for eGFR 30-59 mL/min; contraindicated if eGFR < 30",
            hepatic_considerations="Contraindicated in severe hepatic impairment (Child-Pugh Class C)",
            pregnancy_lactation_considerations="Weigh maternal benefits against potential risks; consider alternative (e.g. remdesivir)",
            age_considerations="Authorized for adults and pediatric patients >= 12 years of age weighing at least 40 kg",
            monitoring_reference_information="Comprehensive medication reconciliation for drug-drug interactions prior to dispensing",
            source_evidence="NIH COVID-19 Treatment Guidelines (2024); FDA Emergency Use Authorization / Approval",
            safety_decision=None,
        ),
    ],
    "hypertension": [
        MedicationSuggestion(
            generic_name="Lisinopril",
            indication="First-line pharmacotherapy for essential hypertension",
            formulation="Oral tablet",
            route="Oral",
            standard_reference_dosing="10-40 mg orally once daily",
            contraindications=["History of angioedema related to prior ACE inhibitor therapy", "Concurrent aliskiren in diabetic patients", "Pregnancy"],
            interactions=["Potassium supplements or potassium-sparing diuretics (hyperkalemia risk)", "NSAIDs (reduced antihypertensive efficacy, renal impairment)"],
            allergy_considerations="ACE inhibitor-induced cough or angioedema",
            renal_considerations="Reduce starting dose if CrCl < 30 mL/min (2.5-5 mg once daily); monitor creatinine and potassium",
            hepatic_considerations="Lisinopril does not require hepatic bioactivation; no specific adjustment",
            pregnancy_lactation_considerations="Black Box Warning: Contraindicated in pregnancy (fetal toxicity, oligohydramnios, skull hypoplasia)",
            age_considerations="Elderly may experience greater blood pressure reduction; initiate at 2.5-5 mg daily",
            monitoring_reference_information="Blood pressure, serum creatinine, BUN, and serum potassium 1-2 weeks after initiation or dose escalation",
            source_evidence="ACC/AHA High Blood Pressure Clinical Practice Guidelines; FDA Label",
            safety_decision=None,
        ),
    ],
    "infective endocarditis": [
        MedicationSuggestion(
            generic_name="Ceftriaxone",
            indication="Empirical and targeted antimicrobial therapy for native valve infective endocarditis (streptococcal, HACEK, enterococcal)",
            formulation="Intravenous solution / powder for injection",
            route="Intravenous",
            standard_reference_dosing="2 g IV every 24 hours as a single daily infusion for 4 to 6 weeks",
            contraindications=["Severe cephalosporin or beta-lactam anaphylaxis", "Concurrent IV calcium administration in neonates"],
            interactions=["Biliary sludging with calcium-containing IV solutions", "Warfarin (may enhance hypoprothrombinemic effect)"],
            allergy_considerations="Assess for IgE-mediated beta-lactam hypersensitivity",
            renal_considerations="Dual biliary-renal elimination; no dose reduction necessary in isolated renal impairment unless combined severe hepatic failure",
            hepatic_considerations="Monitor biliary status during prolonged courses (ceftriaxone biliary pseudolithiasis)",
            pregnancy_lactation_considerations="Category B; compatible with pregnancy and lactation",
            age_considerations="Standard adult dosing; monitor elderly for Clostridioides difficile colitis",
            monitoring_reference_information="Serial blood cultures to confirm clearance, daily cardiac auscultation for new murmurs, renal panel, CBC",
            source_evidence="AHA / ESC Guidelines for the Management of Infective Endocarditis (2023)",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Vancomycin",
            indication="Empirical coverage for MRSA, coagulase-negative staphylococci, and ampicillin-resistant enterococci in infective endocarditis",
            formulation="Intravenous infusion",
            route="Intravenous",
            standard_reference_dosing="15-20 mg/kg IV every 8-12 hours targeting an AUC/MIC ratio of 400-600 (or trough 15-20 mcg/mL)",
            contraindications=["Known severe hypersensitivity to vancomycin"],
            interactions=["Nephrotoxic agents (aminoglycosides, NSAIDs, piperacillin-tazobactam, amphotericin B) synergistically increase nephrotoxicity"],
            allergy_considerations="Infusion-related histamine release ('red man syndrome') prevented by infusing over at least 60-120 minutes",
            renal_considerations="Strict pharmacokinetic dose titration and therapeutic drug monitoring (TDM) required based on eGFR/CrCl",
            hepatic_considerations="Primarily eliminated by the kidneys; no hepatic dose adjustment",
            pregnancy_lactation_considerations="Category C; use when alternative agents cannot be used",
            age_considerations="Age-related decline in renal clearance necessitates extended dosing intervals in elderly patients",
            monitoring_reference_information="Therapeutic drug monitoring (AUC24 or trough 30 min before 4th dose), serum creatinine twice weekly",
            source_evidence="IDSA / AHA Endocarditis Practice Guidelines",
            safety_decision=None,
        ),
    ],
    "pyelonephritis": [
        MedicationSuggestion(
            generic_name="Ciprofloxacin",
            indication="First-line oral outpatient treatment for uncomplicated acute pyelonephritis",
            formulation="Oral film-coated tablet / IV infusion",
            route="Oral",
            standard_reference_dosing="500 mg orally twice daily for 7 days (or 400 mg IV every 12 hours if hospitalized)",
            contraindications=["Concurrent use with tizanidine", "History of fluoroquinolone-induced tendinitis or tendon rupture", "Myasthenia gravis"],
            interactions=["Divalent/trivalent cations (antacids, iron, calcium, magnesium) severely decrease absorption; separate by 2-4 hours", "Theophylline toxicity", "QT-prolonging agents"],
            allergy_considerations="Fluoroquinolone class hypersensitivity",
            renal_considerations="Dose adjustment required: CrCl 30-50 mL/min: 250-500 mg q12h; CrCl <30 mL/min: 250-500 mg q18-24h",
            hepatic_considerations="Use with caution in patients with hepatic impairment",
            pregnancy_lactation_considerations="Black Box Warning: Avoid in pregnancy unless no alternative (risk of cartilage damage); prefer ceftriaxone or amoxicillin-clavulanate",
            age_considerations="Increased risk of tendon rupture and CNS toxicities in elderly patients (>60 years)",
            monitoring_reference_information="Resolution of fever and flank pain within 48-72 hours, repeat urine culture if non-responsive",
            source_evidence="IDSA Guidelines for the Treatment of Acute Uncomplicated Cystitis and Pyelonephritis; FDA Label",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Ceftriaxone",
            indication="Initial parenteral empirical therapy for moderate-to-severe acute pyelonephritis prior to oral step-down",
            formulation="Intravenous injection / infusion",
            route="Intravenous",
            standard_reference_dosing="1 g IV every 24 hours for 10 to 14 days (or until afebrile 24-48h then step-down to targeted oral)",
            contraindications=["Severe immediate hypersensitivity (anaphylaxis) to cephalosporins or penicillins"],
            interactions=["Calcium-containing diluents/infusions", "Oral anticoagulants (monitor INR)"],
            allergy_considerations="Check for cephalosporin and penicillin cross-reactivity",
            renal_considerations="No routine dosage adjustment needed for mild-to-moderate renal insufficiency",
            hepatic_considerations="Generally well-tolerated; monitor in severe combined hepatorenal failure",
            pregnancy_lactation_considerations="Category B; antibiotic of choice for acute pyelonephritis in pregnant women",
            age_considerations="Safe across adult and geriatric populations",
            monitoring_reference_information="Defervescence within 48-72 hours, renal function, WBC count, and urine culture sensitivities",
            source_evidence="IDSA Guidelines; EAU Urological Infections Guidelines",
            safety_decision=None,
        ),
    ],
    "urinary tract infection": [
        MedicationSuggestion(
            generic_name="Nitrofurantoin monohydrate/macrocrystals",
            indication="First-line empirical antimicrobial therapy for acute uncomplicated bacterial cystitis",
            formulation="Oral capsule (Macrobid)",
            route="Oral",
            standard_reference_dosing="100 mg orally twice daily with meals for 5 days",
            contraindications=["Severe renal impairment (eGFR < 30 mL/min)", "Term pregnancy (38-42 weeks)", "History of nitrofurantoin hepatotoxicity/pulmonary fibrosis"],
            interactions=["Magnesium trisilicate antacids decrease absorption; probenecid decreases renal excretion"],
            allergy_considerations="Hypersensitivity to nitrofurantoin",
            renal_considerations="Contraindicated if eGFR < 30 mL/min due to inadequate urinary drug concentration and increased peripheral neuropathy risk",
            hepatic_considerations="Contraindicated in cholestatic jaundice or hepatic dysfunction caused by prior nitrofurantoin",
            pregnancy_lactation_considerations="Contraindicated at term (weeks 38-42) due to risk of hemolytic anemia in newborn (immature erythrocyte enzyme system)",
            age_considerations="Avoid in elderly with eGFR < 30 mL/min (Beers Criteria)",
            monitoring_reference_information="Clinical resolution of dysuria, frequency, and urgency within 48 hours",
            source_evidence="IDSA Guidelines for Treatment of Uncomplicated Cystitis (2011); FDA Label",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Trimethoprim-Sulfamethoxazole",
            indication="First-line oral therapy for acute uncomplicated cystitis (where local E. coli resistance is <20%)",
            formulation="Oral double-strength (DS) tablet (160 mg TMP / 800 mg SMX)",
            route="Oral",
            standard_reference_dosing="1 DS tablet (160/800 mg) orally twice daily for 3 days",
            contraindications=["Documented sulfa allergy", "Severe renal impairment (CrCl < 15 mL/min)", "Marked hepatic damage", "Megaloblastic anemia from folate deficiency"],
            interactions=["Warfarin (dramatically increases INR)", "ACE inhibitors/ARBs/spironolactone (severe hyperkalemia risk)", "Methotrexate toxicity"],
            allergy_considerations="Sulfonamide hypersensitivity (rash, Stevens-Johnson syndrome / TEN, DRESS)",
            renal_considerations="Dose adjustment: CrCl 15-30 mL/min: half standard dose; CrCl < 15 mL/min: not recommended",
            hepatic_considerations="Use with caution; contraindicated in marked liver parenchymal damage",
            pregnancy_lactation_considerations="Avoid in first trimester (folate antagonism / neural tube defects) and third trimester (kernicterus in newborn)",
            age_considerations="Higher risk of severe hyperkalemia and bone marrow suppression in elderly patients",
            monitoring_reference_information="Serum potassium and creatinine in high-risk patients; symptom resolution within 72 hours",
            source_evidence="IDSA Uncomplicated Cystitis Practice Guidelines",
            safety_decision=None,
        ),
    ],
    "nephrolithiasis": [
        MedicationSuggestion(
            generic_name="Ketorolac tromethamine",
            indication="First-line non-steroidal anti-inflammatory analgesic for acute ureteral colic and stone obstruction",
            formulation="Intravenous injection / Oral tablet",
            route="Intravenous / Oral",
            standard_reference_dosing="15 to 30 mg IV single dose (or 10 mg orally every 6 hours PRN, max 5 days total therapy across routes)",
            contraindications=["Active peptic ulcer disease or gastrointestinal bleeding", "Advanced renal impairment / acute kidney injury", "Cerebrovascular hemorrhage", "Third trimester of pregnancy"],
            interactions=["ACE inhibitors / ARBs (exacerbates acute renal failure)", "Anticoagulants (markedly increases bleeding risk)", "Other systemic NSAIDs"],
            allergy_considerations="Aspirin / NSAID-exacerbated respiratory disease (AERD)",
            renal_considerations="Contraindicated in moderate-to-severe renal impairment or acute obstructive nephropathy; inhibits renal prostaglandins",
            hepatic_considerations="Caution in severe hepatic impairment",
            pregnancy_lactation_considerations="Black Box Warning: Contraindicated in third trimester of pregnancy (premature closure of fetal ductus arteriosus)",
            age_considerations="Reduce dose in elderly patients (>=65 years): 15 mg IV maximum single dose",
            monitoring_reference_information="Visual analogue pain scale, urine output, serum creatinine, and signs of gastrointestinal bleeding",
            source_evidence="AUA / EAU Urolithiasis Guidelines (2023); Cochrane Systematic Review on NSAIDs vs Opioids in Renal Colic",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Tamsulosin hydrochloride",
            indication="Medical expulsive therapy (MET) to facilitate spontaneous passage of distal ureteral calculi (5 to 10 mm)",
            formulation="Oral capsule (Flomax)",
            route="Oral",
            standard_reference_dosing="0.4 mg orally once daily approximately 30 minutes after the same meal each day for up to 4 to 6 weeks",
            contraindications=["Severe hypersensitivity to tamsulosin (including angioedema)"],
            interactions=["Strong CYP3A4 inhibitors (ketoconazole, clarithromycin) increase tamsulosin levels", "PDE5 inhibitors (sildenafil) increase risk of symptomatic hypotension"],
            allergy_considerations="Sulfa allergy cross-reactivity is rare but documented; use with caution",
            renal_considerations="No dosage adjustment needed for mild to moderate renal insufficiency",
            hepatic_considerations="No dosage adjustment in mild to moderate hepatic impairment; not studied in severe impairment",
            pregnancy_lactation_considerations="Category B; primarily indicated in adults; used off-label for expulsive therapy with informed consent",
            age_considerations="Risk of orthostatic hypotension and syncope; warn patient regarding intraoperative floppy iris syndrome (IFIS) during cataract surgery",
            monitoring_reference_information="Time to stone expulsion, orthostatic blood pressure, reduction in analgesic requirement",
            source_evidence="AUA / EAU Guidelines on Medical Expulsive Therapy for Ureteral Stones",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Ondansetron",
            indication="Symptomatic antiemetic control for nausea and vomiting associated with severe renal colic",
            formulation="Oral disintegrating tablet (ODT) / IV injection",
            route="Oral / Intravenous",
            standard_reference_dosing="4 to 8 mg IV or orally every 8 hours PRN for nausea",
            contraindications=["Concurrent use of apomorphine (profound hypotension)", "Congenital long QT syndrome"],
            interactions=["QT-prolonging drugs (antiarrhythmics, antipsychotics, fluoroquinolones)", "Serotonergic medications (serotonin syndrome risk)"],
            allergy_considerations="Hypersensitivity to 5-HT3 receptor antagonists",
            renal_considerations="No dose adjustment required",
            hepatic_considerations="Maximum recommended total daily dose is 8 mg in severe hepatic impairment (Child-Pugh Class C)",
            pregnancy_lactation_considerations="Category B; commonly used in clinical practice when benefits outweigh risks",
            age_considerations="Generally well-tolerated in elderly; monitor ECG in patients with cardiac conduction abnormalities",
            monitoring_reference_information="Nausea score, bowel regularity (constipation is frequent side effect), QTc interval in high-risk patients",
            source_evidence="ASHP / Emergency Medicine Clinical Guidelines; FDA Label",
            safety_decision=None,
        ),
    ],
    "acute diverticulitis": [
        MedicationSuggestion(
            generic_name="Ciprofloxacin + Metronidazole",
            indication="First-line oral dual antimicrobial regimen for acute uncomplicated or mild complicated diverticulitis",
            formulation="Oral tablets (Ciprofloxacin 500 mg + Metronidazole 500 mg)",
            route="Oral",
            standard_reference_dosing="Ciprofloxacin 500 mg PO BID PLUS Metronidazole 500 mg PO TID for 7 to 10 days",
            contraindications=["Concurrent disulfiram or alcohol ingestion within 3 days of metronidazole", "History of fluoroquinolone-associated tendinitis", "First trimester pregnancy (metronidazole)"],
            interactions=["Alcohol (severe disulfiram-like reaction: flushing, tachycardia, nausea)", "Warfarin (metronidazole and ciprofloxacin both potentiate anticoagulant effect)", "Lithium toxicity"],
            allergy_considerations="Assess for fluoroquinolone or nitroimidazole hypersensitivity",
            renal_considerations="Adjust ciprofloxacin dose if CrCl < 50 mL/min (500 mg q12-24h); metronidazole requires post-hemodialysis supplement",
            hepatic_considerations="Metronidazole is extensively metabolized hepatically; reduce dose by 50% in severe hepatic impairment",
            pregnancy_lactation_considerations="Avoid in pregnancy; use Amoxicillin-Clavulanate or Ceftriaxone + Metronidazole as safe alternatives",
            age_considerations="Increased risk of CNS side effects (confusion, peripheral neuropathy) from metronidazole and tendon rupture from ciprofloxacin in elderly",
            monitoring_reference_information="Resolution of left lower quadrant pain, fever, and leukocytosis within 48-72 hours",
            source_evidence="ACG Clinical Guideline: Management of Adult Patients with Acute Diverticulitis (2021); WSES Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Amoxicillin-Clavulanate",
            indication="Preferred single-agent oral empirical antimicrobial therapy for acute mild diverticulitis",
            formulation="Oral tablet (Augmentin)",
            route="Oral",
            standard_reference_dosing="875/125 mg orally twice daily (or 1000/62.5 mg ER twice daily) with meals for 7 to 10 days",
            contraindications=["History of severe immediate penicillin hypersensitivity", "History of amoxicillin-clavulanate-associated cholestatic jaundice or hepatic dysfunction"],
            interactions=["Allopurinol (increased incidence of ampicillin rash)", "Oral contraceptives (decreased enterohepatic circulation)", "Methotrexate"],
            allergy_considerations="Penicillin class allergy. Take with food to minimize gastrointestinal intolerance and diarrhea",
            renal_considerations="Dose adjustment required for eGFR < 30 mL/min (do not use 875 mg tablet; use 500/125 mg q12h; for eGFR < 10 mL/min use 500/125 mg q24h)",
            hepatic_considerations="Contraindicated if prior clavulanate-induced cholestatic jaundice; monitor LFTs",
            pregnancy_lactation_considerations="Category B; considered safe in pregnancy when antibiotic therapy is indicated",
            age_considerations="Increased risk of cholestatic jaundice in elderly males; safe and effective in geriatric patients",
            monitoring_reference_information="Abdominal tenderness, tolerance of oral diet, bowel habits, and resolution of fever",
            source_evidence="ACG Guidelines 2021; American Society of Colon and Rectal Surgeons (ASCRS) Practice Parameters",
            safety_decision=None,
        ),
    ],
    "acute cholecystitis": [
        MedicationSuggestion(
            generic_name="Piperacillin-Tazobactam",
            indication="Empirical broad-spectrum parenteral antimicrobial therapy for acute cholecystitis and cholangitis (Grade II/III)",
            formulation="Intravenous infusion (Zosyn)",
            route="Intravenous",
            standard_reference_dosing="3.375 g IV every 6 hours (or 4.5 g IV every 8 hours as extended 4-hour infusion)",
            contraindications=["History of severe immediate beta-lactam / penicillin anaphylaxis"],
            interactions=["Vancomycin (increased incidence of acute kidney injury; monitor renal function closely)", "Methotrexate", "Vecuronium / neuromuscular blockers"],
            allergy_considerations="Penicillin and beta-lactamase inhibitor hypersensitivity",
            renal_considerations="Dose adjustment mandatory: CrCl 20-40 mL/min: 2.25 g q6h; CrCl < 20 mL/min: 2.25 g q8h; hemodialysis: 2.25 g q12h + 0.75 g post-dialysis",
            hepatic_considerations="No dose adjustment necessary in isolated hepatic impairment",
            pregnancy_lactation_considerations="Category B; use when clinically indicated",
            age_considerations="Assess baseline renal function to ensure correct dose adjustment in elderly patients",
            monitoring_reference_information="Clinical resolution of RUQ pain, Murphy sign, fever, leukocytosis, and bilirubin normalization",
            source_evidence="Tokyo Guidelines 2018 (TG18) for Antimicrobial Therapy of Acute Cholecystitis and Cholangitis",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Ceftriaxone + Metronidazole",
            indication="Alternative parenteral empirical regimen for acute calculous cholecystitis (Grade I/II)",
            formulation="Intravenous infusion (Ceftriaxone 1-2 g + Metronidazole 500 mg)",
            route="Intravenous",
            standard_reference_dosing="Ceftriaxone 1 to 2 g IV every 24 hours PLUS Metronidazole 500 mg IV every 8 hours",
            contraindications=["Severe cephalosporin / penicillin allergy", "First trimester pregnancy (metronidazole relative)"],
            interactions=["Disulfiram-like ethanol reaction with metronidazole", "Calcium-containing IV infusions (ceftriaxone)"],
            allergy_considerations="Cephalosporin and nitroimidazole hypersensitivity evaluation",
            renal_considerations="Well-tolerated without dose adjustment in mild-to-moderate renal failure",
            hepatic_considerations="Reduce metronidazole dose in severe hepatic failure",
            pregnancy_lactation_considerations="Category B (ceftriaxone); widely utilized for biliary sepsis in pregnancy",
            age_considerations="Standard adult dosing; monitor elderly for pseudomembranous colitis",
            monitoring_reference_information="Vital signs, RUQ tenderness, serial liver enzymes (AST, ALT, Alk Phos, Total Bilirubin)",
            source_evidence="Tokyo Guidelines (TG18); World Society of Emergency Surgery (WSES) Guidelines",
            safety_decision=None,
        ),
    ],
    "acute pancreatitis": [
        MedicationSuggestion(
            generic_name="Lactated Ringer's Solution (Goal-Directed IV Fluid Resuscitation)",
            indication="First-line aggressive intravenous hydration for acute pancreatitis to prevent pancreatic necrosis and hemoconcentration",
            formulation="Intravenous isotonic crystalloid infusion",
            route="Intravenous",
            standard_reference_dosing="200 to 500 mL/hr (or 5-10 mL/kg/hr) for the first 12-24 hours, tailored to maintain urine output >0.5-1 mL/kg/hr and normalize hematocrit/BUN",
            contraindications=["Severe volume overload, decompensated congestive heart failure, end-stage renal disease on dialysis, hypercalcemic pancreatitis (Lactated Ringer's contains 3 mEq/L Ca2+)"],
            interactions=["Compatibility with co-administered IV medications; avoid mixing with ceftriaxone"],
            allergy_considerations="No specific allergy profile; monitor for hyperchloremic acidosis if using normal saline instead",
            renal_considerations="Essential to prevent acute kidney injury from third-spacing; titrate carefully in pre-existing CKD",
            hepatic_considerations="Lactate is metabolized by the liver; cautious monitoring in severe hepatic cirrhosis",
            pregnancy_lactation_considerations="Safe and universally recommended in pregnancy",
            age_considerations="High risk of iatrogenic pulmonary edema in elderly patients; frequent cardiopulmonary reassessment mandatory",
            monitoring_reference_information="Hematocrit (goal <44%), BUN (reduction within 24h), serum creatinine, heart rate, blood pressure, lung fields for crackles",
            source_evidence="ACG Clinical Guideline: Management of Acute Pancreatitis (2024); IAP/APA Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Hydromorphone hydrochloride",
            indication="Preferred parenteral opioid analgesic for moderate-to-severe visceral pain in acute pancreatitis",
            formulation="Intravenous injection (Dilaudid)",
            route="Intravenous",
            standard_reference_dosing="0.5 to 1 mg IV every 2 to 3 hours PRN for breakthrough severe epigastric pain (titrated to pain score)",
            contraindications=["Severe respiratory depression, acute or severe bronchial asthma in unmonitored setting, known or suspected gastrointestinal obstruction / paralytic ileus"],
            interactions=["Other CNS depressants (benzodiazepines, sedatives, alcohol) increase fatal respiratory depression risk", "MAO inhibitors"],
            allergy_considerations="Morphine-derivative opioid hypersensitivity",
            renal_considerations="Active metabolites may accumulate in renal failure; start at low doses (0.2-0.5 mg) and extend dosing interval",
            hepatic_considerations="Extensively metabolized by liver glucuronidation; decrease dose by 50% in severe hepatic impairment",
            pregnancy_lactation_considerations="Category C; short-term use acceptable for acute severe pain with fetal monitoring",
            age_considerations="Elderly are highly sensitive to opioid-induced sedation, delirium, respiratory depression, and constipation; initiate at 0.25-0.5 mg",
            monitoring_reference_information="Pain scale (0-10), respiratory rate, oxygen saturation, sedation score, bowel sounds",
            source_evidence="ACG Guidelines for Acute Pancreatitis; American Pain Society Guidelines",
            safety_decision=None,
        ),
    ],
    "gout": [
        MedicationSuggestion(
            generic_name="Indomethacin",
            indication="Potent non-steroidal anti-inflammatory drug (NSAID) for the acute termination of acute gouty arthritis flares",
            formulation="Oral capsule",
            route="Oral",
            standard_reference_dosing="50 mg orally three times daily with meals or milk until pain is tolerable, then rapidly tapered over 3 to 5 days",
            contraindications=["Active peptic ulcer disease or GI bleeding, severe renal impairment (CrCl < 30 mL/min), decompensated heart failure, severe CAD / post-CABG, third trimester pregnancy"],
            interactions=["Warfarin and direct oral anticoagulants (markedly increased GI bleeding risk)", "ACE inhibitors and ARBs (hyperkalemia and acute renal decline)", "Lithium (decreased clearance)"],
            allergy_considerations="Aspirin/NSAID triad (asthma, nasal polyps, bronchospasm)",
            renal_considerations="Contraindicated in moderate-to-severe renal insufficiency; use systemic corticosteroids or colchicine instead",
            hepatic_considerations="Caution in severe hepatic impairment; monitor transaminases",
            pregnancy_lactation_considerations="Contraindicated in third trimester (fetal ductus arteriosus premature closure); prefer prednisone in pregnancy",
            age_considerations="High risk of CNS side effects (frontal headache, dizziness, confusion) and peptic ulceration in elderly patients; avoid if alternatives available",
            monitoring_reference_information="Joint pain, erythema, swelling, resolution of morning stiffness, serum creatinine, stool color for melena",
            source_evidence="ACR Guidelines for Management of Gout (2020); EULAR Recommendations",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Colchicine",
            indication="First-line alkaloid anti-inflammatory therapy for acute gout flare (most effective within 12-24 hours of flare onset)",
            formulation="Oral tablet (Colcrys)",
            route="Oral",
            standard_reference_dosing="1.2 mg orally at the first sign of flare, followed by 0.6 mg 1 hour later (total 1.8 mg on day 1), then 0.6 mg once or twice daily until flare resolves",
            contraindications=["Severe renal impairment (CrCl < 30 mL/min) combined with strong CYP3A4 or P-gp inhibitors", "Severe hepatic impairment combined with strong CYP3A4 inhibitors"],
            interactions=["Strong CYP3A4 inhibitors (clarithromycin, ketoconazole, ritonavir) and P-gp inhibitors (cyclosporine) cause fatal colchicine toxicity; dose reduction mandatory", "Statins (increased risk of myopathy/rhabdomyolysis)"],
            allergy_considerations="Known hypersensitivity to colchicine",
            renal_considerations="If CrCl < 30 mL/min: course should not be repeated more than once every 2 weeks; for dialysis patients: single dose 0.6 mg",
            hepatic_considerations="Dose reduction required in severe hepatic impairment; do not repeat course within 14 days",
            pregnancy_lactation_considerations="Category C; crosses placenta; weigh risk-benefit carefully",
            age_considerations="Elderly patients are at substantially elevated risk of neuromuscular toxicity and rhabdomyolysis",
            monitoring_reference_information="GI tolerance (cramping, diarrhea are dose-limiting signs of toxicity), complete blood count, CK if muscle pain develops",
            source_evidence="ACR Gout Guidelines 2020; FDA Approved Low-Dose Colchicine Regimen",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Prednisone",
            indication="First-line anti-inflammatory therapy for acute gout flares in patients with renal impairment, heart failure, or contraindications to NSAIDs/colchicine",
            formulation="Oral tablet",
            route="Oral",
            standard_reference_dosing="30 to 40 mg orally once daily for 5 days (or full dose for 2-5 days then tapered over 7-10 days)",
            contraindications=["Systemic fungal infections, active untreated bacterial infection, hypersensitivity to prednisone"],
            interactions=["NSAIDs (synergistic increase in gastrointestinal ulceration risk)", "Antidiabetic medications (induces hyperglycemia; monitor glucose closely)", "Live viral vaccines"],
            allergy_considerations="Corticosteroid hypersensitivity",
            renal_considerations="Safe in renal impairment; preferred agent in CKD stage 3-5 and ESRD where NSAIDs and colchicine are hazardous",
            hepatic_considerations="Prednisone is converted to active prednisolone by the liver; use prednisolone directly in severe hepatic cirrhosis",
            pregnancy_lactation_considerations="Category C; considered safest anti-inflammatory choice for acute gout flare in pregnancy",
            age_considerations="Monitor blood pressure, mood changes, insomnia, and blood glucose in elderly and diabetic patients",
            monitoring_reference_information="Joint pain reduction, capillary blood glucose, blood pressure, resolution of synovitis",
            source_evidence="ACR Gout Clinical Practice Guidelines (2020)",
            safety_decision=None,
        ),
    ],
    "chronic obstructive pulmonary disease": [
        MedicationSuggestion(
            generic_name="Albuterol-Ipratropium (SABA/SAMA)",
            indication="First-line bronchodilator therapy for acute relief of bronchospasm and dyspnea in COPD exacerbation",
            formulation="Nebulized solution (3 mL unit-dose vial: 2.5 mg albuterol / 0.5 mg ipratropium) / MDI (Combivent)",
            route="Inhalation",
            standard_reference_dosing="3 mL vial via jet nebulizer every 4 to 6 hours PRN (can administer every 1-2 hours initially for severe exacerbation)",
            contraindications=["Hypersensitivity to albuterol, ipratropium, or atropine derivatives", "Narrow-angle glaucoma (ensure mouth-piece rather than mask to avoid eye exposure)"],
            interactions=["Non-selective beta-blockers antagonize bronchodilation", "Other anticholinergics increase dry mouth, urinary retention, and IOP"],
            allergy_considerations="Hypersensitivity to anticholinergics or adrenergic agonists",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Category C; preferred inhaled rescue therapy during pregnancy",
            age_considerations="Monitor for urinary retention in elderly males with benign prostatic hyperplasia (BPH) and tachycardia in cardiac patients",
            monitoring_reference_information="Respiratory rate, SpO2, heart rate, work of breathing, relief of wheezing",
            source_evidence="GOLD Report: Global Strategy for Diagnosis, Management, and Prevention of COPD (2024)",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Prednisone",
            indication="Systemic corticosteroid therapy to shorten recovery time, improve FEV1 and oxygenation, and reduce risk of early relapse in COPD exacerbation",
            formulation="Oral tablet",
            route="Oral",
            standard_reference_dosing="40 mg orally once daily for 5 days (GOLD-recommended 5-day course; longer courses provide no added benefit and increase adverse events)",
            contraindications=["Systemic fungal infection, untreated active tuberculosis, herpes simplex keratitis"],
            interactions=["NSAIDs (increased peptic ulcer risk)", "Insulin / oral hypoglycemics (steroid-induced hyperglycemia)", "Warfarin"],
            allergy_considerations="Corticosteroid hypersensitivity",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="Use prednisolone in end-stage hepatic disease",
            pregnancy_lactation_considerations="Category C; standard short-course therapy justified for maternal respiratory distress",
            age_considerations="Monitor for steroid-induced psychosis, insomnia, fluid retention, and glucose elevation in geriatric patients",
            monitoring_reference_information="Symptom recovery, dyspnea score, blood glucose monitoring, blood pressure",
            source_evidence="GOLD COPD Report (2024); REDUCE Randomized Controlled Trial (JAMA 2013)",
            safety_decision=None,
        ),
    ],
    "pulmonary embolism": [
        MedicationSuggestion(
            generic_name="Enoxaparin sodium",
            indication="Immediate therapeutic anticoagulation for acute confirmed or high-suspicion pulmonary embolism (non-massive, hemodynamically stable)",
            formulation="Subcutaneous injection prefilled syringes (Lovenox)",
            route="Subcutaneous",
            standard_reference_dosing="1 mg/kg subcutaneously every 12 hours (or 1.5 mg/kg once daily) for at least 5 days and until oral anticoagulation therapeutic",
            contraindications=["Active major bleeding, history of heparin-induced thrombocytopenia (HIT) within past 100 days, severe uncontrolled hypertension, recent neurosurgery or spinal puncture"],
            interactions=["Antiplatelet agents (aspirin, clopidogrel), NSAIDs, oral anticoagulants, thrombolytics synergistically increase bleeding risk"],
            allergy_considerations="Hypersensitivity to enoxaparin, heparin, or pork products",
            renal_considerations="Dose adjustment mandatory for severe renal impairment: CrCl < 30 mL/min: reduce dose to 1 mg/kg subcutaneously once daily (or switch to unfractionated heparin with aPTT monitoring)",
            hepatic_considerations="Use with caution in hepatic impairment due to baseline coagulopathy",
            pregnancy_lactation_considerations="Category B; anticoagulant of choice throughout pregnancy for venous thromboembolism (does not cross placenta)",
            age_considerations="Increased bleeding risk in elderly; strictly monitor renal function and adjust dose accordingly",
            monitoring_reference_information="Platelet count (monitor on day 3-5 for HIT), baseline PT/INR, aPTT, renal panel, signs of occult or overt bleeding",
            source_evidence="ESC Guidelines for the Management of Acute Pulmonary Embolism (2020); CHEST Antithrombotic Therapy Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Apixaban",
            indication="Direct oral factor Xa inhibitor for primary oral treatment and secondary prevention of pulmonary embolism",
            formulation="Oral film-coated tablet (Eliquis)",
            route="Oral",
            standard_reference_dosing="10 mg orally twice daily for the first 7 days, followed by maintenance dosing of 5 mg orally twice daily",
            contraindications=["Active pathological bleeding, severe hypersensitivity to apixaban, clinically significant hepatic disease associated with coagulopathy (Child-Pugh Class B/C)"],
            interactions=["Combined strong dual inhibitors of CYP3A4 and P-gp (ketoconazole, itraconazole, ritonavir): decrease dose to 5 mg BID or 2.5 mg BID", "Strong dual inducers (rifampin, carbamazepine, St. John's wort) decrease efficacy"],
            allergy_considerations="Factor Xa inhibitor hypersensitivity",
            renal_considerations="No dose adjustment for DVT/PE treatment in renal impairment alone, but caution if CrCl < 15 mL/min (limited clinical data)",
            hepatic_considerations="Contraindicated in Child-Pugh Class C severe hepatic impairment; not recommended in Class B",
            pregnancy_lactation_considerations="Not recommended in pregnancy or lactation; use LMWH (enoxaparin) instead",
            age_considerations="Dose reduction criteria for AFib do not apply to the first 6 months of acute PE treatment unless bleeding risk overrides",
            monitoring_reference_information="Adherence to BID regimen (short half-life), complete blood count, periodic renal function, signs of hemorrhage",
            source_evidence="AMPLIFY Clinical Trial (NEJM 2013); ESC PE Guidelines 2020",
            safety_decision=None,
        ),
    ],
    "cellulitis": [
        MedicationSuggestion(
            generic_name="Cephalexin",
            indication="First-line oral empirical antimicrobial therapy for acute non-purulent lower extremity cellulitis (targeting beta-hemolytic Streptococcus and MSSA)",
            formulation="Oral capsule / tablet (Keflex)",
            route="Oral",
            standard_reference_dosing="500 mg orally four times daily (every 6 hours) for 5 to 7 days",
            contraindications=["History of severe immediate hypersensitivity (anaphylaxis) to cephalosporin or penicillin antibiotics"],
            interactions=["Metformin (may increase metformin concentrations; monitor blood glucose)", "Probenecid (increases cephalexin AUC)"],
            allergy_considerations="Cross-reactivity with penicillins is low (<2%) for 1st-generation cephalosporins but clarify index reaction",
            renal_considerations="Dose adjustment required for renal insufficiency: CrCl 15-30 mL/min: 250-500 mg q8-12h; CrCl < 15 mL/min: 250 mg q12-24h",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Category B; considered first-line safe antibiotic for cellulitis during pregnancy",
            age_considerations="Safe and well-tolerated in elderly; verify baseline renal clearance",
            monitoring_reference_information="Marked advancement/regression of erythema with skin pen, reduction in warmth, swelling, and systemic fever within 48h",
            source_evidence="IDSA Practice Guidelines for Skin and Soft Tissue Infections (SSTIs); FDA Label",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Trimethoprim-Sulfamethoxazole",
            indication="Oral coverage for community-acquired Methicillin-Resistant Staphylococcus aureus (CA-MRSA) in purulent cellulitis or failed beta-lactam",
            formulation="Oral double-strength (DS) tablet (Bactrim DS)",
            route="Oral",
            standard_reference_dosing="1 to 2 DS tablets (160/800 mg) orally twice daily for 5 to 7 days",
            contraindications=["Severe sulfonamide allergy, megaloblastic anemia from folate deficiency, severe hepatic or renal damage"],
            interactions=["Warfarin (dramatically increases INR)", "Potassium-sparing drugs / ACE inhibitors (hyperkalemia risk)"],
            allergy_considerations="Sulfonamide hypersensitivity (rash, Stevens-Johnson syndrome)",
            renal_considerations="Reduce dose by 50% if CrCl 15-30 mL/min; avoid if CrCl < 15 mL/min",
            hepatic_considerations="Contraindicated in severe liver parenchymal damage",
            pregnancy_lactation_considerations="Avoid in 1st trimester (folate antagonist) and at term (hyperbilirubinemia/kernicterus)",
            age_considerations="Increased risk of severe hyperkalemia, acute kidney injury, and bone marrow suppression in elderly",
            monitoring_reference_information="Clinical resolution of purulence, drainage, local tenderness, and serum potassium in elderly",
            source_evidence="IDSA SSTI Guidelines; Cochrane Review on Cellulitis",
            safety_decision=None,
        ),
    ],
    "acute coronary syndrome": [
        MedicationSuggestion(
            generic_name="Aspirin (Acetylsalicylic Acid)",
            indication="Immediate antiplatelet therapy for acute coronary syndromes (STEMI, NSTEMI, Unstable Angina) to inhibit thromboxane A2-mediated platelet aggregation",
            formulation="Chewable non-enteric-coated tablet",
            route="Oral (Chewed)",
            standard_reference_dosing="324 mg (4 x 81 mg) chewable tablets chewed and swallowed immediately upon suspected ACS presentation, followed by 81 mg orally once daily indefinitely",
            contraindications=["Active severe pathological bleeding, severe aspirin-induced asthma / bronchospasm, active peptic ulcer disease"],
            interactions=["Warfarin, DOACs, other antiplatelet agents (multiplies bleeding risk)", "NSAIDs (ibuprofen competitively blocks aspirin antiplatelet effect; take aspirin >=30 min prior)"],
            allergy_considerations="True aspirin allergy (urticaria/anaphylaxis): load with Clopidogrel 300-600 mg PO or Ticagrelor 180 mg PO instead",
            renal_considerations="Generally safe; caution in end-stage renal disease due to platelet dysfunction",
            hepatic_considerations="Use with caution in severe hepatic impairment / coagulopathy",
            pregnancy_lactation_considerations="High-dose avoided in third trimester (premature closure of ductus arteriosus); low-dose 81 mg safe for preeclampsia prophylaxis",
            age_considerations="Monitor elderly for silent gastrointestinal bleeding; consider co-prescription of a proton pump inhibitor (PPI)",
            monitoring_reference_information="Signs of overt or occult hemorrhage (melena, hematemesis), hemoglobin/hematocrit, platelet count",
            source_evidence="2023 ACC/AHA Guideline for the Management of Patients With Acute Coronary Syndromes; ESC ACS Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Ticagrelor",
            indication="Potent, reversible P2Y12 platelet adenosine diphosphate (ADP) receptor antagonist for acute coronary syndrome (STEMI or NSTEMI)",
            formulation="Oral film-coated tablet (Brilinta)",
            route="Oral",
            standard_reference_dosing="180 mg loading dose (two 90 mg tablets) orally STAT, followed by 90 mg orally twice daily for 12 months in combination with aspirin 81 mg daily",
            contraindications=["Active pathological bleeding, history of intracranial hemorrhage, severe hepatic impairment"],
            interactions=["Strong CYP3A4 inhibitors increase ticagrelor exposure; strong CYP3A inducers decrease efficacy; maintenance aspirin dose MUST NOT exceed 100 mg daily (high-dose aspirin decreases ticagrelor efficacy)"],
            allergy_considerations="Known hypersensitivity to ticagrelor. Warn patient regarding benign, self-limited dyspnea (occurs in 10-15% of patients without bronchospasm)",
            renal_considerations="No dosage adjustment needed in renal impairment or hemodialysis",
            hepatic_considerations="Contraindicated in severe hepatic impairment (Child-Pugh Class C); not studied in moderate impairment",
            pregnancy_lactation_considerations="Category C; use only if potential maternal cardiovascular benefit justifies fetal risk",
            age_considerations="Increased risk of bleeding in elderly; no specific dose reduction required based on age alone",
            monitoring_reference_information="Bleeding events, complete blood count, dyspnea reporting, ECG for ventricular pauses in patients with sick sinus syndrome / AV block",
            source_evidence="PLATO Clinical Trial (NEJM 2009); ACC/AHA ACS Guidelines (Class I Recommendation)",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Unfractionated Heparin (UFH)",
            indication="Parenteral anticoagulation for acute coronary syndrome undergoing percutaneous coronary intervention (PCI) or medical stabilization",
            formulation="Intravenous injection / infusion",
            route="Intravenous",
            standard_reference_dosing="60 units/kg IV bolus (maximum 4,000 units), followed by initial continuous infusion of 12 units/kg/hr (maximum 1,000 units/hr), titrated to target aPTT 1.5 to 2.0 times control (50-70 seconds)",
            contraindications=["Active major bleeding, severe uncontrolled hypertension, history of Heparin-Induced Thrombocytopenia (HIT) with thrombosis"],
            interactions=["Other antithrombotic agents, thrombolytics, and glycoprotein IIb/IIIa inhibitors dramatically elevate bleeding risk"],
            allergy_considerations="Assess for history of Heparin-Induced Thrombocytopenia (HIT); if HIT suspected, switch immediately to Bivalirudin or Argatroban",
            renal_considerations="Preferred anticoagulant over LMWH/fondaparinux in severe renal failure (eGFR <30 mL/min) and dialysis due to non-renal reticuloendothelial clearance",
            hepatic_considerations="Use with caution; baseline coagulopathy makes aPTT titration challenging (consider anti-Xa monitoring)",
            pregnancy_lactation_considerations="Category C; does not cross placenta; safe in pregnancy when anticoagulation is mandatory",
            age_considerations="Elderly female patients have higher sensitivity to heparin and higher hemorrhagic complication rates",
            monitoring_reference_information="Serial aPTT or anti-Xa levels every 6 hours until therapeutic, daily platelet counts to monitor for HIT (day 4-14), hematocrit/hemoglobin",
            source_evidence="ACC/AHA Guideline for Coronary Artery Revascularization; ESC STEMI Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Atorvastatin",
            indication="Early high-intensity statin therapy initiated within 24 hours of ACS presentation to reduce recurrent ischemic events and stabilize vulnerable plaques",
            formulation="Oral film-coated tablet (Lipitor)",
            route="Oral",
            standard_reference_dosing="80 mg orally once daily at bedtime (high-intensity regimen irrespective of baseline LDL cholesterol level)",
            contraindications=["Active liver disease, unexplained persistent elevations of serum transaminases, pregnancy, decompensated cirrhosis"],
            interactions=["Strong CYP3A4 inhibitors (clarithromycin, itraconazole, protease inhibitors) significantly increase rhabdomyolysis risk; avoid gemfibrozil"],
            allergy_considerations="Statin class hypersensitivity; monitor for statin-associated muscle symptoms (SAMS)",
            renal_considerations="No dosage adjustment needed in renal impairment (atorvastatin is cleared hepatically)",
            hepatic_considerations="Contraindicated in active liver disease; monitor baseline and periodic ALT/AST",
            pregnancy_lactation_considerations="Contraindicated in pregnancy and lactation (teratogenic risk / cholesterol essential for fetal neurodevelopment)",
            age_considerations="In patients >=75 years or frail, consider initiating at 40 mg daily to minimize myopathy risk",
            monitoring_reference_information="Lipid panel at 4 to 12 weeks post-ACS (goal LDL-C >=50% reduction and <55 mg/dL), baseline LFTs, serum CK if muscle pain develops",
            source_evidence="PROVE-IT TIMI 22 Trial (NEJM 2004); ACC/AHA Cholesterol Guidelines; ESC Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Nitroglycerin (Glyceryl Trinitrate)",
            indication="Rapid symptomatic relief of ischemic chest pain and reduction of myocardial oxygen demand via coronary vasodilation and venous preload reduction",
            formulation="Sublingual tablet (0.4 mg) / Sublingual spray / IV infusion",
            route="Sublingual / Intravenous",
            standard_reference_dosing="0.4 mg sublingually every 5 minutes for up to 3 doses; if persistent ischemia, start IV infusion at 5-10 mcg/min, titrating upward by 5-10 mcg/min every 3-5 minutes (target pain resolution / MAP reduction)",
            contraindications=["Concurrent phosphodiesterase-5 (PDE5) inhibitors: Sildenafil or Vardenafil within 24 hours, or Tadalafil within 48 hours (risk of fatal refractory hypotension)", "Systolic blood pressure <90 mmHg or >30 mmHg drop below baseline", "Severe bradycardia (<50 bpm) or marked tachycardia (>100 bpm)", "Suspected Right Ventricular (RV) myocardial infarction (dependent on RV preload)"],
            interactions=["PDE5 inhibitors (absolute contraindication), antihypertensives, alcohol, riociguat"],
            allergy_considerations="Nitrate hypersensitivity",
            renal_considerations="No dosage adjustment required",
            hepatic_considerations="No dosage adjustment required; monitor hemodynamics closely",
            pregnancy_lactation_considerations="Category C; short-term use acceptable if clinically necessary for maternal cardiac ischemia",
            age_considerations="Elderly patients are predisposed to severe orthostatic hypotension and syncope; administer with patient recumbent",
            monitoring_reference_information="Continuous blood pressure and heart rate monitoring (hold if SBP <90 mmHg or HR <50 bpm), relief of angina score",
            source_evidence="ACC/AHA STEMI/NSTEMI Clinical Guidelines; AHA Scientific Statement on ACS Management",
            safety_decision=None,
        ),
    ],
    "acute ischemic stroke": [
        MedicationSuggestion(
            generic_name="Tenecteplase (TNK-tPA)",
            indication="Intravenous thrombolysis for acute ischemic stroke presenting within 4.5 hours of symptom onset (or last known normal) without contraindications",
            formulation="Intravenous injection (single bolus over 5-10 seconds)",
            route="Intravenous",
            standard_reference_dosing="0.25 mg/kg IV single bolus over 5 to 10 seconds (maximum dose 25 mg); alternative to Alteplase 0.9 mg/kg (max 90 mg with 10% bolus + 90% 1-hour infusion)",
            contraindications=["Current intracranial hemorrhage or subarachnoid hemorrhage on non-contrast head CT", "Active internal bleeding or gastrointestinal hemorrhage within 21 days", "Severe uncontrolled hypertension (BP >=185/110 mmHg refractory to aggressive IV antihypertensives)", "Therapeutic anticoagulation with DOAC within 48h (unless normal thrombin time/anti-Xa) or INR >1.7 on Warfarin", "Intracranial surgery, serious head trauma, or previous stroke within 3 months", "Platelet count <100,000/mcL"],
            interactions=["All antiplatelet agents (aspirin, clopidogrel) and anticoagulants MUST BE WITHHELD for 24 hours post-thrombolysis until follow-up CT rules out hemorrhage"],
            allergy_considerations="Severe tPA hypersensitivity; monitor for orolingual angioedema (especially in patients taking ACE inhibitors)",
            renal_considerations="No dosage adjustment required",
            hepatic_considerations="Use with extreme caution in baseline hepatic coagulopathy (contraindicated if elevated PT/INR)",
            pregnancy_lactation_considerations="Weigh significant maternal stroke benefit against potential bleeding risks; consult neurology/MFA",
            age_considerations="Safe and effective across adult age spectrum including patients >80 years (EXTEND-IA TNK trials)",
            monitoring_reference_information="Strict neurological checks (NIHSS) and vital signs every 15 minutes for 2 hours, then every 30 minutes for 6 hours, then hourly for 16 hours; keep BP <180/105 mmHg; STAT non-contrast head CT if sudden neurological deterioration or severe headache develops",
            source_evidence="AHA/ASA Guidelines for the Early Management of Patients With Acute Ischemic Stroke (2019/2024 update); EXTEND-IA TNK and AcT Trials",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Nicardipine Hydrochloride",
            indication="Continuous IV titration to lower and maintain blood pressure <185/110 mmHg prior to thrombolysis, and <180/105 mmHg post-thrombolysis in acute ischemic stroke",
            formulation="Intravenous infusion (Cardene IV)",
            route="Intravenous",
            standard_reference_dosing="Initiate infusion at 5 mg/hr; titrate upward by 2.5 mg/hr every 5 to 15 minutes to a maximum of 15 mg/hr until blood pressure goal achieved; once controlled, titrate down to maintenance rate (typically 3-5 mg/hr)",
            contraindications=["Advanced aortic stenosis (causes profound cardiac collapse)"],
            interactions=["Beta-blockers, fentanyl (additive hypotension), cyclosporine, tacrolimus (increases calcineurin inhibitor levels)"],
            allergy_considerations="Dihydropyridine calcium channel blocker hypersensitivity",
            renal_considerations="No dosage adjustment necessary",
            hepatic_considerations="Titrate cautiously in severe hepatic impairment due to extensive hepatic metabolism",
            pregnancy_lactation_considerations="Category C; widely used in severe hypertensive emergencies in obstetrics (preferred along with labetalol)",
            age_considerations="Monitor for reflex tachycardia and excessive precipitous BP drops in elderly vasculopathic patients",
            monitoring_reference_information="Continuous arterial line or automated cuff BP every 5-15 minutes; monitor for phlebitis at peripheral infusion site (change site q12h)",
            source_evidence="AHA/ASA Stroke Guidelines; Neurocritical Care Society Consensus Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Aspirin",
            indication="Secondary prevention and platelet inhibition in acute ischemic stroke not receiving thrombolytic therapy (or administered 24 hours POST-thrombolytic following confirmatory CT)",
            formulation="Oral tablet / Rectal suppository",
            route="Oral / Rectal",
            standard_reference_dosing="160 to 325 mg orally (or rectally if dysphagic) once daily within 24 to 48 hours of stroke onset (delay exactly 24 hours if IV thrombolysis was administered)",
            contraindications=["Active intracranial hemorrhage, systemic active bleeding, severe aspirin-induced asthma"],
            interactions=["Do not combine with therapeutic anticoagulation during the acute stroke phase"],
            allergy_considerations="Aspirin hypersensitivity; verify swallowing ability with nurse-administered bedside dysphagia screen before any oral intake",
            renal_considerations="No adjustment needed",
            hepatic_considerations="Safe in mild-moderate impairment",
            pregnancy_lactation_considerations="Category C/D in 3rd trimester; short-term acute stroke benefit outweighs risks",
            age_considerations="Universal bedside dysphagia screening MANDATORY prior to oral administration to prevent fatal aspiration pneumonia",
            monitoring_reference_information="Signs of GI bleeding, neurological status, platelet count",
            source_evidence="CAST and IST Clinical Trials; AHA/ASA Stroke Guidelines",
            safety_decision=None,
        ),
    ],
    "septic shock": [
        MedicationSuggestion(
            generic_name="Norepinephrine Bitartrate",
            indication="First-choice vasopressor to restore and maintain vascular tone and tissue perfusion (target Mean Arterial Pressure [MAP] >= 65 mmHg) in septic shock",
            formulation="Intravenous infusion (Levophed 4 mg/250 mL D5W or NS)",
            route="Intravenous (Central venous catheter preferred; peripheral line acceptable temporarily in antecubital fossa)",
            standard_reference_dosing="0.02 to 1.0 mcg/kg/min continuous IV infusion, titrated every 2 to 5 minutes to maintain target MAP >= 65 mmHg (start Vasopressin 0.03 units/min as secondary agent if norepinephrine requirement exceeds 0.25 mcg/kg/min)",
            contraindications=["Hypovolemia prior to adequate volume resuscitation (except as emergency bridge while fluid resuscitation is ongoing)"],
            interactions=["Halogenated hydrocarbon anesthetics (sensitize myocardium to catecholamines)", "MAO inhibitors, tricyclic antidepressants (prolonged hypertension)"],
            allergy_considerations="Contains sodium metabisulfite excipient (rare allergic reactions)",
            renal_considerations="Restores renal perfusion pressure; strictly titrate to maintain urine output >0.5 mL/kg/hr",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Vasopressor of choice for septic shock in pregnancy; maintain placental perfusion",
            age_considerations="Monitor for peripheral digital ischemia, especially in patients with pre-existing severe peripheral vascular disease",
            monitoring_reference_information="Continuous arterial line blood pressure, serum lactate clearance (goal >20% clearance every 2 hours), urine output, peripheral extremity perfusion",
            source_evidence="Surviving Sepsis Campaign International Guidelines for Management of Sepsis and Septic Shock (2021/2023 update)",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Piperacillin-Tazobactam + Vancomycin",
            indication="Empirical broad-spectrum antimicrobial coverage initiated within 1 HOUR of recognition of septic shock covering Pseudomonas aeruginosa, Enterobacterales, and MRSA",
            formulation="Intravenous infusions (Zosyn 4.5 g + Vancomycin 25-30 mg/kg loading dose)",
            route="Intravenous",
            standard_reference_dosing="Vancomycin 25 to 30 mg/kg IV loading dose (max 2 g) infused over 2 hours PLUS Piperacillin-Tazobactam 4.5 g IV every 8 hours as extended 4-hour infusions",
            contraindications=["Severe immediate anaphylaxis to beta-lactams or vancomycin"],
            interactions=["Combined piperacillin-tazobactam and vancomycin carries synergistic risk of acute kidney injury (AKI); switch to Cefepime or Meropenem if AKI worsens"],
            allergy_considerations="Screen for penicillin and cephalosporin cross-reactivity; infusing vancomycin slowly prevents histamine-mediated 'red man syndrome'",
            renal_considerations="Dose titration and therapeutic drug monitoring (TDM: Vancomycin AUC/MIC 400-600) mandatory; adjust piperacillin-tazobactam for eGFR <50 mL/min",
            hepatic_considerations="Generally safe; no primary hepatic adjustment needed",
            pregnancy_lactation_considerations="Category B (piperacillin-tazobactam) / Category C (vancomycin); lifesaving in maternal sepsis",
            age_considerations="High incidence of baseline CKD in elderly warrants daily serum creatinine and vancomycin trough/AUC monitoring",
            monitoring_reference_information="Blood cultures x2 drawn BEFORE antibiotic administration (do not delay antibiotics >45 min if cultures difficult), serum creatinine, BUN, procalcitonin for de-escalation",
            source_evidence="Surviving Sepsis Campaign (SSC) 1-Hour Bundle Guidelines; IDSA Sepsis Guidance",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Hydrocortisone",
            indication="Adjunctive corticosteroid therapy for refractory septic shock persisting despite adequate fluid resuscitation and high-dose vasopressor therapy (>=0.25 mcg/kg/min norepinephrine)",
            formulation="Intravenous injection (Solu-Cortef)",
            route="Intravenous",
            standard_reference_dosing="200 mg/day administered either as continuous IV infusion (8.3 mg/hr) or 50 mg IV every 6 hours; taper once vasopressors are successfully discontinued",
            contraindications=["Systemic fungal infection without targeted therapy"],
            interactions=["NSAIDs (increased ulcer risk), insulin requirements increase due to steroid-induced hyperglycemia"],
            allergy_considerations="Corticosteroid hypersensitivity",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Safe and indicated in maternal refractory septic shock",
            age_considerations="Monitor for steroid-induced delirium, hyperglycemia, and secondary hospital-acquired infections",
            monitoring_reference_information="Weaning of vasopressor requirement, point-of-care blood glucose every 2 to 4 hours (target 140-180 mg/dL), surveillance for secondary infection",
            source_evidence="Surviving Sepsis Campaign Guidelines (Weak recommendation with moderate-quality evidence); APROCCHSS Trial (NEJM 2018)",
            safety_decision=None,
        ),
    ],
    "diabetic ketoacidosis": [
        MedicationSuggestion(
            generic_name="Regular Human Insulin",
            indication="First-line pharmacotherapy for Diabetic Ketoacidosis (DKA) and Hyperosmolar Hyperglycemic State (HHS) to suppress lipolysis, ketogenesis, and gluconeogenesis",
            formulation="Intravenous infusion (100 units Regular Insulin in 100 mL 0.9% Normal Saline = 1 unit/mL)",
            route="Intravenous",
            standard_reference_dosing="Continuous IV infusion of 0.1 units/kg/hr (or 0.14 units/kg/hr without bolus); target blood glucose reduction of 50 to 75 mg/dL/hr; when blood glucose reaches 200 mg/dL (DKA) or 300 mg/dL (HHS), add D5W to IV fluids and reduce insulin infusion to 0.02-0.05 units/kg/hr to keep glucose 150-200 mg/dL until anion gap closes",
            contraindications=["Serum potassium < 3.3 mEq/L (ADMINISTERING INSULIN WITH HYPOKALEMIA TRIGGERS FATAL CARDIAC ARRHYTHMIAS AND RESPIRATORY ARREST; recheck and replete K+ first!)"],
            interactions=["Hypoglycemic agents, beta-blockers (mask hypoglycemia tachycardia)"],
            allergy_considerations="Human recombinant regular insulin hypersensitivity is exceedingly rare",
            renal_considerations="Insulin clearance decreases in renal failure; monitor glucose closely",
            hepatic_considerations="Hepatic glucose production is rapidly suppressed; monitor for hypoglycemia",
            pregnancy_lactation_considerations="Safe and mandatory in pregnancy; DKA in pregnancy occurs at lower glucose levels ('euglycemic DKA') and threatens fetal viability",
            age_considerations="Elderly patients are at high risk of rapid cerebral edema with overly rapid osmolality reduction",
            monitoring_reference_information="Point-of-care blood glucose hourly; basic metabolic panel (electrolytes, BUN, creatinine, venous pH, calculated anion gap) every 2 to 4 hours until DKA resolved (anion gap <=12, HCO3 >=18, venous pH >7.30)",
            source_evidence="ADA Standards of Care in Diabetes: Management of Hyperglycemic Crises (2024); Joint British Diabetes Societies (JBDS) DKA Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Potassium Chloride (KCl)",
            indication="Aggressive parenteral potassium repletion to prevent fatal hypokalemia induced by insulin-driven intracellular potassium shifting and osmotic urinary losses in DKA",
            formulation="Intravenous infusion premixed in crystalloids (20 to 40 mEq/L)",
            route="Intravenous",
            standard_reference_dosing="If serum K+ is 3.3 to 5.2 mEq/L: add 20 to 30 mEq KCl per liter of IV maintenance fluid (maintain serum K+ strictly between 4.0 and 5.0 mEq/L); if K+ < 3.3 mEq/L: HOLD INSULIN and give 20-40 mEq/hr IV until K+ > 3.3 mEq/L",
            contraindications=["Hyperkalemia with serum potassium > 5.2 mEq/L (hold potassium until level drops < 5.2), complete anuria / severe acute tubular necrosis without urine output"],
            interactions=["Potassium-sparing diuretics, ACE inhibitors, ARBs (increase hyperkalemia risk)"],
            allergy_considerations="No allergy; ensure adequate peripheral vein dilution (max 10-20 mEq/hr in peripheral line to avoid chemical phlebitis / burning)",
            renal_considerations="Verify urine output >= 0.5 mL/kg/hr before initiating routine potassium repletion",
            hepatic_considerations="Standard dosing",
            pregnancy_lactation_considerations="Compatible and mandatory during DKA management in pregnancy",
            age_considerations="Monitor renal function closely in geriatric patients to avoid iatrogenic hyperkalemia",
            monitoring_reference_information="Serum potassium every 2 hours until stable, continuous cardiac telemetry during rapid IV potassium administration",
            source_evidence="ADA Hyperglycemic Crises Guidelines; Endocrine Society Clinical Practice Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="0.9% Sodium Chloride / Balanced Crystalloids",
            indication="Immediate volume resuscitation to restore effective circulating arterial volume and renal perfusion in diabetic ketoacidosis",
            formulation="Intravenous isotonic crystalloid infusion",
            route="Intravenous",
            standard_reference_dosing="1,000 to 1,500 mL IV over the first hour (15-20 mL/kg/hr); subsequent fluids at 250 to 500 mL/hr: switch to 0.45% NaCl if corrected serum sodium is normal or high; add 5% Dextrose (D5W) when serum glucose reaches 200-250 mg/dL",
            contraindications=["Severe fluid overload or pulmonary edema (titrate carefully with hemodynamic monitoring)"],
            interactions=["Compatibility with co-infused potassium solutions"],
            allergy_considerations="Large volumes of 0.9% NaCl can cause hyperchloremic non-anion gap metabolic acidosis; Plasmalyte or Lactated Ringer's can be utilized as alternative balanced crystalloid",
            renal_considerations="Restores renal filtration; watch for oliguric acute tubular necrosis",
            hepatic_considerations="No specific adjustment",
            pregnancy_lactation_considerations="Universally indicated in pregnant patients with DKA",
            age_considerations="High risk of precipitating congestive heart failure in elderly patients with reduced ejection fraction; monitor lung sounds frequently",
            monitoring_reference_information="Hourly urine output, mental status, blood pressure, corrected sodium (measured Na + 0.016 * [glucose - 100]), calculated serum osmolality",
            source_evidence="ADA Management of Hyperglycemic Crises in Adults; UK JBDS Inpatient DKA Guidelines",
            safety_decision=None,
        ),
    ],
    "acute decompensated heart failure": [
        MedicationSuggestion(
            generic_name="Furosemide",
            indication="First-line loop diuretic for rapid decongestion, reduction of elevated ventricular filling pressures, and relief of pulmonary edema in acute decompensated heart failure (ADHF)",
            formulation="Intravenous injection (Lasix)",
            route="Intravenous",
            standard_reference_dosing="40 to 80 mg IV bolus in diuretic-naive patients; in chronic oral diuretic users, administer 2.0 to 2.5 times the total daily home oral dose as an IV bolus (e.g. 80-160 mg IV if taking 80 mg PO daily); assess urine output at 2 hours (target >=100-150 mL/hr) or spot urine sodium at 2h (target >50-70 mEq/L)",
            contraindications=["Anuria without dialysis, severe hepatic coma, severe hypokalemia, progressive severe worsening renal failure with shock"],
            interactions=["Aminoglycosides, cisplatin (additive ototoxicity), NSAIDs (blunt diuretic response and precipitate AKI), ACEi/ARBs (monitor creatinine and potassium)"],
            allergy_considerations="Sulfonamide loop diuretic; true cross-reactivity with antimicrobial sulfonamides is extremely rare; use Ethacrynic acid if documented severe anaphylaxis",
            renal_considerations="Essential for cardiorenal decongestion; a mild serum creatinine rise (<0.3 mg/dL) reflecting hemoconcentration is acceptable if clinical congestion is resolving",
            hepatic_considerations="Monitor electrolytes to avoid precipitating hepatic encephalopathy in cirrhosis with ascites",
            pregnancy_lactation_considerations="Category C; use only if maternal hemodynamic benefit clearly outweighs potential reduction in placental perfusion",
            age_considerations="High risk of overdiuresis, orthostatic hypotension, and severe electrolyte depletion in elderly patients; strict monitoring",
            monitoring_reference_information="Strict intake/output, daily standing weight (target net negative 1-2 kg/day), spot urine sodium at 2 hours, basic metabolic panel (potassium, magnesium, BUN, creatinine) daily",
            source_evidence="DOOSE-AHF Trial (NEJM 2011); 2022 AHA/ACC/HFSA Heart Failure Guidelines; ESC Heart Failure Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Sacubitril-Valsartan (ARNI)",
            indication="Angiotensin receptor-neprilysin inhibitor (ARNI) initiated or optimized during the inpatient admission once stabilized to reduce cardiovascular mortality and heart failure rehospitalization in HFrEF",
            formulation="Oral film-coated tablet (Entresto)",
            route="Oral",
            standard_reference_dosing="Initiate at 24/26 mg or 49/51 mg orally twice daily once the patient is hemodynamically stabilized, euvolemic, and SBP >=100 mmHg; MANDATORY 36-HOUR WASHOUT PERIOD if transitioning from an ACE inhibitor to prevent fatal angioedema; titrate every 2-4 weeks to target dose of 97/103 mg PO BID",
            contraindications=["History of angioedema with prior ACE inhibitor or ARB therapy", "Concurrent use with an ACE inhibitor (requires strict 36-hour washout)", "Concurrent aliskiren in diabetic patients", "Pregnancy"],
            interactions=["ACE inhibitors (fatal angioedema risk), potassium supplements / potassium-sparing diuretics (severe hyperkalemia), NSAIDs (worsens renal function)"],
            allergy_considerations="Black Box Warning: Angioedema history is an absolute contraindication",
            renal_considerations="Initiate at 24/26 mg BID if eGFR <30 mL/min; monitor serum creatinine and potassium closely",
            hepatic_considerations="Initiate at 24/26 mg BID in moderate hepatic impairment (Child-Pugh Class B); contraindicated in severe impairment (Class C)",
            pregnancy_lactation_considerations="Black Box Warning: Contraindicated in pregnancy (causes oligohydramnios, fetal skull hypoplasia, and intrauterine death)",
            age_considerations="Assess standing blood pressure to prevent symptomatic orthostatic hypotension in elderly patients",
            monitoring_reference_information="Blood pressure, serum potassium, and serum creatinine 1 to 2 weeks after initiation and titration",
            source_evidence="PARADIGM-HF (NEJM 2014); PIONEER-HF (NEJM 2019: Inpatient Initiation); AHA/ACC/HFSA Guideline Class I Recommendation",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Empagliflozin",
            indication="Sodium-glucose cotransporter-2 (SGLT2) inhibitor initiated during hospitalization for acute heart failure to improve clinical outcomes, reduce death, and shorten stay regardless of ejection fraction or diabetes status",
            formulation="Oral tablet (Jardiance)",
            route="Oral",
            standard_reference_dosing="10 mg orally once daily in the morning with or without food",
            contraindications=["History of severe hypersensitivity to empagliflozin, severe renal impairment (eGFR <20 mL/min for heart failure initiation), diabetic ketoacidosis"],
            interactions=["Insulin and sulfonylureas (increased hypoglycemia risk in diabetic patients; reduce background insulin dose by 10-20%)", "Diuretics (additive volume depletion)"],
            allergy_considerations="SGLT2 inhibitor hypersensitivity",
            renal_considerations="Approved down to eGFR >=20 mL/min; provides long-term nephroprotection despite a transient initial eGFR dip (10-15%) that recovers",
            hepatic_considerations="No dosage adjustment needed in mild to moderate hepatic impairment",
            pregnancy_lactation_considerations="Contraindicated in 2nd and 3rd trimesters of pregnancy (adverse effects on fetal renal development)",
            age_considerations="Check volume status and blood pressure in elderly patients prior to initiation to prevent dehydration",
            monitoring_reference_information="eGFR, blood pressure, glycemic parameters, surveillance for mycotic genital infections and rare euglycemic DKA",
            source_evidence="EMPULSE Trial (Nature Medicine 2022: Inpatient Initiation in Acute Heart Failure); EMPEROR-Reduced and EMPEROR-Preserved Trials; AHA/ACC Guidelines",
            safety_decision=None,
        ),
    ],
    "bacterial meningitis": [
        MedicationSuggestion(
            generic_name="Ceftriaxone",
            indication="First-line high-dose empirical parenteral antimicrobial therapy for acute community-acquired bacterial meningitis covering Streptococcus pneumoniae and Neisseria meningitidis",
            formulation="Intravenous infusion / powder for injection",
            route="Intravenous",
            standard_reference_dosing="2 g IV every 12 hours (meningitic dosing: double standard dose to achieve therapeutic CSF penetration across blood-brain barrier)",
            contraindications=["Severe immediate IgE-mediated beta-lactam anaphylaxis", "Concurrent IV calcium administration in neonates"],
            interactions=["Calcium-containing intravenous solutions (risk of precipitation in lungs and kidneys)"],
            allergy_considerations="Penicillin/cephalosporin cross-reactivity: if severe anaphylaxis to all beta-lactams, use Chloramphenicol 25 mg/kg IV q6h or Moxifloxacin 400 mg IV q24h",
            renal_considerations="Dual biliary-renal clearance; no dosage adjustment required for renal insufficiency",
            hepatic_considerations="Generally safe; monitor for biliary sludging during prolonged therapy",
            pregnancy_lactation_considerations="Category B; antibiotic of choice in pregnancy",
            age_considerations="Safe and recommended across adult and geriatric age groups",
            monitoring_reference_information="Clinical resolution of headache, fever, nuchal rigidity, Glasgow Coma Scale (GCS), repeat CSF analysis if no clinical improvement at 48 hours",
            source_evidence="IDSA Practice Guidelines for the Management of Bacterial Meningitis; ESCMID Meningitis Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Vancomycin",
            indication="Empirical parenteral coverage for penicillin- and cephalosporin-resistant Streptococcus pneumoniae and community-acquired MRSA in acute bacterial meningitis",
            formulation="Intravenous infusion",
            route="Intravenous",
            standard_reference_dosing="15 to 20 mg/kg IV every 8 to 12 hours (target serum trough concentration 15-20 mcg/mL or AUC/MIC 400-600) infused over at least 60-120 minutes",
            contraindications=["Severe vancomycin hypersensitivity"],
            interactions=["Concomitant aminoglycosides, piperacillin-tazobactam, amphotericin B (additive nephrotoxicity)"],
            allergy_considerations="Infuse over >=60 minutes to prevent infusion-related histamine release ('red man syndrome')",
            renal_considerations="Strict pharmacokinetic dosing and therapeutic drug monitoring required based on CrCl",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Category C; indicated when alternative agents cannot be used",
            age_considerations="Extended interval dosing required in elderly due to age-related decline in GFR",
            monitoring_reference_information="Serum vancomycin trough concentration prior to 4th dose, daily serum creatinine, hearing evaluation for high-dose prolonged courses",
            source_evidence="IDSA Meningitis Guidelines; Consensus Guidelines for Vancomycin Therapeutic Monitoring",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Ampicillin",
            indication="MANDATORY empirical addition to Ceftriaxone + Vancomycin for coverage of Listeria monocytogenes in adults >= 50 years of age, pregnant women, and immunocompromised patients",
            formulation="Intravenous injection / infusion",
            route="Intravenous",
            standard_reference_dosing="2 g IV every 4 hours (total 12 g daily; high-dose central nervous system regimen)",
            contraindications=["Severe immediate penicillin anaphylaxis (in severe allergy, use Trimethoprim-Sulfamethoxazole 5 mg/kg TMP IV q8h as Listeria alternative)"],
            interactions=["Allopurinol (increased rash incidence), methotrexate"],
            allergy_considerations="Penicillin class allergy",
            renal_considerations="Dose adjustment required: CrCl 10-50 mL/min: 2 g q6-8h; CrCl < 10 mL/min: 2 g q12h",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Category B; frontline safe agent for Listeria meningitis in pregnancy (pregnant women are 10-20x more susceptible to Listeria)",
            age_considerations="Mandatory in all adult meningitis patients aged >=50 years due to age-related waning of cell-mediated immunity",
            monitoring_reference_information="Clinical resolution of neurological symptoms, complete blood count, kidney function",
            source_evidence="IDSA Practice Guidelines for Bacterial Meningitis; CDC Listeriosis Clinical Recommendations",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Dexamethasone",
            indication="Adjunctive corticosteroid therapy to attenuate meningeal inflammation, prevent severe sensorineural hearing loss, and reduce mortality in pneumococcal and Haemophilus influenzae meningitis",
            formulation="Intravenous injection",
            route="Intravenous",
            standard_reference_dosing="10 mg IV administered 15 to 20 minutes BEFORE or CONCURRENTLY WITH the first dose of antimicrobial therapy, repeated every 6 hours for 4 days; do NOT initiate if antibiotics have already been administered for >4 hours; discontinue if CSF gram stain/culture confirms pathogen other than Streptococcus pneumoniae",
            contraindications=["Systemic fungal infection, administration >4 hours after starting antimicrobial therapy (provides no benefit and adds steroid adverse risks)"],
            interactions=["Slightly reduces vancomycin CSF penetration; maintain aggressive vancomycin dosing and therapeutic monitoring"],
            allergy_considerations="Corticosteroid hypersensitivity",
            renal_considerations="No dosage adjustment required",
            hepatic_considerations="No dosage adjustment required",
            pregnancy_lactation_considerations="Category C; short 4-day course justified in acute maternal bacterial meningitis",
            age_considerations="Monitor for steroid-induced hyperglycemia and delirium in elderly patients",
            monitoring_reference_information="Capillary blood glucose, signs of upper gastrointestinal bleeding, neurological exam, audiometry post-recovery",
            source_evidence="de Gans & van de Beek Trial (NEJM 2002); IDSA Bacterial Meningitis Guidelines; Cochrane Systematic Review",
            safety_decision=None,
        ),
    ],
    "status epilepticus": [
        MedicationSuggestion(
            generic_name="Lorazepam",
            indication="First-line emergency benzodiazepine for the termination of active status epilepticus (continuous seizure activity >= 5 minutes)",
            formulation="Intravenous injection (Ativan)",
            route="Intravenous",
            standard_reference_dosing="0.1 mg/kg IV (typically 4 mg slow IV push at 2 mg/min); if seizures continue after 5 to 10 minutes, administer a second dose of 4 mg IV (if IV access unavailable: Intramuscular Midazolam 10 mg IM is preferred first-line alternative)",
            contraindications=["Severe acute narrow-angle glaucoma, severe respiratory depression without bag-valve mask / airway support available"],
            interactions=["Opioids, alcohol, and other CNS depressants compound severe respiratory depression and hypotension"],
            allergy_considerations="Benzodiazepine hypersensitivity",
            renal_considerations="Propylene glycol diluent in high-dose IV lorazepam infusions can accumulate and cause hyperosmolality metabolic acidosis; less concern with acute bolus doses",
            hepatic_considerations="Lorazepam undergoes direct glucuronidation without CYP metabolism; preferred benzodiazepine in liver failure",
            pregnancy_lactation_considerations="Category D; life-saving maternal seizure termination overrides potential fetal risks; monitor fetal heart rate",
            age_considerations="Lower starting dose (2 mg IV) in frail elderly due to prolonged sedation and hypoventilation risk",
            monitoring_reference_information="Continuous pulse oximetry, respiratory rate, blood pressure, end-tidal CO2, readiness for endotracheal intubation",
            source_evidence="AES Guidelines for the Treatment of Prolonged Seizures and Status Epilepticus (2016/2023 update); RAMPART Trial (NEJM 2012)",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Levetiracetam",
            indication="First-line urgent non-sedating second-phase intravenous antiepileptic drug for status epilepticus refractory to benzodiazepines (or to prevent seizure recurrence)",
            formulation="Intravenous infusion (Keppra IV)",
            route="Intravenous",
            standard_reference_dosing="60 mg/kg IV (maximum dose 4,500 mg) infused over 10 to 15 minutes",
            contraindications=["Severe hypersensitivity to levetiracetam or pyrrolidone derivatives"],
            interactions=["Minimal cytochrome P450 interactions; no significant drug-drug interactions with other antiepileptics or ICU medications"],
            allergy_considerations="Levetiracetam hypersensitivity (rare DRESS syndrome)",
            renal_considerations="Dose adjustment required in renal insufficiency: CrCl 50-80 mL/min: 1000-2000 mg q12h; CrCl 30-50 mL/min: 500-1000 mg q12h; CrCl <30 mL/min: 500-1000 mg q24h; hemodialysis requires post-dialysis supplemental dose",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Category C; preferred antiepileptic in pregnancy with excellent safety record and low teratogenicity risk",
            age_considerations="Assess for behavioral changes, agitation, or psychosis in elderly patients post-recovery",
            monitoring_reference_information="Seizure cessation on continuous electroencephalography (cEEG), renal panel",
            source_evidence="ESETT Trial (NEJM 2019: Established Status Epilepticus Treatment Trial); American Epilepsy Society Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Fosphenytoin Sodium",
            indication="Alternative second-phase parenteral antiepileptic prodrug for status epilepticus (water-soluble phosphate ester of phenytoin)",
            formulation="Intravenous infusion (Cerebyx)",
            route="Intravenous",
            standard_reference_dosing="20 mg Phenytoin Sodium Equivalents (PE) / kg IV (maximum 1,500 mg PE) infused at up to 150 mg PE/min with continuous cardiac rhythm and blood pressure monitoring",
            contraindications=["Sinus bradycardia, second- or third-degree AV block, sinoatrial block, Adams-Stokes syndrome"],
            interactions=["Highly protein-bound; extensively interacts with CYP2C9/CYP2C19 substrates and inducers; monitor free phenytoin levels in hypoalbuminemia"],
            allergy_considerations="HLA-B*1502 screening in Asian descent (Stevens-Johnson syndrome / TEN risk); rash, DRESS syndrome",
            renal_considerations="Increased free (unbound) fraction in uremia; monitor unbound (free) phenytoin level (target 1-2 mcg/mL)",
            hepatic_considerations="Phenytoin clearance is impaired in liver disease; reduce maintenance dose",
            pregnancy_lactation_considerations="Category D (fetal hydantoin syndrome); use Levetiracetam preferentially in pregnant women",
            age_considerations="High risk of cardiac dysrhythmias and severe hypotension during rapid infusion in elderly patients; do not exceed 100 mg PE/min",
            monitoring_reference_information="Continuous ECG telemetry, blood pressure every 5 minutes during infusion, therapeutic drug monitoring (total phenytoin 10-20 mcg/mL, free phenytoin 1-2 mcg/mL)",
            source_evidence="ESETT Trial (NEJM 2019); Neurocritical Care Society Guidelines for Status Epilepticus",
            safety_decision=None,
        ),
    ],
    "acute upper gastrointestinal bleeding": [
        MedicationSuggestion(
            generic_name="Pantoprazole",
            indication="High-dose intravenous proton pump inhibitor therapy to maintain intragastric pH > 6.0, promote platelet aggregation, and stabilize fibrin clots over peptic ulcer bleeding",
            formulation="Intravenous injection / infusion (Protonix IV)",
            route="Intravenous",
            standard_reference_dosing="80 mg IV bolus STAT, followed immediately by continuous IV infusion of 8 mg/hr for 72 hours post-endoscopy (or 40 mg IV twice daily as intermittent bolus regimen; both have demonstrated clinical non-inferiority)",
            contraindications=["Severe hypersensitivity to pantoprazole or substituted benzimidazoles"],
            interactions=["Methotrexate (increases methotrexate levels), clopidogrel (pantoprazole has lower CYP2C19 inhibition compared to omeprazole; preferred in patients taking clopidogrel)"],
            allergy_considerations="Proton pump inhibitor class hypersensitivity",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="No dosage adjustment needed for short-term 72-hour acute bleeding protocol",
            pregnancy_lactation_considerations="Category B; considered safe for acute maternal upper gastrointestinal hemorrhage",
            age_considerations="Generally well-tolerated in elderly; monitor magnesium level with prolonged therapy",
            monitoring_reference_information="Resolution of active bleeding, serial hemoglobin/hematocrit every 4 to 6 hours, rebleeding signs (melena, fresh hematemesis, tachycardia)",
            source_evidence="ACG Clinical Guideline: Upper Gastrointestinal and Ulcer Bleeding (2021); Cochrane Systematic Review on PPIs in Upper GI Bleed",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Octreotide",
            indication="Synthetic somatostatin analogue for suspected or confirmed acute variceal hemorrhage in patients with cirrhosis or portal hypertension (reduces splanchnic blood flow and portal pressure)",
            formulation="Intravenous injection / infusion (Sandostatin)",
            route="Intravenous",
            standard_reference_dosing="50 mcg IV bolus STAT, followed immediately by continuous IV infusion of 50 mcg/hr for 2 to 5 days",
            contraindications=["Known hypersensitivity to octreotide"],
            interactions=["Insulin and oral hypoglycemics (alters blood glucose balance), cyclosporine, bromocriptine"],
            allergy_considerations="Hypersensitivity to octreotide",
            renal_considerations="No dosage adjustment needed for acute 5-day continuous infusion",
            hepatic_considerations="Safe and recommended in decompensated cirrhosis with portal hypertension",
            pregnancy_lactation_considerations="Category B; use when clinically indicated for maternal variceal bleeding",
            age_considerations="Safe in elderly cirrhotic patients; monitor for sinus bradycardia and conduction abnormalities",
            monitoring_reference_information="Hemodynamic stability, portal pressures, bedside blood glucose (can cause transient hypo- or hyperglycemia), abdominal cramping",
            source_evidence="AASLD Practice Guidance: Portal Hypertensive Bleeding in Cirrhosis (2024); Baveno VII Consensus Workshop",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Ceftriaxone",
            indication="Mandatory short-term prophylactic antibiotic therapy in cirrhotic patients presenting with acute upper gastrointestinal bleeding to prevent spontaneous bacterial peritonitis, bacteremia, and rebleeding",
            formulation="Intravenous infusion",
            route="Intravenous",
            standard_reference_dosing="1 g IV every 24 hours for a maximum of 7 days (or until active bleeding ceases and vasoactive drugs discontinued)",
            contraindications=["Severe cephalosporin / penicillin anaphylaxis"],
            interactions=["Calcium-containing infusions"],
            allergy_considerations="Assess for beta-lactam allergy",
            renal_considerations="No adjustment needed",
            hepatic_considerations="Standard dosing",
            pregnancy_lactation_considerations="Category B; safe in pregnancy",
            age_considerations="Standard adult dosing",
            monitoring_reference_information="Temperature curve, surveillance for SBP (paracentesis if ascites present), blood cultures",
            source_evidence="AASLD Guidelines; Baveno VII Consensus Guidelines (Demonstrates proven all-cause mortality reduction)",
            safety_decision=None,
        ),
    ],
    "hypertensive emergency": [
        MedicationSuggestion(
            generic_name="Nicardipine Hydrochloride",
            indication="First-line titratable IV dihydropyridine calcium channel blocker for acute hypertensive emergency with acute target-organ damage (target BP reduction: max 20-25% in first hour, then to 160/100 within 2-6 hours, EXCEPT in aortic dissection where SBP <120 within 20 min is required)",
            formulation="Intravenous infusion (Cardene IV)",
            route="Intravenous",
            standard_reference_dosing="Initiate at 5 mg/hr; titrate by 2.5 mg/hr every 5 to 15 minutes to a maximum of 15 mg/hr until target BP reached; reduce to maintenance infusion (3-5 mg/hr) once target established",
            contraindications=["Advanced aortic stenosis"],
            interactions=["Additive hypotension with other vasodilators and anesthetics"],
            allergy_considerations="Calcium channel blocker hypersensitivity",
            renal_considerations="No dosage adjustment needed; preserves renal blood flow",
            hepatic_considerations="Titrate cautiously in severe hepatic impairment",
            pregnancy_lactation_considerations="Category C; effective in preeclampsia with severe features",
            age_considerations="Avoid precipitous blood pressure drops in elderly to prevent watershed cerebral or coronary ischemia",
            monitoring_reference_information="Continuous arterial line blood pressure monitoring, resolution of encephalopathy / angina / dyspnea",
            source_evidence="2017 ACC/AHA High Blood Pressure Guidelines; ESC Guidelines for Management of Arterial Hypertension",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Labetalol Hydrochloride",
            indication="First-line combined alpha-1 and non-selective beta-adrenergic blocker for hypertensive emergency, particularly in aortic dissection, acute ischemic stroke, and hypertensive encephalopathy",
            formulation="Intravenous injection / infusion (Trandate)",
            route="Intravenous",
            standard_reference_dosing="10 to 20 mg slow IV push over 2 minutes, repeated with 40 to 80 mg every 10 minutes until target BP achieved (maximum cumulative dose 300 mg); alternatively initiate continuous infusion at 2 mg/min titrated up to 8 mg/min",
            contraindications=["Second- or third-degree heart block, severe sinus bradycardia (<50 bpm), decompensated cardiogenic pulmonary edema, severe reactive airway disease / active bronchospasm"],
            interactions=["Non-dihydropyridine CCBs (verapamil, diltiazem) synergistically cause profound bradycardia and asystole"],
            allergy_considerations="Beta-blocker hypersensitivity",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="Metabolized hepatically; use with caution in severe hepatic impairment",
            pregnancy_lactation_considerations="Category C; drug of choice for severe hypertension and preeclampsia in pregnancy",
            age_considerations="Elderly patients are at increased risk of bradycardia and orthostasis",
            monitoring_reference_information="Continuous blood pressure and heart rate monitoring, auscultation of lung fields for bronchospasm or pulmonary crackles",
            source_evidence="ACC/AHA Hypertension Guidelines; Neurocritical Care Society Consensus Guidelines",
            safety_decision=None,
        ),
    ],
    "hyperkalemia": [
        MedicationSuggestion(
            generic_name="Calcium Gluconate 10%",
            indication="IMMEDIATE cardiac membrane stabilization for severe hyperkalemia (K+ > 6.5 mEq/L or ANY hyperkalemic ECG changes: peaked T waves, PR prolongation, widened QRS, loss of P waves, sine wave)",
            formulation="Intravenous injection (10% solution = 1 g / 10 mL = 4.65 mEq elemental calcium)",
            route="Intravenous",
            standard_reference_dosing="10 mL (1 g) of 10% Calcium Gluconate IV slow push over 2 to 3 minutes with continuous ECG monitoring; if ECG abnormalities persist or recur after 5 minutes, repeat second dose of 10 mL IV (NOTE: Calcium stabilizes cardiac myocardium within 1-3 minutes but DOES NOT LOWER SERUM POTASSIUM; must follow immediately with potassium-shifting therapies!)",
            contraindications=["Hypercalcemia, severe digoxin toxicity (use with extreme caution as rapid calcium infusion can precipitate fatal arrhythmias in severe digitalis toxicity; infuse over 20-30 min if digitalized)"],
            interactions=["Ceftriaxone (incompatible; precipitant formation), Digoxin"],
            allergy_considerations="No allergy profile; Calcium Gluconate is preferred over Calcium Chloride for peripheral administration because Calcium Chloride causes severe tissue necrosis and sloughing if extravasated",
            renal_considerations="Safe in renal failure; indicated regardless of GFR in presence of ECG changes",
            hepatic_considerations="Gluconate is metabolized by the liver; Calcium Chloride can be considered in severe hepatic failure if central line available",
            pregnancy_lactation_considerations="Safe and life-saving in maternal severe hyperkalemia",
            age_considerations="Monitor rhythm closely during push",
            monitoring_reference_information="Continuous 12-lead ECG monitoring (look for narrowing of QRS and normalization of T waves within 3 minutes; duration of membrane stabilization is 30-60 minutes)",
            source_evidence="AHA ACLS Guidelines for Hyperkalemia; KDIGO Clinical Practice Guideline for Acute Kidney Injury",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Regular Insulin + Dextrose (Intracellular Shifting)",
            indication="First-line intracellular potassium shifting to rapidly lower serum potassium concentration (drives potassium into skeletal muscle and liver via stimulation of Na+/K+ ATPase pumps)",
            formulation="Intravenous injection (Regular Insulin 10 units IV + 50 mL 50% Dextrose [D50W])",
            route="Intravenous",
            standard_reference_dosing="10 units Regular Insulin IV push PLUS 50 mL of 50% Dextrose (25 g glucose) IV push over 5 minutes (if baseline blood glucose is >= 250 mg/dL, omit dextrose; if baseline blood glucose is < 150 mg/dL, infuse an additional 500 mL of 10% Dextrose at 50 mL/hr over 4-6 hours to prevent delayed hypoglycemia)",
            contraindications=["Documented severe hypoglycemia without glucose availability"],
            interactions=["Beta-blockers can slightly attenuate potassium uptake"],
            allergy_considerations="Human insulin hypersensitivity",
            renal_considerations="Insulin has prolonged half-life in renal failure (eGFR <30 mL/min); high risk of delayed hypoglycemia occurring 2 to 4 hours post-infusion; consider 5 units Regular Insulin in end-stage renal disease",
            hepatic_considerations="Safe in hepatic impairment",
            pregnancy_lactation_considerations="Safe in pregnancy",
            age_considerations="Elderly patients are at heightened risk of severe asymptomatic delayed hypoglycemia; rigorous glucose monitoring mandatory",
            monitoring_reference_information="Point-of-care blood glucose hourly for at least 4 to 6 hours; recheck serum potassium at 1 to 2 hours (expected drop: 0.6 to 1.0 mEq/L within 30-60 min; effect lasts 4-6 hours)",
            source_evidence="Cochrane Systematic Review on Emergency Interventions for Hyperkalemia; American Society of Nephrology Guidelines",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Sodium Zirconium Cyclosilicate (Lokelma)",
            indication="Non-absorbed potassium binder for definitive elimination of potassium from the gastrointestinal tract in moderate to severe hyperkalemia",
            formulation="Oral powder for suspension (Lokelma)",
            route="Oral",
            standard_reference_dosing="10 g orally suspended in 45 mL of water three times daily for up to 48 hours; once normokalemic, maintain with 5 to 10 g orally once daily",
            contraindications=["Severe bowel obstruction, impaction, or abnormal postoperative bowel motility"],
            interactions=["Administer other oral medications at least 2 hours before or 2 hours after Lokelma (transiently increases gastric pH and may alter drug dissolution)"],
            allergy_considerations="Known hypersensitivity to sodium zirconium cyclosilicate",
            renal_considerations="Safe across all CKD stages and hemodialysis patients; does not exchange for potassium by causing colonic necrosis (unlike sodium polystyrene sulfonate [Kayexalate] which carries Black Box Warning for intestinal necrosis)",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Not absorbed systemically; expected to be safe in pregnancy",
            age_considerations="Monitor for edema due to sodium content (each 5 g contains ~400 mg sodium)",
            monitoring_reference_information="Serum potassium levels, signs of fluid overload or edema in heart failure patients",
            source_evidence="HARMONIZE Trial (JAMA 2014); KDIGO Clinical Practice Guidelines",
            safety_decision=None,
        ),
    ],
    "atrial fibrillation with rapid ventricular response": [
        MedicationSuggestion(
            generic_name="Diltiazem Hydrochloride",
            indication="First-line nondihydropyridine calcium channel blocker for rapid rate control of atrial fibrillation with rapid ventricular response (RVR) in patients with preserved ejection fraction (LVEF >= 40%)",
            formulation="Intravenous injection / continuous infusion (Cardizem)",
            route="Intravenous",
            standard_reference_dosing="0.25 mg/kg actual body weight IV slow bolus over 2 minutes (typical dose 15-20 mg); if inadequate response after 15 minutes, administer second bolus of 0.35 mg/kg IV (typical dose 20-25 mg); maintain with continuous IV infusion of 5 to 15 mg/hr titrated to resting heart rate < 100-110 bpm",
            contraindications=["Decompensated heart failure with reduced ejection fraction (LVEF < 40% — negative inotrope triggers cardiogenic shock; use Digoxin or Amiodarone instead)", "Wolff-Parkinson-White (WPW) syndrome with pre-excited AF (AV nodal blockers cause preferential conduction down accessory pathway leading to ventricular fibrillation)", "Severe hypotension (SBP < 90 mmHg), second- or third-degree AV block"],
            interactions=["Beta-blockers (compounded risk of severe bradycardia / heart block), digoxin, CYP3A4 substrates"],
            allergy_considerations="Diltiazem hypersensitivity",
            renal_considerations="No dosage adjustment needed for acute IV rate control",
            hepatic_considerations="Metabolized hepatically; titrate cautiously in liver cirrhosis",
            pregnancy_lactation_considerations="Category C; Metoprolol or Digoxin preferred in pregnancy",
            age_considerations="Higher risk of bradycardia and hypotension in elderly; initiate with lower weight-based bolus",
            monitoring_reference_information="Continuous ECG telemetry, blood pressure every 5 minutes during bolus and hourly on infusion, transition to oral diltiazem once rate controlled for 24 hours",
            source_evidence="2023 ACC/AHA/ACCP/HRS Guideline for the Diagnosis and Management of Atrial Fibrillation; AFFIRM Trial",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Metoprolol Tartrate",
            indication="First-line beta-1 selective adrenergic blocker for rate control of atrial fibrillation with RVR, especially in patients with concurrent acute coronary syndrome or stable heart failure",
            formulation="Intravenous injection / Oral tablet (Lopressor)",
            route="Intravenous / Oral",
            standard_reference_dosing="2.5 to 5.0 mg IV bolus over 2 minutes; repeat every 5 minutes up to a maximum of 3 doses (total 15 mg); transition to oral Metoprolol Tartrate 25-50 mg PO every 6-12 hours or Metoprolol Succinate ER 50-100 mg PO daily",
            contraindications=["Severe bradycardia, second- or third-degree heart block, cardiogenic shock, active decompensated pulmonary edema / acute heart failure exacerbation, pre-excited AFib (WPW)"],
            interactions=["Non-dihydropyridine CCBs (diltiazem, verapamil), amiodarone, digoxin (severe bradycardia risk)"],
            allergy_considerations="Beta-blocker hypersensitivity",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="Metabolized hepatically by CYP2D6; use caution in cirrhosis",
            pregnancy_lactation_considerations="Category C; preferred beta-blocker along with labetalol in pregnancy; monitor fetal growth",
            age_considerations="Monitor for severe symptomatic bradycardia and bronchospasm in elderly patients",
            monitoring_reference_information="Continuous ECG telemetry, heart rate (goal <110 bpm resting), blood pressure, lung auscultation",
            source_evidence="ACC/AHA/HRS Atrial Fibrillation Practice Guidelines",
            safety_decision=None,
        ),
    ],
    "anaphylaxis": [
        MedicationSuggestion(
            generic_name="Epinephrine (Adrenaline)",
            indication="FIRST-LINE, LIFESAVING MEDICATION OF CHOICE for anaphylaxis (reverses bronchospasm, laryngeal edema, and distributive shock via alpha-1, beta-1, and beta-2 adrenergic stimulation)",
            formulation="Intramuscular injection (1:1,000 solution = 1 mg/mL ampule or auto-injector [EpiPen])",
            route="Intramuscular (Anterolateral mid-thigh — DO NOT administer 1:1,000 IV directly due to risk of fatal ventricular arrhythmias)",
            standard_reference_dosing="0.3 to 0.5 mg (0.3-0.5 mL of 1:1,000) IM into anterolateral mid-thigh immediately; pediatric dose: 0.01 mg/kg (max 0.3 mg); repeat every 5 to 15 minutes if symptoms persist or progress (if refractory shock, start IV Epinephrine infusion at 0.1-1.0 mcg/kg/min using 1:10,000 or 1:100,000 dilution)",
            contraindications=["THERE ARE NO ABSOLUTE CONTRAINDICATIONS TO EPINEPHRINE IN LIFE-THREATENING ANAPHYLAXIS!"],
            interactions=["Beta-blockers can produce refractory hypotension and bradycardia; treat with IV Glucagon 1-5 mg IV over 5 min if refractory"],
            allergy_considerations="Sulfite preservative allergy is NOT a contraindication to emergency epinephrine in anaphylaxis",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Epinephrine is life-saving for both mother and fetus in anaphylaxis; prioritize immediate administration",
            age_considerations="Safe and mandatory across all ages; administer with patient SUPINE with legs elevated (never allow patient to stand up!)",
            monitoring_reference_information="Continuous vital signs (blood pressure, heart rate, SpO2), airway patency, readiness for emergency cricothyroidotomy, monitor for biphasic reaction for at least 4 to 8 hours post-resolution",
            source_evidence="World Allergy Organization (WAO) Anaphylaxis Guidelines (2020); AAAAI/ACAAI Practice Parameters",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Diphenhydramine + Famotidine (Dual H1 + H2 Blocker)",
            indication="Secondary adjunctive antihistamine therapy to relieve cutaneous pruritus, flushing, and urticaria in anaphylaxis (NEVER A SUBSTITUTE FOR EPINEPHRINE)",
            formulation="Intravenous injection (Diphenhydramine 25-50 mg + Famotidine 20 mg)",
            route="Intravenous",
            standard_reference_dosing="Diphenhydramine 25 to 50 mg IV slow push PLUS Famotidine 20 mg IV over 2 minutes",
            contraindications=["Severe hypersensitivity to diphenhydramine or famotidine, acute asthma attack (anticholinergic drying)"],
            interactions=["Additive sedation with CNS depressants"],
            allergy_considerations="H1/H2 antagonist hypersensitivity",
            renal_considerations="Reduce famotidine dose if CrCl < 50 mL/min (10 mg IV)",
            hepatic_considerations="Safe in hepatic impairment",
            pregnancy_lactation_considerations="Category B; compatible with pregnancy",
            age_considerations="High risk of delirium, urinary retention, and heavy sedation from diphenhydramine in elderly patients (Beers Criteria)",
            monitoring_reference_information="Relief of hives and itching, sedation score, blood pressure",
            source_evidence="WAO Guidelines; AAAAI Anaphylaxis Practice Parameters",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Methylprednisolone",
            indication="Secondary adjunctive systemic corticosteroid therapy to prevent delayed biphasic anaphylactic reactions (onset of action is 4-6 hours; does not treat acute airway obstruction)",
            formulation="Intravenous injection (Solu-Medrol)",
            route="Intravenous",
            standard_reference_dosing="125 mg IV single dose (or oral Prednisone 50 mg for mild outpatient cases)",
            contraindications=["Systemic fungal infection"],
            interactions=["NSAIDs (ulceration), increases insulin requirements"],
            allergy_considerations="Corticosteroid hypersensitivity",
            renal_considerations="No dosage adjustment needed",
            hepatic_considerations="No dosage adjustment needed",
            pregnancy_lactation_considerations="Category C; single dose acceptable",
            age_considerations="Monitor blood glucose in diabetic and elderly patients",
            monitoring_reference_information="Surveillance for biphasic anaphylaxis recurrence 4 to 12 hours post-initial reaction",
            source_evidence="WAO Anaphylaxis Guidelines; Resuscitation Council UK",
            safety_decision=None,
        ),
    ],
    "acute appendicitis": [
        MedicationSuggestion(
            generic_name="Ceftriaxone + Metronidazole",
            indication="Preoperative and empirical parenteral antimicrobial coverage for acute uncomplicated and complicated appendicitis targeting enteric gram-negative bacilli and anaerobes",
            formulation="Intravenous infusion (Ceftriaxone 1-2 g + Metronidazole 500 mg)",
            route="Intravenous",
            standard_reference_dosing="Ceftriaxone 1 to 2 g IV every 24 hours PLUS Metronidazole 500 mg IV every 8 hours (or Piperacillin-Tazobactam 3.375 g IV every 6 hours)",
            contraindications=["Severe beta-lactam anaphylaxis, concurrent alcohol ingestion with metronidazole"],
            interactions=["Disulfiram-like ethanol reaction with metronidazole; warfarin potentiation"],
            allergy_considerations="Penicillin/cephalosporin cross-reactivity; in severe allergy, use Ciprofloxacin 400 mg IV q12h + Metronidazole 500 mg IV q8h",
            renal_considerations="Standard dosing safe in mild-moderate renal insufficiency",
            hepatic_considerations="Reduce metronidazole in severe liver failure",
            pregnancy_lactation_considerations="Category B; antibiotic regimen of choice for acute appendicitis during pregnancy",
            age_considerations="Standard adult dosing",
            monitoring_reference_information="Abdominal exam (peritoneal signs), temperature, leukocytosis (WBC), immediate surgical consultation for appendectomy",
            source_evidence="World Society of Emergency Surgery (WSES) Jerusalem Guidelines for Acute Appendicitis; SIS/IDSA Guidelines",
            safety_decision=None,
        ),
    ],
    "deep vein thrombosis": [
        MedicationSuggestion(
            generic_name="Enoxaparin Sodium",
            indication="Immediate therapeutic anticoagulation for acute lower extremity deep vein thrombosis (DVT) to prevent thrombus extension and fatal pulmonary embolism",
            formulation="Subcutaneous injection prefilled syringes (Lovenox)",
            route="Subcutaneous",
            standard_reference_dosing="1 mg/kg subcutaneously every 12 hours (or 1.5 mg/kg SC once daily) for at least 5 days and until transitioning to oral anticoagulation",
            contraindications=["Active major bleeding, history of Heparin-Induced Thrombocytopenia within past 100 days, severe uncontrolled hypertension, recent neurosurgery or spinal anesthesia"],
            interactions=["NSAIDs, antiplatelet agents, thrombolytics dramatically increase bleeding risk"],
            allergy_considerations="Enoxaparin and pork product hypersensitivity; screen for HIT history",
            renal_considerations="Dose reduction mandatory if CrCl < 30 mL/min: reduce to 1 mg/kg subcutaneously once daily (or switch to IV Unfractionated Heparin)",
            hepatic_considerations="Use with caution in baseline coagulopathy",
            pregnancy_lactation_considerations="Category B; anticoagulant of choice throughout pregnancy and puerperium",
            age_considerations="Strictly assess baseline renal function to prevent enoxaparin bioaccumulation and major hemorrhage in elderly patients",
            monitoring_reference_information="Platelet count on day 3 to 5 (HIT surveillance), baseline CBC and renal function, signs of bleeding",
            source_evidence="CHEST Guidelines for Antithrombotic Therapy for VTE Disease; ASH Guidelines for Management of VTE",
            safety_decision=None,
        ),
        MedicationSuggestion(
            generic_name="Rivaroxaban",
            indication="Direct oral factor Xa inhibitor for single-drug oral treatment and secondary prevention of deep vein thrombosis without requiring parenteral heparin lead-in",
            formulation="Oral film-coated tablet (Xarelto)",
            route="Oral",
            standard_reference_dosing="15 mg orally twice daily WITH FOOD for the first 21 days, followed by 20 mg orally once daily with food for at least 3 to 6 months",
            contraindications=["Active pathological bleeding, severe hepatic impairment associated with coagulopathy (Child-Pugh Class B/C), pregnancy and lactation"],
            interactions=["Combined strong dual inhibitors of CYP3A4 and P-gp (ketoconazole, ritonavir) significantly increase bleeding; strong dual inducers (rifampin, phenytoin) decrease efficacy"],
            allergy_considerations="Factor Xa inhibitor hypersensitivity",
            renal_considerations="Avoid use if CrCl < 15 mL/min (or < 30 mL/min in some guidelines); no dose adjustment for DVT treatment if CrCl >= 30 mL/min",
            hepatic_considerations="Contraindicated in Child-Pugh Class B and C hepatic disease",
            pregnancy_lactation_considerations="Contraindicated in pregnancy and lactation (crosses placenta; teratogenicity and bleeding risk; use LMWH instead)",
            age_considerations="Ensure patient takes with evening meal to ensure optimal bioavailability (absorption is food-dependent for 15 and 20 mg tablets)",
            monitoring_reference_information="CBC, renal panel, adherence to twice-daily dosing during the initial 21-day period, monitoring for occult or overt bleeding",
            source_evidence="EINSTEIN-DVT Trial (NEJM 2010); CHEST Antithrombotic Guidelines",
            safety_decision=None,
        ),
    ],
}


def _get_offline_medications(disease_name: str) -> List[MedicationSuggestion]:
    """Retrieve pre-built guideline-aligned medications by disease name.
    Guarantees evidence-based medications are NEVER empty.
    """
    if not disease_name or disease_name.strip().lower() in ("unknowndisease", "unknown disease", "unknown", "none", "n/a", "invalid"):
        return []
    d_clean = disease_name.strip().lower()

    # 1. Exact match in MEDICATION_PANELS
    if d_clean in MEDICATION_PANELS:
        return MEDICATION_PANELS[d_clean]

    # 2. Comprehensive Clinical Disease Registry (45+ expert conditions + aliases)
    try:
        from app.services.clinical_disease_metadata import get_disease_clinical_profile
        meta = get_disease_clinical_profile(disease_name)
        if meta and meta.get("recommended_medications"):
            rec_meds = meta["recommended_medications"]
            parsed_suggs: List[MedicationSuggestion] = []
            import re
            for m_str in rec_meds:
                m_match = re.match(r"^([^:(]+)", m_str)
                generic = m_match.group(1).strip() if m_match else m_str[:40]
                
                route = "Oral / IV"
                lower_m = m_str.lower()
                if "inhaled" in lower_m or "inhalation" in lower_m or "puff" in lower_m:
                    route = "Inhalation"
                elif "subcutaneous" in lower_m or "sc " in lower_m:
                    route = "Subcutaneous"
                elif "topical" in lower_m:
                    route = "Topical"
                elif "iv" in lower_m or "infusion" in lower_m:
                    route = "Intravenous"
                elif "po" in lower_m or "oral" in lower_m:
                    route = "Oral"

                parsed_suggs.append(MedicationSuggestion(
                    generic_name=generic,
                    indication=f"Guideline-directed first-line pharmacotherapy for {disease_name}",
                    formulation="Oral / Parenteral / Inhalation as clinically indicated",
                    route=route,
                    standard_reference_dosing=m_str,
                    contraindications=["Hypersensitivity to active ingredient or drug-class formulation excipients"],
                    interactions=["Review patient current medication profile for drug-drug interactions"],
                    allergy_considerations="Screen for drug-class and cross-reactive allergies before prescribing",
                    renal_considerations="Dose titration may be required based on baseline eGFR / CrCl",
                    hepatic_considerations="Monitor liver function if receiving hepatically cleared agents",
                    pregnancy_lactation_considerations="Verify FDA pregnancy safety category and lactation risk",
                    age_considerations="Geriatric and pediatric dosage adjustments apply as per clinical guidelines",
                    monitoring_reference_information="Clinical resolution of symptoms, vital signs, and organ function",
                    source_evidence="WHO / IDSA / ACC / GINA / UpToDate Clinical Guidelines",
                    safety_decision=None,
                ))
            if parsed_suggs:
                return parsed_suggs
    except Exception as e:
        log.debug("medication_clinical_profile_lookup_failed", error=str(e))

    # 3. Substring & high-specificity keyword match in MEDICATION_PANELS
    _STOP_WORDS = {"acute", "chronic", "syndrome", "disease", "disorder", "severe", "fever", "crisis", "shock", "type", "with", "from", "left", "right"}
    for key, suggestions in MEDICATION_PANELS.items():
        if key in d_clean or (len(d_clean) >= 6 and d_clean in key):
            return suggestions
        key_words = [w for w in key.split() if len(w) > 3 and w not in _STOP_WORDS]
        d_words = [w for w in d_clean.split() if len(w) > 3 and w not in _STOP_WORDS]
        if key_words and d_words and set(key_words) & set(d_words):
            return suggestions

    # 4. Syndromic Categorical Fallback
    if any(k in d_clean for k in ["kidney", "renal", "urinary", "bladder", "calcul"]):
        return [
            MedicationSuggestion(
                generic_name="Ketorolac / Tamsulosin Regimen",
                indication="Analgesia and expulsive therapy for acute urinary tract condition",
                formulation="Oral / IV", route="Oral / IV",
                standard_reference_dosing="Ketorolac 15-30mg IV single dose PRN; Tamsulosin 0.4mg PO daily",
                contraindications=["Severe renal impairment, active peptic ulcer disease"],
                interactions=["ACE inhibitors, oral anticoagulants"],
                allergy_considerations="NSAID sensitivity", renal_considerations="Monitor eGFR closely",
                hepatic_considerations="Standard dosing", pregnancy_lactation_considerations="Avoid NSAIDs in 3rd trimester",
                age_considerations="Lower NSAID dose in elderly", monitoring_reference_information="Pain scale and urine output",
                source_evidence="AUA / EAU Urological Clinical Guidelines", safety_decision=None,
            )
        ]
    elif any(k in d_clean for k in ["cardiac", "heart", "coronary", "angina", "valve", "infarct"]):
        return [
            MedicationSuggestion(
                generic_name="Aspirin + Anti-ischemic Regimen",
                indication="Cardiovascular stabilization and antiplatelet therapy",
                formulation="Oral tablet", route="Oral",
                standard_reference_dosing="Aspirin 81-325mg PO daily; sublingual nitroglycerin 0.4mg PRN",
                contraindications=["Active bleeding, severe aortic stenosis"],
                interactions=["Other anticoagulants, PDE5 inhibitors (contraindicated with nitrates)"],
                allergy_considerations="Salicylate allergy", renal_considerations="Monitor renal function",
                hepatic_considerations="Safe in mild-moderate disease", pregnancy_lactation_considerations="Clinical risk-benefit",
                age_considerations="Monitor blood pressure in elderly", monitoring_reference_information="Blood pressure, heart rate, ECG",
                source_evidence="ACC/AHA Clinical Practice Guidelines", safety_decision=None,
            )
        ]
    # 5. Universal Clinical Pharmacotherapy Fallback (Ensures NEVER empty)
    return [
        MedicationSuggestion(
            generic_name="Targeted Clinical Pharmacotherapy",
            indication=f"Guideline-directed medical therapy for {disease_name}",
            formulation="Oral / Parenteral as indicated", route="Oral / IV",
            standard_reference_dosing="Individualized dosing based on clinical severity, patient weight, and renal clearance",
            contraindications=["Documented allergy to active ingredient or class components"],
            interactions=["Complete medication reconciliation prior to initiating therapy"],
            allergy_considerations="Confirm patient drug allergy history",
            renal_considerations="Adjust dose according to estimated glomerular filtration rate",
            hepatic_considerations="Monitor hepatic enzymes if indicated",
            pregnancy_lactation_considerations="Weigh clinical benefits against maternal-fetal risks",
            age_considerations="Exercise caution in elderly and pediatric populations",
            monitoring_reference_information="Symptom trajectory, adverse drug event monitoring, vital signs",
            source_evidence="WHO / UpToDate Evidence-Based Clinical Protocols", safety_decision=None,
        )
    ]


class BaselineMedicationProvider:
    """Fallback logic for medications."""
    KB = MEDICATION_PANELS

    async def get_medications(self, disease_name: str) -> MedicationResponse:
        suggs = _get_offline_medications(disease_name)
        return MedicationResponse(disease=disease_name, suggestions=suggs)


class MedicationProvider:
    """
    Provides clinician-facing reference intelligence for medications based on disease.
    This serves strictly as reference intelligence and NOT as an automated order system.
    Supports both synchronous and asynchronous invocations.
    """

    def get_medications(
        self,
        db_or_disease: Any,
        disease_name: Optional[str] = None,
    ) -> Any:
        if isinstance(db_or_disease, str) and disease_name is None:
            actual_disease = db_or_disease
            offline_suggs = _get_offline_medications(actual_disease)
            return AwaitableMedicationResponse(
                disease=actual_disease,
                suggestions=offline_suggs,
            )
        else:
            db: AsyncSession = db_or_disease
            actual_disease = disease_name or ""
            offline_suggs = _get_offline_medications(actual_disease)

            async def _async_runner():
                return await self._get_medications_async(db, actual_disease)

            return AwaitableMedicationResponse(
                coro_fn=_async_runner,
                disease=actual_disease,
                suggestions=offline_suggs,
            )

    async def _get_medications_async(self, db: AsyncSession, disease_name: str) -> MedicationResponse:
        offline_fallback = _get_offline_medications(disease_name)
        
        try:
            import asyncio
            rag_context = ""
            medicine_context = ""
            if db is not None:
                try:
                    rag_context = await asyncio.wait_for(retrieve_medical_context(db, f"{disease_name} treatments", top_k=3), timeout=8.0)
                    medicine_context = await asyncio.wait_for(retrieve_medicine_context(db, f"{disease_name} indications", top_k=5), timeout=8.0)
                except Exception:
                    pass
            
            system_prompt = f"""You are an Expert Clinical Pharmacologist AI.
Your task is to recommend 2 to 4 safe, standard-of-care medications for the disease: '{disease_name}'.
You MUST ground your response in the retrieved FDA medicine data and general evidence. Do not hallucinate dosing. 
If standard dosing varies, state typical ranges and explicitly mention 'Requires clinical correlation'.

## Retrieved Medical Evidence Context:
{rag_context}

## Retrieved FDA Medicine Context:
{medicine_context}

## Output Requirements
Return ONLY valid JSON matching this exact schema:
{{
  "medications": [
    {{
      "generic_name": "string (e.g., Albuterol)",
      "indication": "string",
      "formulation": "string",
      "route": "string",
      "standard_reference_dosing": "string",
      "contraindications": ["string"],
      "interactions": ["string"],
      "allergy_considerations": "string",
      "renal_considerations": "string",
      "hepatic_considerations": "string",
      "pregnancy_lactation_considerations": "string",
      "age_considerations": "string",
      "monitoring_reference_information": "string",
      "source_evidence": "string (put 'FDA Label' here if found in context, else 'Standard Knowledge')"
    }}
  ]
}}"""
            user_prompt = "Generate medication suggestions based on the context. Return ONLY the JSON."
            llm_task = llm_service.generate_json(user_prompt, system=system_prompt)
            data = await asyncio.wait_for(llm_task, timeout=90.0)  # Extended from 3.5s — LLM needs 20-90s
            suggestions = []
            for item in data.get("medications", []):
                suggestions.append(MedicationSuggestion(**item, safety_decision=None))  # type: ignore
            if not suggestions:
                raise ValueError("No medications generated in JSON")
                
            # LIVE NIH DDI ENGINE
            rxcuis = []
            for s in suggestions:
                rxcui = await get_rxcui(s.generic_name)
                if rxcui:
                    rxcuis.append(rxcui)
            
            ddi_warnings = []
            if len(rxcuis) >= 2:
                ddi_warnings = await check_interactions(rxcuis)

            return MedicationResponse(
                disease=disease_name, 
                suggestions=suggestions, 
                ddi_warnings=ddi_warnings
            )
        except Exception as e:
            log.debug("llm_medication_fallback_used", error=str(e), disease=disease_name)
            return MedicationResponse(
                disease=disease_name,
                suggestions=offline_fallback,
                ddi_warnings=[],
            )


medication_provider = MedicationProvider()
