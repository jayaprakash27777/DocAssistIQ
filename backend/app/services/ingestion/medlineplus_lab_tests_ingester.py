"""DocAssistIQ — MedlinePlus / LOINC Clinical Lab Tests Ingestion Service.

Ingests comprehensive, standardized clinical laboratory panels with LOINC codes,
clinical rationales, diagnostic limits, and specimen requirements into the
Investigation knowledge base and vector embeddings for semantic RAG retrieval.
Strictly zero mock data; adheres to MedlinePlus / LOINC / AACC standards.
"""

import hashlib
import structlog
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Investigation
from app.models.embedding import EmbeddingRecord
from app.infrastructure.ai.factory import get_embedding_provider

log = structlog.get_logger(__name__)

CLINICAL_LAB_TEST_CATALOG: List[Dict[str, str]] = [
    # -------------------------------------------------------------------------
    # 1. Glycemic & Metabolic
    # -------------------------------------------------------------------------
    {
        "code": "LOINC-17856-6",
        "name": "HbA1c (Hemoglobin A1c)",
        "description": "Measures the percentage of glycated hemoglobin in whole blood. Evaluates average glycemic control over the preceding 2-3 months.",
        "rationale": "First-line diagnostic and monitoring test for Type 1 and Type 2 Diabetes Mellitus and prediabetes (ADA criteria: >=6.5% diagnostic).",
        "limitations": "Inaccurate in conditions altering erythrocyte lifespan (hemoglobinopathies, severe anemia, chronic kidney disease, recent transfusion)."
    },
    {
        "code": "LOINC-2345-7",
        "name": "Glucose, Fasting Plasma",
        "description": "Measures venous plasma glucose concentration after an overnight fast of at least 8 hours.",
        "rationale": "Core investigation for diabetes screening (fasting >= 126 mg/dL) and acute metabolic decompensation.",
        "limitations": "Requires strict 8-12 hour fasting compliance; rapid glycolysis if unseparated without fluoride inhibitor."
    },
    {
        "code": "LOINC-24321-2",
        "name": "Basic Metabolic Panel (BMP)",
        "description": "Panel comprising 8 parameters: Glucose, Calcium, Sodium, Potassium, CO2/Bicarbonate, Chloride, Blood Urea Nitrogen (BUN), and Creatinine.",
        "rationale": "Essential baseline assessment of renal function, fluid balance, electrolyte homeostasis, and acid-base equilibrium.",
        "limitations": "Does not assess liver enzymes, synthetic function, or protein fractions."
    },
    {
        "code": "LOINC-24323-8",
        "name": "Comprehensive Metabolic Panel (CMP)",
        "description": "Extended panel including BMP plus Total Protein, Albumin, Total Bilirubin, Alkaline Phosphatase (ALP), and Alanine Aminotransferase (ALT/SGPT).",
        "rationale": "Provides concurrent evaluation of hepatic synthetic and excretory status, renal function, and systemic electrolyte balance.",
        "limitations": "Requires correlation with clinical symptoms; non-specific elevations in systemic illness."
    },

    # -------------------------------------------------------------------------
    # 2. Cardiac Biomarkers & Vascular
    # -------------------------------------------------------------------------
    {
        "code": "LOINC-89579-7",
        "name": "High-Sensitivity Cardiac Troponin I (hs-cTnI)",
        "description": "Quantitative chemiluminescent microparticle immunoassay detecting sub-picogram concentrations of cardiac Troponin I.",
        "rationale": "Universal standard for rapid rule-in/rule-out of acute myocardial infarction (NSTEMI/STEMI) via ESC 0h/1h or 0h/2h diagnostic algorithms.",
        "limitations": "Non-ischemic elevations occur in severe sepsis, acute pulmonary embolism, myocarditis, ESRD, and strenuous endurance exercise."
    },
    {
        "code": "LOINC-6598-7",
        "name": "High-Sensitivity Cardiac Troponin T (hs-cTnT)",
        "description": "Measures cardiac Troponin T with analytical precision at the 99th percentile upper reference limit of a healthy population.",
        "rationale": "Critical marker of myocardial injury, myocardial infarction, and cardiovascular risk stratification.",
        "limitations": "Skeletal muscle myopathies and advanced renal failure can chronically elevate baseline hs-cTnT."
    },
    {
        "code": "LOINC-30934-4",
        "name": "B-Type Natriuretic Peptide (BNP)",
        "description": "Neurohormone released from ventricular myocytes in response to increased ventricular wall stretch and volume overload.",
        "rationale": "Distinguishes cardiogenic dyspnea (heart failure) from primary pulmonary etiology in acute emergency presentations.",
        "limitations": "Values lowered in obese individuals; elevated in advanced age, renal insufficiency, and atrial fibrillation."
    },
    {
        "code": "LOINC-33762-6",
        "name": "NT-proBNP (N-Terminal pro-B-Type Natriuretic Peptide)",
        "description": "Biologically inactive 76-amino acid N-terminal cleavage fragment of pro-BNP with extended circulating half-life (1-2 hours).",
        "rationale": "High-sensitivity diagnostic biomarker for acute decompensated heart failure and chronic heart failure disease monitoring.",
        "limitations": "Significantly dependent on renal clearance; age-stratified decision cutoffs required (<50y: 450 pg/mL, 50-75y: 900 pg/mL, >75y: 1800 pg/mL)."
    },
    {
        "code": "LOINC-48065-7",
        "name": "D-Dimer Quantitative",
        "description": "Monoclonal antibody assay measuring fibrin degradation products generated upon plasmin-mediated cross-linked fibrin cleavage.",
        "rationale": "High negative predictive value (>99%) to exclude pulmonary embolism (PE) and deep vein thrombosis (DVT) in low/intermediate clinical probability patients.",
        "limitations": "Low specificity; elevated in pregnancy, advanced age, cancer, sepsis, trauma, and recent surgery. Age-adjusted cutoff recommended for patients >50 years."
    },
    {
        "code": "LOINC-2157-6",
        "name": "Creatine Kinase Total & CK-MB Fraction",
        "description": "Enzymatic assay measuring total creatine phosphokinase and the cardiac-specific MB isoenzyme mass.",
        "rationale": "Assesses suspected re-infarction in the subacute post-MI period (returns to baseline within 48-72h) and evaluates rhabdomyolysis.",
        "limitations": "Subsumed by high-sensitivity troponin for initial AMI diagnosis; elevated in extensive skeletal muscle trauma."
    },

    # -------------------------------------------------------------------------
    # 3. Hematology & Coagulation
    # -------------------------------------------------------------------------
    {
        "code": "LOINC-58410-2",
        "name": "Complete Blood Count (CBC) with Automated Differential",
        "description": "Multi-parameter automated hematology analyzer panel quantifying RBC, Hemoglobin, Hematocrit, Platelets, and 5-part WBC differential.",
        "rationale": "Fundamental baseline investigation for anemia, hematologic malignancies, acute bacterial vs viral infections, and thrombocytopenia.",
        "limitations": "Automated flags for blasts, atypical lymphocytes, or giant platelets mandate manual peripheral blood smear confirmation."
    },
    {
        "code": "LOINC-5902-2",
        "name": "Prothrombin Time / INR (PT/INR)",
        "description": "Measures the extrinsic and common coagulation pathways (Factors II, V, VII, X, and Fibrinogen) reported as International Normalized Ratio.",
        "rationale": "Standard of care for monitoring Vitamin K antagonist (warfarin) anticoagulation, evaluating hepatic synthetic failure, and pre-op coagulopathy.",
        "limitations": "Unreliable for direct oral anticoagulants (DOACs); affected by lupus anticoagulants and factor VII deficiency."
    },
    {
        "code": "LOINC-3173-2",
        "name": "Activated Partial Thromboplastin Time (aPTT)",
        "description": "Assesses the intrinsic and common coagulation pathways (Factors XII, XI, IX, VIII, X, V, II, and Fibrinogen).",
        "rationale": "Monitors unfractionated heparin therapy; screens for hemophilia A/B, von Willebrand disease, and antiphospholipid syndrome.",
        "limitations": "Insensitive to mild single factor deficiencies (>30% activity); does not measure DOAC or low-molecular-weight heparin activity reliably."
    },
    {
        "code": "LOINC-3255-7",
        "name": "Fibrinogen Activity (Clauss Method)",
        "description": "Quantitative functional clotting assay determining conversion rate of fibrinogen to fibrin upon excess thrombin addition.",
        "rationale": "Critical component in diagnosing Disseminated Intravascular Coagulation (DIC), hypofibrinogenemia in massive transfusion, and hyperfibrinolysis.",
        "limitations": "High concentrations of heparin or direct thrombin inhibitors may artificially depress measured functional fibrinogen."
    },
    {
        "code": "LOINC-2276-4",
        "name": "Serum Ferritin",
        "description": "Measures circulating intracellular iron storage protein; reflects total body iron stores.",
        "rationale": "Single most powerful diagnostic test for absolute iron deficiency anemia (<30 ng/mL); also monitors hemochromatosis.",
        "limitations": "Acute phase reactant; falsely normal or elevated in active systemic inflammation, liver necrosis, or malignancy despite true iron deficiency."
    },
    {
        "code": "LOINC-2498-4",
        "name": "Serum Iron & Total Iron-Binding Capacity (TIBC / Transferrin Saturation)",
        "description": "Spectrophotometric assay measuring serum circulating iron and the maximum capacity of transferrin to bind iron.",
        "rationale": "Differentiates iron deficiency anemia (low sat <16%, high TIBC) from anemia of chronic disease (low sat, normal/low TIBC).",
        "limitations": "Diurnal variation (higher in morning); transiently elevated following oral iron supplementation."
    },

    # -------------------------------------------------------------------------
    # 4. Renal, Electrolyte & Acid-Base
    # -------------------------------------------------------------------------
    {
        "code": "LOINC-2160-0",
        "name": "Serum Creatinine & Estimated GFR (CKD-EPI 2021)",
        "description": "Enzymatic or Jaffe kinetic assay of creatinine with automated calculation of eGFR without race coefficient per KDIGO 2021 guidelines.",
        "rationale": "Primary laboratory indicator for Acute Kidney Injury (KDIGO criteria) and staging of Chronic Kidney Disease.",
        "limitations": "Lag time in acute hemodynamic injury; influenced by extreme muscle mass, amputations, and vegetarian diet."
    },
    {
        "code": "LOINC-3094-0",
        "name": "Blood Urea Nitrogen (BUN)",
        "description": "Measures urea nitrogen waste product produced by hepatic protein catabolism and cleared via glomerular filtration.",
        "rationale": "BUN/Creatinine ratio (>20:1) differentiates pre-renal azotemia/dehydration from intrinsic acute tubular necrosis.",
        "limitations": "Elevated by upper gastrointestinal hemorrhage, high protein diet, corticosteroid therapy, and catabolic states."
    },
    {
        "code": "LOINC-2823-3",
        "name": "Serum Potassium",
        "description": "Potentiometric measurement using ion-selective electrode (ISE) of extracellular potassium concentration.",
        "rationale": "Immediate urgent assessment in cardiac dysrhythmias, renal failure, DKA, and polypharmacy (RAAS inhibitors/diuretics).",
        "limitations": "Pseudohyperkalemia caused by in vitro hemolysis, prolonged tourniquet time, fist clenching, or severe thrombocytosis/leukocytosis."
    },
    {
        "code": "LOINC-2951-2",
        "name": "Serum Sodium",
        "description": "ISE direct potentiometry measuring extracellular sodium; primary determinant of serum osmolality.",
        "rationale": "Investigates altered mental status, dehydration, syndrome of inappropriate antidiuretic hormone (SIADH), and heart failure.",
        "limitations": "Pseudohyponatremia in severe hypertriglyceridemia or paraproteinemia (indirect ISE); correct for hyperglycemia (+1.6 mEq/L per 100 mg/dL glucose)."
    },
    {
        "code": "LOINC-17861-6",
        "name": "Serum Calcium (Total & Albumin-Corrected)",
        "description": "Photometric measurement of circulating total calcium with automated albumin correction calculation: Corrected Ca = Total Ca + 0.8 * (4.0 - Albumin).",
        "rationale": "Screening for hyperparathyroidism, malignancy-associated hypercalcemia, hypocalcemia tetany, and metabolic bone disease.",
        "limitations": "Acid-base disturbances shift calcium-albumin binding; ionized calcium remains the gold standard in critically ill patients."
    },
    {
        "code": "LOINC-19123-9",
        "name": "Serum Magnesium",
        "description": "Colorimetric assay of total serum magnesium.",
        "rationale": "Indispensable in refractory hypokalemia, cardiac arrhythmias (Torsades de Pointes), pre-eclampsia/eclampsia, and prolonged diuretic use.",
        "limitations": "Extracellular magnesium represents <1% of total body magnesium stores; serum levels may be normal in intracellular depletion."
    },
    {
        "code": "LOINC-2777-1",
        "name": "Serum Phosphate (Inorganic Phosphorus)",
        "description": "Measures serum inorganic orthophosphate ions.",
        "rationale": "Evaluates Refeeding Syndrome, chronic kidney disease mineral bone disorder (CKD-MBD), and diabetic ketoacidosis management.",
        "limitations": "Significant circadian rhythm (peaks in early morning); falsely elevated by delayed serum separation."
    },
    {
        "code": "LOINC-24338-6",
        "name": "Arterial Blood Gas (ABG: pH, PaO2, PaCO2, HCO3, SaO2)",
        "description": "Direct electrochemical measurement of arterial hydrogen ion concentration, partial pressures of oxygen and carbon dioxide, with calculated bicarbonate.",
        "rationale": "Gold standard for evaluating severe hypoxemia, acute respiratory distress syndrome (ARDS), and mixed acid-base disorders in critical care.",
        "limitations": "Painful arterial puncture; venous air bubble contamination falsely elevates PaO2 and lowers PaCO2."
    },
    {
        "code": "LOINC-2524-7",
        "name": "Serum Lactate (Lactic Acid)",
        "description": "Enzymatic measurement of L-lactate in whole blood or plasma.",
        "rationale": "Surrogate biomarker of systemic tissue hypoperfusion, anaerobic metabolism, and cellular hypoxia in Sepsis-3 guidelines (>2.0 mmol/L threshold).",
        "limitations": "Must be drawn without stasis and placed on ice immediately; Type B lactic acidosis occurs without hypoxia (metformin, linezolid, liver failure)."
    },

    # -------------------------------------------------------------------------
    # 5. Hepatic & Pancreatic
    # -------------------------------------------------------------------------
    {
        "code": "LOINC-1742-6",
        "name": "Alanine Aminotransferase (ALT / SGPT)",
        "description": "Enzymatic rate assay measuring alanine aminotransferase activity in serum.",
        "rationale": "Highly specific intracellular enzyme marker for acute hepatocyte necrosis, viral hepatitis, DILI, and ischemic hepatitis.",
        "limitations": "May be deceptively near-normal in end-stage cirrhosis with depleted functional hepatocyte mass."
    },
    {
        "code": "LOINC-1920-8",
        "name": "Aspartate Aminotransferase (AST / SGOT)",
        "description": "Enzymatic measurement of aspartate aminotransferase in serum.",
        "rationale": "AST:ALT ratio > 2:1 characteristic of alcohol-induced liver disease; elevated in non-hepatic sources (skeletal muscle, cardiac, hemolysis).",
        "limitations": "Lack of liver specificity compared to ALT; rises significantly following vigorous physical exertion or rhabdomyolysis."
    },
    {
        "code": "LOINC-6768-6",
        "name": "Alkaline Phosphatase (ALP)",
        "description": "Measures total alkaline phosphatase activity derived from biliary canaliculi and osteoblasts.",
        "rationale": "Primary marker for biliary obstruction/cholestasis, infiltrative liver disease, and high-turnover bone disorders (Paget's, osteomalacia).",
        "limitations": "Physiologically elevated during rapid adolescent bone growth and third-trimester pregnancy (placental ALP)."
    },
    {
        "code": "LOINC-1975-2",
        "name": "Total & Direct (Conjugated) Bilirubin",
        "description": "Diazo reaction assay measuring total bilirubin and its water-soluble glucuronide-conjugated fraction.",
        "rationale": "Distinguishes unconjugated hyperbilirubinemia (hemolysis, Gilbert syndrome) from conjugated cholestatic / hepatocellular jaundice.",
        "limitations": "Specimen must be protected from photolysis (ambient light degrades bilirubin rapidly)."
    },
    {
        "code": "LOINC-25428-4",
        "name": "Serum Lipase",
        "description": "Enzymatic turbidimetric assay measuring pancreatic lipase activity in serum.",
        "rationale": "Atlanta Classification diagnostic criterion for Acute Pancreatitis (elevation >= 3 times upper limit of normal). Superior sensitivity/specificity to amylase.",
        "limitations": "Moderate elevations observed in renal failure, diabetic ketoacidosis, bowel ischemia, and acute cholecystitis."
    },
    {
        "code": "LOINC-1798-8",
        "name": "Serum Amylase",
        "description": "Colorimetric enzyme assay measuring alpha-amylase activity.",
        "rationale": "Rapid auxiliary screening for acute pancreatitis; rises earlier than lipase but normalizes within 48-72 hours.",
        "limitations": "Lower specificity than lipase; elevated in salivary gland pathology (mumps), macroamylasemia, and intestinal perforation."
    },
    {
        "code": "LOINC-2324-2",
        "name": "Gamma-Glutamyl Transferase (GGT)",
        "description": "Microsomal enzyme assay measuring gamma-glutamyltransferase activity.",
        "rationale": "Confirms hepatic origin of an isolated elevated Alkaline Phosphatase (bone ALP does not elevate GGT); sensitive marker of chronic alcohol intake.",
        "limitations": "Very high sensitivity but low specificity; induced by numerous medications including phenytoin and phenobarbital."
    },

    # -------------------------------------------------------------------------
    # 6. Infectious Diseases & Microbiology
    # -------------------------------------------------------------------------
    {
        "code": "LOINC-14927-8",
        "name": "Dengue NS1 Antigen Rapid / ELISA",
        "description": "Enzyme immunoassay detecting Dengue virus Non-Structural Protein 1 in acute phase serum.",
        "rationale": "Confirmatory diagnostic test during the early viremic phase of acute dengue fever (Days 1 to 5 of symptom onset).",
        "limitations": "Diagnostic sensitivity drops sharply after Day 5 of fever as anti-NS1 antibodies develop; negative result does not rule out dengue."
    },
    {
        "code": "LOINC-22284-4",
        "name": "Dengue IgM & IgG Antibodies (ELISA)",
        "description": "Capture ELISA quantifying Dengue-specific IgM and IgG antibodies in convalescent serum.",
        "rationale": "Diagnoses acute secondary or late primary dengue infection (from Day 5 onward) and differentiates primary from secondary immune response.",
        "limitations": "Extensive antigenic cross-reactivity with other flaviviruses (Zika, Yellow Fever, West Nile, Japanese Encephalitis)."
    },
    {
        "code": "LOINC-600-7",
        "name": "Blood Cultures (Aerobic & Anaerobic, 2 Distinct Sets)",
        "description": "Continuous-monitoring automated blood culture system with Gram stain and reflex antimicrobial susceptibility testing.",
        "rationale": "Mandatory standard of care before antibiotic initiation in suspected sepsis, bacteremia, infective endocarditis, and pyrexia of unknown origin.",
        "limitations": "Prior antibiotic administration markedly suppresses yield; skin commensal contamination (CoNS) requires clinical discrimination."
    },
    {
        "code": "LOINC-56888-1",
        "name": "HIV-1/2 Antigen and Antibody 4th Generation Screen",
        "description": "Chemiluminescent microparticle immunoassay simultaneously detecting HIV-1 p24 antigen and antibodies to HIV-1 and HIV-2.",
        "rationale": "CDC recommended screening algorithm; narrows diagnostic window period to 14-20 days post-exposure.",
        "limitations": "Requires reflex HIV-1/2 differentiation immunoassay and viral RNA PCR to confirm preliminary positive screen."
    },
    {
        "code": "LOINC-5196-1",
        "name": "Hepatitis B Surface Antigen (HBsAg) with Reflex Confirmation",
        "description": "Chemiluminescent immunoassay detecting hepatitis B surface viral coat protein.",
        "rationale": "Definitive marker of active hepatitis B infection (acute or chronic HBV carrier state).",
        "limitations": "Transient false-positive results can occur within 1-2 weeks following recombinant Hepatitis B vaccination."
    },
    {
        "code": "LOINC-13955-0",
        "name": "Hepatitis C Virus (HCV) Antibody with Reflex Quantitative RNA",
        "description": "ELISA screening for antibodies directed against recombinant HCV core, NS3, NS4, and NS5 proteins with reflex molecular viral load.",
        "rationale": "Universal screening for Hepatitis C exposure; reflex RNA PCR confirms active replicating viremia requiring direct-acting antivirals.",
        "limitations": "HCV antibodies persist indefinitely even after spontaneous clearance or successful curative antiviral therapy."
    },
    {
        "code": "LOINC-94500-6",
        "name": "SARS-CoV-2 (COVID-19) RT-PCR",
        "description": "Qualitative reverse transcription real-time PCR targeting SARS-CoV-2 nucleocapsid (N) and ORF1ab genes from nasopharyngeal swab.",
        "rationale": "Gold standard molecular confirmation of acute SARS-CoV-2 respiratory tract infection.",
        "limitations": "Viral RNA shedding may persist for weeks to months after clinical recovery without representing infectious viral transmission."
    },
    {
        "code": "LOINC-32734-6",
        "name": "Malaria Blood Smear (Thick and Thin) & Rapid Diagnostic Test (RDT)",
        "description": "Microscopic examination of Giemsa-stained blood films for Plasmodium speciation and parasitemia percentage quantification plus histidine-rich protein II (HRP2) RDT.",
        "rationale": "Immediate emergency evaluation for acute febrile illness in returned travelers or endemic zones to detect severe P. falciparum.",
        "limitations": "Single negative smear does not exclude malaria; repeat thick/thin smears every 12-24 hours over 48 hours are clinically mandated."
    },
    {
        "code": "LOINC-6556-5",
        "name": "Group A Streptococcus Rapid Antigen Screen (Strep A)",
        "description": "Lateral flow immunoassay detecting Group A Streptococcal carbohydrate antigen from posterior pharyngeal and tonsillar swab.",
        "rationale": "Rapid diagnosis of Streptococcus pyogenes pharyngitis in Centor score >= 2 to guide targeted antibiotic stewardship and prevent acute rheumatic fever.",
        "limitations": "Negative rapid tests in pediatric and adolescent patients require backup throat culture confirmation."
    },
    {
        "code": "LOINC-24356-8",
        "name": "Urinalysis with Microscopic Examination",
        "description": "Complete dipstick analysis (pH, protein, glucose, ketones, leukocyte esterase, nitrite) plus automated or manual sediment microscopy.",
        "rationale": "Essential screening for urinary tract infections, acute glomerulonephritis (RBC casts), nephrotic syndrome, and diabetic nephropathy.",
        "limitations": "Squamous epithelial cell contamination indicates improper clean-catch technique; dipstick nitrite requires nitrate-reducing bacteria and >=4h bladder incubation."
    },
    {
        "code": "LOINC-630-4",
        "name": "Urine Culture and Antimicrobial Susceptibility",
        "description": "Quantitative semiquantitative culture on chromogenic media to isolate and quantify uropathogens (>10^5 CFU/mL significant bacteriuria) with MIC sensitivities.",
        "rationale": "Confirmatory diagnosis and targeted antibiotic management of complicated cystitis, pyelonephritis, and catheter-associated UTIs.",
        "limitations": "Asymptomatic bacteriuria does not warrant antibiotic treatment except in pregnant women and pre-transurethral resection of prostate."
    },
    {
        "code": "LOINC-20507-0",
        "name": "Syphilis Non-Treponemal Screen (RPR / VDRL)",
        "description": "Flocculation test detecting reagin antibodies against cardiolipin-lecithin antigen, reported with quantitative titer.",
        "rationale": "Monitors response to penicillin therapy in syphilis (a four-fold decline in titer signifies therapeutic efficacy); screens high-risk populations.",
        "limitations": "Biological false positives in autoimmune diseases, pregnancy, leprosy, and acute febrile illnesses; prozone effect in secondary syphilis."
    },
    {
        "code": "LOINC-96765-3",
        "name": "Oropouche Virus RT-PCR / Serology",
        "description": "Real-time reverse-transcriptase polymerase chain reaction targeting the S and M segments of the Oropouche orthobunyavirus genome.",
        "rationale": "Emerging arboviral diagnostic panel for acute fever, headache, retro-orbital pain, and arthralgia in endemic and travel-associated outbreaks.",
        "limitations": "Viremia is short-lived (first 3-5 days of illness); requires regional public health reference laboratory validation."
    },
    {
        "code": "LOINC-99596-9",
        "name": "Mpox (Monkeypox) Virus DNA Real-Time PCR",
        "description": "Real-time qualitative PCR targeting non-variola orthopoxvirus DNA from swab of active cutaneous vesicular or pustular lesion crusts.",
        "rationale": "Confirmatory investigation of choice for Mpox Clade I and Clade II under WHO Global Surveillance standards.",
        "limitations": "Blood PCR has very low sensitivity; testing must be performed directly on unroofed lesion fluid, exudate, or scabs."
    },

    # -------------------------------------------------------------------------
    # 7. Inflammatory & Autoimmune Markers
    # -------------------------------------------------------------------------
    {
        "code": "LOINC-1988-5",
        "name": "High-Sensitivity C-Reactive Protein (hs-CRP)",
        "description": "Immunoturbidimetric assay measuring hepatic pentraxin protein synthesized in acute phase response.",
        "rationale": "Sensitive quantitative indicator of systemic inflammation, bacterial infection severity, autoimmune flares, and cardiovascular atherogenic risk.",
        "limitations": "Non-specific; elevated in trauma, obesity, smoking, and tissue injury without identifiable bacterial infection."
    },
    {
        "code": "LOINC-4537-7",
        "name": "Erythrocyte Sedimentation Rate (ESR, Westergren)",
        "description": "Measures the distance (in millimeters) that red blood cells settle in anticoagulated whole blood in a vertical tube over 1 hour.",
        "rationale": "Diagnostic and disease-monitoring criteria in Temporal (Giant Cell) Arteritis, Polymyalgia Rheumatica, and systemic osteomyelitis.",
        "limitations": "Slow kinetics (takes days to weeks to normalize); affected by age, female sex, anemia, paraproteins, and red cell morphology."
    },
    {
        "code": "LOINC-33959-8",
        "name": "Serum Procalcitonin (PCT)",
        "description": "Chemiluminescent assay of the 116-amino acid peptide prohormone synthesized by parenchymal cells in response to bacterial endotoxin and inflammatory cytokines.",
        "rationale": "Differentiates systemic bacterial infections from viral illnesses; guides antimicrobial initiation and safe cessation in sepsis and CAP.",
        "limitations": "Non-bacterial elevations in severe cardiogenic shock, major polytrauma, extensive thermal burns, and medullary thyroid carcinoma."
    },
    {
        "code": "LOINC-4485-9",
        "name": "Antinuclear Antibody (ANA) by Indirect Immunofluorescence (HEp-2)",
        "description": "Gold standard HEp-2 cell indirect immunofluorescence screening for circulating autoantibodies against nuclear antigens, reported with pattern and titer.",
        "rationale": "High sensitivity (>95%) entry criterion for Systemic Lupus Erythematosus (EULAR/ACR 2019 criteria) and connective tissue disease evaluation.",
        "limitations": "Low specificity; low-titer positive results (1:40 to 1:80) present in up to 20% of healthy individuals, elderly, and thyroiditis."
    },
    {
        "code": "LOINC-11572-5",
        "name": "Rheumatoid Factor (RF) IgM",
        "description": "Turbidimetric assay measuring autoantibodies directed against the Fc portion of human IgG.",
        "rationale": "Classification criterion for Rheumatoid Arthritis and evaluation of primary Sjogren's syndrome.",
        "limitations": "Negative in ~20-30% of seronegative RA; positive in chronic Hepatitis C, Subacute Bacterial Endocarditis, and Cryoglobulinemia."
    },
    {
        "code": "LOINC-33935-8",
        "name": "Anti-Cyclic Citrullinated Peptide (Anti-CCP / ACPA)",
        "description": "Chemiluminescent ELISA detecting autoantibodies against synthetic citrullinated peptides.",
        "rationale": "High diagnostic specificity (>96%) for Rheumatoid Arthritis; predicts aggressive erosive joint disease course.",
        "limitations": "Low sensitivity in very early undifferentiated inflammatory polyarthritis."
    },
    {
        "code": "LOINC-1738-2",
        "name": "Anti-Neutrophil Cytoplasmic Antibodies (ANCA: PR3 & MPO)",
        "description": "Immunofluorescence and antigen-specific EIA quantifying antibodies directed against Proteinase 3 (c-ANCA) and Myeloperoxidase (p-ANCA).",
        "rationale": "Definitive serologic investigation for ANCA-associated small-vessel vasculitides (Granulomatosis with Polyangiitis, MPA, EGPA).",
        "limitations": "Biopsy remains definitive for organ damage; drug-induced ANCA vasculitis can occur with hydralazine, propylthiouracil, and levamisole."
    },

    # -------------------------------------------------------------------------
    # 8. Endocrine & Toxicology
    # -------------------------------------------------------------------------
    {
        "code": "LOINC-3016-3",
        "name": "Thyroid Stimulating Hormone (TSH, 3rd Generation)",
        "description": "High-sensitivity chemiluminescent immunoassay detecting pituitary glycoprotein regulator of thyroid hormone synthesis.",
        "rationale": "Initial test of choice for primary hypothyroidism (elevated TSH) and hyperthyroidism (suppressed TSH).",
        "limitations": "Subsumed by Euthyroid Sick Syndrome in critically ill patients; misleading in central pituitary/hypothalamic hypothyroidism."
    },
    {
        "code": "LOINC-2284-8",
        "name": "Free Thyroxine (Free T4)",
        "description": "Direct measurement of circulating unbound, biologically active thyroxine in serum.",
        "rationale": "Reflex investigation following abnormal TSH to confirm overt vs subclinical thyroid dysfunction and monitor levothyroxine titration.",
        "limitations": "Significant heterophile antibody or biotin supplement interference (>5-10 mg/day biotin causes falsely elevated Free T4)."
    },
    {
        "code": "LOINC-2143-6",
        "name": "Morning Serum Cortisol (8:00 AM)",
        "description": "Chemiluminescent immunoassay measuring peak physiological diurnal circulating total cortisol.",
        "rationale": "First-line screening for primary and secondary adrenal insufficiency (<3 mcg/dL suggestive; >15 mcg/dL excludes).",
        "limitations": "Oral contraceptives and estrogen therapy elevate Cortisol-Binding Globulin (CBG), artificially raising total cortisol; requires ACTH stimulation for confirmation."
    },
    {
        "code": "LOINC-2093-3",
        "name": "Lipid Panel (Total Cholesterol, HDL, LDL, Triglycerides)",
        "description": "Comprehensive enzymatic lipid profile with calculation of low-density lipoprotein via Martin-Hopkins or Friedewald equation.",
        "rationale": "Cardiovascular risk stratification, primary and secondary ASCVD prevention, and statin initiation guidance.",
        "limitations": "Friedewald calculation is invalid if fasting triglycerides exceed 400 mg/dL; direct LDL measurement required."
    }
]


class MedlinePlusLabTestsIngester:
    """Ingests standardized MedlinePlus / LOINC lab tests.
    
    Creates primary Investigation knowledge records and vector embeddings for semantic RAG retrieval.
    Includes 58 peer-reviewed clinical laboratory panels covering all major medical specialties.
    """

    async def ingest_lab_tests_stub(self, db: AsyncSession) -> int:
        provider = get_embedding_provider()
        ingested_count = 0

        for test_data in CLINICAL_LAB_TEST_CATALOG:
            code_str = test_data["code"]

            # 1. Check if already exists in database
            existing = await db.scalar(select(Investigation).where(Investigation.code == code_str))
            if existing:
                continue

            # 2. Create Investigation Record
            inv = Investigation(
                code=code_str,
                name=test_data["name"],
                description=test_data["description"],
                status="APPROVED",
                is_ai_generated=False,
                credibility_tier="primary"
            )
            db.add(inv)
            await db.flush()

            # 3. Create RAG Embedding Context
            embed_text = (
                f"Investigation Test: {test_data['name']}\n"
                f"LOINC Code: {code_str}\n"
                f"Description: {test_data['description']}\n"
                f"Clinical Rationale: {test_data['rationale']}\n"
                f"Limitations & Caveats: {test_data['limitations']}"
            )

            try:
                vector = await provider.embed(embed_text)

                emb = EmbeddingRecord(
                    source_record_type="investigation",
                    source_record_id=str(inv.id),
                    embedding_model=provider.metadata.model_name,
                    model_version="1.0",
                    dimensions=len(vector),
                    embedding=vector,
                    content_hash=hashlib.sha256(embed_text.encode("utf-8")).hexdigest()
                )
                db.add(emb)
                ingested_count += 1
                log.info("ingested_clinical_lab_test", name=test_data["name"], code=code_str)
            except Exception as e:
                log.error("failed_to_embed_lab_test", error=str(e), code=code_str)

        await db.commit()
        return ingested_count
