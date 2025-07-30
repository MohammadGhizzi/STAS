// CTAS Triage System - Frontend JavaScript
// This file handles form navigation, validation, and API communication

let currentStep = 1;
const totalSteps = 4;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Update pain score display
    const painSlider = document.getElementById('pain-score');
    const painOutput = document.getElementById('pain-score-output');
    if(painSlider && painOutput) {
        painOutput.textContent = painSlider.value;
        painSlider.oninput = function() {
            painOutput.textContent = this.value;
        }
    }
});

// Medical validation ranges (extreme but possible clinical values)
const MEDICAL_RANGES = {
    age: { min: 0, max: 120, unit: 'years' },
    heart_rate: { min: 30, max: 220, unit: 'bpm' },
    resp_rate: { min: 5, max: 60, unit: '/min' },
    spo2: { min: 70, max: 100, unit: '%' },
    bp_systolic: { min: 50, max: 250, unit: 'mmHg' },
    bp_diastolic: { min: 30, max: 150, unit: 'mmHg' },
    temperature: { min: 32, max: 45, unit: '°C' },
    gcs_score: { min: 3, max: 15, unit: 'points' },
    pain_score: { min: 0, max: 10, unit: 'points' },
    glucose: { min: 1, max: 50, unit: 'mmol/L' }
};

function validateMedicalRange(fieldName, value, showWarning = true) {
    const range = MEDICAL_RANGES[fieldName];
    if (!range || value === '' || value === null || value === undefined) return true;
    
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return false;
    
    const lang = document.documentElement.lang;
    
    if (numValue < range.min || numValue > range.max) {
        if (showWarning) {
            const fieldLabel = getFieldLabel(fieldName, lang);
            const message = lang === 'ar' 
                ? `تحذير: ${fieldLabel} (${numValue}) خارج النطاق الطبيعي (${range.min}-${range.max} ${range.unit}). هل تريد المتابعة؟`
                : `Warning: ${fieldLabel} (${numValue}) is outside normal range (${range.min}-${range.max} ${range.unit}). Continue anyway?`;
            
            return confirm(message);
        }
        return false;
    }
    return true;
}

function getFieldLabel(fieldName, lang) {
    const labels = {
        age: lang === 'ar' ? 'العمر' : 'Age',
        heart_rate: lang === 'ar' ? 'معدل النبض' : 'Heart Rate',
        resp_rate: lang === 'ar' ? 'معدل التنفس' : 'Respiratory Rate',
        spo2: lang === 'ar' ? 'تشبع الأكسجين' : 'SpO2',
        bp_systolic: lang === 'ar' ? 'الضغط الانقباضي' : 'Systolic BP',
        bp_diastolic: lang === 'ar' ? 'الضغط الانبساطي' : 'Diastolic BP',
        temperature: lang === 'ar' ? 'درجة الحرارة' : 'Temperature',
        gcs_score: lang === 'ar' ? 'مقياس غلاسكو' : 'GCS Score',
        glucose: lang === 'ar' ? 'مستوى السكر' : 'Glucose'
    };
    return labels[fieldName] || fieldName;
}

// Function to navigate to the next step
function nextStep(step) {
    // Basic validation
    if (step === 1) {
        const ageInput = document.getElementById('patient-age');
        if (!ageInput.value || parseInt(ageInput.value) < 0) {
            const lang = document.documentElement.lang;
            alert(lang === 'ar' ? 'الرجاء إدخال عمر صحيح.' : 'Please enter a valid age.');
            ageInput.focus();
            return;
        }
        
        // Medical range validation for age
        if (!validateMedicalRange('age', ageInput.value)) {
            ageInput.focus();
            return;
        }
    }
    if (step === 2) {
        const complaintSelect = document.getElementById('chief-complaint');
        if (!complaintSelect.value) {
            const lang = document.documentElement.lang;
            alert(lang === 'ar' ? 'الرجاء اختيار الشكوى الرئيسية.' : 'Please select a chief complaint.');
            complaintSelect.focus();
            return;
        }
    }
    if (step === 3) {
        const gcs = document.getElementById('gcs-score').value;
        const avpuElement = document.querySelector('input[name="avpu"]:checked');
        if (!gcs && !avpuElement) {
            const lang = document.documentElement.lang;
            alert(lang === 'ar' ? 'الرجاء تقييم مستوى الوعي (GCS أو AVPU).' : 'Please assess Level of Consciousness (GCS or AVPU).');
            return;
        }
        
        // Medical range validation for vital signs
        const vitalChecks = [
            { id: 'heart-rate', field: 'heart_rate' },
            { id: 'resp-rate', field: 'resp_rate' },
            { id: 'spo2', field: 'spo2' },
            { id: 'bp-systolic', field: 'bp_systolic' },
            { id: 'bp-diastolic', field: 'bp_diastolic' },
            { id: 'temperature', field: 'temperature' },
            { id: 'gcs-score', field: 'gcs_score' },
            { id: 'glucose', field: 'glucose' }
        ];
        
        for (const check of vitalChecks) {
            const element = document.getElementById(check.id);
            if (element && element.value) {
                if (!validateMedicalRange(check.field, element.value)) {
                    element.focus();
                    return;
                }
            }
        }
    }

    if (currentStep < totalSteps) {
        document.getElementById(`step-${currentStep}`).classList.add('hidden-section');
        currentStep++;
        document.getElementById(`step-${currentStep}`).classList.remove('hidden-section');
        window.scrollTo(0, 0);
    }
}

// Function to navigate to the previous step
function prevStep(step) {
    if (currentStep > 1) {
        document.getElementById(`step-${currentStep}`).classList.add('hidden-section');
        currentStep--;
        document.getElementById(`step-${currentStep}`).classList.remove('hidden-section');
        window.scrollTo(0, 0);
    }
}

// Function to gather data and display summary using backend API
function showSummary() {
    // Gather data from form
    const formData = new FormData(document.getElementById('triage-form'));
    formData.set('is_frail', document.getElementById('is_frail').checked ? 'true' : 'false');
    
    // Call backend API to calculate CTAS
    fetch('/calculate_ctas', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Check for errors
        if (data.error) {
            const lang = document.documentElement.lang;
            alert(`${lang === 'ar' ? 'خطأ' : 'Error'}: ${data.error}`);
            return;
        }
        
        // Display validation warnings if any
        if (data.validation_warnings && data.validation_warnings.length > 0) {
            const lang = document.documentElement.lang;
            const warningTitle = lang === 'ar' ? 'تحذيرات طبية:' : 'Medical Warnings:';
            let warningMessage = warningTitle + '\n';
            
            data.validation_warnings.forEach(warning => {
                warningMessage += `• ${warning.message} (${warning.range})\n`;
            });
            
            const proceed = confirm(warningMessage + '\n' + (lang === 'ar' ? 'هل تريد المتابعة؟' : 'Do you want to continue?'));
            if (!proceed) {
                return;
            }
        }
        
        // Populate summary fields with API response
        document.getElementById('summary-name').textContent = data.name;
        document.getElementById('summary-age').textContent = data.age;
        document.getElementById('summary-gender').textContent = data.gender;
        document.getElementById('summary-id').textContent = data.id;
        document.getElementById('summary-complaint').textContent = data.complaint;
        document.getElementById('summary-complaint-details').textContent = data.complaint_details;
        document.getElementById('summary-vitals').textContent = data.vitals;
        document.getElementById('summary-loc').textContent = data.loc;
        document.getElementById('summary-pain').textContent = data.pain;
        document.getElementById('summary-resp-distress').textContent = data.resp_distress;
        document.getElementById('summary-bleeding').textContent = data.bleeding;
        document.getElementById('summary-moi').textContent = data.moi;
        document.getElementById('summary-glucose').textContent = data.glucose;
        document.getElementById('summary-dehydration').textContent = data.dehydration;
        
        // Display CTAS Level and Apply Color
        const levelSpan = document.getElementById('summary-ctas-level');
        levelSpan.textContent = data.ctas_level;
        levelSpan.className = 'font-bold px-2 py-1 rounded';
        switch(data.ctas_level) {
            case 1: levelSpan.classList.add('ctas-level-1'); break;
            case 2: levelSpan.classList.add('ctas-level-2'); break;
            case 3: levelSpan.classList.add('ctas-level-3'); break;
            case 4: levelSpan.classList.add('ctas-level-4'); break;
            case 5: levelSpan.classList.add('ctas-level-5'); break;
            default: levelSpan.classList.add('ctas-level-5'); break;
        }
        
        // Show wait time estimate
        document.getElementById('summary-wait-time').textContent = data.wait_time_estimate;

        // Show reassessment interval
        const reassessmentEl = document.getElementById('summary-reassessment');
        if (data.reassessment_interval === 0) {
            reassessmentEl.textContent = data.lang === 'ar' ? 'مراقبة مستمرة' : 'Continuous Monitoring';
        } else {
            reassessmentEl.textContent = `${data.reassessment_interval} ${data.lang === 'ar' ? 'دقيقة' : 'minutes'}`;
        }
        
        // Show summary step
        nextStep(3);
    })
    .catch(error => {
        console.error('Error calculating CTAS:', error);
        const lang = document.documentElement.lang;
        alert(lang === 'ar' ? 'حدث خطأ في حساب مستوى الفرز.' : 'Error calculating triage level.');
    });
}

// Function to prepare content for printing
function preparePrint() {
    const summaryContent = document.getElementById('summary-output').innerHTML;
    const printArea = document.getElementById('print-area');
    const lang = document.documentElement.lang;
    const title = lang === 'ar' ? 'ملخص الفحص' : 'Examination Summary';
    
    printArea.innerHTML = `<h2 style="text-align: center; font-family: Inter, sans-serif; color: black; margin-bottom: 20px;">${title}</h2>` + summaryContent;
    printArea.style.fontFamily = 'Inter, sans-serif';
    printArea.style.color = 'black';
    printArea.classList.remove('hidden');
    window.print();
    printArea.classList.add('hidden');
    printArea.innerHTML = '';
}

// Function to download data as CSV using backend
function downloadCSV() {
    const formData = new FormData(document.getElementById('triage-form'));
    formData.set('is_frail', document.getElementById('is_frail').checked ? 'true' : 'false');
    
    fetch('/download_csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        a.download = `ctas_assessment_${timestamp}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error downloading CSV:', error);
        const lang = document.documentElement.lang;
        alert(lang === 'ar' ? 'حدث خطأ في تحميل الملف.' : 'Error downloading file.');
    });
}

// Function to reset the form and go back to step 1
function startNew() {
    const lang = document.documentElement.lang;
    const confirmMessage = lang === 'ar' 
        ? 'هل أنت متأكد من رغبتك في بدء فحص جديد؟ سيتم فقدان جميع البيانات الحالية.'
        : 'Are you sure you want to start a new examination? All current data will be lost.';
    
    if (confirm(confirmMessage)) {
        document.getElementById('triage-form').reset();
        
        // Reset pain slider display
        const painOutput = document.getElementById('pain-score-output');
        if(painOutput) painOutput.textContent = '0';
        const painSlider = document.getElementById('pain-score');
        if(painSlider) painSlider.value = '0';

        // Hide all steps except the first one
        document.querySelectorAll('.step-section').forEach(section => {
            if (section.id !== 'step-1') {
                section.classList.add('hidden-section');
            }
        });
        document.getElementById('step-1').classList.remove('hidden-section');
        currentStep = 1;
        window.scrollTo(0, 0);
    }
}

// Language Toggle Function
function toggleLanguage() {
    const currentLang = document.documentElement.lang;
    const newLang = currentLang === 'en' ? 'ar' : 'en';
    
    fetch('/set_language', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: newLang })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error switching language:', error);
    });
} 