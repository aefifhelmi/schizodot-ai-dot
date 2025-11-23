# 🧠 Schizodot AI - Patient Web Portal

A comprehensive end-to-end patient portal for mental health compliance monitoring.

## 🎯 Features

### 1. **Patient Identification**
- Secure patient ID entry
- Session tracking

### 2. **Clinical Assessment**
- 5 clinical questions displayed to patient
- Single video recording session for all answers
- Questions include:
  1. Mood and emotional state
  2. Medication adherence
  3. Side effects
  4. Sleep patterns
  5. Additional concerns

### 3. **Video Recording**
- Real-time webcam access
- High-quality video/audio capture
- Recording timer
- Review and re-record capability
- Direct upload to backend

### 4. **AI Analysis**
- Emotion detection
- Speech transcription
- LLM-powered clinical insights
- Real-time progress tracking

### 5. **Pill Compliance**
- Integration with YOLOv11-based real-time monitoring
- 6-phase verification protocol
- MediaPipe jaw tracking
- Live verification feedback

## 🚀 Quick Start

### Prerequisites
1. **Backend services running** (Docker):
   ```bash
   cd /Users/tengkuafif/schizodot-ai-dot
   docker compose up -d backend celery-worker redis dynamodb-local s3-local
   ```

2. **Proto.py running** (Local):
   ```bash
   cd /Users/tengkuafif/Desktop/zahin
   source .venv/bin/activate
   OPENCV_AVFOUNDATION_SKIP_AUTH=1 python proto.py
   ```

### Run the Web Portal

**Option 1: Simple Python Server**
```bash
cd /Users/tengkuafif/schizodot-ai-dot/patient-webapp
python3 -m http.server 3000
```

**Option 2: Node.js HTTP Server**
```bash
cd /Users/tengkuafif/schizodot-ai-dot/patient-webapp
npx http-server -p 3000 -c-1
```

Then open: **http://localhost:3000**

## 📊 Architecture

```
Patient Portal (Frontend - Port 3000)
           |
           v
    +-----------------+
    |  1. Patient ID  |
    +-----------------+
           |
           v
    +-----------------+
    | 2. Questions    |
    |    Display      |
    +-----------------+
           |
           v
    +-----------------+
    | 3. Video        |
    |    Recording    |
    +-----------------+
           |
           v
    +------------------+          +-------------------+
    | Backend API      | -------> | AWS Services      |
    | (Port 8000)      |          | (S3, DynamoDB)    |
    +------------------+          +-------------------+
           |
           v
    +------------------+
    | Celery Worker    |
    | - Emotion AI     |
    | - Transcription  |
    | - LLM Analysis   |
    +------------------+
           |
           v
    +------------------+
    | 4. Results       |
    |    Display       |
    +------------------+
           |
           v
    +------------------+
    | 5. Pill Check    | -----> Proto.py (Port 5000)
    |    (Optional)    |        - YOLOv11 Detection
    +------------------+        - MediaPipe Tracking
```

## 🔧 Configuration

Edit `app.js` to change API endpoints:

```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
const PROTO_URL = 'http://localhost:5000';
```

## 📝 User Flow

1. **Enter Patient ID** → Validates and starts session
2. **Review Questions** → Patient reads 5 clinical questions
3. **Record Video** → Single recording answering all questions
4. **Upload & Analyze** → Automatic upload and AI processing
5. **View Results** → Emotion analysis, transcript, clinical summary
6. **Pill Compliance** → Optional real-time verification
7. **Complete** → Session summary and results

## 🎨 UI Features

- **Modern Design**: Clean, professional healthcare interface
- **Responsive**: Works on desktop and mobile
- **Accessible**: WCAG compliant
- **Real-time Feedback**: Progress indicators and live updates
- **Smooth Animations**: Professional transitions
- **Error Handling**: User-friendly error messages

## 🔒 Security & Privacy

- HIPAA compliant data handling
- Secure video upload via presigned URLs
- Patient ID validation
- No video stored locally (direct S3 upload)
- Encrypted transmission

## 🐛 Troubleshooting

### Camera not working
- Grant camera/microphone permissions
- Check browser compatibility (Chrome/Firefox recommended)
- Ensure no other apps are using the camera

### Backend connection errors
- Verify backend is running: `docker compose ps`
- Check API URL in `app.js`
- Look at browser console for errors

### Proto.py window won't open
- Allow pop-ups in browser settings
- Verify proto.py is running: `http://localhost:5000`

## 📱 Browser Support

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## 🎬 Demo Video Flow

1. Patient enters ID: `PAT-001`
2. Reads clinical questions
3. Clicks "Start Recording"
4. Answers all 5 questions clearly
5. Clicks "Stop Recording"
6. Reviews video
7. Clicks "Upload & Analyze"
8. Watches real-time analysis progress
9. Views comprehensive results
10. Optionally completes pill compliance check
11. Receives session completion confirmation

## 📊 Expected Results

After video analysis, patient sees:
- **Emotion Analysis**: Primary emotion and confidence score
- **Transcript**: Full text of spoken responses
- **Clinical Summary**: AI-generated insights for healthcare provider

## 🔗 Integration Points

- **Backend API**: FastAPI endpoints for job creation and status
- **S3**: Direct video upload
- **DynamoDB**: Job and result storage
- **Celery**: Async task processing
- **Proto.py**: Real-time pill compliance monitoring

## 📞 Support

For technical support or questions, contact your healthcare provider or system administrator.

---

**Built with ❤️ for better mental health monitoring**
