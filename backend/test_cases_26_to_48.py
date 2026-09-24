import urllib.request
import json
import time
import sys

CASES = [
    # --- Travel / Tropical (Cases 26 - 35) ---
    (
        "Case 26 (DRC - Bundibugyo Virus Disease)",
        """A 36-year-old previously healthy man presents to an infectious-disease unit in India with five days of fever after returning from northeastern Democratic Republic of the Congo. He initially developed abrupt fever, headache, generalized weakness, myalgia, and sore throat approximately eight days after leaving the region. During the first 48 hours he remained ambulatory and was treated with paracetamol at home. On the third day, he developed nausea followed by repeated vomiting and several episodes of watery diarrhea. He reports increasing abdominal discomfort but no focal abdominal pain. His wife notes that he has become unusually quiet and has twice appeared confused about the date. He has been drinking very little because of persistent nausea and reports passing urine only twice during the previous day. On examination he is febrile, tachycardic, markedly fatigued, and clinically dehydrated. His mucous membranes are dry and he becomes dizzy when sitting upright. There is diffuse abdominal tenderness without guarding. He has no obvious rash. During observation he develops a small amount of bleeding from the gums. The patient's travel itinerary shows that he passed through several communities affected by an ongoing outbreak and spent one night in crowded accommodation where another traveler reportedly had a febrile illness. There was no known animal bite. The treating team considers several causes of severe febrile illness, including malaria and other tropical infections, but the combination of rapid gastrointestinal deterioration, altered behavior, reduced urine output, dehydration, and mucosal bleeding raises concern for a high-consequence viral illness. Appropriate isolation and urgent diagnostic testing are initiated.""",
        ["Bundibugyo", "Bundibugyo Virus Disease"]
    ),
    (
        "Case 27 (Nicaragua - Chikungunya)",
        """A 31-year-old woman presents seven days after returning from Nicaragua with fever, severe generalized joint pain, headache, and profound fatigue. She states that the illness began suddenly rather than gradually. Within several hours of developing fever, she experienced severe pain in both ankles and wrists, followed by pain in the knees and small joints of both hands. She describes the pain as deep inside the joints and says that even walking short distances has become difficult. On the second day she develops a faint rash over the trunk and upper arms. She also reports nausea and mild photophobia. She has no persistent vomiting, no abdominal tenderness, no bleeding, and no altered mental status. She remembers being bitten repeatedly by mosquitoes while sitting outdoors in the evenings. Her husband, who travelled with her, developed fever two days earlier but has predominantly headache and muscle aches without significant joint pain. On examination, the patient is febrile and uncomfortable. Both wrists and ankles are tender, with mild swelling and substantially reduced movement because of pain. There is a scattered maculopapular rash. No neck stiffness is present. Platelet count is mildly reduced but there is no clinical bleeding. The clinician initially considers dengue, chikungunya, and other arboviral infections. The patient specifically reports that the joint pain is much more disabling than the fever itself and has remained prominent even when the temperature temporarily falls. Her recent stay in an area with an active mosquito-borne outbreak is considered important in interpreting the presentation.""",
        ["Chikungunya"]
    ),
    (
        "Case 28 (Colombia - Yellow Fever)",
        """A 40-year-old man returns from Colombia after spending two weeks in a rural forested region. He received no documented travel vaccination before departure. Six days after returning to India, he develops abrupt fever, chills, headache, severe back pain, nausea, and marked weakness. During the first two days he remains conscious and is able to drink fluids. On the third day, he develops repeated vomiting and complains of pain beneath the right costal margin. His urine becomes noticeably darker despite adequate fluid intake. His family subsequently notices yellow discoloration of his eyes. He develops bleeding from his gums and a small amount of nasal bleeding. On the following day, his fever remains high and he becomes increasingly lethargic. Examination reveals jaundice, dehydration, tachycardia, and tenderness in the right upper abdomen. There is no prominent rash. He has no chronic liver disease and does not consume alcohol regularly. Initial laboratory testing shows significant hepatic dysfunction and abnormalities of coagulation. His platelet count is reduced. The clinical team initially considers several mosquito-borne infections because the patient travelled through a region where multiple arboviruses circulate. However, the progression from acute fever to jaundice, dark urine, hepatic dysfunction, and bleeding becomes a major concern. The patient is admitted for close monitoring of hepatic failure, hemorrhage, renal dysfunction, and circulatory instability.""",
        ["Yellow Fever"]
    ),
    (
        "Case 29 (Yemen - Severe / Falciparum Malaria)",
        """A 25-year-old woman presents with fever, headache, and generalized weakness approximately twelve days after returning from Yemen. During her trip she stayed in both an urban area and a rural settlement and reports substantial mosquito exposure. She did not use chemoprophylaxis. Her illness began with intermittent fever and chills accompanied by headache and muscle aches. She initially improved after taking antipyretics, but the fever returned repeatedly. On the fourth day of illness, she develops nausea, vomiting, and increasing weakness. Her mother notices that she appears confused during one febrile episode. On examination, she is febrile, pale, tachycardic, and mildly disoriented. There is no prominent rash or jaundice. Her abdomen is soft, and there is no neck stiffness. Laboratory testing demonstrates anemia and thrombocytopenia. A rapid diagnostic test for a mosquito-borne febrile illness is obtained, but the clinician emphasizes that a single negative result may not be sufficient if clinical suspicion remains high. A peripheral blood smear is requested and repeated testing is planned. During observation, the patient develops worsening confusion and difficulty maintaining oral intake. The treating physician becomes particularly concerned about progression to severe disease because of the combination of altered mental status, hematological abnormalities, recurrent fever, and recent travel to an area where increased transmission has been reported.""",
        ["Malaria", "Severe Malaria"]
    ),
    (
        "Case 30 (Bali - Zika Virus)",
        """A 22-year-old male returns from Bali and develops a mild illness approximately one week later. He initially experiences low-grade fever, headache, fatigue, and generalized muscle discomfort. By the following day, a diffuse erythematous rash appears over his chest and upper limbs. He develops bilateral conjunctival redness without discharge and mild pain involving his wrists and fingers. Unlike his previous viral illnesses, he has almost no respiratory symptoms and does not develop significant vomiting or diarrhea. His partner, who travelled with him, remains asymptomatic. During the consultation, he reports unprotected sexual intercourse with his partner after returning home. He also recalls numerous mosquito bites during the trip. On examination, he is alert, afebrile, and hemodynamically stable. The rash is still visible but fading. Both conjunctivae are mildly injected. There is no meningism, no focal neurological deficit, no significant lymphadenopathy, and no bleeding. The clinician specifically asks about the possibility of pregnancy in the patient's partner and explains that the travel-associated infection under consideration has implications for sexual transmission and fetal health even when the infected person has only mild symptoms. The patient is advised regarding mosquito avoidance and sexual precautions while testing is arranged.""",
        ["Zika Virus"]
    ),
    (
        "Case 31 (Costa Rica - Hepatitis A)",
        """A 48-year-old man returns to India from Costa Rica and develops progressive fatigue approximately three weeks later. Initially he reports only reduced appetite and generalized tiredness. Two days later he develops nausea, mild fever, and vague upper abdominal discomfort. He denies severe diarrhea and has no respiratory symptoms. Over the next several days, he notices that his urine has become dark brown and that his stools are unusually pale. His wife notices yellow discoloration of his eyes. He reports persistent nausea but no major vomiting. On examination, he is alert but visibly fatigued. There is scleral icterus and mild jaundice. The liver is mildly tender. There is no rash, no joint swelling, no neurological deficit, and no evidence of active bleeding. He reports eating extensively at local restaurants during the trip and consuming fresh foods from street vendors. He also recalls that several people in the group developed gastrointestinal symptoms while abroad. He has no known chronic liver disease and does not take hepatotoxic medications. His vaccination history is uncertain. Laboratory testing demonstrates a hepatocellular pattern of liver injury. The physician notes that the interval between travel and onset is substantially longer than would be expected for many acute food-poisoning syndromes and asks specifically about vaccination, household contacts, sanitation, food and water exposures, and recent travel. The patient is admitted for evaluation of acute hepatitis.""",
        ["Hepatitis A", "Acute Viral Hepatitis"]
    ),
    (
        "Case 32 (DRC - Meningococcal Disease / Meningitis with Petechial Rash)",
        """A 19-year-old college student returns from the Democratic Republic of the Congo and develops an abrupt febrile illness approximately one week later. He initially reports severe headache, fever, generalized weakness, nausea, and vomiting. Within several hours, he becomes increasingly sensitive to light and complains of severe neck pain. His parents bring him to the emergency department after he becomes confused and has difficulty answering questions. On examination, he is febrile, tachycardic, confused, and markedly uncomfortable. He has pronounced neck stiffness and photophobia. Several small purplish-red lesions are visible on both legs and lower abdomen. The lesions remain visible when firm pressure is applied. Over the next few hours, additional lesions appear on his trunk. He has no significant cough, diarrhea, or abdominal symptoms. His blood pressure begins to fall despite initial fluid administration. The clinician learns that the patient had stayed in a crowded settlement during his trip and had close contact with several local residents. The treating team immediately considers an invasive bacterial infection involving the meninges and bloodstream. Blood cultures and urgent cerebrospinal-fluid evaluation are arranged when clinically safe. The patient is monitored for rapid neurological deterioration, seizures, shock, and other complications.""",
        ["Meningococcal", "Meningococcal Meningitis", "Meningococcal Disease"]
    ),
    (
        "Case 33 (DRC - Bundibugyo Virus Disease)",
        """A 29-year-old man presents with fever and progressive weakness after returning from a region of the Democratic Republic of the Congo affected by a large ongoing outbreak. Symptoms begin approximately nine days after his return. The first two days consist of fever, severe headache, myalgia, and sore throat. On day three, he develops vomiting and watery diarrhea. By day four, he develops severe abdominal pain and becomes unable to maintain adequate oral intake. On day five, his family reports that he is intermittently confused and unusually drowsy. He has passed very little urine since the previous evening. During examination, he is febrile, severely dehydrated, tachycardic, and lethargic. He has diffuse abdominal tenderness and dry mucous membranes. There is mild bleeding from the gums but no large-volume hemorrhage. His family reports no animal bite and no known exposure to a deceased person. However, he stayed in crowded accommodation and visited a healthcare facility during his trip. The physician recognizes that the absence of a known direct exposure does not exclude infection because healthcare and household transmission can occur. The team immediately begins appropriate infection-control procedures and requests urgent laboratory confirmation while monitoring fluid status, renal function, neurological status, and coagulation abnormalities.""",
        ["Bundibugyo", "Bundibugyo Virus Disease"]
    ),
    (
        "Case 34 (Mauritius - Chikungunya)",
        """A 42-year-old woman develops fever five days after returning from Mauritius. The fever is accompanied by severe bilateral ankle and wrist pain, generalized muscle aches, headache, and marked fatigue. She reports that the joint pain is so severe that she cannot climb stairs without assistance. By the second day, she develops a widespread rash and mild swelling around several joints. Her fever fluctuates but the joint symptoms remain prominent. She has mild nausea but no persistent vomiting, no mucosal bleeding, and no altered mental status. She recalls frequent mosquito bites and reports that several people in her hotel developed similar illnesses during the week she stayed there. On examination, she is febrile and has tenderness and reduced movement of multiple joints. There is mild periarticular swelling and a diffuse maculopapular rash. Her platelet count is mildly decreased. The physician considers several mosquito-borne infections, including dengue and chikungunya, because both can produce fever, headache, myalgia, rash, and laboratory abnormalities. However, the severity and distribution of the joint pain are disproportionately prominent compared with the other symptoms. The patient is advised to prevent additional mosquito bites during the illness while confirmatory testing is arranged.""",
        ["Chikungunya"]
    ),
    (
        "Case 35 (DRC - Bundibugyo Virus Disease)",
        """A 34-year-old previously healthy man presents to an Indian hospital after returning from a region of the Democratic Republic of the Congo where an ongoing outbreak has caused substantial mortality. He reports that his illness began with sudden fever, headache, fatigue, sore throat, and generalized muscle pain. For the first two days he remained ambulatory. On day three he developed nausea, vomiting, abdominal discomfort, and diarrhea. By day four, he became profoundly weak and stopped eating. His wife noticed that he was becoming confused and that he was producing very little urine. On day five, he developed bleeding from the gums and blood-stained vomitus. During examination he is febrile, hypotensive, tachycardic, severely dehydrated, and intermittently confused. His abdomen is diffusely tender. There is no obvious focal source of infection and no prominent rash. The patient reports no known animal exposure but had spent time in crowded mining and community areas during his trip. The medical team considers severe malaria, bacterial sepsis, viral hemorrhagic illness, and other tropical infections. However, the travel location, incubation interval, rapidly progressive gastrointestinal illness, dehydration, neurological changes, oliguria, and bleeding lead the team to implement high-level infection-control precautions while urgent confirmatory testing is arranged. His condition requires close monitoring for shock, renal failure, coagulation abnormalities, and further neurological deterioration.""",
        ["Bundibugyo", "Bundibugyo Virus Disease"]
    ),

    # --- Rare, Metabolic, Genetic & Rheumatologic (Cases 36 - 48) ---
    (
        "Case 36 (Insulin Autoimmune Syndrome / Hirata Disease)",
        """A 22-year-old man is evaluated for recurrent episodes of profound fatigue, confusion, sweating, tremulousness, blurred vision, and near-syncope. The episodes usually occur several hours after meals rather than after prolonged fasting. On several occasions, family members have noticed that he becomes irritable and behaves unusually before developing marked drowsiness. One episode resulted in a brief loss of consciousness. He has no history of diabetes and does not take glucose-lowering medication. Physical examination between episodes is unremarkable. During a supervised symptomatic episode, plasma glucose is markedly reduced. Laboratory evaluation demonstrates an inappropriately elevated insulin concentration together with elevated C-peptide and suppressed ketone production during hypoglycemia. He has no evidence of adrenal insufficiency, severe liver disease, or renal failure. The patient reports that symptoms became more frequent after he began taking a commercially available nutritional supplement several months earlier. Imaging of the pancreas does not demonstrate an obvious mass. Because spontaneous hypoglycemia continues despite the absence of a pancreatic lesion, the endocrine team considers an unusual mechanism involving antibodies directed against endogenous insulin and orders specialized immunological testing.""",
        ["Insulin Autoimmune", "Hirata", "Hypoglycemia"]
    ),
    (
        "Case 37 (Pachydermoperiostosis / Primary Hypertrophic Osteoarthropathy)",
        """A 17-year-old boy is referred for progressive enlargement of the fingertips and toes. His parents first noticed persistent swelling around the fingers several years earlier, but it was initially attributed to sports-related activity. He now has prominent bulbous enlargement of the distal digits, increased curvature of the nails, and chronic pain around both knees and ankles. He reports excessive sweating of the hands and feet and intermittent deep aching of the long bones. There is no history of inflammatory arthritis, psoriasis, inflammatory bowel disease, or recurrent infection. Examination demonstrates marked digital clubbing, thickened facial skin, and periosteal tenderness over the lower limbs. The knees and ankles are mildly swollen but without the typical pattern of an acute inflammatory arthritis. Blood tests show inflammatory-marker abnormalities but no disease-specific autoimmune antibodies. Plain radiographs demonstrate periosteal new bone formation involving multiple long bones. Echocardiography and chest imaging do not identify an obvious cardiopulmonary cause for secondary clubbing. His father recalls having unusually large fingertips and persistent joint discomfort during adulthood. Genetic evaluation is subsequently considered because the combination of pachydermia, digital clubbing, periostosis, and a possible affected first-degree relative suggests a rare inherited skeletal disorder.""",
        ["Pachydermoperiostosis", "Hypertrophic Osteoarthropathy"]
    ),
    (
        "Case 38 (Acute Intermittent Porphyria)",
        """A 28-year-old woman presents with recurrent episodes of severe abdominal pain that have resulted in multiple emergency-department visits over the previous two years. The pain is diffuse and disproportionate to the abdominal examination. During attacks she develops nausea, vomiting, constipation, tachycardia, and marked anxiety. On several occasions she has complained of weakness in both arms and legs and tingling in the hands. Extensive abdominal imaging repeatedly fails to demonstrate an obstructive or inflammatory cause. During one admission, she develops dark reddish-brown urine several hours after the onset of abdominal symptoms. Liver enzymes, pancreatic enzymes, and inflammatory markers are not significantly elevated. She reports that attacks sometimes occur after severe dietary restriction or periods of sleep deprivation. She has recently started a hormonal medication, after which the frequency of attacks appears to increase. During the most severe episode, she becomes confused and develops generalized weakness without a clear sensory level. Electrolyte testing demonstrates significant hyponatremia. Because recurrent unexplained abdominal crises are accompanied by neurological manifestations, autonomic symptoms, hyponatremia, and unusual urine discoloration, the medical team orders specialized biochemical testing for an inherited disorder of heme synthesis.""",
        ["Porphyria", "Acute Intermittent Porphyria"]
    ),
    (
        "Case 39 (Duchenne Muscular Dystrophy)",
        """A 9-year-old boy is brought to a pediatric clinic because of progressive difficulty walking and frequent falls. His parents report that he previously developed normally but over the last year has become increasingly clumsy. He has difficulty running, climbing stairs, and rising from the floor. Examination demonstrates proximal muscle weakness, calf enlargement, and a waddling gait. He has preserved sensation and no significant joint pain. Serum creatine kinase is markedly elevated. Electromyography demonstrates a myopathic pattern. There is no history of recurrent infection or inflammatory disease. His maternal uncle reportedly developed progressive weakness during childhood and required assistance with mobility as a young adult. The child has no obvious cognitive impairment. Cardiac evaluation demonstrates subtle abnormalities despite the absence of cardiac symptoms. Genetic testing is arranged after clinicians note the pattern of childhood-onset progressive proximal weakness, calf pseudohypertrophy, markedly elevated muscle enzymes, and a family history suggesting an X-linked inheritance pattern.""",
        ["Duchenne", "Muscular Dystrophy"]
    ),
    (
        "Case 40 (Gyrate Atrophy of Choroid & Retina)",
        """A 14-year-old girl is evaluated for progressive visual difficulties that have been developing slowly over several years. She initially noticed difficulty seeing at night and began bumping into objects in dimly lit environments. More recently, she has developed loss of peripheral vision and difficulty reading small print. Ophthalmological examination demonstrates progressive retinal degeneration. She also reports occasional episodes of muscle weakness and has become increasingly fatigued during physical activity. Neurological examination reveals mild reduction in deep tendon reflexes but no major sensory deficit. Her school performance has recently declined because of visual impairment, although formal cognitive testing is initially normal. Routine blood tests are largely unremarkable. Electroretinography demonstrates severe impairment of retinal function. The combination of progressive retinal degeneration, neurological manifestations, and a possible metabolic disorder leads the team to perform plasma and urine metabolic screening. A characteristic abnormality involving an amino-acid transport pathway is subsequently identified, prompting molecular genetic testing.""",
        ["Gyrate Atrophy"]
    ),
    (
        "Case 41 (Cryopyrin-Associated Periodic Syndrome - CAPS Spectrum)",
        """A 6-year-old boy is admitted because of recurrent episodes of unexplained fever, painful swelling around multiple joints, and a rapidly developing rash. His parents report that symptoms began during infancy and occur without an obvious infectious trigger. Episodes may last several days and are associated with marked irritability and poor sleep. The rash is not associated with vesicles or pustules and becomes more prominent during febrile periods. He has chronic joint pain and has developed progressive difficulty hearing normal conversation. Growth is below expected for age. On examination, he has a faint erythematous rash over the trunk and limbs, tenderness around several joints, and reduced range of motion. He is not toxic-appearing despite the fever. Repeated cultures during previous episodes have been negative. Inflammatory markers are persistently elevated even between acute attacks. Autoimmune screening is unrevealing. His parents report that he had symptoms beginning within the first months of life and that there is no similar illness among siblings. Because of the combination of early-onset recurrent inflammation, urticarial-type rash, sensorineural hearing impairment, and chronic systemic inflammation, genetic testing for an inherited autoinflammatory disorder is arranged.""",
        ["Cryopyrin-Associated Periodic Syndrome", "CAPS Spectrum", "CAPS"]
    ),
    (
        "Case 42 (Idiopathic Inflammatory Myopathy / Anti-Synthetase Spectrum)",
        """A 34-year-old man presents with progressive difficulty swallowing and gradually worsening weakness of the proximal limbs. Over the preceding year, he has developed difficulty climbing stairs and lifting objects above shoulder height. More recently, swallowing solid food has become difficult and he occasionally coughs while drinking liquids. He denies sensory loss. Examination reveals symmetrical proximal muscle weakness and subtle weakness of the neck flexors. His respiratory function is mildly reduced. Creatine kinase is elevated but not dramatically so. Electromyography demonstrates a myopathic pattern. Muscle biopsy reveals inflammatory changes with a characteristic perifascicular distribution. He has no prominent skin eruption and no history of joint disease. Because the absence of a typical cutaneous presentation initially led to consideration of several muscular disorders, additional serological testing is performed. The patient subsequently develops rapidly progressive shortness of breath despite relatively modest limb weakness. High-resolution chest imaging demonstrates bilateral interstitial abnormalities, and pulmonary function testing shows a restrictive pattern. The combination of clinically amyopathic-appearing disease, severe muscle-independent pulmonary involvement, and characteristic biopsy findings prompts testing for a specific myositis-associated antibody.""",
        ["Idiopathic Inflammatory Myopathy", "Anti-Synthetase"]
    ),
    (
        "Case 43 (Collodion Baby Phenotype / Congenital Ichthyosis)",
        """A 4-month-old infant is brought to hospital because of extensive skin abnormalities present since birth. The newborn had a tightly stretched, shiny membrane covering almost the entire body at delivery. Within several days, the membrane began to crack and peel, leaving widespread red, raw-appearing skin. The infant has difficulty regulating body temperature and has developed recurrent episodes of dehydration. Feeding is difficult because of restricted mouth movement and tight skin around the face. The eyelids and lips are pulled outward, and the infant has difficulty closing the eyes completely. There is no history of maternal infection during pregnancy. Repeated cultures are negative, but the infant requires close monitoring because of recurrent skin-barrier disruption and risk of infection. Over time, thick scaling develops over multiple body surfaces. Dermatological examination demonstrates severe generalized ichthyosis with characteristic facial changes. The clinical team considers inherited disorders of epidermal differentiation and performs molecular testing to identify the underlying genetic abnormality.""",
        ["Collodion Baby Phenotype", "Collodion Baby", "Congenital Ichthyosis"]
    ),
    (
        "Case 44 (Mitochondrial Encephalopathy / MELAS-like)",
        """A 32-year-old man is evaluated for recurrent episodes of severe headache, visual disturbance, and transient neurological symptoms. The headaches began in adolescence but have progressively changed in character. He now experiences episodes of vertigo, imbalance, and difficulty coordinating his hands. Between attacks he remains neurologically functional, although examination reveals subtle gait ataxia and horizontal nystagmus. Brain MRI demonstrates bilateral abnormalities involving the white matter and deep cerebral structures, with additional changes around the posterior fossa. He has no history of multiple sclerosis, autoimmune disease, or recurrent infection. Several relatives on his mother's side reportedly developed migraine-like headaches and progressive neurological problems, although none received a definitive diagnosis. During a particularly severe episode, he develops prolonged vomiting, dysarthria, and inability to walk independently. Cerebrospinal-fluid analysis does not demonstrate an inflammatory pattern. Because the combination of migraine-like attacks, progressive ataxia, characteristic MRI abnormalities, and maternal-family clustering suggests a mitochondrial rather than a conventional inflammatory neurological disorder, genetic analysis of mitochondrial DNA is requested.""",
        ["Mitochondrial Encephalopathy", "MELAS"]
    ),
    (
        "Case 45 (Carnitine Palmitoyltransferase II - CPT II Deficiency)",
        """A 26-year-old woman presents with repeated episodes of severe muscle pain, weakness, and dark urine following relatively modest physical activity. The first episode occurred after a long walk, but subsequent episodes have occurred after routine exercise and occasionally during viral illnesses. She reports that she can usually tolerate short bursts of activity but becomes symptomatic after prolonged exercise. During an acute episode, serum creatine kinase is extremely elevated and urine testing is strongly positive for blood despite very few red blood cells on microscopy. Renal function begins to deteriorate. Between episodes, neurological examination is normal and muscle strength is preserved. She reports that her mother has experienced several unexplained episodes of muscle pain but has never been formally diagnosed. The patient has no history of autoimmune disease or chronic medication use. Metabolic screening demonstrates an abnormality involving fatty-acid utilization during prolonged exertion. The clinical team considers an inherited metabolic myopathy rather than inflammatory muscle disease because symptoms are episodic, exercise-associated, and accompanied by recurrent rhabdomyolysis.""",
        ["Carnitine Palmitoyltransferase", "CPT II"]
    ),
    (
        "Case 46 (Subacute Necrotizing Encephalomyelopathy / Leigh-like)",
        """A 12-year-old boy is evaluated for progressive developmental difficulties, loss of previously acquired motor skills, and unusual eye movements. He was born after an uncomplicated pregnancy and developed normally during early childhood. Over the previous eighteen months, his parents noticed increasing difficulty with balance and coordination. He subsequently developed tremor, problems with speech, and declining school performance. Examination demonstrates ataxia, dysarthria, abnormal eye movements, and reduced reflexes. MRI of the brain demonstrates progressive cerebellar and brainstem abnormalities. Routine metabolic investigations are initially unrevealing. There is no history of toxin exposure or significant infection preceding the neurological decline. His parents report that an older sibling died during childhood after a similar progressive neurological illness but had never received a definitive diagnosis. Because the condition appears to involve multiple neurological systems and follows a pattern suggesting inherited mitochondrial or neurodegenerative disease, targeted metabolic and genetic investigations are undertaken.""",
        ["Subacute Necrotizing Encephalomyelopathy", "Leigh Syndrome", "Leigh"]
    ),
    (
        "Case 47 (Hereditary Spastic Paraplegia)",
        """A 45-year-old man presents with gradually progressive weakness of the legs, stiffness, and difficulty maintaining balance. Symptoms began subtly several years earlier but have recently accelerated. He reports urinary urgency and occasional episodes of incomplete bladder emptying. Examination reveals bilateral lower-limb spasticity, brisk reflexes, ankle clonus, and a positive plantar response. Sensation is relatively preserved. There is no clear sensory level and no history of acute attacks. MRI of the brain and spinal cord shows abnormalities involving long spinal tracts but does not demonstrate the typical pattern expected for multiple sclerosis. Extensive testing for infectious, inflammatory, nutritional, and structural causes is unrevealing. His mother had developed progressive difficulty walking in later adulthood but was never diagnosed. Additional questioning reveals that several maternal relatives had similar gait problems. The combination of slowly progressive spastic paraparesis, bladder dysfunction, relatively preserved sensation, negative inflammatory evaluation, and maternal family clustering leads the neurologist to investigate a rare inherited disorder affecting mitochondrial function.""",
        ["Hereditary Spastic Paraplegia", "HSP"]
    ),
    (
        "Case 48 (Mitochondrial Energy Metabolism Disorder)",
        """A 7-year-old girl is evaluated for recurrent episodes of severe abdominal pain, vomiting, and unexplained lethargy. During several attacks she becomes pale and unusually sleepy. Her parents initially suspect gastrointestinal infection, but episodes repeatedly resolve without antimicrobial treatment. During one admission, she develops severe metabolic acidosis and elevated lactate. She has mild developmental delay and poor exercise tolerance between attacks. Neurological examination reveals subtle hypotonia and impaired coordination. Cardiac evaluation demonstrates mild hypertrophic changes. Standard metabolic screening is inconclusive. The episodes frequently occur after prolonged fasting or intercurrent illness. During one episode, laboratory testing demonstrates hypoglycemia together with elevated lactate and ketone abnormalities. Because the episodes involve multiple organ systems and are precipitated by metabolic stress rather than infection, the metabolic team investigates disorders of mitochondrial energy production. Genetic testing is subsequently recommended after biochemical findings suggest impaired cellular oxidative metabolism.""",
        ["Mitochondrial Energy Metabolism Disorder", "Mitochondrial Complex Deficiency"]
    ),
]

def main():
    url = "http://127.0.0.1:8000/api/v1/consultations/predict-realtime"
    server_available = False
    try:
        req = urllib.request.Request(url, data=b'{"symptoms":"test"}', headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=0.3) as resp:
            server_available = (resp.status == 200)
    except Exception:
        server_available = False

    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from app.services.realtime_prediction_service import realtime_prediction_service

    print("=" * 95)
    print("DOCASSISTIQ REAL-TIME BENCHMARK (CASES 26-48)")
    print(f"Mode: {'Live HTTP Server' if server_available else 'Direct Sub-30ms In-Memory Engine'}")
    print("Evaluates species-level accuracy, disease intelligence, investigations, medications, and calibrated confidence")
    print("=" * 95)

    results = []
    for title, note, expected in CASES:
        payload = json.dumps({"symptoms": note}).encode("utf-8")
        data = None
        elapsed_ms = 0.0
        if server_available:
            try:
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                t0 = time.perf_counter()
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception:
                t0 = time.perf_counter()
                data = realtime_prediction_service.predict(symptoms=note)
                elapsed_ms = (time.perf_counter() - t0) * 1000
        else:
            t0 = time.perf_counter()
            data = realtime_prediction_service.predict(symptoms=note)
            elapsed_ms = (time.perf_counter() - t0) * 1000

        top1 = data["top_candidates"][0] if data.get("top_candidates") else None
        top2 = data["top_candidates"][1] if len(data.get("top_candidates", [])) > 1 else None
        alert = data.get("emergency_alert")
        alert_title = alert.get("condition") if alert else "None"

        # Diagnostic match
        is_diag_match = any(exp.lower() in top1["disease"].lower() for exp in expected) if top1 else False

        # Verify clinical intelligence fields
        has_investigations = bool(top1 and len(top1.get("recommended_investigations", [])) >= 2)
        has_medications = bool(top1 and len(top1.get("recommended_medications", [])) >= 2)
        has_treatment = bool(top1 and len(top1.get("treatment_summary", "")) >= 10)
        has_intelligence = bool(top1 and isinstance(top1.get("disease_intelligence"), dict) and "cardinal_symptoms" in top1["disease_intelligence"])

        # Confidence calibration check: score between 70% and 94%, never 99% or 100%
        score_num = int(top1["display_score"].replace("%", "")) if top1 and "display_score" in top1 else 0
        is_calibrated = (70 <= score_num <= 94)

        all_criteria_met = is_diag_match and has_investigations and has_medications and has_treatment and has_intelligence and is_calibrated
        status_symbol = "[PASS]" if all_criteria_met else "[FAIL]"
        results.append((title, all_criteria_met, is_diag_match, top1, alert_title, data.get('latency_ms', 0)))

        safe_title = title.encode("ascii", errors="replace").decode("ascii")
        print(f"\n{status_symbol} {safe_title}")
        print(f"Latency: {data.get('latency_ms', 0):.1f}ms (Client: {elapsed_ms:.1f}ms)")
        if top1:
            safe_d1 = top1['disease'].encode("ascii", errors="replace").decode("ascii")
            print(f"  #1: {safe_d1} ({top1.get('icd10', '')}) - {top1['display_score']} | Uncertainty: {top1.get('uncertainty')}")
            print(f"      Investigations: {len(top1.get('recommended_investigations', []))} items | Medications: {len(top1.get('recommended_medications', []))} items")
            intel = top1.get("disease_intelligence", {})
            pearl = intel.get("clinical_pearl", top1.get("pearl", ""))[:75]
            safe_pearl = pearl.encode("ascii", errors="replace").decode("ascii")
            print(f"      Intelligence Pearl: {safe_pearl}...")
        if top2:
            safe_d2 = top2['disease'].encode("ascii", errors="replace").decode("ascii")
            print(f"  #2: {safe_d2} ({top2.get('icd10', '')}) - {top2['display_score']}")
        safe_alert = alert_title.encode("ascii", errors="replace").decode("ascii")
        print(f"  Alert: {safe_alert}")

    passed_count = sum(1 for _, met, _, _, _, _ in results if met)
    print("\n" + "=" * 95)
    print(f"BENCHMARK RESULT: {passed_count}/{len(results)} PASSED ALL CLINICAL & SCIENTIFIC CRITERIA")
    print("=" * 95)

if __name__ == "__main__":
    main()
