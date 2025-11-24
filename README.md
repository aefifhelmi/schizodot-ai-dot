# DOMINO - Digital Observation & Monitoring Intelligence for Neuro-Output

AI-powered Digital Observation Therapy Platform for Mental Health Assessment

## 🏗️ Project Structure

```
schizodot-ai-dot/
├── backend/                      # FastAPI backend server
│   ├── app/                     # Application code
│   ├── tests/                   # Backend tests
│   └── uploads/                 # Temporary file storage
│
├── frontend/                     # All web applications
│   ├── patient-portal/          # Patient check-in interface
│   ├── clinician-dashboard/     # Clinician review dashboard
│   └── legacy/                  # Old frontend versions
│
├── services/                     # Microservices
│   ├── emotion-detection/       # Audio/facial emotion analysis
│   ├── pill-compliance/         # Medication compliance verification
│   └── external/                # Third-party services
│
├── ai_models/                    # AI model configurations
├── infra/                        # Infrastructure & deployment
│   ├── docker/                  # Dockerfiles
│   └── k8s/                     # Kubernetes configs
│
├── docs/                         # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── ARCHITECTURE.md
│   ├── AWS_GUIDE.md
│   └── examples/                # Code examples
│
├── tests/                        # Integration & E2E tests
├── scripts/                      # Utility scripts
└── docker-compose.yml            # Local development setup
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- AWS Account (for cloud deployment)
- Python 3.11+
- Node.js 18+ (for frontends)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/schizodot-ai-dot.git
   cd schizodot-ai-dot
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Access applications**
   - Backend API: http://localhost:8000
   - Patient Portal: http://localhost:3000
   - Clinician Dashboard: http://localhost:3001
   - Emotion Service: http://localhost:5000
   - Pill Compliance: http://localhost:5001

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [AWS Deployment Guide](docs/AWS_GUIDE.md)
- [Docker Setup](docs/DOCKER_SETUP.md)
- [Quick Start Guide](docs/QUICK_START.md)

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_end_to_end.py

# Check services
./scripts/check-services.sh
```

## 🏥 Features

### Patient Portal
- Video-based check-in
- Clinical questionnaire
- Real-time emotion analysis
- Medication compliance verification

### Clinician Dashboard
- Patient assessment review
- Emotion analysis visualization
- Risk assessment
- Clinical recommendations

### AI Capabilities
- **Audio Emotion Detection**: Speech emotion recognition
- **Facial Emotion Detection**: Computer vision emotion analysis
- **Multimodal Fusion**: Combined audio-visual emotion assessment
- **Pill Detection**: Medication compliance verification
- **Clinical Summarization**: AWS Bedrock AI-powered insights

## 🔧 Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend/patient-portal
python -m http.server 3000
```

### Services
Each service has its own README in its directory.

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests
4. Submit pull request

## 👥 Team - Pulse & Code

**Universiti Teknologi MARA (UiTM)**

### Development Team
- **Tengku Afif Helmi Bin Tengku Shahrulizam** 
- **Muhammad Zahin Bin Mohd Zulflida** 
- **Ishaza Arianna Binti Ismadee Asmara** 

### Medical Advisory Team
- **Nur Liyana Binti Zuraimi** 
- **Mumtazah Aiesyah Binti Hassan** 
- **Muhammad Ammer Haziq Bin Johari** 

---

*DOMINO (Digital Observation & Monitoring Intelligence for Neuro-psychiatric Oversight) is a collaborative project between Computer Science and Medicine students at UiTM, combining technical expertise with clinical knowledge to create an AI-powered mental health assessment platform.*

## 📞 Support

For issues and questions, please open a GitHub issue.
