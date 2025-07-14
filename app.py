import streamlit as st

# Helper function for boolean inputs (Streamlit checkboxes handle this naturally)
def get_yes_no_input_streamlit(label):
    return st.checkbox(label)

# Main Triage Logic Function - based on AIIMS ATP criteria
def classify_patient_aiims_atp(data):
    reasons = []
    triage_level = "GREEN" # Default to Green, then upgrade

    # --- 1. CHECK FOR RED CRITERIA FIRST ---
    # Physiological Compromise
    if data['stridor'] or data['angioedema'] or data['active_seizures']:
        reasons.append("Airway compromise (Stridor/Angioedema/Active Seizures)")
        triage_level = "RED"
        return triage_level, reasons # Exit early if RED

    if data['talking_incomplete_sentences'] or data['audible_wheeze'] or \
       data['rr'] > 22 or data['rr'] < 10 or data['spo2'] < 90:
        reasons.append("Breathing compromise (Abnormal RR/SpO2, Dyspnea, Wheeze)")
        triage_level = "RED"
        return triage_level, reasons # Exit early if RED

    # Handle SBP=0 for shock index calculation to prevent division by zero
    shock_index = data['hr'] / data['sbp'] if data['sbp'] != 0 else 0
    if data['hr'] < 50 or data['hr'] > 120 or \
       data['sbp'] < 90 or data['sbp'] > 220 or data['dbp'] < 60 or data['dbp'] > 110 or \
       shock_index > 1.0 or data['active_bleeding']:
        reasons.append("Circulation compromise (Abnormal HR/BP, Shock Index >1, Active Bleeding)")
        triage_level = "RED"
        return triage_level, reasons # Exit early if RED

    if data['avpu'] in ['V', 'P', 'U']: # AVPU is 'V' (verbal), 'P' (pain), or 'U' (unresponsive).
        reasons.append("Altered sensorium (AVPU < Alert)")
        triage_level = "RED"
        return triage_level, reasons # Exit early if RED

    # Time-Sensitive Conditions (simplified for direct input)
    if data['acute_chest_pain_lt_24hr'] or data['suspected_stroke_lt_24hr'] or \
       data['acute_sob_lt_12hr'] or data['pain_score'] > 7 or \
       data['sudden_severe_headache'] or data['acute_limb_ischemia'] or \
       data['history_syncope'] or data['abdominal_pain_sudden_onset'] or \
       data['fever_immunocompromised'] or data['acute_urinary_retention'] or \
       data['temp'] > 40.0 or data['temp'] < 35.0: # Added temperature to RED
        reasons.append("Time-sensitive/Urgent condition requiring immediate attention (including extreme temp).")
        triage_level = "RED"
        return triage_level, reasons # Exit early if RED

    # Other Conditions with Increased Urgency
    if data['agitated_violent'] or data['suspected_poisoning_bite'] or \
       data['pregnant_3rd_trimester_abdominal_bleed']:
        reasons.append("Other highly urgent condition (Agitation/Poisoning/Pregnancy complication).")
        triage_level = "RED"
        return triage_level, reasons # Exit early if RED

    # --- 2. CHECK FOR YELLOW CRITERIA (If not RED) ---
    # Vitals (less critical but still warranting urgency)
    if (data['rr'] >= 20 and data['rr'] <= 22) or \
       (data['hr'] >= 100 and data['hr'] <= 120) or \
       (data['sbp'] >= 180 and data['sbp'] <= 220) or \
       (data['dbp'] >= 100 and data['dbp'] <= 110) or \
       (data['temp'] >= 38.0 and data['temp'] <= 40.0): # Added temperature to YELLOW range
        reasons.append("Vital signs slightly abnormal, warranting urgent assessment (including fever).")
        triage_level = "YELLOW"
        # Don't return yet, check other yellow conditions, but don't re-classify as RED

    # Symptoms/Conditions needing urgent assessment/admission
    if (data['pain_score'] >= 4 and data['pain_score'] <= 7) or \
       data['vomiting_diarrhea_persistent'] or data['minor_trauma_with_deformity'] or \
       data['fever_no_red_flags'] or data['urinary_symptoms_moderate'] or \
       data['older_adult_minor_fall'] or data['pediatric_fever_irritable'] or \
       data['chronic_condition_exacerbation']:
        if triage_level == "GREEN": # Only upgrade to YELLOW if no higher priority set
            reasons.append("Semi-urgent condition requiring evaluation/admission.")
            triage_level = "YELLOW"
        elif triage_level == "YELLOW" and not reasons: # If already yellow from vitals, add this reason
            reasons.append("Semi-urgent condition requiring evaluation/admission.")


    # --- 3. DEFAULT TO GREEN (If not RED and not YELLOW) ---
    if not reasons: # If reasons list is still empty, no Red or Yellow criteria met
        reasons.append("No specific red or yellow criteria met. Appears non-urgent.")
        triage_level = "GREEN"
    elif triage_level == "GREEN" and not reasons: # Ensure a reason is captured for GREEN if it falls through
        reasons.append("Minor condition with stable vitals.")


    return triage_level, reasons


# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="AIIMS ATP Triage Simulator")

st.title("AIIMS Triage Protocol Simulator (Rule-Based Prototype)")
st.markdown("---")
st.write("Enter patient information to classify their triage level according to a simplified AIIMS ATP. "
         "This is a rule-based simulation to demonstrate the logic.")

# Input Form using Streamlit columns for better layout
col1, col2, col3 = st.columns(3)

with col1:
    st.header("1. Vital Signs")
    spo2 = st.number_input("Oxygen Saturation (SpO2 %)", min_value=0.0, max_value=100.0, value=98.0, step=0.1)
    hr = st.number_input("Heart Rate (bpm)", min_value=0, max_value=200, value=80)
    sbp = st.number_input("Systolic BP (mmHg)", min_value=0, max_value=250, value=120)
    dbp = st.number_input("Diastolic BP (mmHg)", min_value=0, max_value=150, value=80)
    rr = st.number_input("Respiratory Rate (breaths/min)", min_value=0, max_value=40, value=16)
    temp = st.number_input("Temperature (°C)", min_value=25.0, max_value=45.0, value=37.0)
    avpu = st.radio("AVPU Scale (Consciousness)", ['A - Alert', 'V - Verbal', 'P - Pain', 'U - Unresponsive'], index=0)
    pain_score = st.slider("Pain Score (0-10)", 0, 10, 0) # Used for both Red (extreme) and Yellow (moderate)

with col2:
    st.header("2. Key Red-Flag Symptoms / Conditions")
    st.markdown("*(Any 'yes' here likely results in **RED**)*")

    st.subheader("Airway & Breathing Critical:")
    stridor = st.checkbox("Noisy breathing (Stridor)?", key="stridor_ui") # Changed key for clarity
    angioedema = st.checkbox("Facial/throat swelling (Angioedema)?", key="angioedema_ui") # Changed key
    active_seizures = st.checkbox("Actively seizing?", key="active_seizures_ui") # Changed key
    talking_incomplete_sentences = st.checkbox("Talking in incomplete sentences?", key="talking_incomplete_sentences_ui") # Changed key
    audible_wheeze = st.checkbox("Audible wheeze (without stethoscope)?", key="audible_wheeze_ui") # Changed key

    st.subheader("Circulation Critical:")
    active_bleeding = st.checkbox("Active, significant bleeding?", key="active_bleeding_ui") # Changed key

    st.subheader("Neurological / Systemic Critical:")
    sudden_severe_headache = st.checkbox("Sudden, severe headache ('worst of life')?", key="sudden_severe_headache_ui") # Changed key
    history_syncope = st.checkbox("History of syncope (fainting) with current symptoms?", key="history_syncope_ui") # Changed key
    agitated_violent = st.checkbox("Patient agitated/violent?", key="agitated_violent_ui") # Changed key

    st.subheader("Time-Sensitive Emergencies:")
    acute_chest_pain_lt_24hr = st.checkbox("Acute chest pain (< 24 hrs duration)?", key="acute_chest_pain_lt_24hr_ui") # Changed key
    suspected_stroke_lt_24hr = st.checkbox("Suspected stroke symptoms (< 24 hrs duration)?", key="suspected_stroke_lt_24hr_ui") # Changed key
    acute_sob_lt_12hr = st.checkbox("Acute Shortness of Breath (< 12 hrs duration)?", key="acute_sob_lt_12hr_ui") # Changed key
    acute_limb_ischemia = st.checkbox("Signs of acute limb ischemia (cold/pale limb, sudden pain)?", key="acute_limb_ischemia_ui") # Changed key
    abdominal_pain_sudden_onset = st.checkbox("Sudden onset severe abdominal pain?", key="abdominal_pain_sudden_onset_ui") # Changed key
    acute_urinary_retention = st.checkbox("Acute urinary retention (cannot pass urine)?", key="acute_urinary_retention_ui") # Changed key
    pregnant_3rd_trimester_abdominal_bleed = st.checkbox("Pregnant (3rd trimester) with abdominal pain/vaginal bleed?", key="pregnant_3rd_trimester_abdominal_bleed_ui") # Changed key
    suspected_poisoning_bite = st.checkbox("Suspected poisoning, snake/scorpion bite?", key="suspected_poisoning_bite_ui") # Changed key
    fever_immunocompromised = st.checkbox("Fever AND immunocompromised (e.g., recent chemotherapy, severe chronic illness)?", key="fever_immunocompromised_ui") # Changed key


with col3:
    st.header("3. Urgent (Yellow) & Non-Urgent (Green) Indicators")
    st.markdown("*(Reviewed if not **RED**)*")

    st.subheader("Yellow Indicators:")
    vomiting_diarrhea_persistent = st.checkbox("Persistent vomiting/diarrhea (mild dehydration, not severe)?", key="vomiting_diarrhea_persistent_ui") # Changed key
    minor_trauma_with_deformity = st.checkbox("Minor trauma with suspected deformity/fracture (stable vitals)?", key="minor_trauma_with_deformity_ui") # Changed key
    fever_no_red_flags = st.checkbox("Fever (≥38°C) without any 'Red' flags from above?", key="fever_no_red_flags_ui") # Changed key
    urinary_symptoms_moderate = st.checkbox("Moderate urinary symptoms (e.g., severe dysuria, no retention)?", key="urinary_symptoms_moderate_ui") # Changed key
    older_adult_minor_fall = st.checkbox("Older adult (>65) with minor fall, stable?", key="older_adult_minor_fall_ui") # Changed key
    pediatric_fever_irritable = st.checkbox("Pediatric patient with fever & irritability (not lethargy/seizures)?", key="pediatric_fever_irritable_ui") # Changed key
    chronic_condition_exacerbation = st.checkbox("Stable exacerbation of a known chronic condition (e.g., controlled asthma flare)?", key="chronic_condition_exacerbation_ui") # Changed key

    st.subheader("Green Indicators:")
    minor_cut_abrasion = st.checkbox("Minor cut/abrasion (not actively bleeding)?", key="minor_cut_abrasion_ui") # Changed key
    mild_cold_symptoms = st.checkbox("Mild cold symptoms (cough, runny nose, no breathing difficulty/fever)?", key="mild_cold_symptoms_ui") # Changed key
    medication_refill_request = st.checkbox("Visit primarily for routine medication refill?", key="medication_refill_request_ui") # Changed key


if st.button("Classify Triage Level"):
    # Prepare data dictionary for classification function.
    # IMPORTANT: The keys in this dictionary MUST match the keys accessed in classify_patient_aiims_atp()
    patient_data = {
        'spo2': spo2,
        'hr': hr,
        'sbp': sbp,
        'dbp': dbp,
        'rr': rr,
        'temp': temp,
        'avpu': avpu[0], # Extracts 'A', 'V', 'P', 'U' from 'A - Alert' string
        'pain_score': pain_score,
        # Red-specific inputs (use direct variable names, which align with logic function)
        'stridor': stridor,
        'angioedema': angioedema,
        'active_seizures': active_seizures,
        'talking_incomplete_sentences': talking_incomplete_sentences,
        'audible_wheeze': audible_wheeze,
        'active_bleeding': active_bleeding,
        'sudden_severe_headache': sudden_severe_headache,
        'history_syncope': history_syncope,
        'agitated_violent': agitated_violent,
        'acute_chest_pain_lt_24hr': acute_chest_pain_lt_24hr,
        'suspected_stroke_lt_24hr': suspected_stroke_lt_24hr,
        'acute_sob_lt_12hr': acute_sob_lt_12hr,
        'acute_limb_ischemia': acute_limb_ischemia,
        'abdominal_pain_sudden_onset': abdominal_pain_sudden_onset,
        'acute_urinary_retention': acute_urinary_retention,
        'pregnant_3rd_trimester_abdominal_bleed': pregnant_3rd_trimester_abdominal_bleed,
        'suspected_poisoning_bite': suspected_poisoning_bite,
        'fever_immunocompromised': fever_immunocompromised,
        # Yellow & Green specific inputs (use direct variable names)
        'vomiting_diarrhea_persistent': vomiting_diarrhea_persistent,
        'minor_trauma_with_deformity': minor_trauma_with_deformity,
        'fever_no_red_flags': fever_no_red_flags,
        'urinary_symptoms_moderate': urinary_symptoms_moderate,
        'older_adult_minor_fall': older_adult_minor_fall,
        'pediatric_fever_irritable': pediatric_fever_irritable,
        'chronic_condition_exacerbation': chronic_condition_exacerbation,
        'minor_cut_abrasion': minor_cut_abrasion,
        'mild_cold_symptoms': mild_cold_symptoms,
        'medication_refill_request': medication_refill_request
    }

    triage_level, reasons_list = classify_patient_aiims_atp(patient_data)

    st.markdown("---")
    st.subheader("🏥 Triage Result:")
    if triage_level == "RED":
        st.error(f"**Triage Level: {triage_level} - IMMEDIATE ATTENTION REQUIRED**")
    elif triage_level == "YELLOW":
        st.warning(f"**Triage Level: {triage_level} - URGENT CARE REQUIRED**")
    else: # GREEN
        st.success(f"**Triage Level: {triage_level} - NON-URGENT CARE**")

    st.markdown("#### Reasons for Classification:")
    for reason in reasons_list:
        st.write(f"- {reason}")

st.markdown("---")
st.header("💡 Conceptual AI/ML Enhancements for a Real-World System")
st.write("""
This prototype demonstrates the core rule-based logic of the AIIMS Triage Protocol, enabling clear classification based on predefined criteria.
However, a truly 'AI-based' triage system would integrate advanced machine learning techniques to overcome the limitations of
a purely rule-based approach and provide more sophisticated decision support:

1.  **Natural Language Processing (NLP) for Chief Complaint:** Automatically extract and interpret rich medical information and severity from the patient's free-text chief complaint (e.g., "my chest feels like it's going to explode") and extract relevant medical features automatically. This would eliminate the need for many explicit yes/no checkboxes and capture nuances.
2.  **Complex Pattern Recognition & Data Integration:** Machine learning models (e.g., Gradient Boosting Machines, Neural Networks) can learn from vast amounts of historical, multi-modal patient data (vitals, symptoms, lab results, medical history, demographics) to identify subtle correlations and complex patterns that might not fit simple 'if-else' rules. This is crucial for ambiguous cases or when multiple criteria are partially met.
3.  **Predictive Analytics:** Beyond just assigning a triage level, AI could predict the likelihood of adverse patient outcomes (e.g., ICU admission, need for surgery, mortality, readmission) or anticipated resource utilization (e.g., imaging, specialist consults). This helps in proactive resource allocation and patient flow management.
4.  **Learning and Adaptation:** A deployed AI system could continuously learn and improve its decision-making over time as new patient data and actual outcomes become available. This allows the system to adapt to evolving medical knowledge, local patient populations, and improve its accuracy without manual rule updates.
5.  **Handling Missing/Incomplete Data:** ML models can be more robust in making reasonable predictions even when some data points are missing, unlike a strict rule-based system that might fail if a required input is absent.

In essence, while this prototype provides a solid foundation, a real-world AI triage system would leverage data-driven insights and learning capabilities to provide more nuanced, predictive, and adaptable decision support.
""")