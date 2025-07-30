# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac: venv\Scripts\activate on Windows
pip install -r requirements.txt
cp new.txt .env  # Edit .env with proper SECRET_KEY
python app.py  # Development server on port 5000
```

### Production Server
```bash
gunicorn -c gunicorn.conf.py app:app  # Production WSGI server
```

### Testing & Validation
```bash
# Manual testing endpoints
curl http://localhost:5000/health  # Health check
curl -X POST http://localhost:5000/calculate_ctas -H "Content-Type: application/json" -d '{...}'  # CTAS calculation
```

## Architecture Overview

### Core System
**STAS** is a Flask-based medical triage system implementing the Canadian Triage and Acuity Scale (CTAS) adapted for Saudi Arabian healthcare. The application serves both healthcare professionals and patients with bilingual support (Arabic RTL/English LTR).

### Key Components

#### Backend (app.py - 820 lines)
- **CTAS Algorithm**: `calculate_ctas_logic()` implements 5-level triage classification
- **Dual Interfaces**: Professional triage tool and patient self-assessment
- **Saudi Medical Adaptations**: Heat illness detection, enhanced diabetes monitoring, MOH-compliant pediatric vital ranges
- **Security**: Comprehensive headers, session management, input validation
- **Export**: CSV generation with UTF-8 BOM encoding for medical records

#### Frontend (static/js/triage.js - 214 lines)
- **Multi-step Forms**: Progressive navigation with validation
- **Real-time Calculation**: AJAX-based CTAS computation
- **Print Integration**: Clean assessment summaries
- **Accessibility**: Touch-friendly, high contrast mode, keyboard navigation

#### API Structure
| Endpoint | Purpose |
|----------|---------|
| `/` | Professional triage interface |
| `/self_diagnosis` | Patient self-assessment |
| `/calculate_ctas` | CTAS level calculation (POST) |
| `/download_csv` | Export professional data (POST) |
| `/health` | Health monitoring |
| `/set_language` | Language switching (POST) |

### Medical Algorithm Details
The CTAS implementation uses a complex scoring system with:
- **Vital Signs Assessment**: Age-specific ranges per Saudi MOH standards
- **Symptom Severity Mapping**: Direct symptom-to-CTAS level assignments
- **Environmental Factors**: Heat-related illness detection for desert climate
- **Chronic Condition Monitoring**: Enhanced diabetes and hypertension protocols

### Production Configuration
- **Deployment**: Railway platform via Procfile
- **WSGI Server**: Gunicorn with auto-scaling workers (gunicorn.conf.py)
- **Runtime**: Python 3.11.3 (runtime.txt)
- **Environment**: Uses .env file with SECRET_KEY, FLASK_ENV, language settings
- **Logging**: Rotating logs (10MB, 10 backups) with Railway stdout integration

### Template System
Templates follow a bilingual pattern with conditional RTL/LTR rendering:
- `professional_triage.html`: Healthcare professional interface
- `self_assessment.html`: Patient-facing simplified assessment
- `reference.html`: Vital signs reference guide

### Data Flow
1. **Form Submission** → JavaScript validation → AJAX POST to Flask
2. **CTAS Calculation** → Algorithm processing → JSON response with triage level
3. **Results Display** → Dynamic UI update → Optional CSV export
4. **Session Management** → Language preference → Persistent user experience

### Security Implementation
- **Content Security Policy**: Restricts external resources
- **Session Security**: Secure, HTTPOnly, SameSite cookies
- **XSS Protection**: Multiple header-based protections
- **Input Validation**: Form sanitization and medical data validation

## Development Notes

### Language Support
The application dynamically switches between Arabic (RTL) and English (LTR) with complete UI adaptation including medical terminology translation.

### Medical Data Handling
All patient data is session-based with no persistent storage. CSV exports include medical disclaimers and proper encoding for international character support.

### Error Handling
Comprehensive error pages (404.html, 500.html) with logging integration. Health endpoint returns JSON status for monitoring systems.