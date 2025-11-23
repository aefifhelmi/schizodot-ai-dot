# Directory Structure & Organization

**Last Updated**: November 23, 2025  
**Status**: ✅ Cleaned and Organized

## 📁 Complete Directory Tree

```
schizodot-ai-dot/
│
├── 📁 backend/                          # FastAPI Backend Server
│   ├── app/                            # Application code
│   │   ├── api/                        # API routes
│   │   ├── core/                       # Core utilities
│   │   ├── models/                     # Data models
│   │   ├── services/                   # Business logic
│   │   └── main.py                     # App entry point
│   ├── tests/                          # Backend unit tests
│   └── uploads/                        # Temporary file storage
│
├── 📁 frontend/                         # Web Applications
│   ├── patient-portal/                 # Patient Check-in Interface
│   │   ├── index-new.html             # Main UI
│   │   ├── app-new.js                 # Application logic
│   │   ├── styles-new.css             # Styling
│   │   └── README.md                  # Documentation
│   │
│   ├── clinician-dashboard/           # Clinician Review Dashboard
│   │   ├── index-new.html             # Dashboard UI
│   │   ├── app-new.js                 # Data handling
│   │   ├── styles-new.css             # Clinical styling
│   │   └── README.md                  # Documentation
│   │
│   ├── legacy/                        # Old frontend versions
│   └── README.md                      # Frontend overview
│
├── 📁 services/                         # Microservices
│   ├── emotion-detection/             # Emotion Analysis Service
│   │   ├── ai/                        # AI models
│   │   ├── infra/                     # Docker configs
│   │   ├── main.py                    # Service entry
│   │   └── requirements.txt           # Dependencies
│   │
│   ├── pill-compliance/               # Medication Compliance
│   │   ├── proto.py                   # Main Flask app
│   │   ├── templates/                 # HTML templates
│   │   ├── static/                    # CSS/JS files
│   │   └── requirements.txt           # Dependencies
│   │
│   └── README.md                      # Services documentation
│
├── 📁 ai_models/                        # AI Model Configurations
│   └── README.md                      # Model documentation
│
├── 📁 infra/                            # Infrastructure & Deployment
│   ├── docker/                        # Dockerfiles
│   │   ├── Dockerfile.fastapi         # Backend container
│   │   ├── emotion.Dockerfile         # Emotion service
│   │   └── worker.Dockerfile          # Celery worker
│   │
│   ├── k8s/                           # Kubernetes manifests
│   └── terraform/                     # Infrastructure as Code
│
├── 📁 docs/                             # Documentation
│   ├── API_DOCUMENTATION.md           # API reference
│   ├── ARCHITECTURE.md                # System architecture
│   ├── AWS_GUIDE.md                   # AWS deployment
│   ├── DOCKER_SETUP.md                # Docker guide
│   ├── QUICK_START.md                 # Getting started
│   ├── DIRECTORY_STRUCTURE.md         # This file
│   ├── FRONTEND_AESTHETICS.md         # UI design guide
│   ├── WINDSURF_REFERENCES.txt        # Development notes
│   │
│   └── examples/                      # Code examples
│       └── developer_version/         # Reference implementation
│
├── 📁 tests/                            # All Test Files
│   ├── test_end_to_end.py             # E2E workflow test
│   ├── test_api_final.py              # API tests
│   ├── test_audio_model.py            # Audio model test
│   ├── test_bedrock_*.py              # AWS Bedrock tests
│   ├── test_emotion_docker.sh         # Docker test
│   ├── test_full_pipeline_docker.sh   # Pipeline test
│   ├── test_pill_detection.sh         # Compliance test
│   └── README.md                      # Testing guide
│
├── 📁 scripts/                          # Utility Scripts
│   ├── check-services.sh              # Health check script
│   ├── build_emotion_docker.sh        # Build script
│   └── README.md                      # Scripts guide
│
├── 📁 external/                         # External Dependencies
│   └── emotion-av/                    # Third-party emotion lib
│
├── 📁 logs/                             # Application Logs
├── 📁 models/                           # Downloaded ML Models
├── 📁 uploads/                          # Temporary Uploads
│
├── 📄 Configuration Files (Root)
│   ├── .env                           # Environment variables
│   ├── .env.example                   # Example config
│   ├── .gitignore                     # Git ignore rules
│   ├── .dockerignore                  # Docker ignore
│   ├── docker-compose.yml             # Docker orchestration
│   ├── LICENSE                        # License file
│   └── README.md                      # Main README
│
└── 📄 Development Files
    └── .git/                          # Git repository
```

## 🎯 Organization Principles

### 1. **Separation of Concerns**
- **Frontend**: All UI code in `frontend/`
- **Backend**: API server in `backend/`
- **Services**: Microservices in `services/`
- **Infrastructure**: Deployment configs in `infra/`

### 2. **Clear Naming**
- Descriptive directory names
- Consistent file naming conventions
- No ambiguous abbreviations

### 3. **Logical Grouping**
- Related files together
- Tests in dedicated directory
- Scripts centralized
- Documentation organized

### 4. **Scalability**
- Easy to add new services
- Clear extension points
- Modular architecture

## 📦 Key Directories Explained

### `backend/`
**Purpose**: Main API server handling all business logic

**Key Features**:
- FastAPI framework
- RESTful API endpoints
- Celery task queue
- AWS integrations (S3, DynamoDB, Bedrock)
- Video processing orchestration

**Port**: 8000

### `frontend/`
**Purpose**: All user-facing web applications

**Applications**:
1. **Patient Portal** (port 3000): Patient check-in interface
2. **Clinician Dashboard** (port 3001): Clinical review tool

**Technology**: Vanilla JavaScript (no framework)

### `services/`
**Purpose**: Specialized microservices for AI processing

**Services**:
1. **Emotion Detection** (port 5000): Audio & facial emotion analysis
2. **Pill Compliance** (port 5001): Real-time medication verification

**Benefits**:
- Independent scaling
- Technology flexibility
- Fault isolation

### `infra/`
**Purpose**: Infrastructure as Code and deployment configurations

**Contents**:
- Docker containers
- Kubernetes manifests
- Terraform scripts
- Deployment pipelines

### `docs/`
**Purpose**: Comprehensive project documentation

**Structure**:
- API documentation
- Architecture diagrams
- Setup guides
- Code examples
- Developer notes

### `tests/`
**Purpose**: All test files for quality assurance

**Test Types**:
- Unit tests
- Integration tests
- End-to-end tests
- Service verification
- Docker tests

### `scripts/`
**Purpose**: Automation and utility scripts

**Use Cases**:
- Service health checks
- Build automation
- Deployment helpers
- Maintenance tasks

## 🔄 Migration Summary

### Files Moved
```
✅ patient-webapp/          → frontend/patient-portal/
✅ clinician-webapp/        → frontend/clinician-dashboard/
✅ schizodot_emotion_demo/  → services/emotion-detection/
✅ flask-styled-ui-main/    → services/pill-compliance/
✅ developer_version/       → docs/examples/developer_version/
✅ test_*.py, test_*.sh     → tests/
✅ *.sh scripts             → scripts/
✅ <frontend_aesthetics>.md → docs/FRONTEND_AESTHETICS.md
✅ windsurf-references.txt  → docs/WINDSURF_REFERENCES.txt
```

### Paths Updated
```
✅ docker-compose.yml       → Updated service paths
✅ README.md                → Updated with new structure
```

### Documentation Created
```
✅ README.md (root)         → Comprehensive project overview
✅ frontend/README.md       → Frontend apps guide
✅ services/README.md       → Services documentation
✅ tests/README.md          → Testing guide
✅ scripts/README.md        → Scripts reference
✅ docs/DIRECTORY_STRUCTURE.md → This file
```

## 🚀 Quick Navigation

### For New Developers
1. Start with root `README.md`
2. Read `docs/ARCHITECTURE.md`
3. Follow `docs/QUICK_START.md`
4. Check `docs/DOCKER_SETUP.md`

### For Frontend Developers
```bash
cd frontend/patient-portal/
# or
cd frontend/clinician-dashboard/
```

### For Backend Developers
```bash
cd backend/
```

### For DevOps Engineers
```bash
cd infra/
```

### For Testing
```bash
cd tests/
./test_full_pipeline_docker.sh
```

## 🎨 Design Philosophy

### Clean Root Directory
Only essential configuration files at root:
- `.env` (environment)
- `docker-compose.yml` (orchestration)
- `README.md` (documentation)
- `LICENSE` (legal)

### Self-Documenting Structure
Each directory has:
- Clear, descriptive name
- `README.md` explaining purpose
- Consistent internal organization

### Easy Onboarding
New developers can:
- Understand structure at a glance
- Find files quickly
- Navigate without confusion

## 📝 Maintenance Guidelines

### Adding New Features

**New Frontend App**:
```bash
mkdir -p frontend/new-app
# Add index.html, app.js, styles.css, README.md
```

**New Service**:
```bash
mkdir -p services/new-service
# Add main.py, requirements.txt, Dockerfile, README.md
```

**New Test**:
```bash
# Add to tests/ directory
touch tests/test_new_feature.py
```

**New Script**:
```bash
# Add to scripts/ directory
touch scripts/deploy-to-staging.sh
chmod +x scripts/deploy-to-staging.sh
```

### Updating Documentation

When making structural changes:
1. Update relevant README.md files
2. Update this DIRECTORY_STRUCTURE.md
3. Update root README.md if needed
4. Update docker-compose.yml if paths change

## ✅ Benefits of New Structure

1. **Clarity**: Easy to find any file
2. **Scalability**: Simple to add new components
3. **Professionalism**: Industry-standard organization
4. **Collaboration**: Clear ownership and boundaries
5. **Maintenance**: Easy to update and refactor
6. **Onboarding**: New developers understand quickly

## 🎓 Learning Path

For new team members:

```
Day 1: Read root README.md + docs/ARCHITECTURE.md
Day 2: Set up environment with docs/QUICK_START.md
Day 3: Explore frontend/ directory
Day 4: Explore backend/ directory
Day 5: Run tests/ and review code
```

## 📞 Support

Questions about structure?
- Check relevant README.md first
- Review this document
- Ask in team chat
- Open GitHub issue
