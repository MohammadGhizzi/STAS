# Saudi Arabian Medical Triage System (CTAS)

[![Railway Deploy](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/MohammadGhizzi/STAS)

## 🏥 Overview

A comprehensive medical triage application implementing the **Canadian Triage and Acuity Scale (CTAS)** as adopted by the Saudi Arabian Ministry of Health. This system helps healthcare professionals and patients assess the urgency of medical conditions in healthcare centers across Saudi Arabia.

## ✨ Features

- **🩺 Professional Triage Tool**: Complete CTAS assessment for healthcare professionals
- **👤 Patient Self-Assessment**: Simplified symptom checker for patients
- **🇸🇦 Saudi-Specific Adaptations**: 
  - Heat-related illness detection (desert climate)
  - High diabetes prevalence considerations
  - Pediatric vital signs based on Saudi standards
- **🌐 Bilingual Interface**: Arabic (RTL) and English support
- **📊 Data Export**: CSV export functionality for medical records
- **🔒 Production Security**: Full security headers and HTTPS ready
- **📱 Mobile Responsive**: Optimized for tablets and mobile devices

## 🚀 Quick Deploy to Railway

1. **Click the Deploy button above** or manually:
   - Fork this repository
   - Connect to Railway
   - Deploy automatically

2. **Set Environment Variables** in Railway dashboard:
   ```
   SECRET_KEY=your-super-secret-key-minimum-32-characters
   FLASK_ENV=production
   ```

3. **Your app will be live** at your Railway domain!

## 🏗️ Local Development

### Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MohammadGhizzi/STAS.git
   cd STAS
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**:
   ```bash
   # Copy new.txt to .env and update SECRET_KEY
   cp new.txt .env
   ```

5. **Run the application**:
   ```bash
   # Development
   python app.py
   
   # Production (with Gunicorn)
   gunicorn -c gunicorn.conf.py app:app
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key (32+ chars) | Generated | **Yes** |
| `FLASK_ENV` | Environment mode | `production` | No |
| `HOST` | Server host | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `DEFAULT_LANGUAGE` | Default language | `ar` | No |
| `SUPPORTED_LANGUAGES` | Supported languages | `ar,en` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Production Configuration

The application is configured for production deployment with:

- **Gunicorn WSGI server**: High-performance production server
- **Security headers**: XSS protection, CSRF, content type validation
- **Session security**: Secure, HTTPOnly, SameSite cookies
- **Error handling**: Comprehensive error pages and logging
- **Health checks**: `/health` endpoint for monitoring

## 🏥 Medical Information

### CTAS Levels

| Level | Priority | Wait Time | Color | Description |
|-------|----------|-----------|-------|-------------|
| **I** | Resuscitation | Immediate | 🔴 Red | Life-threatening |
| **II** | Emergent | ≤ 15 min | 🟠 Orange | Urgent care needed |
| **III** | Urgent | ≤ 30 min | 🟡 Yellow | Stable but needs attention |
| **IV** | Less Urgent | ≤ 60 min | 🟢 Green | Minor conditions |
| **V** | Non-Urgent | ≤ 120 min | 🔵 Blue | Routine care |

### Saudi-Specific Features

- **Heat Illness Detection**: Automatic priority escalation for heat exposure + fever
- **Pediatric Ranges**: Age-appropriate vital sign thresholds per Saudi MOH standards
- **Diabetes Management**: Enhanced glucose level monitoring
- **Arabic Language**: Full RTL support with medical terminology

## 📱 Usage

### For Healthcare Professionals

1. **Access the professional tool** at the main page
2. **Enter patient information**: Demographics, medical history
3. **Record vital signs**: HR, RR, SpO2, BP, temperature, GCS
4. **Document symptoms**: Chief complaint, pain scale, clinical observations
5. **Get CTAS level**: Automatic calculation with wait time estimate
6. **Export data**: CSV download for medical records

### For Patients (Self-Assessment)

1. **Access self-assessment** via the dedicated page
2. **Answer simple questions**: Age, symptoms, alertness level
3. **Get preliminary guidance**: Priority level and recommendations
4. **Appropriate referral**: Clear instructions for next steps

## 🛡️ Security Features

- **HTTPS Ready**: SSL/TLS encryption support
- **Security Headers**: XSS, CSRF, clickjacking protection
- **Input Validation**: Comprehensive form and data validation
- **Error Handling**: Safe error messages without data exposure
- **Session Security**: Secure session management

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Professional triage interface |
| `/self_diagnosis` | GET | Patient self-assessment |
| `/reference` | GET | Vital signs reference |
| `/calculate_ctas` | POST | CTAS calculation |
| `/calculate_self_assessment` | POST | Self-assessment calculation |
| `/health` | GET | Health check for monitoring |
| `/download_csv` | POST | Export professional triage data |
| `/download_self_assessment_csv` | POST | Export self-assessment data |

## 📊 File Structure

```
STAS/
├── app.py                 # Main Flask application
├── gunicorn.conf.py      # Gunicorn production configuration
├── requirements.txt      # Python dependencies
├── Procfile             # Railway deployment command
├── runtime.txt          # Python version specification
├── new.txt              # Environment variables template
├── templates/           # HTML templates
│   ├── professional_triage.html
│   ├── self_assessment.html
│   ├── reference.html
│   └── ...
└── logs/               # Application logs (production)
```

## 🚀 Deployment

### Railway (Recommended)

Railway automatically detects the configuration and deploys:

1. **Connect GitHub repository** to Railway
2. **Set environment variables** in Railway dashboard
3. **Deploy automatically** with zero configuration

### Manual Production Deployment

1. **Set up server** with Python 3.11+
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure environment**: Copy and update `.env` file
4. **Run with Gunicorn**: `gunicorn -c gunicorn.conf.py app:app`
5. **Set up reverse proxy** (Nginx recommended)
6. **Enable HTTPS** with SSL certificates

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:
- **GitHub Issues**: [Create an issue](https://github.com/MohammadGhizzi/STAS/issues)
- **Medical Questions**: Consult with qualified healthcare professionals

## ⚠️ Medical Disclaimer

This application is a **clinical decision support tool** and does not replace professional medical judgment. All medical decisions should be made by qualified healthcare professionals. In emergencies, call **997** (Saudi Arabia emergency services) immediately.

---

**Built with ❤️ for Saudi Arabian Healthcare**

*Implementing CTAS standards as adopted by the Saudi Ministry of Health* 