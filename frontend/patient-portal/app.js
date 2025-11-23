// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
const PROTO_URL = 'http://localhost:5002';  // Changed from 5000 to 5002 (AirPlay conflict)

// State Management
const state = {
    currentStep: 1,
    patientId: '',
    recordedBlob: null,
    mediaRecorder: null,
    stream: null,
    recordingTimer: null,
    recordingStartTime: 0,
    jobId: null,
    pollInterval: null
};

// Step Navigation
function nextStep() {
    const currentContent = document.getElementById(`step${state.currentStep}`);
    currentContent.classList.remove('active');
    
    const currentIndicator = document.querySelector(`.step-item[data-step="${state.currentStep}"]`);
    currentIndicator.classList.remove('active');
    currentIndicator.classList.add('completed');
    
    state.currentStep++;
    
    const nextContent = document.getElementById(`step${state.currentStep}`);
    nextContent.classList.add('active');
    
    const nextIndicator = document.querySelector(`.step-item[data-step="${state.currentStep}"]`);
    nextIndicator.classList.add('active');
    
    // Initialize step
    if (state.currentStep === 3) {
        initializeCamera();
    }
}

function previousStep() {
    const currentContent = document.getElementById(`step${state.currentStep}`);
    currentContent.classList.remove('active');
    
    const currentIndicator = document.querySelector(`.step-item[data-step="${state.currentStep}"]`);
    currentIndicator.classList.remove('active');
    
    state.currentStep--;
    
    const prevContent = document.getElementById(`step${state.currentStep}`);
    prevContent.classList.add('active');
    
    const prevIndicator = document.querySelector(`.step-item[data-step="${state.currentStep}"]`);
    prevIndicator.classList.add('active');
    prevIndicator.classList.remove('completed');
}

// Step 1: Patient Information
function startSession() {
    const patientId = document.getElementById('patientId').value.trim();
    
    if (!patientId) {
        alert('Please enter your Patient ID');
        return;
    }
    
    state.patientId = patientId;
    nextStep();
}

// Step 3: Video Recording
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
    } catch (error) {
        console.error('Camera error:', error);
        alert('Unable to access camera. Please grant camera permissions and try again.');
    }
}

function startRecording() {
    if (!state.stream) {
        alert('Camera not initialized');
        return;
    }
    
    // Set up MediaRecorder
    const options = {
        mimeType: 'video/webm;codecs=vp9,opus'
    };
    
    // Check if codec is supported, fallback if not
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
        
        // Show playback
        const videoPreview = document.getElementById('videoPreview');
        const videoPlayback = document.getElementById('videoPlayback');
        
        videoPreview.style.display = 'none';
        videoPlayback.style.display = 'block';
        videoPlayback.src = URL.createObjectURL(blob);
        
        // Update UI
        document.getElementById('retryRecordBtn').style.display = 'inline-flex';
        document.getElementById('uploadBtn').style.display = 'inline-flex';
        document.getElementById('step3NavButtons').style.display = 'none';
        
        console.log('✅ Recording stopped, blob size:', blob.size);
    };
    
    state.mediaRecorder = mediaRecorder;
    mediaRecorder.start();
    
    // Update UI
    document.getElementById('startRecordBtn').style.display = 'none';
    document.getElementById('stopRecordBtn').style.display = 'inline-flex';
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
        
        // Update UI
        document.getElementById('stopRecordBtn').style.display = 'none';
        document.getElementById('recordingIndicator').style.display = 'none';
    }
}

function retryRecording() {
    // Reset UI
    const videoPreview = document.getElementById('videoPreview');
    const videoPlayback = document.getElementById('videoPlayback');
    
    videoPreview.style.display = 'block';
    videoPlayback.style.display = 'none';
    videoPlayback.src = '';
    
    document.getElementById('startRecordBtn').style.display = 'inline-flex';
    document.getElementById('retryRecordBtn').style.display = 'none';
    document.getElementById('uploadBtn').style.display = 'none';
    document.getElementById('step3NavButtons').style.display = 'flex';
    
    state.recordedBlob = null;
}

function updateRecordingTimer() {
    const elapsed = Math.floor((Date.now() - state.recordingStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const seconds = (elapsed % 60).toString().padStart(2, '0');
    document.getElementById('recordingTimer').textContent = `${minutes}:${seconds}`;
}

// Step 4: Upload and Analysis
async function uploadVideo() {
    if (!state.recordedBlob) {
        alert('No video recorded');
        return;
    }
    
    // Move to analysis step
    nextStep();
    
    try {
        // Step 1: Create job
        updateProgress(10, 'Creating analysis job...');
        updateAnalysisStep('uploadStep', 'active');
        
        console.log('🚀 Creating job for patient:', state.patientId);
        
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
        });
        
        console.log('📡 Create job response status:', createJobResponse.status);
        
        if (!createJobResponse.ok) {
            const errorData = await createJobResponse.json().catch(() => ({}));
            console.error('❌ Job creation failed:', errorData);
            throw new Error(errorData.detail?.message || 'Failed to create job');
        }
        
        const jobData = await createJobResponse.json();
        state.jobId = jobData.job_id;
        
        console.log('✅ Job created:', state.jobId);
        
        // Step 2: Upload to S3
        updateProgress(30, 'Uploading video...');
        
        console.log('📤 Uploading to S3, blob size:', state.recordedBlob.size, 'bytes');
        console.log('📤 Presigned URL:', jobData.presigned_url.substring(0, 100) + '...');
        
        const uploadResponse = await fetch(jobData.presigned_url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'video/webm'
            },
            body: state.recordedBlob
        });
        
        console.log('📡 Upload response status:', uploadResponse.status);
        
        if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            console.error('❌ Upload failed:', errorText);
            throw new Error(`Failed to upload video: ${uploadResponse.status} ${uploadResponse.statusText}`);
        }
        
        console.log('✅ Video uploaded successfully');
        updateAnalysisStep('uploadStep', 'completed');
        updateProgress(50, 'Video uploaded successfully');
        
        // Step 3: Poll for results
        startPollingJobStatus();
        
    } catch (error) {
        console.error('❌ Upload error:', error);
        updateProgress(0, 'Error: ' + error.message);
        alert('Failed to upload video. Please check the console (F12) for details and try again.\n\nError: ' + error.message);
    }
}

function updateProgress(percent, text) {
    document.getElementById('analysisProgress').style.width = `${percent}%`;
    document.getElementById('progressText').textContent = text;
}

function updateAnalysisStep(stepId, status) {
    const step = document.getElementById(stepId);
    step.classList.remove('active', 'completed');
    step.classList.add(status);
    
    const icon = step.querySelector('.step-icon');
    if (status === 'completed') {
        icon.textContent = '✓';
    } else if (status === 'active') {
        icon.textContent = '⏳';
    }
}

async function startPollingJobStatus() {
    updateAnalysisStep('emotionStep', 'active');
    
    state.pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/jobs/${state.jobId}/status`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch job status');
            }
            
            const status = await response.json();
            console.log('📊 Job status:', status.status, status.progress + '%');
            
            // Update progress based on status
            if (status.status === 'processing') {
                // Smooth progress updates
                const progress = Math.min(status.progress || 60, 95);
                updateProgress(progress, status.message || 'Processing video...');
                
                // Update analysis steps based on progress
                if (progress < 50) {
                    updateAnalysisStep('emotionStep', 'active');
                } else if (progress < 80) {
                    updateAnalysisStep('emotionStep', 'completed');
                    updateAnalysisStep('llmStep', 'active');
                } else {
                    updateAnalysisStep('emotionStep', 'completed');
                    updateAnalysisStep('llmStep', 'active');
                }
            } else if (status.status === 'completed') {
                console.log('✅ Analysis completed! Fetching results...');
                clearInterval(state.pollInterval);
                
                // Mark all steps as completed
                updateAnalysisStep('uploadStep', 'completed');
                updateAnalysisStep('emotionStep', 'completed');
                updateAnalysisStep('llmStep', 'completed');
                
                updateProgress(100, 'Analysis complete!');
                
                // Small delay for visual feedback, then fetch results
                setTimeout(async () => {
                    await fetchResults();
                }, 500);
            } else if (status.status === 'failed') {
                console.error('❌ Analysis failed:', status.error);
                clearInterval(state.pollInterval);
                updateProgress(0, 'Analysis failed: ' + (status.error || 'Unknown error'));
                alert('Analysis failed. Please try again.');
            }
            
        } catch (error) {
            console.error('❌ Polling error:', error);
            // Don't stop polling on network errors, will retry
        }
    }, 3000); // Poll every 3 seconds
}

async function fetchResults() {
    try {
        const response = await fetch(`${API_BASE_URL}/results/job/${state.jobId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch results');
        }
        
        const results = await response.json();
        displayResults(results);
        
    } catch (error) {
        console.error('Results fetch error:', error);
        alert('Failed to fetch results');
    }
}

function displayResults(results) {
    const container = document.getElementById('resultsContent');
    console.log('📊 Analysis completed:', results);
    
    // Patient-friendly simple message (no technical details)
    let html = `
        <div style="text-align: center;">
            <div style="margin-bottom: 2rem;">
                <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 50%; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; animation: scaleIn 0.5s ease;">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
                <h3 style="color: #10b981; margin-bottom: 0.5rem; font-size: 1.5rem;">✅ Video Uploaded Successfully!</h3>
                <p style="color: var(--text-secondary); font-size: 1rem;">Your session has been recorded and processed.</p>
            </div>
            
            <div style="background: var(--bg-color); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 6v6l4 2"></path>
                    </svg>
                    <span style="color: var(--text-secondary); font-size: 0.875rem;">Processing completed in ${results.processing_time_seconds ? parseFloat(results.processing_time_seconds).toFixed(1) : '~30'} seconds</span>
                </div>
                
                <div style="text-align: left; max-width: 400px; margin: 0 auto;">
                    <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem; background: white; border-radius: 8px; margin-bottom: 0.5rem;">
                        <div style="width: 32px; height: 32px; background: #dbeafe; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2">
                                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                            </svg>
                        </div>
                        <div style="flex: 1;">
                            <div style="font-weight: 500; color: var(--text-primary); font-size: 0.875rem;">Video Recorded</div>
                            <div style="color: var(--text-secondary); font-size: 0.75rem;">Clinical questions answered</div>
                        </div>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </div>
                    
                    <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem; background: white; border-radius: 8px;">
                        <div style="width: 32px; height: 32px; background: #dbeafe; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                        </div>
                        <div style="flex: 1;">
                            <div style="font-weight: 500; color: var(--text-primary); font-size: 0.875rem;">Analysis Complete</div>
                            <div style="color: var(--text-secondary); font-size: 0.75rem;">Data securely stored</div>
                        </div>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 1.5rem; text-align: center;">
                <p style="color: #92400e; margin: 0 0 1rem 0; font-size: 0.875rem;">
                    <strong>📋 Next Step:</strong> Please complete the medication compliance check
                </p>
                <button onclick="openPillCompliance()" style="background: linear-gradient(135deg, #6366f1, #4f46e5); color: white; border: none; padding: 0.875rem 2rem; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease; box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(99, 102, 241, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(99, 102, 241, 0.3)'">
                    Start Medication Compliance Check →
                </button>
            </div>
        </div>
        
        <style>
            @keyframes scaleIn {
                from { transform: scale(0); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
        </style>
    `;
    
    container.innerHTML = html;
    document.getElementById('resultsContainer').style.display = 'block';
}

// Tab Switching
function switchTab(tabName) {
    console.log('🔄 Switching to tab:', tabName);
    
    // Hide all tab contents
    document.getElementById('assessmentContent').style.display = 'none';
    document.getElementById('complianceContent').style.display = 'none';
    
    // Remove active class from all tabs
    document.getElementById('assessmentTab').classList.remove('active');
    document.getElementById('complianceTab').classList.remove('active');
    
    // Show selected tab content and mark as active
    if (tabName === 'assessment') {
        document.getElementById('assessmentContent').style.display = 'block';
        document.getElementById('assessmentTab').classList.add('active');
    } else if (tabName === 'compliance') {
        document.getElementById('complianceContent').style.display = 'block';
        document.getElementById('complianceTab').classList.add('active');
        
        // Load iframe if not already loaded
        loadComplianceMonitor();
    }
}

// Load compliance monitor in iframe
function loadComplianceMonitor() {
    const iframe = document.getElementById('complianceFrame');
    const loading = document.getElementById('complianceLoading');
    const errorDiv = document.getElementById('complianceError');
    
    // Check if already loaded
    if (iframe.src && iframe.src !== window.location.href) {
        console.log('✅ Compliance monitor already loaded');
        return;
    }
    
    console.log('📡 Loading compliance monitor from:', PROTO_URL);
    
    // Show loading indicator
    loading.style.display = 'block';
    errorDiv.style.display = 'none';
    iframe.style.display = 'none';
    
    // Test if proto.py is accessible
    fetch(PROTO_URL + '/status_update')
        .then(response => {
            if (response.ok) {
                console.log('✅ Proto.py is accessible, loading iframe...');
                iframe.src = PROTO_URL;
                
                // Set timeout to hide loading if iframe doesn't load
                setTimeout(() => {
                    if (loading.style.display !== 'none') {
                        loading.style.display = 'none';
                        iframe.style.display = 'block';
                    }
                }, 3000);
            } else {
                throw new Error('Proto.py not responding');
            }
        })
        .catch(error => {
            console.error('❌ Failed to load proto.py:', error);
            loading.style.display = 'none';
            errorDiv.style.display = 'block';
            iframe.style.display = 'none';
        });
}

// Iframe load success callback
function onComplianceFrameLoad() {
    console.log('✅ Compliance monitor loaded successfully');
    document.getElementById('complianceLoading').style.display = 'none';
    document.getElementById('complianceError').style.display = 'none';
    document.getElementById('complianceFrame').style.display = 'block';
}

// Iframe load error callback
function onComplianceFrameError() {
    console.error('❌ Compliance monitor failed to load');
    document.getElementById('complianceLoading').style.display = 'none';
    document.getElementById('complianceError').style.display = 'block';
    document.getElementById('complianceFrame').style.display = 'none';
}

// Retry loading compliance monitor
function retryComplianceLoad() {
    console.log('🔄 Retrying compliance monitor load...');
    const iframe = document.getElementById('complianceFrame');
    iframe.src = '';  // Clear the iframe
    setTimeout(() => {
        loadComplianceMonitor();
    }, 100);
}

// Step 5: Pill Compliance (now opens in tab instead of new window)
function openPillCompliance() {
    // Enable the compliance tab
    const complianceTab = document.getElementById('complianceTab');
    complianceTab.disabled = false;
    
    // Switch to compliance tab
    switchTab('compliance');
    
    // Smooth scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Complete compliance verification and finish session
function completeComplianceVerification() {
    console.log('✅ Completing compliance verification...');
    
    // Show confirmation
    if (confirm('Have you completed all 6 phases of the medication compliance protocol?\n\n✓ Phase 1: Hold medication up\n✓ Phase 2: Open mouth WIDE\n✓ Phase 3: Place pill on tongue\n✓ Phase 4: Close mouth\n✓ Phase 5: Open mouth for check\n✓ Phase 6: SWALLOW CHECK')) {
        completeSession();
    }
}

function completeSession() {
    console.log('🎉 Completing session...');
    
    // Hide current step
    document.getElementById(`step${state.currentStep}`).classList.remove('active');
    document.getElementById('stepComplete').style.display = 'block';
    
    // Populate completion summary
    const summary = document.getElementById('completionSummary');
    summary.innerHTML = `
        <h3 style="color: var(--primary-color); margin-bottom: 1.5rem; font-size: 1.25rem;">📋 Session Summary</h3>
        
        <div style="display: grid; gap: 1rem;">
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: white; border-radius: 8px; border-left: 4px solid #10b981;">
                <span style="font-size: 2rem;">✓</span>
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">Patient Information</div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary);">ID: ${state.patientId}</div>
                </div>
            </div>
            
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: white; border-radius: 8px; border-left: 4px solid #10b981;">
                <span style="font-size: 2rem;">✓</span>
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">Clinical Assessment</div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary);">5 questions answered</div>
                </div>
            </div>
            
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: white; border-radius: 8px; border-left: 4px solid #10b981;">
                <span style="font-size: 2rem;">✓</span>
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">Video Analysis</div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary);">Uploaded and processed successfully</div>
                </div>
            </div>
            
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: white; border-radius: 8px; border-left: 4px solid #10b981;">
                <span style="font-size: 2rem;">✓</span>
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">Medication Compliance</div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary);">6-phase protocol completed</div>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 2rem; padding: 1rem; background: #eff6ff; border-radius: 8px; border-left: 4px solid #3b82f6;">
            <div style="font-size: 0.875rem; color: #1e40af;">
                <strong>📅 Completed:</strong> ${new Date().toLocaleString()}<br>
                <strong>🔖 Reference ID:</strong> ${state.jobId || 'N/A'}
            </div>
        </div>
    `;
    
    // Clean up camera
    if (state.stream) {
        state.stream.getTracks().forEach(track => track.stop());
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOMINO Patient Portal initialized');
    console.log('📍 Direct Object Medication Intake Neuro Output');
    console.log('API Base URL:', API_BASE_URL);
    console.log('Proto URL:', PROTO_URL);
});
