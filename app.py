# Import necessary libraries
# Added render_template
from flask import Flask, render_template, request, jsonify, Response, session
import csv
import io
from datetime import datetime
import os
import secrets
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# Production configuration using environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['PERMANENT_SESSION_LIFETIME'] = int(os.environ.get('PERMANENT_SESSION_LIFETIME', '3600'))

# Application settings
DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'ar')
SUPPORTED_LANGUAGES = os.environ.get('SUPPORTED_LANGUAGES', 'ar,en').split(',')
DEFAULT_THEME = os.environ.get('DEFAULT_THEME', 'light')

# Setup logging for production
flask_env = os.environ.get('FLASK_ENV', 'production')
if flask_env == 'production':
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    log_file = os.environ.get('LOG_FILE', 'app.log')
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    
    file_handler = RotatingFileHandler(
        f"logs/{log_file}", 
        maxBytes=10240000, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(getattr(logging, log_level))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, log_level))
    app.logger.info('CTAS Triage System startup - Production Mode')

# Security headers middleware
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' https://cdn.tailwindcss.com https://fonts.googleapis.com https://fonts.gstatic.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    app.logger.warning(f'404 error: {request.url}')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 error: {str(error)}')
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled exception: {str(e)}')
    return render_template('500.html'), 500

def safe_int(value):
    """Helper function to safely convert to int or return None."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def safe_float(value):
    """Helper function to safely convert to float or return None."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def calculate_ctas_logic(data):
    """Calculate CTAS level using Canadian Triage and Acuity Scale as implemented in Saudi Arabia."""
    
    # --- Get Input Data ---
    age = safe_int(data.get('patient_age'))
    complaint = data.get('chief_complaint', '')
    hr = safe_int(data.get('heart_rate'))
    rr = safe_int(data.get('resp_rate'))
    spo2 = safe_int(data.get('spo2'))
    bp_sys = safe_int(data.get('bp_systolic'))
    temp = safe_float(data.get('temperature'))
    gcs = safe_int(data.get('gcs_score'))
    avpu = data.get('avpu')
    pain = safe_int(data.get('pain_score', 0))
    resp_distress = data.get('respiratory_distress', 'none')
    bleeding = data.get('bleeding', 'none')
    moi = data.get('mechanism_injury', 'none')
    glucose = safe_float(data.get('glucose'))
    dehydration = data.get('dehydration', 'none')
    
    # Saudi-specific factors
    heat_exposure = data.get('heat_exposure', 'no')
    diabetes_status = data.get('has_diabetes', 'no')
    time_waiting = safe_int(data.get('time_waiting', 0))

    # Use AVPU if GCS is not provided
    loc_indicator = gcs if gcs is not None else avpu

    ctas_level = 5  # Default to CTAS V (Non-urgent)

    # --- Determine Age Group (Saudi pediatric ranges) ---
    age_group = 'adult'  # Default
    if age is not None:
        if age < 1/12: age_group = 'newborn'  # < 1 month
        elif age < 1: age_group = 'infant'
        elif age < 3: age_group = 'toddler'
        elif age < 5: age_group = 'preschool'
        elif age < 12: age_group = 'school_age'
        elif age < 18: age_group = 'adolescent'

    # --- Saudi-specific heat illness check (HIGH PRIORITY) ---
    if heat_exposure == 'yes' and temp is not None and temp >= 40.0:
        return 1  # Heat stroke - CTAS I
    elif heat_exposure == 'yes' and (temp is not None and temp >= 38.5) and dehydration in ['moderate', 'severe']:
        return 2  # Heat exhaustion - CTAS II

    # --- CTAS I: Resuscitation (Immediate) ---
    is_ctas1 = False
    
    # Critical LOC
    if (gcs is not None and gcs < 9) or (gcs is None and avpu in ['U', 'P']):
        is_ctas1 = True
    
    # Life-threatening conditions
    elif complaint in ['cardiac_arrest', 'resp_arrest'] or \
         resp_distress == 'severe' or \
         (spo2 is not None and spo2 < 90) or \
         bleeding == 'severe' or \
         complaint in ['shock', 'major_trauma', 'anaphylaxis', 'seizure_active']:
        is_ctas1 = True
    
    # Critical vital signs (Saudi pediatric ranges)
    elif age_group == 'newborn' and ((hr is not None and (hr < 120 or hr > 200)) or (rr is not None and (rr < 30 or rr > 80))):
        is_ctas1 = True
    elif age_group == 'infant' and ((hr is not None and (hr < 100 or hr > 200)) or (rr is not None and (rr < 25 or rr > 70))):
        is_ctas1 = True
    elif age_group == 'toddler' and ((hr is not None and (hr < 90 or hr > 180)) or (rr is not None and (rr < 20 or rr > 50))):
        is_ctas1 = True
    elif age_group == 'preschool' and ((hr is not None and (hr < 80 or hr > 160)) or (rr is not None and (rr < 20 or rr > 40))):
        is_ctas1 = True
    elif age_group == 'school_age' and ((hr is not None and (hr < 70 or hr > 140)) or (rr is not None and (rr < 15 or rr > 35))):
        is_ctas1 = True
    elif age_group == 'adolescent' and ((hr is not None and (hr < 60 or hr > 140)) or (rr is not None and (rr < 12 or rr > 30))):
        is_ctas1 = True
    elif age_group == 'adult' and ((hr is not None and (hr < 40 or hr > 140)) or (rr is not None and (rr < 8 or rr > 35)) or (bp_sys is not None and bp_sys < 80)):
        is_ctas1 = True

    if is_ctas1: return 1

    # --- CTAS II: Emergent (≤15 minutes) ---
    is_ctas2 = False
    
    # Altered LOC
    if (gcs is not None and 9 <= gcs <= 13) or (gcs is None and avpu == 'V'):
        is_ctas2 = True
    
    # High-risk conditions
    elif complaint in ['chest_pain_cardiac', 'stroke', 'sepsis', 'overdose'] or \
         resp_distress == 'moderate' or \
         (pain is not None and pain >= 8) or \
         complaint in ['severe_pain', 'head_injury_moderate', 'vaginal_bleeding_heavy', 'fever_infant', 'psych_severe'] or \
         dehydration == 'severe' or moi == 'significant':
        is_ctas2 = True
    
    # Diabetic emergency (high prevalence in Saudi Arabia)
    elif diabetes_status == 'yes' and glucose is not None and (glucose < 3.0 or glucose > 20.0):
        is_ctas2 = True
    
    # Concerning vital signs
    elif (spo2 is not None and 90 <= spo2 < 92):
        is_ctas2 = True

    if is_ctas2: return 2

    # --- CTAS III: Urgent (≤30 minutes) ---
    is_ctas3 = False
    
    if gcs is not None and gcs == 14:
        is_ctas3 = True
    elif resp_distress == 'mild' or \
         (pain is not None and 4 <= pain <= 7) or \
         complaint == 'abdominal_pain_severe' or \
         bleeding == 'moderate' or dehydration == 'moderate' or \
         (temp is not None and temp >= 39.0):
        is_ctas3 = True
    
    # Time-based upgrade for patients waiting too long
    elif time_waiting is not None and time_waiting > 120:
        is_ctas3 = True

    if is_ctas3: return 3

    # --- CTAS IV: Less Urgent (≤60 minutes) ---
    is_ctas4 = False
    if complaint in ['minor_trauma', 'vomiting_diarrhea_mild'] or \
       (pain is not None and 1 <= pain <= 3) or \
       bleeding == 'minor' or dehydration == 'mild' or \
       (temp is not None and temp >= 38.0):
        is_ctas4 = True

    if is_ctas4: return 4

    # --- CTAS V: Non-Urgent (≤120 minutes) ---
    return ctas_level

# Simple function to get text representation from value (for selects)
# This needs the actual mapping from the HTML, stored here for convenience
# In a real app, this mapping might be better placed elsewhere (config, db)
def get_text_from_value(field_id, value, tool_type='professional'):
    """Gets text representation for select/radio values from different forms."""

    # Mappings specific to mepw.html (professional tool)
    professional_mapping = {
        'patient-gender': {
            'male': 'ذكر (Male)', 'female': 'أنثى (Female)', 'other': 'آخر (Other)', '': 'اختر (Select)'
        },
        'chief-complaint': {
             'cardiac_arrest': 'توقف القلب (Cardiac Arrest / VSA)', 'resp_arrest': 'توقف التنفس (Respiratory Arrest)',
             'major_trauma': 'إصابة بليغة (Major Trauma)', 'chest_pain_cardiac': 'ألم في الصدر (يشتبه بالقلب) (Chest Pain - Cardiac?)',
             'resp_distress_severe': 'ضيق تنفس حاد (Resp Distress - Severe)', 'shock': 'صدمة (Shock)',
             'loc_decreased': 'انخفاض مستوى الوعي (LOC Decreased)', 'seizure_active': 'تشنج نشط (Seizure - Active)',
             'stroke': 'جلطة دماغية (Stroke / CVA)', 'anaphylaxis': 'حساسية مفرطة (Anaphylaxis)',
             'overdose': 'جرعة زائدة (Overdose)', 'sepsis': 'تسمم الدم (Sepsis)',
             'severe_pain': 'ألم شديد (Severe Pain)', 'resp_distress_moderate': 'ضيق تنفس متوسط (Resp Distress - Moderate)',
             'abdominal_pain_severe': 'ألم بطن شديد (Abdominal Pain - Severe)', 'head_injury_moderate': 'إصابة رأس متوسطة (Head Injury - Moderate)',
             'vaginal_bleeding_heavy': 'نزيف مهبلي غزير (Vaginal Bleeding - Heavy)', 'fever_infant': 'حمى (رضيع < 3 أشهر) (Fever - Infant < 3mo)',
             'psych_severe': 'حالة نفسية حادة (Psychiatric - Severe)', 'minor_trauma': 'إصابة طفيفة (Minor Trauma)',
             'mild_pain': 'ألم خفيف (Mild Pain)', 'vomiting_diarrhea_mild': 'قيء/إسهال خفيف (Vomiting/Diarrhea - Mild)',
             'rash': 'طفح جلدي (Rash)', 'other': 'أخرى (Other - specify below)', '': '-- اختر الشكوى --'
        },
        'respiratory-distress': {
            'none': 'لا يوجد (None)', 'mild': 'خفيف (Mild)', 'moderate': 'متوسط (Moderate)', 'severe': 'شديد (Severe)'
        },
        'bleeding': {
            'none': 'لا يوجد (None)', 'minor': 'طفيف (Minor)', 'moderate': 'متوسط / كبير يمكن السيطرة عليه (Moderate / Significant Controlled)', 'severe': 'شديد / غير مسيطر عليه (Severe / Uncontrolled)'
        },
        'mechanism-injury': {
            'none': 'لا يوجد/غير مطبق (None/NA)', 'minor': 'آلية بسيطة (Minor Mechanism)', 'significant': 'آلية خطرة (Significant Mechanism - e.g., high fall/speed, rollover, penetrating)', 'other': 'أخرى (Other)'
        },
        'dehydration': {
             'none': 'لا يوجد (None)', 'mild': 'خفيف (Mild - e.g., thirsty)', 'moderate': 'متوسط (Moderate - e.g., dry mucous membranes)', 'severe': 'شديد (Severe - e.g., poor turgor, lethargy)'
        }
    }

    # Mappings specific to meow.html (self-assessment tool)
    self_assessment_mapping = {
        'patient-gender': {
            'male': 'ذكر (Male)', 'female': 'أنثى (Female)', 'prefer_not_say': 'أفضل عدم القول (Prefer not to say)', '': 'اختر (Select)'
        },
        'has-diabetes': {
            'no': 'لا (No)', 'yes': 'نعم (Yes)', 'unsure': 'غير متأكد (Unsure)'
        },
        'main-symptom': {
            'cannot_breathe': 'لا أستطيع التنفس / غصة شديدة (Cannot breathe / Severe choking)',
            'severe_chest_pain': 'ألم شديد أو ضغط في الصدر (Severe chest pain or pressure)',
            'severe_breathing_difficulty': 'صعوبة شديدة في التنفس (Severe difficulty breathing)',
            'severe_bleeding': 'نزيف حاد لا يتوقف (Severe bleeding that won\'t stop)',
            'not_responding': 'فقدان الوعي / صعوبة شديدة في الإفاقة (Unconscious / Very difficult to wake up)',
            'active_seizure': 'نوبة تشنج مستمرة الآن (Ongoing seizure now)',
            'stroke_signs': 'علامات جلطة دماغية (مثل: تدلي الوجه، ضعف ذراع، صعوبة كلام) (Stroke signs)',
            'severe_allergic_reaction': 'رد فعل تحسسي شديد (تورم، صعوبة تنفس) (Severe allergic reaction)',
            'confusion_severe': 'تشوش ذهني حاد / ارتباك شديد (Severe confusion)',
            'severe_pain_other': 'ألم شديد جداً (غير الصدر) (Very severe pain - non-chest)',
            'moderate_breathing_difficulty': 'صعوبة متوسطة في التنفس (Moderate difficulty breathing)',
            'poison_overdose': 'اشتباه تسمم أو جرعة زائدة (Suspected poisoning or overdose)',
            'moderate_bleeding': 'نزيف متوسط (يحتاج ضغط) (Moderate bleeding - needs pressure)',
            'fever_very_high': 'حمى شديدة جداً (Very high fever)',
            'severe_headache': 'صداع شديد جداً ومفاجئ (Very severe, sudden headache)',
            'severe_abdominal_pain': 'ألم شديد في البطن (Severe abdominal pain)',
            'moderate_pain': 'ألم متوسط (Moderate pain)',
            'mild_breathing_difficulty': 'صعوبة خفيفة في التنفس (Mild difficulty breathing)',
            'vomiting_diarrhea': 'قيء أو إسهال (Vomiting or diarrhea)',
            'fever_mild_moderate': 'حمى خفيفة أو متوسطة (Mild or moderate fever)',
            'minor_injury': 'إصابة طفيفة (Minor injury)',
            'mild_pain_symptoms': 'ألم خفيف / أعراض خفيفة أخرى (Mild pain / Other mild symptoms)',
            'other': 'شيء آخر (Something else - describe below)',
            '': '-- اختر العرض الأهم --'
        },
        'alertness': {
            'A': 'طبيعي وواعي تماماً (Fully awake and alert)',
            'V': 'أشعر بالنعاس أو الارتباك قليلاً (Drowsy or a bit confused, but respond)',
            'P': 'مرتبك جداً / يصعب إيقاظي (Very confused / Difficult to wake up)',
            'U': 'لا أستجيب / فاقد الوعي (Unresponsive / Unconscious)'
        },
        'breathing-difficulty': {
            'none': 'لا توجد صعوبة (No trouble)', 'mild': 'صعوبة خفيفة (Mild trouble)',
            'moderate': 'صعوبة متوسطة (Moderate trouble)', 'severe': 'صعوبة شديدة (Severe trouble)',
            'cannot_breathe': 'لا أستطيع التنفس (Cannot breathe at all)'
        },
        'bleeding': {
            'none': 'لا يوجد (None)', 'minor': 'نزيف خفيف (يتوقف بسهولة) (Minor - stops easily)',
            'moderate': 'نزيف متوسط (يحتاج ضغط) (Moderate - needs pressure)',
            'severe': 'نزيف شديد (يصعب إيقافه) (Severe - hard to stop)'
        },
        'dehydration': {
            'none': 'لا (No)', 'mild': 'قليلاً (A little)',
            'moderate': 'نعم، بشكل متوسط (Yes, moderately)', 'severe': 'نعم، بشكل شديد (Yes, severely)'
        },
        'feverish': {
            'no': 'لا (No)', 'yes_mild_mod': 'نعم، خفيفة أو متوسطة (Yes, mild/moderate)',
            'yes_high': 'نعم، عالية (Yes, high)', 'unsure': 'غير متأكد (Unsure)'
        },
        'trauma_occurred': {
            'no': 'لا (No)', 'yes_minor': 'نعم، إصابة بسيطة (Yes, minor injury)',
            'yes_significant': 'نعم، حادث أو إصابة خطيرة (Yes, serious accident/injury)'
        }
    }

    # Select the correct mapping based on tool_type
    mapping_to_use = professional_mapping if tool_type == 'professional' else self_assessment_mapping
    return mapping_to_use.get(field_id, {}).get(value, value) # Return original value if not found

@app.route('/')
def index():
    # Get language preference from session or default
    lang = session.get('language', DEFAULT_LANGUAGE)
    theme = session.get('theme', DEFAULT_THEME)
    return render_template('professional_triage.html', lang=lang, theme=theme)

@app.route('/reference')
def reference_page():
    """Serves the vital sign reference page."""
    lang = session.get('language', DEFAULT_LANGUAGE)
    theme = session.get('theme', DEFAULT_THEME)
    return render_template('reference.html', lang=lang, theme=theme)

@app.route('/self_diagnosis')
def self_diagnosis_page():
    """Serves the patient self-diagnosis page."""
    lang = session.get('language', DEFAULT_LANGUAGE)
    theme = session.get('theme', DEFAULT_THEME)
    return render_template('self_assessment.html', lang=lang, theme=theme)

@app.route('/set_language', methods=['POST'])
def set_language():
    """Set user's language preference."""
    lang = request.json.get('language', DEFAULT_LANGUAGE)
    if lang in SUPPORTED_LANGUAGES:
        session['language'] = lang
        return jsonify({'status': 'success', 'language': lang})
    return jsonify({'status': 'error', 'message': 'Unsupported language'}), 400

@app.route('/set_theme', methods=['POST'])
def set_theme():
    """Set user's theme preference."""
    theme = request.json.get('theme', DEFAULT_THEME)
    if theme in ['light', 'dark']:
        session['theme'] = theme
        return jsonify({'status': 'success', 'theme': theme})
    return jsonify({'status': 'error', 'message': 'Invalid theme'}), 400

@app.route('/calculate_ctas', methods=['POST'])
def calculate_ctas_route():
    try:
        data = request.form.to_dict()
        ctas_level = calculate_ctas_logic(data)

        # Prepare summary data for JSON response
        summary_data = {
            'name': data.get('patient_name', 'N/A'),
            'age': data.get('patient_age', 'N/A'),
            'gender': get_text_from_value('patient-gender', data.get('patient_gender'), 'professional'),
            'id': data.get('patient_id', 'N/A'),
            'complaint': get_text_from_value('chief-complaint', data.get('chief_complaint'), 'professional'),
            'complaint_details': data.get('complaint_details', 'N/A'),
            'vitals': f"HR: {data.get('heart_rate', 'N/A')}, RR: {data.get('resp_rate', 'N/A')}, SpO2: {data.get('spo2', 'N/A')}%, BP: {data.get('bp_systolic', 'N/A')}/{data.get('bp_diastolic', 'N/A')}, Temp: {data.get('temperature', 'N/A')}°C",
            'loc': f"GCS: {data.get('gcs_score', 'N/A')}" + (f" (AVPU: {data.get('avpu')})" if data.get('avpu') else '') if data.get('gcs_score') else (f"AVPU: {data.get('avpu')}" if data.get('avpu') else 'N/A'),
            'pain': data.get('pain_score', '0'),
            'resp_distress': get_text_from_value('respiratory-distress', data.get('respiratory_distress'), 'professional'),
            'bleeding': get_text_from_value('bleeding', data.get('bleeding'), 'professional'),
            'moi': get_text_from_value('mechanism-injury', data.get('mechanism_injury'), 'professional'),
            'glucose': data.get('glucose', 'N/A'),
            'dehydration': get_text_from_value('dehydration', data.get('dehydration'), 'professional'),
            'heat_exposure': data.get('heat_exposure', 'N/A'),
            'diabetes': data.get('has_diabetes', 'N/A'),
            'ctas_level': ctas_level,
            'wait_time_estimate': get_wait_time_estimate(ctas_level)
        }
        return jsonify(summary_data)
    except Exception as e:
        app.logger.error(f"Error in calculate_ctas: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500

def get_wait_time_estimate(ctas_level):
    """Get estimated wait time based on CTAS level."""
    wait_times = {
        1: "فوري (Immediate)",
        2: "≤ 15 دقيقة (≤ 15 minutes)",
        3: "≤ 30 دقيقة (≤ 30 minutes)",
        4: "≤ 60 دقيقة (≤ 60 minutes)",
        5: "≤ 120 دقيقة (≤ 120 minutes)"
    }
    return wait_times.get(ctas_level, "N/A")

@app.route('/download_csv', methods=['POST'])
def download_csv_route():
    data = request.form.to_dict()
    ctas_level = calculate_ctas_logic(data)

    # Prepare data for CSV, getting text values
    csv_data = {
        'Patient Name': data.get('patient_name', ''),
        'Age': data.get('patient_age', ''),
        'Gender': get_text_from_value('patient-gender', data.get('patient_gender'), 'professional'),
        'ID/MRN': data.get('patient_id', ''),
        'Chief Complaint': get_text_from_value('chief-complaint', data.get('chief_complaint'), 'professional'),
        'Complaint Details': data.get('complaint_details', ''),
        'Heart Rate': data.get('heart_rate', ''),
        'Resp Rate': data.get('resp_rate', ''),
        'SpO2': data.get('spo2', ''),
        'BP Systolic': data.get('bp_systolic', ''),
        'BP Diastolic': data.get('bp_diastolic', ''),
        'Temperature': data.get('temperature', ''),
        'GCS Score': data.get('gcs_score', ''),
        'AVPU': data.get('avpu', ''),
        'Pain Score': data.get('pain_score', ''),
        'Respiratory Distress': get_text_from_value('respiratory-distress', data.get('respiratory_distress'), 'professional'),
        'Bleeding': get_text_from_value('bleeding', data.get('bleeding'), 'professional'),
        'Mechanism of Injury': get_text_from_value('mechanism-injury', data.get('mechanism_injury'), 'professional'),
        'Glucose': data.get('glucose', ''),
        'Dehydration Signs': get_text_from_value('dehydration', data.get('dehydration'), 'professional'),
        'CTAS Level (Preliminary)': ctas_level
    }

    # Define CSV headers based on the keys prepared above
    csv_headers = list(csv_data.keys())
    csv_data_row = [csv_data[header] for header in csv_headers]

    # Generate CSV in memory with UTF-8 BOM
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(csv_headers)
    writer.writerow(csv_data_row)

    output = si.getvalue()
    si.close()

    # Create safe ASCII-only filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    patient_name = data.get('patient_name', 'unknown')
    # Create a safe ASCII filename - only keep alphanumeric characters and convert to lowercase
    safe_name = ''.join(c for c in patient_name if c.isalnum() and ord(c) < 128).strip().lower()
    if not safe_name or len(safe_name) < 2:
        safe_name = 'patient'
    filename = f"ctas_assessment_{safe_name}_{timestamp}.csv"

    # Add UTF-8 BOM and return CSV as a response with proper encoding
    utf8_bom = '\ufeff'
    output = utf8_bom + output
    
    return Response(
        output.encode('utf-8'),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

# Add routes for self-assessment functionality
@app.route('/calculate_self_assessment', methods=['POST'])
def calculate_self_assessment_route():
    data = request.form.to_dict()
    
    # Calculate CTAS level using the same logic
    ctas_level = calculate_ctas_logic(data)
    
    # Map the main symptom to a recognizable chief complaint for the CTAS algorithm
    main_symptom = data.get('main_symptom', '')
    breathing_difficulty = data.get('breathing_difficulty', 'none')
    
    # Add derived fields that CTAS logic expects
    if main_symptom in ['cannot_breathe', 'severe_breathing_difficulty']:
        data['respiratory_distress'] = 'severe'
    elif main_symptom == 'moderate_breathing_difficulty' or breathing_difficulty == 'moderate':
        data['respiratory_distress'] = 'moderate'
    elif main_symptom == 'mild_breathing_difficulty' or breathing_difficulty == 'mild':
        data['respiratory_distress'] = 'mild'
    else:
        data['respiratory_distress'] = 'none'
        
    # Map alertness to AVPU
    data['avpu'] = data.get('alertness', 'A')
    
    # Map severe symptoms to chief complaints
    if main_symptom in ['severe_chest_pain']:
        data['chief_complaint'] = 'chest_pain_cardiac'
    elif main_symptom in ['active_seizure']:
        data['chief_complaint'] = 'seizure_active'
    elif main_symptom in ['stroke_signs']:
        data['chief_complaint'] = 'stroke'
    elif main_symptom in ['severe_allergic_reaction']:
        data['chief_complaint'] = 'anaphylaxis'
    elif main_symptom in ['poison_overdose']:
        data['chief_complaint'] = 'overdose'
    elif main_symptom in ['severe_pain_other']:
        data['chief_complaint'] = 'severe_pain'
    elif main_symptom in ['severe_abdominal_pain']:
        data['chief_complaint'] = 'abdominal_pain_severe'
    elif main_symptom in ['minor_injury']:
        data['chief_complaint'] = 'minor_trauma'
        
    # Calculate recommendations based on CTAS level
    recommendation_html = generate_recommendation(ctas_level, main_symptom)
    
    # Prepare summary data for JSON response
    summary_data = {
        'age': data.get('patient_age', 'N/A'),
        'gender': get_text_from_value('patient-gender', data.get('patient_gender'), 'self_assessment'),
        'main_symptom': get_text_from_value('main-symptom', main_symptom, 'self_assessment'),
        'symptom_details': data.get('symptom_details', 'N/A'),
        'alertness': get_text_from_value('alertness', data.get('alertness', ''), 'self_assessment'),
        'breathing': get_text_from_value('breathing-difficulty', data.get('breathing_difficulty', ''), 'self_assessment'),
        'pain': data.get('pain_score', '0'),
        'bleeding': get_text_from_value('bleeding', data.get('bleeding', ''), 'self_assessment'),
        'dehydration': get_text_from_value('dehydration', data.get('dehydration', ''), 'self_assessment'),
        'feverish': get_text_from_value('feverish', data.get('feverish', ''), 'self_assessment'),
        'trauma': get_text_from_value('trauma_occurred', data.get('trauma_occurred', ''), 'self_assessment'),
        'diabetes': get_text_from_value('has-diabetes', data.get('has_diabetes', ''), 'self_assessment'),
        'glucose': data.get('glucose', 'N/A'),
        'level': ctas_level,
        'recommendation': recommendation_html
    }
    
    return jsonify(summary_data)

def generate_recommendation(ctas_level, main_symptom):
    """Generate HTML recommendation based on CTAS level and symptoms for healthcare center use."""
    
    if ctas_level == 1:
        return """
        <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-md">
            <p class="font-bold text-lg">🚨 CTAS I - حالة طارئة (Resuscitation)</p>
            <p>هذه الأعراض تشير إلى حالة طبية طارئة تتطلب رعاية فورية.</p>
            <p class="font-bold mt-2">يجب تقييم المريض فوراً من قبل الطبيب - أولوية قصوى</p>
            <p class="mt-2">These symptoms indicate a medical emergency requiring immediate care.</p>
            <p class="font-bold">Patient requires immediate physician assessment - highest priority</p>
        </div>
        """
    elif ctas_level == 2:
        return """
        <div class="bg-orange-100 border-l-4 border-orange-500 text-orange-700 p-4 rounded-md">
            <p class="font-bold text-lg">⚠️ CTAS II - حالة عاجلة (Emergent)</p>
            <p>هذه الأعراض تشير إلى حالة طبية عاجلة تتطلب تقييم سريع.</p>
            <p class="font-bold mt-2">يجب رؤية الطبيب خلال 15 دقيقة</p>
            <p class="mt-2">These symptoms indicate an urgent medical condition requiring prompt care.</p>
            <p class="font-bold">Patient should be seen by physician within 15 minutes</p>
        </div>
        """
    elif ctas_level == 3:
        return """
        <div class="bg-amber-100 border-l-4 border-amber-500 text-amber-700 p-4 rounded-md">
            <p class="font-bold text-lg">⚠️ CTAS III - حالة مستعجلة (Urgent)</p>
            <p>هذه الأعراض تشير إلى حالة تتطلب تقييم طبي خلال 30 دقيقة.</p>
            <p class="font-bold mt-2">يرجى الانتظار في منطقة الانتظار - ستتم رؤية المريض قريباً</p>
            <p class="mt-2">These symptoms indicate a condition requiring medical assessment within 30 minutes.</p>
            <p class="font-bold">Please wait in waiting area - patient will be seen soon</p>
        </div>
        """
    elif ctas_level == 4:
        return """
        <div class="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 rounded-md">
            <p class="font-bold text-lg">ℹ️ CTAS IV - أقل استعجالاً (Less Urgent)</p>
            <p>هذه الأعراض تشير إلى حالة تتطلب تقييم طبي خلال 60 دقيقة.</p>
            <p class="font-bold mt-2">يرجى الانتظار - الوقت المتوقع للانتظار أقل من ساعة</p>
            <p class="mt-2">These symptoms indicate a condition requiring medical assessment within 60 minutes.</p>
            <p class="font-bold">Please wait - expected wait time less than one hour</p>
        </div>
        """
    else:  # CTAS 5
        return """
        <div class="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 rounded-md">
            <p class="font-bold text-lg">ℹ️ CTAS V - غير عاجل (Non-Urgent)</p>
            <p>هذه الأعراض لا تشير إلى حالة طارئة في الوقت الحالي.</p>
            <p class="font-bold mt-2">يرجى الانتظار - الوقت المتوقع للانتظار أقل من ساعتين</p>
            <p class="mt-2">These symptoms do not indicate an emergency at this time.</p>
            <p class="font-bold">Please wait - expected wait time less than two hours</p>
        </div>
        """

@app.route('/download_self_assessment_csv', methods=['POST'])
def download_self_assessment_csv_route():
    data = request.form.to_dict()
    ctas_level = calculate_ctas_logic(data)
    
    # Map alertness to AVPU for calculation
    data['avpu'] = data.get('alertness', 'A')
    
    # Prepare data for CSV, getting text values using the self-assessment mappings
    csv_data = {
        'Age': data.get('patient_age', ''),
        'Gender': get_text_from_value('patient-gender', data.get('patient_gender', ''), 'self_assessment'),
        'Main Symptom': get_text_from_value('main-symptom', data.get('main_symptom', ''), 'self_assessment'),
        'Symptom Details': data.get('symptom_details', ''),
        'Alertness Level': get_text_from_value('alertness', data.get('alertness', ''), 'self_assessment'),
        'Breathing Difficulty': get_text_from_value('breathing-difficulty', data.get('breathing_difficulty', ''), 'self_assessment'),
        'Pain Score': data.get('pain_score', ''),
        'Bleeding': get_text_from_value('bleeding', data.get('bleeding', ''), 'self_assessment'),
        'Dehydration Signs': get_text_from_value('dehydration', data.get('dehydration', ''), 'self_assessment'),
        'Fever': get_text_from_value('feverish', data.get('feverish', ''), 'self_assessment'),
        'Recent Trauma': get_text_from_value('trauma_occurred', data.get('trauma_occurred', ''), 'self_assessment'),
        'Diabetes': get_text_from_value('has-diabetes', data.get('has_diabetes', ''), 'self_assessment'),
        'Blood Glucose': data.get('glucose', ''),
        'CTAS Level (Preliminary)': ctas_level,
        'Assessment Date/Time': datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # Define CSV headers based on the keys prepared above
    csv_headers = list(csv_data.keys())
    csv_data_row = [csv_data[header] for header in csv_headers]

    # Generate CSV in memory with UTF-8 BOM
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(csv_headers)
    writer.writerow(csv_data_row)

    output = si.getvalue()
    si.close()

    # Create safe ASCII-only filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"self_assessment_{timestamp}.csv"

    # Add UTF-8 BOM and return CSV as a response with proper encoding
    utf8_bom = '\ufeff'
    output = utf8_bom + output

    return Response(
        output.encode('utf-8'),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    try:
        # Basic system check
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0-ctas',
            'system': 'CTAS Triage System - Saudi Arabia',
            'environment': os.environ.get('FLASK_ENV', 'production')
        }
        return jsonify(status), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Production-ready application for Railway
if __name__ == '__main__':
    # This is only used for local development
    # Railway will use Gunicorn in production
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

