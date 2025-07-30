# CTAS Logic Enhancements

This document details the enhancements made to the CTAS triage logic in `app.py`, with direct references to the source documents that justify these changes.

---

### 1. Frailty Modifier Integration

**Description:**
A "Frailty Modifier" has been added to the triage logic. If a patient is identified as frail (e.g., dependent on others for care, advanced age with debility) and their initial calculated score is CTAS Level 4 or 5, they are automatically upgraded to **CTAS Level 3**. This ensures that vulnerable patients who may not present with acute vital sign changes are seen more promptly, reducing the risk of deterioration in the waiting room.

**Files Modified:**
*   `templates/professional_triage.html`: Added a checkbox to the form for the triage nurse to identify a frail patient.
*   `static/js/triage.js`: Updated to send the frailty status to the backend.
*   `app.py`: The `calculate_ctas_logic` function now checks for the `is_frail` flag and upgrades the CTAS level if necessary.

**Reference:**
*   **Document:** `revisions_to_the_canadian_emergency_department_triage_and_acuity_scale_ctas_guidelines_2016.pdf`
*   **Page:** 5 (S22)
*   **Quote:**
    > "**6. New Frailty modifier**
    > 
    > **Rationale**
    > As volume and capacity pressures on emergency departments continue, certain groups are at risk for prolonged wait times who run a greater risk of deteriorating or suffering unduly. These include: the frail elderly, those who are physically disabled, cognitively challenged, with debilitating diseases, or homeless, especially if unaccompanied...
    > The introduction of a CTAS level 3 ‘frailty modifier’ will allow triage nurses to up-triage such patients normally rated as a CTAS level 4 or 5.
    > 
    > **Frailty modifier definition**
    > Any patient completely dependent for personal care; who is wheelchair-bound; suffers from cognitive impairment that limits their awareness of their surroundings or ability to appreciate time; is in the late course of a terminal illness; is showing signs of cachexia and general weakness; or is over 80 years of age unless obviously physically and mentally robust."

---

### 2. Paediatric Fever Logic Refinement

**Description:**
The age range for specific paediatric fever modifiers has been updated to align with the 2016 guidelines. The modifiers for a temperature >38.5°C (“looks unwell” for CTAS 2 and “looks well” for CTAS 3) now apply only to children aged **3 to 18 months**. This change reflects updated evidence and immunization programs that have altered the incidence of serious infections in young children.

**Files Modified:**
*   `app.py`: The `calculate_ctas_logic` function was updated to change the age check from `3-36 months` to `3-18 months` for the paediatric fever logic.

**Reference:**
*   **Document:** `revisions_to_the_canadian_emergency_department_triage_and_acuity_scale_ctas_guidelines_2016.pdf`
*   **Page:** 7 (S24)
*   **Quote:**
    > "**8. Paediatric updates**
    > 
    > The fever modifier ‘temperature greater than 38.5°C looks unwell’ CTAS level 2 and ‘temperature greater than 38.5°C looks well’ CTAS level 3 will be limited to children 3-18 months, rather than the previous 3-36 months. Otherwise Paediatric CTAS remains unchanged.
    > 
    > **Rationale**
    > The fever modifier in paediatrics was adopted to capture the vulnerable population for sepsis in childhood... In recognition of the changing patterns of childhood infections, the temperature greater than 38.5°C fever modifier, which previously included children up to 36 months, will be limited to children 3-18 months."

---

### 3. Time-Sensitive CVA (Stroke) Modifier

**Description:**
A time-sensitive modifier has been implemented for patients presenting with stroke-like symptoms. If the patient's symptom onset was **less than 4.5 hours ago**, they are automatically assigned **CTAS Level 2**. This ensures they are fast-tracked for time-critical interventions like thrombolysis, which can significantly improve outcomes.

**Files Modified:**
*   `templates/professional_triage.html`: Added a field to input the time of symptom onset.
*   `static/js/triage.js`: Updated to include the onset time in the data sent to the backend.
*   `app.py`: The `calculate_ctas_logic` function now includes a specific check for CVA complaints and symptom onset time.

**Reference:**
*   **Document:** `participant_manual_v2.5b_november_2013_0.pdf`
*   **Page:** 35
*   **Quote:**
    > "**2.5.4 Other examples of Selected 2nd Order Modifiers**
    > 
    > | Presenting Complaint | Revised Modifier | CTAS Level |
    > |---|---|---|
    > | Extremity weakness / symptoms of CVA | time of onset of symptoms < 4.5 hours | 2 |
    > | | > 4.5 hours or resolved | 3 |"

---

### 4. Dynamic Reassessment Interval Calculation

**Description:**
The application now calculates and displays the mandatory reassessment interval based on the final CTAS level. This makes the process of re-evaluating waiting patients more explicit and provides a clear timeframe for the triage staff.

**Files Modified:**
*   `app.py`: The `calculate_ctas_logic` function now returns both the CTAS level and the corresponding reassessment interval in minutes. The API response was updated to include this new field.
*   `static/js/triage.js`: The frontend now receives the reassessment interval and displays it in the summary section.
*   `templates/professional_triage.html`: The summary section was updated to include a field for displaying the reassessment time.

**Reference:**
*   **Document:** `participant_manual_v2.5b_november_2013_0.pdf`
*   **Page:** 19
*   **Quote:**
    > "**Reassessments in Waiting Areas**
    > 
    > All waiting patients should be reassessed within the following time frames:
    > 
    > Level 1 – Continuous nursing care
    > 
    > Level 2 – Every 15 minutes
    > 
    > Level 3 – Every 30 Minutes
    > 
    > Level 4 – Every 60 minutes
    > 
    > Level 5 – Every 120 minutes
    > 
    > The extent of the reassessment depends upon the presenting complaint, the initial triage level and any changes identified by the patient. The triage nurse documents the reassessment findings and any changes in the patient’s acuity score, however, the initial triage score is never changed.
    > 
    > With each reassessment the nurse must decide: “How long can this patient safely wait?”"
