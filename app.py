import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MedCode AI Pro | MTBC CareCloud",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: #F0F4FA; }
.block-container { padding: 1.5rem 2rem 3rem; max-width: 1200px; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #0D1B2A; }
section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #F1F5F9 !important; }
section[data-testid="stSidebar"] .stRadio label { color: #CBD5E1 !important; }

/* Top header bar */
.topbar {
    background: linear-gradient(135deg, #0D1B2A 0%, #185FA5 100%);
    border-radius: 14px; padding: 1.4rem 2rem;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(24,95,165,0.25);
}
.topbar-left { display: flex; align-items: center; gap: 16px; }
.topbar-logo {
    width: 52px; height: 52px; border-radius: 12px;
    background: rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; flex-shrink: 0;
}
.topbar h1 { color: #fff; font-size: 22px; font-weight: 700; margin: 0; }
.topbar p  { color: rgba(255,255,255,0.7); font-size: 13px; margin: 3px 0 0; }
.topbar-badge {
    background: rgba(255,255,255,0.15); color: #fff;
    font-size: 11px; font-weight: 600; padding: 4px 10px;
    border-radius: 20px; border: 1px solid rgba(255,255,255,0.25);
}

/* KPI cards */
.kpi-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 1.5rem; }
.kpi {
    background: #fff; border-radius: 12px; padding: 1rem 1.2rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
    transition: box-shadow .2s;
}
.kpi:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); }
.kpi-icon { font-size: 22px; margin-bottom: 6px; }
.kpi-num  { font-size: 26px; font-weight: 700; color: #185FA5; line-height: 1; }
.kpi-lbl  { font-size: 12px; color: #64748B; margin-top: 4px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #fff; border-radius: 10px; padding: 4px 6px;
    border: 1px solid #E2E8F0; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; padding: 8px 20px !important;
    font-size: 14px !important; font-weight: 500 !important;
    color: #64748B !important;
}
.stTabs [aria-selected="true"] {
    background: #185FA5 !important; color: #fff !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

/* Cards */
.card {
    background: #fff; border-radius: 12px; padding: 1.2rem 1.4rem;
    border: 1px solid #E2E8F0; margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.card-title {
    font-size: 13px; font-weight: 700; color: #475569;
    text-transform: uppercase; letter-spacing: .06em; margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
}

/* Code rows */
.code-row {
    background: #F8FAFC; border: 1px solid #E2E8F0;
    border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;
    display: flex; align-items: flex-start; gap: 14px;
}
.code-val {
    font-family: 'Courier New', monospace; font-size: 14px;
    font-weight: 700; color: #185FA5; min-width: 90px; flex-shrink: 0;
}
.code-main { flex: 1; }
.code-desc { font-size: 13px; font-weight: 500; color: #1E293B; line-height: 1.4; }
.code-note { font-size: 12px; color: #64748B; margin-top: 3px; }
.code-right { display: flex; flex-direction: column; align-items: flex-end; gap: 5px; flex-shrink: 0; }

/* Tags & badges */
.tag { display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.tag-icd   { background: #DCFCE7; color: #166534; }
.tag-cpt   { background: #DBEAFE; color: #1E40AF; }
.tag-hcpcs { background: #FEF3C7; color: #92400E; }
.tag-em    { background: #F3E8FF; color: #6B21A8; }

.conf-bar-wrap { width: 70px; background: #E2E8F0; border-radius: 4px; height: 6px; }
.conf-bar { height: 6px; border-radius: 4px; }
.conf-high   { background: #22C55E; }
.conf-medium { background: #F59E0B; }
.conf-low    { background: #EF4444; }
.conf-label  { font-size: 10px; color: #64748B; margin-top: 2px; text-align: right; }

/* Risk badges */
.risk-high   { background: #FEE2E2; color: #991B1B; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
.risk-medium { background: #FEF3C7; color: #92400E; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
.risk-low    { background: #DCFCE7; color: #166534; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }

/* Info boxes */
.seq-box {
    border-left: 4px solid #185FA5; background: #EFF6FF;
    border-radius: 0 10px 10px 0; padding: 12px 16px;
    font-size: 13px; line-height: 1.7; color: #1E3A5F; margin-bottom: 1rem;
}
.comp-box {
    border-left: 4px solid #059669; background: #ECFDF5;
    border-radius: 0 10px 10px 0; padding: 12px 16px;
    font-size: 13px; line-height: 1.7; color: #064E3B; margin-bottom: 1rem;
}
.warn-box {
    border-left: 4px solid #F59E0B; background: #FFFBEB;
    border-radius: 0 10px 10px 0; padding: 12px 16px;
    font-size: 13px; line-height: 1.7; color: #78350F; margin-bottom: 1rem;
}
.query-box {
    background: #F8FAFC; border: 1px solid #CBD5E1;
    border-radius: 10px; padding: 14px 16px; font-size: 13px;
    line-height: 1.8; color: #334155; font-family: Georgia, serif;
    white-space: pre-wrap;
}
.sum-pill {
    background: #F0FDF4; border: 1px solid #BBF7D0;
    border-radius: 10px; padding: 10px 16px; font-size: 13px;
    color: #166534; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 10px;
}
.no-match {
    background: #FFFBEB; border: 1px solid #FDE68A;
    border-radius: 10px; padding: 14px 16px; font-size: 13px; color: #78350F;
}

/* Ref table */
.ref-row {
    background: #F8FAFC; border: 1px solid #E2E8F0;
    border-radius: 8px; padding: 8px 12px; margin-bottom: 5px;
    display: flex; gap: 12px; align-items: flex-start;
}
.ref-code  { font-family: monospace; font-weight: 700; color: #185FA5; min-width: 80px; font-size: 13px; }
.ref-desc  { font-size: 13px; color: #334155; flex: 1; }
.ref-note  { font-size: 11px; color: #64748B; margin-top: 2px; }

/* History table */
.hist-row {
    background: #F8FAFC; border: 1px solid #E2E8F0;
    border-radius: 8px; padding: 8px 14px; margin-bottom: 5px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
}
.hist-time  { font-size: 11px; color: #94A3B8; }
.hist-note  { font-size: 13px; color: #334155; max-width: 400px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hist-codes { font-size: 12px; color: #185FA5; font-weight: 600; }

/* Buttons */
.stButton > button {
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 14px !important; transition: all .2s !important;
}
footer, #MainMenu, header { visibility: hidden; }
.stTextArea textarea {
    border-radius: 10px !important; font-size: 14px !important;
    line-height: 1.65 !important; border: 1px solid #E2E8F0 !important;
}
.stTextArea textarea:focus { border-color: #185FA5 !important; box-shadow: 0 0 0 3px rgba(24,95,165,.1) !important; }
</style>
""", unsafe_allow_html=True)

# ── Code Database ──────────────────────────────────────────────────────────────
DB = [
    # ── ICD-10-CM ──────────────────────────────────────────────────────────────
    {"type":"icd10","code":"E11.9","desc":"Type 2 diabetes mellitus without complications",
     "keys":["type 2 diabetes","t2dm","diabetes mellitus","diabetic","hba1c","glycated","dm type 2"],
     "note":"Use E11.65 if hyperglycemia explicitly documented. Add Z79.4 if on insulin.",
     "seq":"Principal diagnosis for routine DM management visits.",
     "comp":"Document HbA1c, medications, and any complications for complete coding.",
     "risk":"low","category":"Endocrine"},

    {"type":"icd10","code":"E11.65","desc":"Type 2 diabetes mellitus with hyperglycemia",
     "keys":["hyperglycemia","high blood sugar","elevated glucose","glucose elevated"],
     "note":"Only when provider explicitly documents hyperglycemia. Cannot infer from labs.",
     "seq":"Sequence after E11.9 if used as combination code.",
     "comp":"Provider must explicitly document hyperglycemia — do not infer from HbA1c alone.",
     "risk":"medium","category":"Endocrine"},

    {"type":"icd10","code":"E11.40","desc":"Type 2 diabetes with diabetic neuropathy, unspecified",
     "keys":["diabetic neuropathy","peripheral neuropathy","diabetic nerve","neuropathy diabetes"],
     "note":"Specify type when documented: E11.41 mononeuropathy, E11.42 polyneuropathy.",
     "seq":"Sequence with E11.9 as combination. Principal is diabetes.",
     "comp":"Neurological exam findings must be documented.",
     "risk":"medium","category":"Endocrine"},

    {"type":"icd10","code":"I21.19","desc":"STEMI of inferior wall, other coronary artery",
     "keys":["stemi","st elevation","myocardial infarction","heart attack","inferior wall mi","troponin elevated","mi"],
     "note":"I21.09 for anterior wall (LAD). Add I25.10 for underlying CAD if documented.",
     "seq":"Principal diagnosis. Add CAD code if pre-existing disease documented.",
     "comp":"Document artery involved, troponin trend, EKG findings, and PCI details.",
     "risk":"high","category":"Cardiovascular"},

    {"type":"icd10","code":"I21.4","desc":"Non-ST elevation (NSTEMI) myocardial infarction",
     "keys":["nstemi","non-st elevation","non st elevation"],
     "note":"Use when NSTEMI explicitly documented by provider.",
     "seq":"Principal diagnosis for NSTEMI admissions.",
     "comp":"Troponin trend and EKG findings must support NSTEMI diagnosis.",
     "risk":"high","category":"Cardiovascular"},

    {"type":"icd10","code":"I25.10","desc":"Atherosclerotic heart disease of native coronary artery without angina",
     "keys":["coronary artery disease","cad","atherosclerosis","atherosclerotic heart","coronary disease"],
     "note":"Add I25.110 when angina is also present.",
     "seq":"Secondary to acute event (STEMI/NSTEMI). Principal for chronic CAD visits.",
     "comp":"Document extent of disease and vessel involvement.",
     "risk":"medium","category":"Cardiovascular"},

    {"type":"icd10","code":"I10","desc":"Essential (primary) hypertension",
     "keys":["hypertension","high blood pressure","elevated bp","htn","bp 138","bp 140","bp 150","bp 160"],
     "note":"Does not distinguish controlled vs uncontrolled unless stated. Use I11.x with CKD/HF.",
     "seq":"Sequence based on whether HTN is the primary visit reason.",
     "comp":"Document BP readings, medication compliance, and target organ damage.",
     "risk":"low","category":"Cardiovascular"},

    {"type":"icd10","code":"J18.9","desc":"Pneumonia, unspecified organism",
     "keys":["pneumonia","consolidation","community acquired pneumonia","cap","lung infection","lobar"],
     "note":"Add organism code if culture positive. J18.1 for lobar pneumonia.",
     "seq":"Principal. Add J44.1 if COPD exacerbation coexists (sequence pneumonia first).",
     "comp":"Document CAP vs HAP. Await culture for organism specificity.",
     "risk":"medium","category":"Respiratory"},

    {"type":"icd10","code":"J44.1","desc":"COPD with acute exacerbation",
     "keys":["copd","chronic obstructive","exacerbation","emphysema","chronic bronchitis"],
     "note":"J44.0 with acute lower respiratory infection; J44.1 for exacerbation without infection.",
     "seq":"When pneumonia + COPD exacerbation, sequence pneumonia first per guidelines.",
     "comp":"Document severity, spirometry, and triggers for exacerbation.",
     "risk":"medium","category":"Respiratory"},

    {"type":"icd10","code":"J45.20","desc":"Mild intermittent asthma, uncomplicated",
     "keys":["asthma","bronchospasm","wheezing","reactive airway","mild intermittent asthma"],
     "note":"J45.21 for acute exacerbation. Classify severity when documented.",
     "seq":"Principal for asthma-focused visits.",
     "comp":"Document severity classification, trigger factors, and rescue inhaler use.",
     "risk":"low","category":"Respiratory"},

    {"type":"icd10","code":"M17.11","desc":"Primary osteoarthritis, right knee",
     "keys":["osteoarthritis","right knee","oa right","knee arthritis","knee degeneration right","knee pain right"],
     "note":"M17.12 for left, M17.0 for bilateral. Confirm laterality from documentation.",
     "seq":"Principal for knee management visits.",
     "comp":"Document laterality explicitly. X-ray findings must support diagnosis.",
     "risk":"low","category":"Musculoskeletal"},

    {"type":"icd10","code":"M17.12","desc":"Primary osteoarthritis, left knee",
     "keys":["left knee","left knee pain","osteoarthritis left"],
     "note":"Confirm left laterality. Use M17.0 if bilateral.",
     "seq":"Principal or secondary based on chief complaint.",
     "comp":"Laterality must be explicitly documented.",
     "risk":"low","category":"Musculoskeletal"},

    {"type":"icd10","code":"M17.0","desc":"Bilateral primary osteoarthritis of knee",
     "keys":["bilateral knee","both knees","bilateral oa","bilateral osteoarthritis"],
     "note":"Do not code M17.11 + M17.12 separately when bilateral is documented.",
     "seq":"Use instead of coding bilateral individual codes.",
     "comp":"Documentation must state bilateral involvement.",
     "risk":"low","category":"Musculoskeletal"},

    {"type":"icd10","code":"E66.9","desc":"Obesity, unspecified",
     "keys":["obesity","obese","bmi 30","bmi 31","bmi 32","bmi 33","bmi 34","bmi 35","bmi 36","bmi 37","bmi 38","bmi 39","bmi 40"],
     "note":"Physician must document 'obesity'. Add Z68.3x BMI code as secondary.",
     "seq":"Typically secondary unless obesity is the primary reason for visit.",
     "comp":"Cannot assign from BMI alone — physician must explicitly document obesity.",
     "risk":"medium","category":"Endocrine"},

    {"type":"icd10","code":"Z68.34","desc":"Body mass index (BMI) 34.0–34.9",
     "keys":["bmi 34","body mass index 34"],
     "note":"Secondary informational code. Always pair with E66.x.",
     "seq":"Always secondary to obesity diagnosis code.",
     "comp":"Must be documented by the treating provider.",
     "risk":"low","category":"Z-codes"},

    {"type":"icd10","code":"Z68.31","desc":"Body mass index (BMI) 31.0–31.9",
     "keys":["bmi 31","body mass index 31"],
     "note":"Secondary. Pair with E66.9.",
     "seq":"Always secondary.",
     "comp":"Provider must document.",
     "risk":"low","category":"Z-codes"},

    {"type":"icd10","code":"Z79.4","desc":"Long-term (current) use of insulin",
     "keys":["insulin","insulin dependent","on insulin","insulin therapy","basal insulin","bolus insulin"],
     "note":"Add when T2DM patient is on insulin. Not used for T1DM (already implied).",
     "seq":"Always secondary to the diabetes diagnosis code.",
     "comp":"Document insulin regimen type (basal, bolus, or both).",
     "risk":"low","category":"Z-codes"},

    {"type":"icd10","code":"F32.9","desc":"Major depressive disorder, single episode, unspecified",
     "keys":["depression","depressive","major depressive","mdd","low mood","anhedonia","depressed"],
     "note":"Specify severity: F32.0 mild, F32.1 moderate, F32.2 severe, F32.3 with psychosis.",
     "seq":"Principal for mental health-focused visits.",
     "comp":"Document PHQ-9 scores, severity, and functional impact.",
     "risk":"medium","category":"Mental Health"},

    {"type":"icd10","code":"F41.1","desc":"Generalized anxiety disorder",
     "keys":["anxiety","generalized anxiety","gad","anxious","worry","panic"],
     "note":"Use F41.0 for panic disorder. F40.x for specific phobias.",
     "seq":"Principal for anxiety-focused visits.",
     "comp":"Document GAD-7 score and functional impairment.",
     "risk":"low","category":"Mental Health"},

    {"type":"icd10","code":"N39.0","desc":"Urinary tract infection, site not specified",
     "keys":["uti","urinary tract infection","dysuria","urinary infection","bacteriuria","cystitis"],
     "note":"Add organism code (B96.2x for E.coli) if culture documents causative organism.",
     "seq":"Principal when UTI is the primary reason for encounter.",
     "comp":"Culture and sensitivity results should be documented.",
     "risk":"low","category":"Genitourinary"},

    {"type":"icd10","code":"N18.3","desc":"Chronic kidney disease, stage 3",
     "keys":["ckd stage 3","chronic kidney disease stage 3","ckd 3","renal insufficiency","gfr 30","gfr 44","gfr 45","gfr 59"],
     "note":"Use N18.1–N18.6 based on GFR staging documented by physician.",
     "seq":"Secondary to primary condition causing CKD unless CKD is primary reason.",
     "comp":"Document GFR value and CKD stage. Add I12.x if hypertensive CKD.",
     "risk":"medium","category":"Genitourinary"},

    # ── CPT ────────────────────────────────────────────────────────────────────
    {"type":"cpt","code":"99213","desc":"E&M, established patient – low medical decision making",
     "keys":["office visit","follow-up","established patient","routine visit","follow up","low complexity","outpatient visit"],
     "note":"2021 guidelines: time or MDM determines level. Low MDM = 1 chronic stable condition.",
     "seq":"Primary CPT for low-complexity established patient encounters.",
     "comp":"Document MDM elements or total time. High audit risk if MDM underdocumented.",
     "risk":"medium","category":"E&M"},

    {"type":"cpt","code":"99214","desc":"E&M, established patient – moderate medical decision making",
     "keys":["moderate complexity","complex follow up","multiple conditions","medication management","moderate mdm","established moderate"],
     "note":"Moderate MDM: 2+ chronic conditions or Rx drug management or new problem.",
     "seq":"Primary CPT for moderate-complexity established patient visits.",
     "comp":"Document all problems addressed, data reviewed, and risk. Most common audit target.",
     "risk":"high","category":"E&M"},

    {"type":"cpt","code":"99215","desc":"E&M, established patient – high medical decision making",
     "keys":["high complexity","high mdm","severe condition","hospital discharge followup","complex management","critical decision"],
     "note":"High MDM requires: drug therapy monitoring, diagnosis/treatment with uncertain prognosis.",
     "seq":"Primary CPT for highest-complexity established patient visits.",
     "comp":"Extensive documentation required. High audit risk — ensure MDM elements clearly documented.",
     "risk":"high","category":"E&M"},

    {"type":"cpt","code":"99204","desc":"E&M, new patient – moderate medical decision making",
     "keys":["new patient","first visit","initial visit","new pt","new patient moderate"],
     "note":"New patient codes require ALL three key components documented.",
     "seq":"Primary CPT for new patient office visits with moderate complexity.",
     "comp":"HPI, exam, and MDM all required for new patient codes.",
     "risk":"medium","category":"E&M"},

    {"type":"cpt","code":"93010","desc":"Electrocardiogram, routine, interpretation and report",
     "keys":["ekg","ecg","electrocardiogram","cardiac rhythm","st elevation ekg","heart rhythm"],
     "note":"Use 93000 when physician performs, interprets, and provides report in office.",
     "seq":"Bill separately from E&M only when independently indicated.",
     "comp":"Physician interpretation note must be separately documented.",
     "risk":"low","category":"Cardiology"},

    {"type":"cpt","code":"92928","desc":"Percutaneous transcatheter placement of intracoronary stent",
     "keys":["pci","percutaneous coronary intervention","stent","coronary stent","angioplasty","ptca"],
     "note":"92929 for additional vessel. 92941 if performed during acute MI.",
     "seq":"Primary procedure code. Pair with appropriate ICD-10 for indication.",
     "comp":"Operative report must document vessel(s), stent type, and fluoroscopy time.",
     "risk":"high","category":"Cardiology"},

    {"type":"cpt","code":"93306","desc":"Echocardiography, transthoracic, complete",
     "keys":["echocardiogram","echo","transthoracic echo","tte","cardiac echo","cardiac ultrasound"],
     "note":"93307 if limited. 93308 for follow-up. Add 76825 for Doppler.",
     "seq":"Secondary to primary cardiac diagnosis.",
     "comp":"Physician interpretation report must be separately documented.",
     "risk":"low","category":"Cardiology"},

    {"type":"cpt","code":"20610","desc":"Arthrocentesis/injection, major joint",
     "keys":["knee injection","intra-articular injection","joint injection","corticosteroid injection","triamcinolone","steroid injection","arthrocentesis"],
     "note":"20611 with ultrasound guidance. Append modifier -RT or -LT for laterality.",
     "seq":"Bill with E&M if separately identifiable service performed on same day.",
     "comp":"Document: joint injected, medication, dose, lot number, laterality, consent.",
     "risk":"medium","category":"Musculoskeletal"},

    {"type":"cpt","code":"97110","desc":"Therapeutic exercises – per 15 minutes",
     "keys":["physical therapy","therapeutic exercise","pt","exercise therapy","rehabilitation","physiotherapy"],
     "note":"Bill per 15-min increments. Requires direct patient contact by licensed therapist.",
     "seq":"Billed by therapist, not physician. Separate claim.",
     "comp":"Document functional goals, time, and patient response per session.",
     "risk":"low","category":"Physical Therapy"},

    {"type":"cpt","code":"83036","desc":"Hemoglobin A1C",
     "keys":["hba1c","a1c","glycated hemoglobin","hemoglobin a1c","glycosylated"],
     "note":"Include QW modifier for CLIA-waived point-of-care testing.",
     "seq":"Secondary to E&M. Bill with diabetes ICD-10 code.",
     "comp":"Document result value. Ensure ordered by treating provider.",
     "risk":"low","category":"Laboratory"},

    {"type":"cpt","code":"80053","desc":"Comprehensive metabolic panel",
     "keys":["comprehensive metabolic panel","cmp","metabolic panel","bmp","basic metabolic","renal function panel"],
     "note":"Do NOT unbundle and bill individual components separately (NCCI violation).",
     "seq":"Secondary lab code to E&M visit.",
     "comp":"Results and physician interpretation must be in the record.",
     "risk":"medium","category":"Laboratory"},

    {"type":"cpt","code":"85025","desc":"Complete blood count (CBC) with differential",
     "keys":["cbc","complete blood count","blood count","white blood cell","wbc","hemoglobin","hematocrit"],
     "note":"85027 for CBC without differential. Do not bill components separately.",
     "seq":"Secondary lab code.",
     "comp":"Document clinical indication and result interpretation.",
     "risk":"low","category":"Laboratory"},

    {"type":"cpt","code":"87070","desc":"Culture, bacterial; any source, aerobic",
     "keys":["sputum culture","bacterial culture","culture","wound culture"],
     "note":"87086 for urine culture. 87040 for blood culture. Specify source.",
     "seq":"Secondary lab code.",
     "comp":"Document specimen source and ordering provider.",
     "risk":"low","category":"Laboratory"},

    {"type":"cpt","code":"87086","desc":"Culture, bacterial; urine, quantitative",
     "keys":["urine culture","urinary culture","midstream urine","clean catch culture"],
     "note":"Bill with 87088 for organism identification if performed.",
     "seq":"Secondary lab code with UTI diagnosis.",
     "comp":"Document collection method and result interpretation.",
     "risk":"low","category":"Laboratory"},

    {"type":"cpt","code":"71046","desc":"Chest X-ray, 2 views",
     "keys":["chest x-ray","cxr","chest radiograph","chest xray","x-ray chest","pa and lateral"],
     "note":"71045 for single view. 71048 for 4+ views.",
     "seq":"Secondary to E&M visit code.",
     "comp":"Radiologist report must be in the record. Document clinical indication.",
     "risk":"low","category":"Radiology"},

    {"type":"cpt","code":"93000","desc":"Electrocardiogram, routine with interpretation – complete",
     "keys":["12 lead ecg","12 lead ekg","complete ecg","routine ecg office"],
     "note":"Use 93010 when only interpretation performed (no tracing). 93005 for tracing only.",
     "seq":"Primary procedure code when performed and interpreted in-office.",
     "comp":"Both the tracing and the signed interpretation note must be in the record.",
     "risk":"low","category":"Cardiology"},

    # ── HCPCS ──────────────────────────────────────────────────────────────────
    {"type":"hcpcs","code":"J3301","desc":"Injection, triamcinolone acetonide, per 10 mg",
     "keys":["triamcinolone","kenalog","triamcinolone acetonide","corticosteroid injection","steroid injection"],
     "note":"Per 10 mg. For 40 mg dose, bill J3301 × 4 units. Include NDC number.",
     "seq":"Bill alongside CPT 20610 (injection procedure). Include joint condition ICD-10.",
     "comp":"Document drug name, concentration, total dose, lot number, route, NDC, and site.",
     "risk":"low","category":"Drug Codes"},

    {"type":"hcpcs","code":"J0696","desc":"Injection, ceftriaxone sodium, per 250 mg",
     "keys":["ceftriaxone","rocephin","iv antibiotic","ceftriaxone sodium"],
     "note":"Per 250 mg unit. Bill units based on total dose administered.",
     "seq":"Secondary to E&M and diagnosis code.",
     "comp":"Document dose, route, lot number, and NDC number.",
     "risk":"low","category":"Drug Codes"},

    {"type":"hcpcs","code":"J1745","desc":"Injection, infliximab, 10 mg",
     "keys":["infliximab","remicade","biologic","anti-tnf"],
     "note":"Per 10 mg. Requires prior authorization documentation on file.",
     "seq":"Bill with appropriate inflammatory disease ICD-10.",
     "comp":"Document prior auth, dose calculation, infusion time, and monitoring.",
     "risk":"high","category":"Drug Codes"},

    {"type":"hcpcs","code":"G0108","desc":"Diabetes outpatient self-management training, individual, per 30 min",
     "keys":["diabetes education","dsmt","self-management training","diabetes counseling","diabetes self"],
     "note":"Requires physician referral and ADA/AADE-recognized program.",
     "seq":"Secondary to E&M. Bill with E11.x ICD-10.",
     "comp":"Document physician referral, program accreditation, topics covered, and patient progress.",
     "risk":"medium","category":"Preventive"},

    {"type":"hcpcs","code":"G0439","desc":"Annual wellness visit, subsequent visit",
     "keys":["annual wellness","awv","preventive visit","wellness visit","annual physical medicare"],
     "note":"G0438 for initial AWV. Medicare Part B covers at 100% when billed correctly.",
     "seq":"Primary code for Medicare annual wellness visits.",
     "comp":"Document all AWV required elements: HRA, vital signs, cognitive screening, advance care planning.",
     "risk":"medium","category":"Preventive"},

    {"type":"hcpcs","code":"A9150","desc":"Non-prescription drug dispensed",
     "keys":["otc drug","over the counter","non-prescription drug","otc medication"],
     "note":"Rarely reimbursed. Check individual payer policy before billing.",
     "seq":"Secondary to clinical service codes.",
     "comp":"Document drug name, dose, and clinical indication.",
     "risk":"low","category":"Supplies"},

    {"type":"hcpcs","code":"Q4048","desc":"Specialty injection supply, per injection",
     "keys":["injection supply","syringe supply","needle supply","injection kit"],
     "note":"Check payer-specific policy. Not universally covered.",
     "seq":"Secondary to drug and procedure codes.",
     "comp":"Document supplies used per injection event.",
     "risk":"low","category":"Supplies"},
]

CATEGORIES = sorted(set(e["category"] for e in DB))

SAMPLES = {
    "🩺 Type 2 DM + HbA1c check":
        "58-year-old male with type 2 diabetes mellitus without complications presenting for routine follow-up. HbA1c 7.8%. BMI 31. BP 138/86 mmHg. Reports fatigue and nocturia. Patient is on metformin 1000 mg BID and basal insulin 20 units nightly. Comprehensive metabolic panel and HbA1c ordered today. Dietary counselling provided. Established patient, moderate complexity follow-up visit.",

    "❤️ Acute MI – STEMI + PCI":
        "72-year-old female presenting to ED with crushing substernal chest pain radiating to left arm, onset 2 hours ago. EKG shows ST-elevation in leads II, III, aVF. Troponin I elevated at 2.4 ng/mL. Diagnosis: STEMI inferior wall. Known coronary artery disease. Emergent PCI with coronary stent placement of RCA. Aspirin 325 mg and heparin drip administered. BP 94/62 on admission.",

    "🫁 Pneumonia + COPD Exacerbation":
        "45-year-old male, 4-day history of productive cough, fever 38.9°C, dyspnea. CXR shows right lower lobe consolidation consistent with community-acquired pneumonia. Known COPD with current acute exacerbation. Sputum culture ordered. Started on IV amoxicillin-clavulanate. O2 saturation 93% on room air. Spirometry: FEV1 55% predicted.",

    "🦵 Knee OA + Corticosteroid Injection":
        "67-year-old female with bilateral knee osteoarthritis confirmed on X-ray, worse on right side. Right knee intra-articular corticosteroid injection performed in office today: triamcinolone acetonide 40 mg/mL. BMI 34.2. Gait assessment performed. Referred to physical therapy for strengthening exercises. Hypertension noted, BP 142/88.",
}

# ── Matching Engine ─────────────────────────────────────────────────────────────
SECTION_PRIORITY_WEIGHTS = {
    "high": 2.5,
    "default": 1.0,
    "low": 0.5,
}

HIGH_PRIORITY_SECTIONS = (
    "assessment",
    "plan",
    "assessment/plan",
    "a/p",
    "discharge disposition",
    "final diagnosis",
    "diagnosis",
)

LOW_PRIORITY_SECTIONS = (
    "chief complaint",
    "cc",
    "emergency dept workup",
    "emergency department workup",
    "ed workup",
    "ed evaluation",
)

NEGATION_PRE_RE = re.compile(
    r"(?:\b(?:no|denies?|without|negative for|free of|absence of|rule out|ruled out|r/o|excluded)\b(?:\W+\w+){0,7}\W*)$",
    flags=re.IGNORECASE,
)
NEGATION_POST_RE = re.compile(
    r"^(?:\W*\w+){0,5}\W*(?:ruled out|rule out|excluded|not confirmed|not present)\b",
    flags=re.IGNORECASE,
)
SECTION_HEADER_RE = re.compile(r"^\s*([A-Za-z][A-Za-z /&\-\(\)]{2,80})\s*:\s*(.*)$")

def section_priority_weight(section_name: str) -> float:
    name = (section_name or "").strip().lower()
    if any(tag in name for tag in HIGH_PRIORITY_SECTIONS):
        return SECTION_PRIORITY_WEIGHTS["high"]
    if any(tag in name for tag in LOW_PRIORITY_SECTIONS):
        return SECTION_PRIORITY_WEIGHTS["low"]
    return SECTION_PRIORITY_WEIGHTS["default"]

def split_note_sections(note: str):
    sections = []
    current_name = "default"
    current_lines = []

    for line in note.splitlines():
        m = SECTION_HEADER_RE.match(line)
        if m:
            if current_lines:
                sections.append((current_name, "\n".join(current_lines).strip()))
            current_name = m.group(1).strip().lower()
            initial_content = m.group(2).strip()
            current_lines = [initial_content] if initial_content else []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_name, "\n".join(current_lines).strip()))

    if not sections:
        return [("default", note)]
    return sections

def is_negated_span(text: str, start: int, end: int) -> bool:
    pre_window = text[max(0, start - 100):start]
    post_window = text[end:end + 50]
    return bool(NEGATION_PRE_RE.search(pre_window) or NEGATION_POST_RE.search(post_window))

def keyword_has_non_negated_match(text: str, keyword: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(keyword)}\b", flags=re.IGNORECASE)
    for match in pattern.finditer(text):
        if not is_negated_span(text, match.start(), match.end()):
            return True
    return False

def match_codes(note: str):
    sections = split_note_sections(note)
    seen, hits = set(), []
    for entry in DB:
        if entry["code"] in seen:
            continue
        weighted_score = 0.0
        raw_score = 0
        max_section_weight = 0.0

        for section_name, section_text in sections:
            section_weight = section_priority_weight(section_name)
            section_hits = 0
            for key in entry["keys"]:
                if keyword_has_non_negated_match(section_text, key):
                    section_hits += 1
            if section_hits:
                raw_score += section_hits
                weighted_score += section_hits * section_weight
                max_section_weight = max(max_section_weight, section_weight)

        if weighted_score > 0:
            pct = min(100, int((weighted_score / len(entry["keys"])) * 180))
            pct = max(20, pct)
            hits.append({
                **entry,
                "score": raw_score,
                "weighted_score": weighted_score,
                "section_weight": max_section_weight,
                "confidence": pct
            })
            seen.add(entry["code"])
    hits.sort(
        key=lambda x: (
            -x["section_weight"],
            -x["confidence"],
            -x["weighted_score"],
        )
    )
    return (
        [h for h in hits if h["type"] == "icd10"],
        [h for h in hits if h["type"] == "cpt"],
        [h for h in hits if h["type"] == "hcpcs"],
    )

def conf_html(pct):
    cls = "conf-high" if pct >= 70 else ("conf-medium" if pct >= 40 else "conf-low")
    lbl = "High" if pct >= 70 else ("Medium" if pct >= 40 else "Low")
    return f"""
    <div class="conf-bar-wrap"><div class="conf-bar {cls}" style="width:{pct}%;"></div></div>
    <div class="conf-label">{lbl} match</div>"""

def risk_html(risk):
    return f'<span class="risk-{risk}">{"⚠" if risk=="high" else ("●" if risk=="medium" else "✓")} {risk.title()} risk</span>'

def code_row_html(c, tag_cls):
    return f"""
    <div class="code-row">
        <div>
            <span class="tag tag-{tag_cls}">{tag_cls.upper()}</span>
        </div>
        <div class="code-val">{c['code']}</div>
        <div class="code-main">
            <div class="code-desc">{c['desc']}</div>
            <div class="code-note">ℹ {c['note']}</div>
        </div>
        <div class="code-right">
            {risk_html(c['risk'])}
            {conf_html(c['confidence'])}
        </div>
    </div>"""

def generate_query_letter(icd10_codes, cpt_codes, note_snippet):
    if not icd10_codes:
        return ""
    today = datetime.today().strftime("%B %d, %Y")
    code_list = ", ".join([c['code'] for c in icd10_codes[:4]])
    issues = []
    for c in icd10_codes:
        if c['risk'] in ['medium','high']:
            issues.append(f"• {c['code']} – {c['comp']}")
    for c in cpt_codes:
        if c['risk'] in ['medium','high']:
            issues.append(f"• {c['code']} – {c['comp']}")
    issues_text = "\n".join(issues) if issues else "• Please confirm all diagnoses and procedures documented above."
    return f"""Date: {today}

To: Treating Physician / Healthcare Provider
From: Medical Coding Department — MTBC | CareCloud
Re: Coding Query — Clarification Required

Dear Provider,

Thank you for your clinical documentation. While reviewing the encounter, our coding team identified the following codes for assignment: {code_list}. To ensure accurate code assignment, complete reimbursement, and compliance with ICD-10-CM/CPT guidelines, we respectfully request clarification on the following:

{issues_text}

Please review, clarify, and countersign where applicable. Accurate documentation supports correct billing, reduces denial risk, and ensures compliance with payer and HIPAA requirements.

Thank you for your prompt attention.

Respectfully,
Medical Coding Team
MTBC | CareCloud — Rawalpindi Office"""

# ── Session state ───────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏥 MedCode AI Pro")
    st.markdown("---")
    st.markdown("**Quick Load Sample**")
    for label in SAMPLES:
        if st.button(label, key=f"sb_{label}", use_container_width=True):
            st.session_state["loaded_sample"] = SAMPLES[label]

    st.markdown("---")
    st.markdown("**Filter by Category**")
    cat_filter = st.multiselect("Show categories:", CATEGORIES, default=[], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**About**")
    st.markdown("""
    <div style="font-size:12px;color:#94A3B8;line-height:1.7;">
    Built for <strong style="color:#CBD5E1;">MTBC | CareCloud</strong><br>
    Medical Coder Portfolio Project<br><br>
    Covers ICD-10-CM · CPT · HCPCS II<br>
    Sequencing · Compliance · Audit Risk<br><br>
    <em>For educational use only.</em><br>
    Always verify against official manuals.
    </div>""", unsafe_allow_html=True)

# ── Top Bar ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="topbar-left">
        <div class="topbar-logo">🏥</div>
        <div>
            <h1>MedCode AI Pro</h1>
            <p>ICD-10-CM · CPT · HCPCS Level II · Sequencing · Compliance · Audit Risk</p>
        </div>
    </div>
    <span class="topbar-badge">✓ MTBC | CareCloud Portfolio</span>
</div>
""", unsafe_allow_html=True)

# ── KPI Row ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-row">
    <div class="kpi"><div class="kpi-icon">📋</div><div class="kpi-num">{len([d for d in DB if d['type']=='icd10'])}</div><div class="kpi-lbl">ICD-10-CM codes</div></div>
    <div class="kpi"><div class="kpi-icon">🔬</div><div class="kpi-num">{len([d for d in DB if d['type']=='cpt'])}</div><div class="kpi-lbl">CPT codes</div></div>
    <div class="kpi"><div class="kpi-icon">💊</div><div class="kpi-num">{len([d for d in DB if d['type']=='hcpcs'])}</div><div class="kpi-lbl">HCPCS Level II codes</div></div>
    <div class="kpi"><div class="kpi-icon">📁</div><div class="kpi-num">{len(st.session_state.history)}</div><div class="kpi-lbl">Coded this session</div></div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🔍  Code Analyzer", "📚  Code Reference", "📁  Coding History", "ℹ️  Compliance Guide"])

# ─────────────────────────────────────────────────────────────────────────────────
# TAB 1 — CODE ANALYZER
# ─────────────────────────────────────────────────────────────────────────────────
with tab1:
    col_l, col_r = st.columns([3, 2], gap="large")

    with col_l:
        st.markdown('<div class="card-title">📝 Clinical Note Input</div>', unsafe_allow_html=True)

        default_val = st.session_state.pop("loaded_sample", "")
        note_input = st.text_area(
            "Paste clinical documentation below:",
            value=default_val,
            height=200,
            placeholder="Paste clinical note, discharge summary, or encounter documentation here…",
            label_visibility="visible"
        )

        c1, c2 = st.columns([2, 1])
        with c1:
            analyze_btn = st.button("🔍  Analyze & Assign Codes", type="primary", use_container_width=True)
        with c2:
            clear_btn = st.button("🗑 Clear", use_container_width=True)
        if clear_btn:
            st.rerun()

        if note_input:
            words = len(note_input.split())
            st.caption(f"📊 {words} words · {len(note_input)} characters")

    with col_r:
        st.markdown('<div class="card-title">⚡ Quick Load Samples</div>', unsafe_allow_html=True)
        for label, text in SAMPLES.items():
            if st.button(label, key=f"tab1_{label}", use_container_width=True):
                st.session_state["loaded_sample"] = text
                st.rerun()

    st.markdown("---")

    # ── Results ────────────────────────────────────────────────────────────────
    if analyze_btn and note_input.strip():
        icd10, cpt, hcpcs = match_codes(note_input)

        # Apply category filter
        if cat_filter:
            icd10  = [c for c in icd10  if c.get("category") in cat_filter]
            cpt    = [c for c in cpt    if c.get("category") in cat_filter]
            hcpcs  = [c for c in hcpcs  if c.get("category") in cat_filter]

        total = len(icd10) + len(cpt) + len(hcpcs)

        if total == 0:
            st.markdown("""<div class="no-match">
                ⚠️ No matching codes found. Try using specific medical terminology such as
                "type 2 diabetes", "STEMI", "pneumonia", "knee osteoarthritis", or "hypertension".
            </div>""", unsafe_allow_html=True)
        else:
            # Summary
            high_risk = sum(1 for c in icd10+cpt+hcpcs if c['risk']=='high')
            st.markdown(f"""<div class="sum-pill">
                ✅ <strong>{total} code suggestions</strong> found:
                {len(icd10)} ICD-10-CM · {len(cpt)} CPT · {len(hcpcs)} HCPCS
                {"&nbsp;&nbsp;⚠️ <strong>" + str(high_risk) + " high-risk</strong> code(s) — review documentation carefully." if high_risk else ""}
            </div>""", unsafe_allow_html=True)

            # Columns for codes
            res_col1, res_col2 = st.columns(2, gap="medium")

            with res_col1:
                if icd10:
                    st.markdown('<div class="card-title">📋 ICD-10-CM Diagnosis Codes</div>', unsafe_allow_html=True)
                    for c in icd10:
                        st.markdown(code_row_html(c, "icd"), unsafe_allow_html=True)

                if hcpcs:
                    st.markdown('<div class="card-title" style="margin-top:1rem;">💊 HCPCS Level II</div>', unsafe_allow_html=True)
                    for c in hcpcs:
                        st.markdown(code_row_html(c, "hcpcs"), unsafe_allow_html=True)

            with res_col2:
                if cpt:
                    st.markdown('<div class="card-title">🔬 CPT Procedure Codes</div>', unsafe_allow_html=True)
                    for c in cpt:
                        st.markdown(code_row_html(c, "cpt"), unsafe_allow_html=True)

            # Sequencing
            seq_items = [f"<strong>{c['code']}</strong>: {c['seq']}" for c in icd10+cpt+hcpcs if c.get("seq")]
            if seq_items:
                st.markdown("---")
                st.markdown('<div class="card-title">📑 Code Sequencing Guidance</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="seq-box">{"<br><br>".join(seq_items)}</div>', unsafe_allow_html=True)

            # Compliance
            comp_items = [f"<strong>{c['code']}</strong>: {c['comp']}" for c in (icd10+cpt+hcpcs) if c.get("comp")]
            if comp_items:
                st.markdown('<div class="card-title">🛡️ Compliance & Documentation Notes</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="comp-box">{"<br><br>".join(comp_items[:5])}</div>', unsafe_allow_html=True)

            # Denial risk warnings
            high_risk_items = [c for c in icd10+cpt+hcpcs if c['risk']=='high']
            if high_risk_items:
                warn_txt = "<br>".join([f"⚠️ <strong>{c['code']}</strong>: High audit/denial risk — {c['comp']}" for c in high_risk_items])
                st.markdown(f'<div class="warn-box">{warn_txt}</div>', unsafe_allow_html=True)

            # Provider query letter
            st.markdown("---")
            with st.expander("📬 Generate Provider Query Letter"):
                letter = generate_query_letter(icd10, cpt, note_input[:200])
                st.markdown(f'<div class="query-box">{letter}</div>', unsafe_allow_html=True)
                st.download_button("⬇ Download Query Letter (.txt)", letter,
                                   file_name="provider_query.txt", mime="text/plain")

            # CSV export
            st.markdown("---")
            all_codes = (
                [{"Code":c['code'],"Type":"ICD-10","Description":c['desc'],"Risk":c['risk'],"Confidence":f"{c['confidence']}%"} for c in icd10] +
                [{"Code":c['code'],"Type":"CPT",   "Description":c['desc'],"Risk":c['risk'],"Confidence":f"{c['confidence']}%"} for c in cpt] +
                [{"Code":c['code'],"Type":"HCPCS", "Description":c['desc'],"Risk":c['risk'],"Confidence":f"{c['confidence']}%"} for c in hcpcs]
            )
            df = pd.DataFrame(all_codes)
            csv = df.to_csv(index=False)
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.download_button("⬇ Export Codes as CSV", csv,
                                   file_name=f"medcode_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                   mime="text/csv", use_container_width=True)
            with exp_col2:
                st.download_button("⬇ Export as JSON", json.dumps(all_codes, indent=2),
                                   file_name=f"medcode_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                                   mime="application/json", use_container_width=True)

            # Save to history
            st.session_state.history.insert(0, {
                "time": datetime.now().strftime("%H:%M"),
                "note": note_input[:80] + "...",
                "codes": ", ".join([c['code'] for c in icd10+cpt+hcpcs]),
                "total": total,
            })

    elif analyze_btn:
        st.warning("Please paste a clinical note before analyzing.")
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#94A3B8;font-size:14px;">
            🗂️ Paste a clinical note in the input area above and click
            <strong style="color:#185FA5;">Analyze & Assign Codes</strong> to begin.
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────────
# TAB 2 — CODE REFERENCE LIBRARY
# ─────────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 📚 Full Code Reference Library")
    search = st.text_input("🔍 Search by code or description", placeholder="e.g. E11, pneumonia, 20610…")

    type_filter = st.radio("Filter by type:", ["All", "ICD-10", "CPT", "HCPCS"], horizontal=True)

    filtered = DB
    if type_filter != "All":
        type_map = {"ICD-10":"icd10","CPT":"cpt","HCPCS":"hcpcs"}
        filtered = [d for d in filtered if d["type"] == type_map[type_filter]]
    if search:
        s = search.lower()
        filtered = [d for d in filtered if s in d["code"].lower() or s in d["desc"].lower()]
    if cat_filter:
        filtered = [d for d in filtered if d.get("category") in cat_filter]

    st.caption(f"Showing {len(filtered)} of {len(DB)} codes")

    if filtered:
        for c in filtered:
            tag_map = {"icd10":"icd","cpt":"cpt","hcpcs":"hcpcs"}
            tc = tag_map[c["type"]]
            st.markdown(f"""
            <div class="ref-row">
                <span class="tag tag-{tc}">{c['type'].upper()}</span>
                <div class="ref-code">{c['code']}</div>
                <div>
                    <div class="ref-desc">{c['desc']}</div>
                    <div class="ref-note">ℹ {c['note']} &nbsp;|&nbsp; 📂 {c['category']} &nbsp;|&nbsp; {risk_html(c['risk'])}</div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No codes match your search criteria.")

# ─────────────────────────────────────────────────────────────────────────────────
# TAB 3 — CODING HISTORY
# ─────────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 📁 Session Coding History")
    if st.session_state.history:
        if st.button("🗑 Clear History"):
            st.session_state.history = []
            st.rerun()
        for h in st.session_state.history:
            st.markdown(f"""
            <div class="hist-row">
                <span class="hist-time">🕐 {h['time']}</span>
                <span class="hist-note">📋 {h['note']}</span>
                <span class="hist-codes">🏷 {h['codes']}</span>
                <span style="font-size:12px;color:#64748B;">{h['total']} codes</span>
            </div>""", unsafe_allow_html=True)

        # Export history
        hist_df = pd.DataFrame(st.session_state.history)
        st.download_button("⬇ Export History as CSV", hist_df.to_csv(index=False),
                           file_name="coding_history.csv", mime="text/csv")
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#94A3B8;">
            📭 No coding history yet. Run an analysis in the Code Analyzer tab.
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────────
# TAB 4 — COMPLIANCE GUIDE
# ─────────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### ℹ️ Compliance & Coding Guidelines")
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        #### 📌 ICD-10-CM Sequencing Rules
        """)
        st.markdown("""<div class="seq-box">
        <strong>Principal Diagnosis:</strong> The condition established after study to be chiefly responsible for the admission/visit.<br><br>
        <strong>Combination Codes:</strong> A single code that classifies two diagnoses or a diagnosis with a complication (e.g. E11.65 = T2DM + hyperglycemia).<br><br>
        <strong>Excludes1:</strong> Two conditions that cannot occur together. Never code both.<br><br>
        <strong>Excludes2:</strong> The condition is not included here but may be coded additionally if present.<br><br>
        <strong>Pneumonia + COPD:</strong> Sequence pneumonia (J18.9) first; COPD (J44.1) second per official guidelines.
        </div>""", unsafe_allow_html=True)

        st.markdown("#### 🔬 CPT Coding Essentials")
        st.markdown("""<div class="comp-box">
        <strong>2021 E&M Changes:</strong> Level determined by Medical Decision Making (MDM) OR total time — not 3-key-component rule.<br><br>
        <strong>MDM Levels:</strong> Straightforward (99202/99212), Low (99203/99213), Moderate (99204/99214), High (99205/99215).<br><br>
        <strong>Modifier -25:</strong> Required when billing E&M on same day as a procedure (significant, separately identifiable service).<br><br>
        <strong>NCCI Edits:</strong> Never unbundle component codes when a panel/bundled code exists (e.g. never bill individual CMP components separately).
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("#### 🛡️ HIPAA Compliance Essentials")
        st.markdown("""<div class="warn-box">
        <strong>Minimum Necessary Standard:</strong> Access only the PHI required to perform your job function.<br><br>
        <strong>PHI (Protected Health Information):</strong> Any individually identifiable health information — name, DOB, MRN, diagnosis, treatment details.<br><br>
        <strong>Data Security:</strong> Never share patient records via unsecured email. Use encrypted channels only.<br><br>
        <strong>Breach Notification:</strong> Report any suspected PHI breach to your supervisor and compliance officer immediately.<br><br>
        <strong>Audit Trail:</strong> All code assignments must be traceable to source documentation in the medical record.
        </div>""", unsafe_allow_html=True)

        st.markdown("#### ⚠️ Top Audit Triggers")
        st.markdown("""<div class="warn-box">
        <strong>E&M Upcoding:</strong> 99214/99215 without sufficient MDM documentation.<br><br>
        <strong>Unbundling:</strong> Billing component codes instead of panel codes (CMP, CBC).<br><br>
        <strong>Modifier Misuse:</strong> Appending -25, -59 without clinical justification.<br><br>
        <strong>Missing Laterality:</strong> Procedure/diagnosis codes requiring laterality (RT/LT) without documentation.<br><br>
        <strong>Drug Codes:</strong> J-codes without NDC number documentation on the claim.
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:12px;color:#94A3B8;text-align:center;padding:1rem 0;">
    ⚕️ MedCode AI Pro · Built for MTBC | CareCloud Medical Coding Portfolio · Rawalpindi, Pakistan · 2026<br>
    <em>For educational and portfolio use only. Always verify against official ICD-10-CM, CPT, and HCPCS manuals and payer guidelines before clinical submission.</em>
    </div>""", unsafe_allow_html=True)
