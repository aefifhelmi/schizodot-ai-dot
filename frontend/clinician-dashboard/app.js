// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// State
const state = {
    allResults: [],
    filteredResults: [],
    currentFilter: 'all',
    patientIds: []
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🏥 DOMINO Clinician Dashboard initialized');
    loadAllData();
    
    // Auto-refresh every 30 seconds
    setInterval(refreshData, 30000);
});

// Load all patient data
async function loadAllData() {
    console.log('📊 Loading all patient data from backend...');
    
    try {
        // Fetch all jobs from the new /api/v1/jobs/ endpoint
        const jobsResponse = await fetch(`${API_BASE_URL}/jobs/`);
        
        if (!jobsResponse.ok) {
            throw new Error(`HTTP ${jobsResponse.status}: ${jobsResponse.statusText}`);
        }
        
        const jobs = await jobsResponse.json();
        console.log(`✅ Fetched ${jobs.length} jobs from backend`);
        
        if (!Array.isArray(jobs)) {
            throw new Error('Invalid response format from backend');
        }
        
        // Filter for completed jobs only
        const completedJobs = jobs.filter(j => j.status === 'completed');
        console.log(`✅ Found ${completedJobs.length} completed jobs`);
        
        // Extract results from completed jobs
        const allResults = completedJobs
            .filter(job => job.results) // Only jobs with results
            .map(job => ({
                job_id: job.job_id,
                patient_id: job.patient_id,
                s3_key: job.s3_key,
                analyzed_at: job.completed_at || job.updated_at,
                status: job.status,
                processing_time_seconds: calculateProcessingTime(job),
                // Extract results
                audio_emotion: job.results?.emotion_analysis?.audio_emotion,
                facial_emotion: job.results?.emotion_analysis?.facial_emotion,
                multimodal_fusion: job.results?.emotion_analysis?.multimodal_fusion,
                compliance: job.results?.object_detection,
                clinical_summary: job.results?.clinical_summary,
                transcript: job.results?.transcript
            }));
        
        state.allResults = allResults;
        state.filteredResults = allResults;
        
        console.log(`✅ Loaded ${allResults.length} results from ${new Set(allResults.map(r => r.patient_id)).size} unique patients`);
        
        if (allResults.length === 0) {
            console.warn('⚠️ No completed patient sessions found.');
            showError('No patient data found. Patients need to complete assessment sessions first.');
        } else {
            updateDashboard();
            renderTable();
        }
        
    } catch (error) {
        console.error('❌ Error loading data:', error);
        showError(`Failed to load patient data: ${error.message}. Check that backend is running on port 8000.`);
    }
}

// Helper to calculate processing time
function calculateProcessingTime(job) {
    if (job.started_at && job.completed_at) {
        const start = new Date(job.started_at);
        const end = new Date(job.completed_at);
        return (end - start) / 1000; // Convert to seconds
    }
    return null;
}

// Refresh data
function refreshData() {
    console.log('🔄 Refreshing data...');
    loadAllData();
}

// Update dashboard stats
function updateDashboard() {
    const results = state.allResults;
    
    // Total patients (unique patient IDs)
    const uniquePatients = new Set(results.map(r => r.patient_id || r.user_id));
    document.getElementById('totalPatients').textContent = uniquePatients.size;
    
    // Sessions today
    const today = new Date().toDateString();
    const sessionsToday = results.filter(r => {
        const resultDate = r.analyzed_at ? new Date(r.analyzed_at).toDateString() : '';
        return resultDate === today;
    }).length;
    document.getElementById('sessionsToday').textContent = sessionsToday;
    
    // Pending reviews (completed but not reviewed)
    const pending = results.filter(r => r.status === 'completed').length;
    document.getElementById('pendingReviews').textContent = pending;
    
    // High risk alerts
    const highRisk = results.filter(r => {
        const riskLevel = getRiskLevel(r);
        return riskLevel === 'high';
    }).length;
    document.getElementById('highRiskAlerts').textContent = highRisk;
}

// Get risk level from result
function getRiskLevel(result) {
    if (!result.clinical_summary) return 'low';
    
    const summary = result.clinical_summary;
    
    // Check if risk_assessment exists
    if (summary.risk_assessment) {
        return summary.risk_assessment.toLowerCase();
    }
    
    // Fallback: analyze text for risk indicators
    const summaryText = JSON.stringify(summary).toLowerCase();
    if (summaryText.includes('high risk') || summaryText.includes('severe')) {
        return 'high';
    } else if (summaryText.includes('moderate') || summaryText.includes('concern')) {
        return 'moderate';
    }
    return 'low';
}

// Render results table
function renderTable() {
    const tbody = document.getElementById('resultsTableBody');
    const results = state.filteredResults;
    
    if (results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">No patient sessions found.</td></tr>';
        return;
    }
    
    tbody.innerHTML = results.map(result => {
        const patientId = result.patient_id || 'N/A';
        const jobId = result.job_id || 'N/A';
        const date = result.analyzed_at ? new Date(result.analyzed_at).toLocaleString() : 'N/A';
        const status = 'completed'; // Results endpoint only returns completed jobs
        const riskLevel = getRiskLevel(result);
        const compliance = getComplianceStatus(result);
        
        return `
            <tr>
                <td><strong>${patientId}</strong></td>
                <td><code style="font-size: 0.8125rem;">${jobId.substring(0, 16)}...</code></td>
                <td>${date}</td>
                <td><span class="status-badge status-${status}">${status.toUpperCase()}</span></td>
                <td><span class="risk-badge risk-${riskLevel}">${riskLevel.toUpperCase()}</span></td>
                <td>${compliance}</td>
                <td>
                    <button class="action-btn" onclick='viewDetails(${JSON.stringify(result).replace(/'/g, "&#39;")})'>
                        View Details
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// Get compliance status
function getComplianceStatus(result) {
    if (!result.compliance) return 'N/A';
    
    const compliance = result.compliance;
    
    if (compliance.compliance_score !== undefined) {
        const score = parseFloat(compliance.compliance_score);
        if (score >= 80) return `✅ ${score}%`;
        if (score >= 60) return `⚠️ ${score}%`;
        return `❌ ${score}%`;
    }
    
    if (compliance.protocol_status === 'PASSED') return '✅ Compliant';
    if (compliance.protocol_status === 'FAILED') return '❌ Failed';
    
    return 'N/A';
}

// Filter results
function filterByStatus(status) {
    state.currentFilter = status;
    
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    applyFilters();
}

// Apply all filters
function applyFilters() {
    let results = state.allResults;
    
    // Filter by status
    if (state.currentFilter !== 'all') {
        results = results.filter(r => r.status === state.currentFilter);
    }
    
    // Filter by search term
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    if (searchTerm) {
        results = results.filter(r => {
            const patientId = (r.patient_id || r.user_id || '').toLowerCase();
            const jobId = (r.job_id || '').toLowerCase();
            const date = (r.analyzed_at || '').toLowerCase();
            
            return patientId.includes(searchTerm) || 
                   jobId.includes(searchTerm) || 
                   date.includes(searchTerm);
        });
    }
    
    state.filteredResults = results;
    renderTable();
}

// Filter results on search
function filterResults() {
    applyFilters();
}

// View details modal
function viewDetails(result) {
    console.log('📋 Viewing details for:', result);
    
    const modal = document.getElementById('detailModal');
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('modalTitle');
    
    const patientId = result.patient_id || result.user_id || 'N/A';
    modalTitle.textContent = `Session Details - ${patientId}`;
    
    modalBody.innerHTML = `
        ${generatePatientInfoSection(result)}
        ${generateEmotionAnalysisSection(result)}
        ${generateTranscriptSection(result)}
        ${generateClinicalSummarySection(result)}
        ${generateComplianceSection(result)}
        ${generateRawDataSection(result)}
    `;
    
    modal.classList.add('active');
}

// Generate Patient Info Section
function generatePatientInfoSection(result) {
    return `
        <div class="detail-section">
            <h3>👤 Patient Information</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Patient ID</span>
                    <span class="detail-value">${result.patient_id || result.user_id || 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Job ID</span>
                    <span class="detail-value">${result.job_id || 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Analysis Date</span>
                    <span class="detail-value">${result.analyzed_at ? new Date(result.analyzed_at).toLocaleString() : 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Status</span>
                    <span class="detail-value"><span class="status-badge status-${result.status}">${result.status}</span></span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Processing Time</span>
                    <span class="detail-value">${result.processing_time_seconds ? parseFloat(result.processing_time_seconds).toFixed(1) + 's' : 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">S3 Key</span>
                    <span class="detail-value" style="font-size: 0.75rem; word-break: break-all;">${result.s3_key || 'N/A'}</span>
                </div>
            </div>
        </div>
    `;
}

// Generate Emotion Analysis Section
function generateEmotionAnalysisSection(result) {
    if (!result.audio_emotion && !result.facial_emotion) {
        return `
            <div class="detail-section">
                <h3>😊 Emotion Analysis</h3>
                <p style="color: var(--text-secondary);">No emotion analysis data available.</p>
            </div>
        `;
    }
    
    const audioEmotion = result.audio_emotion || {};
    const facialEmotion = result.facial_emotion || {};
    
    return `
        <div class="detail-section">
            <h3>😊 Emotion Analysis</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">🎤 Audio Emotion</span>
                    <span class="detail-value">${audioEmotion.primary_emotion || 'N/A'} (${audioEmotion.confidence ? (audioEmotion.confidence * 100).toFixed(1) + '%' : 'N/A'})</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">👤 Facial Emotion</span>
                    <span class="detail-value">${facialEmotion.primary_emotion || 'N/A'} (${facialEmotion.confidence ? (facialEmotion.confidence * 100).toFixed(1) + '%' : 'N/A'})</span>
                </div>
            </div>
            ${audioEmotion.all_emotions ? `
                <div style="margin-top: 1rem;">
                    <div class="detail-label" style="margin-bottom: 0.5rem;">Audio Emotion Scores:</div>
                    <div class="json-viewer">
                        <pre>${JSON.stringify(audioEmotion.all_emotions, null, 2)}</pre>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

// Generate Transcript Section
function generateTranscriptSection(result) {
    // Transcript might be in audio_emotion object
    const transcript = result.transcript || (result.audio_emotion && result.audio_emotion.transcript) || null;
    
    if (!transcript) {
        return `
            <div class="detail-section">
                <h3>📝 Transcript</h3>
                <p style="color: var(--text-secondary);">No transcript available.</p>
            </div>
        `;
    }
    
    const transcriptText = typeof transcript === 'string' ? transcript : (transcript.transcript || transcript.text || 'No text available');
    
    return `
        <div class="detail-section">
            <h3>📝 Transcript</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Language</span>
                    <span class="detail-value">${transcript.language_code || 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Word Count</span>
                    <span class="detail-value">${transcript.word_count || 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Confidence</span>
                    <span class="detail-value">${transcript.confidence ? (transcript.confidence * 100).toFixed(1) + '%' : 'N/A'}</span>
                </div>
            </div>
            <div style="margin-top: 1rem;">
                <div class="detail-label" style="margin-bottom: 0.5rem;">Transcript Text:</div>
                <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid var(--primary-color);">
                    ${transcriptText}
                </div>
            </div>
        </div>
    `;
}

// Generate Clinical Summary Section (LLM Analysis)
function generateClinicalSummarySection(result) {
    if (!result.clinical_summary) {
        return `
            <div class="detail-section">
                <h3>🏥 Clinical Summary (LLM Analysis)</h3>
                <p style="color: var(--text-secondary);">No clinical summary available.</p>
            </div>
        `;
    }
    
    const summary = result.clinical_summary;
    
    return `
        <div class="detail-section">
            <h3>🏥 Clinical Summary (LLM Analysis)</h3>
            
            ${summary.emotional_state ? `
                <div style="margin-bottom: 1rem;">
                    <div class="detail-label" style="margin-bottom: 0.5rem;">Emotional State:</div>
                    <div style="background: #fef3c7; padding: 1rem; border-radius: 8px; border-left: 4px solid #f59e0b;">
                        ${summary.emotional_state}
                    </div>
                </div>
            ` : ''}
            
            ${summary.verbal_content_analysis ? `
                <div style="margin-bottom: 1rem;">
                    <div class="detail-label" style="margin-bottom: 0.5rem;">Verbal Content Analysis:</div>
                    <div style="background: #e0e7ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #6366f1;">
                        ${summary.verbal_content_analysis}
                    </div>
                </div>
            ` : ''}
            
            ${summary.medication_adherence ? `
                <div style="margin-bottom: 1rem;">
                    <div class="detail-label" style="margin-bottom: 0.5rem;">Medication Adherence:</div>
                    <div style="background: #d1fae5; padding: 1rem; border-radius: 8px; border-left: 4px solid #10b981;">
                        ${summary.medication_adherence}
                    </div>
                </div>
            ` : ''}
            
            <div class="detail-grid">
                ${summary.risk_assessment ? `
                    <div class="detail-item">
                        <span class="detail-label">Risk Assessment</span>
                        <span class="detail-value"><span class="risk-badge risk-${summary.risk_assessment.toLowerCase()}">${summary.risk_assessment.toUpperCase()}</span></span>
                    </div>
                ` : ''}
            </div>
            
            ${summary.recommendations && Array.isArray(summary.recommendations) ? `
                <div style="margin-top: 1rem;">
                    <div class="detail-label" style="margin-bottom: 0.5rem;">Recommendations:</div>
                    <ul style="padding-left: 1.5rem; margin: 0;">
                        ${summary.recommendations.map(rec => `<li style="margin: 0.5rem 0;">${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

// Generate Compliance Section
function generateComplianceSection(result) {
    if (!result.compliance) {
        return `
            <div class="detail-section">
                <h3>💊 Medication Compliance</h3>
                <p style="color: var(--text-secondary);">No compliance data available.</p>
            </div>
        `;
    }
    
    const detection = result.compliance;
    
    return `
        <div class="detail-section">
            <h3>💊 Medication Compliance</h3>
            <div class="detail-grid">
                ${detection.compliance_score !== undefined ? `
                    <div class="detail-item">
                        <span class="detail-label">Compliance Score</span>
                        <span class="detail-value">${parseFloat(detection.compliance_score).toFixed(1)}%</span>
                    </div>
                ` : ''}
                ${detection.protocol_status ? `
                    <div class="detail-item">
                        <span class="detail-label">Protocol Status</span>
                        <span class="detail-value">${detection.protocol_status}</span>
                    </div>
                ` : ''}
                ${detection.phases_completed !== undefined ? `
                    <div class="detail-item">
                        <span class="detail-label">Phases Completed</span>
                        <span class="detail-value">${detection.phases_completed} / 6</span>
                    </div>
                ` : ''}
            </div>
            <div style="margin-top: 1rem;">
                <div class="detail-label" style="margin-bottom: 0.5rem;">Full Detection Data:</div>
                <div class="json-viewer">
                    <pre>${JSON.stringify(detection, null, 2)}</pre>
                </div>
            </div>
        </div>
    `;
}

// Generate Raw Data Section
function generateRawDataSection(result) {
    return `
        <div class="detail-section">
            <h3>🔍 Raw Data (JSON)</h3>
            <div class="json-viewer">
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </div>
        </div>
    `;
}

// Close modal
function closeModal() {
    document.getElementById('detailModal').classList.remove('active');
}

// Export data
function exportData() {
    const results = state.filteredResults;
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `domino-patient-data-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    
    console.log('✅ Data exported');
}

// Show error message
function showError(message) {
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="no-data" style="color: var(--danger-color);">
                ⚠️ ${message}
            </td>
        </tr>
    `;
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('detailModal');
    if (event.target === modal) {
        closeModal();
    }
}
