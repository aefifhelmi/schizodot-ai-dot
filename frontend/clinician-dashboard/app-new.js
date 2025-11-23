// ============================================
// DOMINO Clinician Dashboard - Application Logic
// ============================================

// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// State
const state = {
    allPatients: [],
    currentPatientId: null,
    currentJobId: null,
    currentResults: null,
    activeTab: 'clinical'
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🏥 DOMINO Clinician Dashboard initialized');
    showNotification('System online', 'success');
    
    // Auto-load all patients
    loadAllPatients();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        console.log('🔄 Auto-refreshing patient data...');
        loadAllPatients(true); // Silent refresh
    }, 30000);
});

// ============================================
// Data Loading
// ============================================

async function loadAllPatients(silentRefresh = false) {
    if (!silentRefresh) {
        showLoading();
    }
    
    try {
        console.log('📊 Loading all patients...');
        
        // Fetch all jobs
        const response = await fetch(`${API_BASE_URL}/jobs/`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch jobs: ${response.status}`);
        }
        
        const jobs = await response.json();
        console.log(`✅ Fetched ${jobs.length} jobs`);
        
        // Filter completed jobs with results
        const completedJobs = jobs
            .filter(j => j.status === 'completed' && j.results)
            .map(job => ({
                patient_id: job.patient_id,
                job_id: job.job_id,
                analyzed_at: job.completed_at || job.updated_at,
                emotion_analysis: job.results?.emotion_analysis,
                clinical_summary: job.results?.clinical_summary,
                object_detection: job.results?.object_detection,
                compliance: job.results?.object_detection, // Handle both field names
                audio_emotion: job.results?.audio_emotion,
                facial_emotion: job.results?.facial_emotion,
                transcript: job.results?.transcript,
                multimodal_fusion: job.results?.multimodal_fusion,
                s3_key: job.s3_key,
                processing_time_seconds: job.results?.processing_time_seconds
            }))
            .sort((a, b) => new Date(b.analyzed_at) - new Date(a.analyzed_at)); // Sort by most recent
        
        state.allPatients = completedJobs;
        console.log(`✅ Found ${completedJobs.length} completed assessments`);
        
        // Update patient list sidebar
        updatePatientList(completedJobs);
        
        if (completedJobs.length > 0) {
            // Show first patient by default (only on initial load)
            if (!silentRefresh && !state.currentPatientId) {
                loadPatientData(completedJobs[0].patient_id);
            } else if (silentRefresh && state.currentPatientId) {
                // Refresh current patient if in silent mode
                const currentPatient = completedJobs.find(p => p.patient_id === state.currentPatientId);
                if (currentPatient) {
                    state.currentResults = currentPatient;
                    displayResults(currentPatient);
                }
            }
        } else {
            hideLoading();
            if (!silentRefresh) {
                showNotification('No patient assessments found', 'info');
            }
        }
        
    } catch (error) {
        console.error('❌ Error loading patients:', error);
        if (!silentRefresh) {
            showNotification('Failed to load patient data', 'error');
            hideLoading();
        }
    }
}

function updatePatientList(patients) {
    const listContainer = document.getElementById('patientList');
    const countEl = document.getElementById('patientCount');
    
    if (!listContainer) return;
    
    // Update count
    countEl.textContent = patients.length;
    
    // Clear and populate list
    listContainer.innerHTML = '';
    
    if (patients.length === 0) {
        listContainer.innerHTML = '<div class="list-loading">No patients found</div>';
        return;
    }
    
    patients.forEach(patient => {
        const riskLevel = patient.clinical_summary?.risk_assessment || 'unknown';
        const riskClass = `risk-${riskLevel.toLowerCase()}`;
        
        const item = document.createElement('div');
        item.className = 'patient-item';
        if (patient.patient_id === state.currentPatientId) {
            item.classList.add('active');
        }
        
        const timeAgo = getTimeAgo(patient.analyzed_at);
        
        item.innerHTML = `
            <div class="patient-info">
                <div class="patient-id">${patient.patient_id}</div>
                <div class="patient-time">${timeAgo}</div>
            </div>
            <div class="patient-risk ${riskClass}">${riskLevel}</div>
        `;
        
        item.onclick = () => {
            // Update active state
            document.querySelectorAll('.patient-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
            
            // Load patient data
            loadPatientData(patient.patient_id);
        };
        
        listContainer.appendChild(item);
    });
}

function getTimeAgo(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
}

async function loadPatientData(patientId) {
    if (!patientId) {
        patientId = document.getElementById('patientSearch').value.trim();
    }
    
    if (!patientId) {
        showNotification('Please enter a Patient ID', 'warning');
        return;
    }
    
    // Check if we already have this patient in memory
    const cachedPatient = state.allPatients.find(p => p.patient_id === patientId);
    
    if (cachedPatient) {
        console.log('📊 Loading patient from cache:', patientId);
        state.currentPatientId = patientId;
        state.currentJobId = cachedPatient.job_id;
        state.currentResults = cachedPatient;
        displayResults(cachedPatient);
        return;
    }
    
    // If not in cache, fetch from API
    showLoading();
    
    try {
        console.log('📊 Fetching patient from API:', patientId);
        
        // Fetch results for this patient
        const response = await fetch(`${API_BASE_URL}/results/${patientId}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('No assessment found for this patient');
            }
            throw new Error(`Failed to fetch data: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Results loaded:', data);
        
        // Get the first (most recent) result
        const results = data.results && data.results[0] ? data.results[0] : data;
        
        state.currentPatientId = patientId;
        state.currentJobId = results.job_id;
        state.currentResults = results;
        
        displayResults(results);
        showNotification('Data loaded successfully', 'success');
        
    } catch (error) {
        console.error('❌ Error loading data:', error);
        showNotification(error.message, 'error');
        hideLoading();
    }
}

// ============================================
// Display Functions
// ============================================

function showLoading() {
    document.getElementById('loadingPanel').style.display = 'flex';
    document.getElementById('resultsContainer').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loadingPanel').style.display = 'none';
}

function displayResults(results) {
    hideLoading();
    document.getElementById('resultsContainer').style.display = 'flex';
    
    // Update header
    document.getElementById('displayPatientId').textContent = state.currentPatientId;
    document.getElementById('displayJobId').textContent = state.currentJobId;
    document.getElementById('displayTimestamp').textContent = formatTimestamp(results.analyzed_at);
    
    // Update metrics
    displayEmotionMetrics(results.emotion_analysis);
    displayRiskAssessment(results.clinical_summary);
    displayComplianceScore(results.object_detection);
    
    // Update tabs
    displayClinicalTab(results.clinical_summary);
    displayEmotionTab(results.emotion_analysis);
    displayTranscriptTab(results.transcript);
    displayRawTab(results);
}

function displayEmotionMetrics(emotionAnalysis) {
    const audio = state.currentResults?.audio_emotion || emotionAnalysis?.audio_emotion || {};
    const facial = state.currentResults?.facial_emotion || emotionAnalysis?.facial_emotion || {};
    const fused = state.currentResults?.multimodal_fusion || emotionAnalysis?.multimodal_fusion;
    
    // Audio emotion
    const audioLabel = audio.label || audio.primary_emotion || audio.predicted_emotion || 'N/A';
    const audioConf = audio.confidence || 0;
    document.getElementById('audioEmotion').textContent = `${audioLabel} (${(audioConf * 100).toFixed(0)}%)`;
    
    // Facial emotion
    const facialLabel = facial.label || facial.primary_emotion || facial.predicted_emotion || 'N/A';
    const facialConf = facial.confidence || 0;
    document.getElementById('facialEmotion').textContent = `${facialLabel} (${(facialConf * 100).toFixed(0)}%)`;
    
    // Multimodal Fusion - if null, use average of audio and facial
    if (fused && fused !== null) {
        const fusedLabel = fused.label || fused.primary_emotion || fused.predicted_emotion || 'Unknown';
        document.getElementById('fusedEmotion').textContent = fusedLabel;
        
        let confidence = 0;
        if (fused.probs && fused.label) {
            confidence = (fused.probs[fused.label] * 100).toFixed(1);
        } else if (fused.confidence) {
            confidence = (fused.confidence * 100).toFixed(1);
        }
        document.getElementById('fusedConfidence').textContent = `${confidence}%`;
    } else {
        // Multimodal is null - compute from audio and facial
        const avgConf = ((audioConf + facialConf) / 2 * 100).toFixed(1);
        
        // Determine dominant emotion from audio and facial
        const dominantEmotion = audioConf >= facialConf ? audioLabel : facialLabel;
        
        document.getElementById('fusedEmotion').textContent = dominantEmotion;
        document.getElementById('fusedConfidence').textContent = `${avgConf}% (Computed)`;
    }
}

function displayRiskAssessment(clinicalSummary) {
    if (!clinicalSummary) {
        document.getElementById('riskLevel').textContent = 'N/A';
        return;
    }
    
    const riskLevel = clinicalSummary.risk_assessment || 'Unknown';
    document.getElementById('riskLevel').textContent = riskLevel;
    
    // Set risk indicator width
    const indicator = document.getElementById('riskIndicator').querySelector('.indicator-bar');
    const riskMap = {
        'low': 25,
        'moderate': 50,
        'high': 75,
        'severe': 100
    };
    const width = riskMap[riskLevel.toLowerCase()] || 0;
    indicator.style.width = `${width}%`;
    
    // Display risk factors
    const factorsContainer = document.getElementById('riskFactors');
    factorsContainer.innerHTML = '';
    
    if (clinicalSummary.recommendations) {
        clinicalSummary.recommendations.slice(0, 3).forEach(rec => {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.textContent = rec.substring(0, 20) + '...';
            factorsContainer.appendChild(tag);
        });
    }
}

function displayComplianceScore(objectDetection) {
    // Handle both object_detection and compliance fields
    const compliance = objectDetection || state.currentResults?.compliance || state.currentResults?.object_detection;
    
    if (!compliance) {
        document.getElementById('complianceScore').textContent = 'PENDING';
        document.getElementById('protocolStatus').textContent = 'Not Started';
        document.getElementById('complianceFill').style.width = '0%';
        return;
    }
    
    // Get compliance score and status
    const score = compliance.compliance_score || compliance.score || 0;
    const status = compliance.verification_status || compliance.status || 'unknown';
    const isCompliant = status === 'compliant' || status === 'verified' || compliance.protocol_completed;
    
    // Display score as percentage
    document.getElementById('complianceScore').textContent = `${(score * 100).toFixed(0)}%`;
    
    // Display status
    if (isCompliant) {
        document.getElementById('protocolStatus').textContent = 'Verified';
        document.getElementById('complianceFill').style.width = `${score * 100}%`;
    } else if (compliance.pill_detected) {
        document.getElementById('protocolStatus').textContent = 'Detected';
        document.getElementById('complianceFill').style.width = `${score * 100}%`;
    } else {
        document.getElementById('protocolStatus').textContent = 'In Progress';
        document.getElementById('complianceFill').style.width = '25%';
    }
    
    // Show note if it's stub data
    if (compliance.note && compliance.status === 'stub') {
        document.getElementById('protocolStatus').textContent += ' (Stub)';
    }
}

// ============================================
// Tab Display Functions
// ============================================

function displayClinicalTab(clinicalSummary) {
    const summaryEl = document.getElementById('clinicalSummary');
    const recsContainer = document.getElementById('recommendations');
    
    if (!clinicalSummary) {
        summaryEl.innerHTML = '<p class="text-muted">No clinical summary available</p>';
        recsContainer.innerHTML = '<p class="text-muted">No recommendations available</p>';
        return;
    }
    
    // Build comprehensive clinical summary
    let summaryHtml = '';
    
    // Emotional State
    if (clinicalSummary.emotional_state) {
        summaryHtml += `<div class="summary-section">
            <h4 style="color: var(--cyan); margin-bottom: 10px;">Emotional State</h4>
            <p>${clinicalSummary.emotional_state}</p>
        </div>`;
    }
    
    // Medication Adherence
    if (clinicalSummary.medication_adherence) {
        summaryHtml += `<div class="summary-section" style="margin-top: 20px;">
            <h4 style="color: var(--cyan); margin-bottom: 10px;">Medication Adherence</h4>
            <p>${clinicalSummary.medication_adherence}</p>
        </div>`;
    }
    
    // General Summary (if no specific fields)
    if (!summaryHtml && (clinicalSummary.summary || clinicalSummary.clinical_assessment)) {
        summaryHtml = `<p>${clinicalSummary.summary || clinicalSummary.clinical_assessment}</p>`;
    }
    
    summaryEl.innerHTML = summaryHtml || '<p class="text-muted">No clinical summary available</p>';
    
    // Recommendations
    recsContainer.innerHTML = '';
    
    if (clinicalSummary.recommendations && clinicalSummary.recommendations.length > 0) {
        clinicalSummary.recommendations.forEach((rec, index) => {
            const item = document.createElement('div');
            item.className = 'recommendation-item';
            item.textContent = `${index + 1}. ${rec}`;
            recsContainer.appendChild(item);
        });
    } else {
        recsContainer.innerHTML = '<p class="text-muted">No specific recommendations</p>';
    }
}

function displayEmotionTab(emotionAnalysis) {
    if (!emotionAnalysis) {
        document.getElementById('audioEmotionData').innerHTML = '<p class="text-muted">No data</p>';
        document.getElementById('facialEmotionData').innerHTML = '<p class="text-muted">No data</p>';
        document.getElementById('fusedEmotionData').innerHTML = '<p class="text-muted">No data</p>';
        return;
    }
    
    // Audio emotion
    const audio = emotionAnalysis.audio_emotion || {};
    const audioProbs = audio.probs || audio.all_emotions || {};
    document.getElementById('audioEmotionData').innerHTML = renderEmotionBars(audioProbs);
    
    // Facial emotion
    const facial = emotionAnalysis.facial_emotion || {};
    const facialProbs = facial.probs || facial.all_emotions || {};
    document.getElementById('facialEmotionData').innerHTML = renderEmotionBars(facialProbs);
    
    // Fused emotion
    const fused = emotionAnalysis.multimodal_fusion || state.currentResults?.multimodal_fusion || {};
    const fusedProbs = fused.probs || fused.all_emotions || {};
    document.getElementById('fusedEmotionData').innerHTML = renderEmotionBars(fusedProbs);
}

function renderEmotionBars(probs) {
    const emotions = Object.entries(probs).sort((a, b) => b[1] - a[1]);
    
    if (emotions.length === 0) {
        return '<p class="text-muted">No emotion data</p>';
    }
    
    return emotions.map(([emotion, prob]) => `
        <div class="emotion-bar">
            <div class="emotion-label">${emotion}</div>
            <div class="emotion-bar-bg">
                <div class="emotion-bar-fill" style="width: ${prob * 100}%">
                    <span class="emotion-value">${(prob * 100).toFixed(1)}%</span>
                </div>
            </div>
        </div>
    `).join('');
}

function displayTranscriptTab(transcript) {
    const transcriptEl = document.getElementById('transcriptText');
    
    if (!transcript) {
        transcriptEl.textContent = 'No transcript available';
        return;
    }
    
    // Handle different transcript formats
    const text = typeof transcript === 'string' ? transcript : transcript.text || JSON.stringify(transcript, null, 2);
    transcriptEl.textContent = text;
}

function displayRawTab(results) {
    const rawDataEl = document.getElementById('rawDataDisplay');
    rawDataEl.textContent = JSON.stringify(results, null, 2);
}

// ============================================
// Tab Switching
// ============================================

function switchAnalysisTab(tabName) {
    state.activeTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-item').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        }
    });
    
    // Update tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    const activePanel = document.getElementById(`${tabName}Tab`);
    if (activePanel) {
        activePanel.classList.add('active');
    }
}

// ============================================
// Utility Functions
// ============================================

function refreshData() {
    console.log('🔄 Refreshing all patient data...');
    loadAllPatients();
}

function toggleView() {
    // Placeholder for view toggle functionality
    showNotification('View toggle - coming soon', 'info');
}

function filterPatients() {
    // Placeholder for filtering - currently loads single patient
    const input = document.getElementById('patientSearch').value;
    console.log('Filter:', input);
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return timestamp;
    }
}

// ============================================
// Notifications
// ============================================

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationStack');
    
    const colors = {
        success: 'var(--success)',
        error: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--cyan)'
    };
    
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.style.borderColor = colors[type] || colors.info;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: ${colors[type]};"></div>
            <span style="font-family: var(--font-mono); font-size: 0.875rem;">${message}</span>
        </div>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// ============================================
// Keyboard Shortcuts
// ============================================

document.addEventListener('keydown', (e) => {
    // Enter in search box loads data
    if (e.key === 'Enter' && document.activeElement.id === 'patientSearch') {
        loadPatientData();
    }
    
    // R key refreshes
    if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
        if (document.activeElement.tagName !== 'INPUT') {
            refreshData();
        }
    }
});

// ============================================
// Connection Status
// ============================================

async function checkConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/`, { method: 'HEAD' });
        document.getElementById('connectionStatus').textContent = response.ok ? 'Connected' : 'Error';
    } catch (e) {
        document.getElementById('connectionStatus').textContent = 'Offline';
    }
}

// Check connection every 30 seconds
setInterval(checkConnection, 30000);
checkConnection();

// Export for debugging
window.DOMINO_CLINICIAN = {
    state,
    loadPatientData,
    refreshData
};
