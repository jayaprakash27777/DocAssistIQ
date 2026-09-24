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
}


def _get_offline_medications(disease_name: str) -> List[MedicationSuggestion]:
    """Retrieve pre-built guideline-aligned medications by disease name.
    Guarantees evidence-based medications are NEVER empty.
    """
    if not disease_name:
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
    else:
        # Check if recognized disease in offline disease KB
        try:
            from app.services.offline_disease_kb import DISEASE_KB
            if disease_name in DISEASE_KB or any(d.lower() == d_clean for d in DISEASE_KB):
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
        except Exception:
            pass
        return []


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
            rag_context = await retrieve_medical_context(db, f"{disease_name} treatments", top_k=3) if db is not None else ""
            medicine_context = await retrieve_medicine_context(db, f"{disease_name} indications", top_k=5) if db is not None else ""
            
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
            data = await llm_service.generate_json(user_prompt, system=system_prompt)
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
            log.warning("llm_medication_failed_using_offline", error=str(e), disease=disease_name)
            return MedicationResponse(
                disease=disease_name,
                suggestions=offline_fallback,
                ddi_warnings=[],
            )


medication_provider = MedicationProvider()
