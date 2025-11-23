// ============================================
// DOMINO Patient Portal - Application Logic
// ============================================

// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
const PROTO_URL = 'http://localhost:5001';  // Updated port

// State Management
const state = {
    currentStep: 1,
    currentTab: 'assessment',
    patientId: '',
    recordedBlob: null,
    mediaRecorder: null,
    stream: null,
    recordingTimer: null,
    recordingStartTime: 0,
    jobId: null,
    pollInterval: null
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOMINO Patient Portal initialized');
    updateStepUI();
});

// ============================================
// Step Navigation
// ============================================

function goToStep(stepNumber) {
    // Hide current step
    const currentContent = document.getElementById(`step${state.currentStep}`);
    if (currentContent) {
        currentContent.classList.remove('active');
    }
    
    // Update step indicators
    const allSteps = document.querySelectorAll('.step-item');
    allSteps.forEach((step, index) => {
        const stepNum = index + 1;
        step.classList.remove('active', 'completed');
        
        if (stepNum < stepNumber) {
            step.classList.add('completed');
        } else if (stepNum === stepNumber) {
            step.classList.add('active');
        }
    });
    
    // Show new step
    state.currentStep = stepNumber;
    const nextContent = document.getElementById(`step${state.currentStep}`);
    if (nextContent) {
        nextContent.classList.add('active');
    }
    
    // Initialize step-specific features
    if (state.currentStep === 3) {
        initializeCamera();
    } else if (state.currentStep === 4) {
        showTabNavigation();
    }
    
    updateStepUI();
}

function nextStep() {
    goToStep(state.currentStep + 1);
}

function updateStepUI() {
    // Update session info visibility
    const sessionInfo = document.getElementById('sessionInfo');
    const sessionId = document.getElementById('currentSessionId');
    
    if (state.patientId) {
        sessionInfo.style.display = 'flex';
        sessionId.textContent = state.patientId;
    }
}

// ============================================
// Tab Navigation
// ============================================

function showTabNavigation() {
    const tabNav = document.getElementById('tabNavigation');
    if (tabNav) {
        tabNav.style.display = 'flex';
    }
}

function switchTab(tabName) {
    state.currentTab = tabName;
    
    console.log('🔄 Switching to tab:', tabName);
    
    // Update tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update tab content
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    const activeTab = document.getElementById(`${tabName}Tab`);
    if (activeTab) {
        activeTab.classList.add('active');
        console.log('✅ Activated tab:', `${tabName}Tab`);
    } else {
        console.error('❌ Tab not found:', `${tabName}Tab`);
    }
    
    // Load compliance iframe if switching to compliance tab
    if (tabName === 'compliance') {
        const iframe = document.getElementById('complianceFrame');
        const loadingMsg = document.getElementById('complianceLoadingMessage');
        
        if (iframe) {
            console.log('🔗 Loading compliance iframe...');
            console.log('  Current src:', iframe.src);
            console.log('  Setting src to:', PROTO_URL);
            
            // Show loading message
            if (loadingMsg) {
                loadingMsg.style.display = 'block';
            }
            iframe.style.display = 'none';
            
            // Always reload to ensure fresh state
            iframe.src = PROTO_URL;
            
            // Check if iframe loaded successfully
            iframe.onload = function() {
                console.log('✅ Compliance iframe loaded successfully');
                if (loadingMsg) {
                    loadingMsg.style.display = 'none';
                }
                iframe.style.display = 'block';
                showToast('Compliance check loaded - camera will activate', 'success');
            };
            
            iframe.onerror = function(e) {
                console.error('❌ Compliance iframe failed to load', e);
                if (loadingMsg) {
                    loadingMsg.innerHTML = `
                        <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                            <h3 style="color: var(--primary);">⚠️ Unable to Load Compliance Check</h3>
                            <p>The compliance service is not responding.</p>
                            <p style="font-size: 0.875rem;">Ensure proto.py is running on <code>http://localhost:5001</code></p>
                            <button class="btn btn-secondary" onclick="switchTab('compliance')">
                                <span>Retry</span>
                            </button>
                        </div>
                    `;
                }
                showToast('Failed to load compliance check. Check if proto.py is running.', 'error');
            };
            
            // Timeout fallback
            setTimeout(() => {
                if (loadingMsg && loadingMsg.style.display !== 'none') {
                    console.warn('⚠️ Iframe loading timeout');
                    if (loadingMsg) {
                        loadingMsg.style.display = 'none';
                    }
                    iframe.style.display = 'block';
                }
            }, 5000);
        } else {
            console.error('❌ Compliance iframe element not found!');
            showToast('Compliance interface error', 'error');
        }
    }
}

// ============================================
// Step 1: Patient Information
// ============================================

function startSession() {
    const patientIdInput = document.getElementById('patientId');
    const patientId = patientIdInput.value.trim();
    
    if (!patientId) {
        showToast('Please enter your Patient ID', 'error');
        patientIdInput.focus();
        return;
    }
    
    state.patientId = patientId;
    console.log('✅ Session started for patient:', patientId);
    nextStep();
}

// ============================================
// Step 3: Video Recording
// ============================================

async function initializeCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: true
        });
        
        state.stream = stream;
        const videoPreview = document.getElementById('videoPreview');
        videoPreview.srcObject = stream;
        
        console.log('✅ Camera initialized');
        showToast('Camera ready', 'success');
    } catch (error) {
        console.error('❌ Camera error:', error);
        showToast('Unable to access camera. Please grant permissions.', 'error');
    }
}

function startRecording() {
    if (!state.stream) {
        showToast('Camera not initialized', 'error');
        return;
    }
    
    // Setup MediaRecorder
    const options = {
        mimeType: 'video/webm;codecs=vp9,opus'
    };
    
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'video/webm';
    }
    
    const mediaRecorder = new MediaRecorder(state.stream, options);
    const chunks = [];
    
    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            chunks.push(event.data);
        }
    };
    
    mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'video/webm' });
        state.recordedBlob = blob;
        
        // Show recorded preview
        const videoPreview = document.getElementById('videoPreview');
        const recordedVideo = document.getElementById('recordedVideo');
        const recordedPreview = document.getElementById('recordedPreview');
        
        videoPreview.parentElement.style.display = 'none';
        recordedPreview.style.display = 'block';
        recordedVideo.src = URL.createObjectURL(blob);
        
        console.log('✅ Recording stopped, size:', blob.size, 'bytes');
        showToast('Recording saved', 'success');
    };
    
    state.mediaRecorder = mediaRecorder;
    mediaRecorder.start();
    
    // Update UI
    document.getElementById('startRecordBtn').style.display = 'none';
    document.getElementById('stopRecordBtn').style.display = 'flex';
    document.getElementById('recordingIndicator').style.display = 'flex';
    
    // Start timer
    state.recordingStartTime = Date.now();
    state.recordingTimer = setInterval(updateRecordingTimer, 1000);
    
    console.log('🎥 Recording started');
}

function stopRecording() {
    if (state.mediaRecorder && state.mediaRecorder.state === 'recording') {
        state.mediaRecorder.stop();
        clearInterval(state.recordingTimer);
        
        document.getElementById('stopRecordBtn').style.display = 'none';
        document.getElementById('recordingIndicator').style.display = 'none';
    }
}

function retakeVideo() {
    const videoPreview = document.getElementById('videoPreview');
    const recordedVideo = document.getElementById('recordedVideo');
    const recordedPreview = document.getElementById('recordedPreview');
    
    videoPreview.parentElement.style.display = 'block';
    recordedPreview.style.display = 'none';
    recordedVideo.src = '';
    
    document.getElementById('startRecordBtn').style.display = 'flex';
    document.getElementById('recordingTime').textContent = '00:00';
    
    state.recordedBlob = null;
    console.log('🔄 Reset for retake');
}

function updateRecordingTimer() {
    const elapsed = Math.floor((Date.now() - state.recordingStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const seconds = (elapsed % 60).toString().padStart(2, '0');
    document.getElementById('recordingTime').textContent = `${minutes}:${seconds}`;
}

// ============================================
// Step 4: Upload and Analysis
// ============================================

async function uploadVideo() {
    if (!state.recordedBlob) {
        showToast('No video recorded', 'error');
        return;
    }
    
    // Move to step 4
    nextStep();
    
    // Show uploading card
    const uploadingCard = document.getElementById('uploadingCard');
    const resultsCard = document.getElementById('resultsCard');
    uploadingCard.style.display = 'block';
    resultsCard.style.display = 'none';
    
    try {
        // Step 1: Create job
        updateUploadProgress(10, 'Creating analysis job...', 'Contacting backend server...');
        console.log('🚀 Creating job for patient:', state.patientId);
        console.log('📡 Backend URL:', API_BASE_URL);
        console.log('📦 Video size:', state.recordedBlob.size, 'bytes');
        
        const createJobResponse = await fetch(`${API_BASE_URL}/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                patient_id: state.patientId,
                filename: `checkin-${Date.now()}.webm`,
                content_type: 'video/webm',
                metadata: {
                    session_type: 'clinical_questions',
                    questions_answered: 5
                }
            })
        }).catch(err => {
            // Network error - backend not reachable
            console.error('❌ Network error:', err);
            throw new Error(`Cannot reach backend at ${API_BASE_URL}. Please ensure backend is running.`);
        });
        
        console.log('📡 Response status:', createJobResponse.status);
        
        if (!createJobResponse.ok) {
            const errorText = await createJobResponse.text();
            console.error('❌ Backend error:', errorText);
            let errorData;
            try {
                errorData = JSON.parse(errorText);
            } catch (e) {
                errorData = { detail: { message: errorText || 'Unknown error' } };
            }
            throw new Error(errorData.detail?.message || `Backend error: ${createJobResponse.status}`);
        }
        
        const jobData = await createJobResponse.json();
        state.jobId = jobData.job_id;
        console.log('✅ Job created:', state.jobId);
        console.log('📤 Presigned URL received');
        
        // Step 2: Upload to S3
        updateUploadProgress(30, 'Uploading Video...', 'Transferring data to storage...');
        
        console.log('📤 Uploading to S3...');
        const uploadResponse = await fetch(jobData.presigned_url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'video/webm'
            },
            body: state.recordedBlob
        }).catch(err => {
            console.error('❌ S3 upload error:', err);
            throw new Error('Failed to upload to storage: ' + err.message);
        });
        
        console.log('📡 Upload response status:', uploadResponse.status);
        
        if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            console.error('❌ S3 error:', errorText);
            throw new Error(`Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`);
        }
        
        console.log('✅ Video uploaded successfully');
        updateUploadProgress(50, 'Processing...', 'Analyzing your assessment...');
        
        // Step 3: Poll for results
        startPollingJobStatus();
        
    } catch (error) {
        console.error('❌ Upload error:', error);
        console.error('❌ Error stack:', error.stack);
        
        // Show detailed error message
        const errorMsg = error.message || 'Unknown error occurred';
        showToast('Upload failed: ' + errorMsg, 'error');
        updateUploadProgress(0, 'Upload Failed', errorMsg);
        
        // Show helpful message if backend is not reachable
        if (errorMsg.includes('Cannot reach backend')) {
            const helpText = `
Backend server is not running! 

To start the backend, run:
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

Or use the complete system startup script:
./start-complete-system.sh
            `.trim();
            
            console.error('💡 Help:', helpText);
            
            // Update UI with helpful message
            updateUploadProgress(0, 'Backend Not Running', 
                'Please start the backend server. Check console (F12) for instructions.');
        }
    }
}

function updateUploadProgress(percent, status, subtext) {
    const progressBar = document.getElementById('uploadProgress');
    const statusText = document.getElementById('uploadStatus');
    const subtextEl = document.getElementById('uploadSubtext');
    
    if (progressBar) progressBar.style.width = `${percent}%`;
    if (statusText) statusText.textContent = status;
    if (subtextEl) subtextEl.textContent = subtext;
}

async function startPollingJobStatus() {
    const startTime = Date.now();
    
    state.pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/jobs/${state.jobId}/status`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch job status');
            }
            
            const status = await response.json();
            const progress = Math.min(status.progress || 60, 95);
            
            console.log('📊 Job status:', status.status, progress + '%');
            
            if (status.status === 'processing') {
                updateUploadProgress(progress, 'Processing...', status.message || 'Analyzing video...');
            } else if (status.status === 'completed') {
                console.log('✅ Analysis completed!');
                clearInterval(state.pollInterval);
                
                updateUploadProgress(100, 'Completing...', 'Finalizing results...');
                
                const processingTime = ((Date.now() - startTime) / 1000).toFixed(1);
                
                setTimeout(() => {
                    fetchAndDisplayResults(processingTime);
                }, 500);
            } else if (status.status === 'failed') {
                console.error('❌ Analysis failed:', status.error);
                clearInterval(state.pollInterval);
                showToast('Analysis failed: ' + (status.error || 'Unknown error'), 'error');
            }
            
        } catch (error) {
            console.error('❌ Polling error:', error);
        }
    }, 3000);
}

async function fetchAndDisplayResults(processingTime) {
    try {
        const response = await fetch(`${API_BASE_URL}/results/job/${state.jobId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch results');
        }
        
        const results = await response.json();
        displayResults(results, processingTime);
        
    } catch (error) {
        console.error('❌ Results fetch error:', error);
        showToast('Failed to fetch results', 'error');
    }
}

function displayResults(results, processingTime) {
    console.log('📊 Analysis results:', results);
    
    // Hide uploading, show results
    document.getElementById('uploadingCard').style.display = 'none';
    document.getElementById('resultsCard').style.display = 'block';
    
    // Update job info
    document.getElementById('jobId').textContent = state.jobId;
    document.getElementById('processingTime').textContent = processingTime;
    
    showToast('Analysis complete!', 'success');
}

// ============================================
// Pill Compliance Integration
// ============================================

function openPillCompliance() {
    // Enable compliance tab
    const complianceBtn = document.getElementById('complianceTabBtn');
    complianceBtn.disabled = false;
    
    // Switch to compliance tab
    switchTab('compliance');
    
    console.log('💊 Opening pill compliance check');
    
    // Start monitoring protocol status
    startComplianceMonitoring();
}

// ============================================
// Compliance Protocol Monitoring
// ============================================

let complianceCheckInterval = null;

function startComplianceMonitoring() {
    console.log('📊 Starting compliance protocol monitoring...');
    
    // Clear any existing interval
    if (complianceCheckInterval) {
        clearInterval(complianceCheckInterval);
    }
    
    // Poll every 2 seconds
    complianceCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`${PROTO_URL}/status_update`);
            if (!response.ok) return;
            
            const status = await response.json();
            console.log('📊 Protocol status:', status);
            
            // Check if protocol completed successfully
            if (status.result_status && 
                (status.result_status.includes('SUCCESS') || 
                 status.result_status.includes('COMPLETE'))) {
                console.log('✅ Protocol completed successfully!');
                clearInterval(complianceCheckInterval);
                showComplianceCompletion();
            }
            
        } catch (error) {
            console.error('Error checking protocol status:', error);
        }
    }, 2000);
}

function showComplianceCompletion() {
    console.log('🎉 Showing compliance completion');
    
    // Hide iframe
    const iframe = document.getElementById('complianceFrame');
    if (iframe) {
        iframe.style.display = 'none';
    }
    
    // Show completion section
    const completionSection = document.getElementById('complianceCompletionSection');
    if (completionSection) {
        completionSection.style.display = 'block';
        
        // Populate session ID
        const sessionIdEl = document.getElementById('finalSessionId');
        if (sessionIdEl && state.patientId) {
            sessionIdEl.textContent = state.patientId;
        }
        
        // Animate in
        completionSection.style.animation = 'fadeInUp 0.5s ease-out';
    }
    
    showToast('🎉 All steps completed successfully!', 'success');
}

function completeSession() {
    console.log('✅ Completing session for patient:', state.patientId);
    
    // Show final message
    const completionSection = document.getElementById('complianceCompletionSection');
    if (completionSection) {
        completionSection.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <div style="font-size: 5rem; margin-bottom: 20px; animation: scaleIn 0.5s ease-out;">
                    🎊
                </div>
                <h1 style="color: var(--primary); margin-bottom: 15px; font-size: 2rem;">Thank You!</h1>
                <p style="font-size: 1.125rem; color: var(--text-muted); margin-bottom: 30px;">
                    Your check-in is complete. A clinician will review your assessment.
                </p>
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; max-width: 400px; margin-left: auto; margin-right: auto;">
                    <p style="font-size: 0.875rem; color: var(--text-muted); margin-bottom: 10px;">Session Summary</p>
                    <p><strong>Patient ID:</strong> ${state.patientId}</p>
                    <p><strong>Job ID:</strong> ${state.jobId || 'N/A'}</p>
                    <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
                </div>
                <button class="btn btn-secondary" onclick="window.location.reload()">
                    <span>Start New Session</span>
                </button>
            </div>
        `;
    }
    
    showToast('Session submitted successfully', 'success');
    
    // Reset state after a delay
    setTimeout(() => {
        console.log('🔄 Session complete, ready for new patient');
    }, 3000);
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.25rem;">
                ${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}
            </span>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================
// Cleanup
// ============================================

window.addEventListener('beforeunload', () => {
    if (state.stream) {
        state.stream.getTracks().forEach(track => track.stop());
    }
    if (state.pollInterval) {
        clearInterval(state.pollInterval);
    }
    if (complianceCheckInterval) {
        clearInterval(complianceCheckInterval);
    }
});

// ============================================
// Utility Functions
// ============================================

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Export for debugging
window.DOMINO = {
    state,
    goToStep,
    switchTab,
    showToast
};
