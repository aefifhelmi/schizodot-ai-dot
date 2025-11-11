# 🎨 SchizoDot AI - Test UI

A simple, standalone HTML/JavaScript interface for testing the SchizoDot AI backend with stub data.

## 🚀 Quick Start

### 1. Make sure your backend is running:

```bash
cd /Users/tengkuafif/schizodot-ai-dot
docker compose up -d
```

### 2. Open the test UI:

Simply open `test-ui.html` in your browser:

```bash
open frontend/test-ui.html
```

Or navigate to: `file:///Users/tengkuafif/schizodot-ai-dot/frontend/test-ui.html`

## ✨ Features

### 📋 **Patient Information**
- Enter patient ID (default: `patient-test-001`)
- Select analysis type (Video/Audio)

### 📁 **File Upload**
- Drag & drop files
- Or click to browse
- Supports video and audio files
- Shows file name and size

### ⚡ **Real-Time Progress Tracking**
- Live progress bar (0% → 100%)
- Step-by-step status updates:
  - Job created (10%)
  - Downloading file (20%)
  - Analyzing emotions (40%)
  - Detecting compliance (60%)
  - Combining results (75%)
  - Generating summary (85%)
  - Saving results (95%)
  - Complete! (100%)

### 📊 **Results Display**
Four tabs to view results:

1. **😊 Emotions Tab**
   - Emotional state summary
   - Audio emotion (Calm - 85% confidence)
   - Facial emotion (Neutral - 82% confidence)

2. **💊 Compliance Tab**
   - Medication adherence status
   - Pill detection (Yes/No)
   - Confidence score (92%)
   - Compliance score (0.92)

3. **📋 Summary Tab**
   - Clinical summary
   - Risk assessment
   - Recommendations

4. **🔧 Raw Data Tab**
   - Complete JSON response
   - For debugging

### 💾 **Download Results**
- Download complete results as JSON file
- Filename: `schizodot-results-{job_id}.json`

## 🧪 Testing Workflow

### Complete Test Flow:

1. **Enter Patient Info**
   - Patient ID: `patient-test-001`
   - Analysis Type: Video Analysis

2. **Upload File**
   - Create a dummy file: `echo "test" > test-video.mp4`
   - Drag & drop or click to upload

3. **Start Analysis**
   - Click "🚀 Start Analysis"
   - Watch real-time progress

4. **View Results**
   - Automatically shows when complete
   - Browse through tabs
   - Download results if needed

5. **New Analysis**
   - Click "🔄 New Analysis" to reset

## 📝 What You'll See

### During Processing:
```
⚡ Processing Analysis
Job ID: job-7602b60da084
Progress: 60% - Detecting medication compliance...

✓ Job created
✓ Downloading file from S3
✓ Analyzing emotions
⏳ Detecting medication compliance
○ Combining analysis results
○ Generating clinical summary
○ Saving results
○ Analysis complete!
```

### After Completion:
```
📊 Analysis Results
✅ Analysis completed successfully
Processing time: 8.16 seconds

Tabs:
- 😊 Emotions: Shows emotional state analysis
- 💊 Compliance: Shows medication adherence
- 📋 Summary: Shows clinical summary
- 🔧 Raw Data: Shows complete JSON
```

## 🎯 Testing Scenarios

### Scenario 1: Happy Path
```
1. Enter patient ID: patient-001
2. Upload test file
3. Click Start Analysis
4. Wait ~70 seconds
5. View results in all tabs
6. Download JSON results
```

### Scenario 2: Multiple Patients
```
1. Test with patient-001
2. Reset form
3. Test with patient-002
4. Compare results
```

### Scenario 3: Error Handling
```
1. Try without file → Shows alert
2. Try without patient ID → Shows alert
3. Backend down → Shows error card
```

## 🔍 Troubleshooting

### Issue: "Failed to fetch"
**Solution**: Make sure backend is running:
```bash
docker compose ps
# Should show: schizodot-fastapi, schizodot-worker, schizodot-redis
```

### Issue: "CORS error"
**Solution**: Backend CORS is configured for `http://localhost:3000`. 
The test UI uses `file://` protocol which should work, but if issues persist:
1. Serve via simple HTTP server:
```bash
cd frontend
python3 -m http.server 3000
# Then open: http://localhost:3000/test-ui.html
```

### Issue: Job stuck at "processing"
**Solution**: 
1. Check worker logs: `docker compose logs celery-worker`
2. Check job status manually:
```bash
curl http://localhost:8000/api/v1/jobs/JOB_ID/status
```

### Issue: No results showing
**Solution**:
1. Check if job completed: Look for "status": "completed"
2. Check results endpoint:
```bash
curl http://localhost:8000/api/v1/results/PATIENT_ID
```

## 🎨 UI Features

### Design:
- Modern gradient background
- Smooth animations
- Responsive layout
- Clean card-based design
- Color-coded sections

### Interactions:
- Drag & drop file upload
- Real-time progress updates
- Tab-based results view
- One-click download
- Easy reset

### Status Indicators:
- ✓ Green checkmark = Completed
- ⏳ Blue pulse = In progress
- ○ Gray circle = Pending
- ❌ Red X = Failed

## 📱 Browser Compatibility

Works on:
- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## 🔗 API Endpoints Used

The UI interacts with these endpoints:

1. `POST /api/v1/analyze/` - Create job
2. `GET /api/v1/jobs/{job_id}/status` - Check status
3. `GET /api/v1/results/{patient_id}` - Get results
4. `PUT {presigned_url}` - Upload file to S3

## 💡 Tips

1. **Keep browser console open** to see API calls
2. **Use Chrome DevTools Network tab** to debug
3. **Test with different file sizes** to see timing differences
4. **Try multiple tabs** to test concurrent jobs
5. **Download results** for documentation

## 🎓 Learning Points

This UI demonstrates:
- ✅ Asynchronous job processing
- ✅ Real-time progress tracking
- ✅ File upload with presigned URLs
- ✅ Polling for job status
- ✅ Error handling
- ✅ Result visualization
- ✅ Stub data integration

## 🚀 Next Steps

When real AI models are ready:
1. Set `ENABLE_EMOTION_SERVICE=true` in `.env`
2. Set `ENABLE_COMPLIANCE_SERVICE=true` in `.env`
3. Restart backend: `docker compose restart`
4. Test UI will automatically use real AI results!

No UI changes needed! 🎉

## 📞 Support

If you encounter issues:
1. Check backend logs: `docker compose logs -f`
2. Check worker logs: `docker compose logs -f celery-worker`
3. Check browser console for errors
4. Verify backend is accessible: `curl http://localhost:8000/api/v1/health`

---

**Happy Testing! 🧠✨**
