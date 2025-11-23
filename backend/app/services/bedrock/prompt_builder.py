"""
Clinical Prompt Builder for AWS Bedrock
Optimized for Claude 3 Haiku - concise and structured
"""
import json
from typing import Dict, Any


# System prompt for clinical context
SYSTEM_CONTEXT = """You are an expert psychiatric AI assistant analyzing patient video data for mental health assessment.

Your role:
- Analyze multimodal emotion data (audio tone + facial expressions)
- Analyze patient speech transcript for verbal content and clinical indicators
- Generate professional clinical summaries for psychiatrists
- Assess risk levels based on emotional patterns and verbal content
- Provide evidence-based, actionable recommendations

Key considerations:
- Note emotional incongruence (mismatch between audio, facial, and verbal expressions)
- Cross-reference patient's words with their emotional state
- Flag concerning patterns (high anger, fear, sadness, or concerning verbal content)
- Detect risk indicators in speech (suicidal ideation, self-harm, substance use)
- Consider medication compliance evidence
- Be objective, clinical, and concise

Output: Valid JSON only, no markdown or extra text."""


def build_clinical_prompt(
    emotion_data: Dict[str, Any], 
    patient_id: str,
    transcript: str = None
) -> str:
    """
    Build structured clinical prompt optimized for Claude 3 Haiku
    
    Args:
        emotion_data: Dict with keys: audio_emotion, facial_emotion, compliance
        patient_id: Patient identifier
        transcript: Optional patient speech transcript from video
        
    Returns:
        Formatted prompt string for Bedrock API
    """
    # Extract emotion components
    audio = emotion_data.get('audio_emotion', {})
    face = emotion_data.get('facial_emotion', {})
    compliance = emotion_data.get('compliance', {})
    
    # Get primary emotions and confidence
    audio_primary = audio.get('primary_emotion', 'unknown')
    audio_confidence = audio.get('confidence', 0) * 100
    
    face_primary = face.get('primary_emotion', 'unknown')
    face_confidence = face.get('confidence', 0) * 100
    face_detected = face.get('face_detected', False)
    
    # Compliance status
    pill_detected = compliance.get('pill_detected', False)
    compliance_score = compliance.get('compliance_score', 0) * 100
    compliance_status = compliance.get('verification_status', 'unknown')
    
    # Format emotion distributions
    audio_emotions = json.dumps(audio.get('all_emotions', {}), indent=None)
    face_emotions = json.dumps(face.get('all_emotions', {}), indent=None) if face_detected else "N/A"
    
    # Detect emotional incongruence
    incongruence_note = ""
    if face_detected and audio_primary != face_primary:
        incongruence_note = f"\n⚠️ EMOTIONAL INCONGRUENCE: Audio shows '{audio_primary}' but face shows '{face_primary}'"
    
    # Format transcript section
    transcript_section = ""
    if transcript:
        # Truncate if too long (keep first 500 chars for context)
        transcript_display = transcript[:500] + "..." if len(transcript) > 500 else transcript
        word_count = len(transcript.split())
        transcript_section = f"""
PATIENT SPEECH TRANSCRIPT ({word_count} words):
"{transcript_display}"

⚠️ CRITICAL: Cross-reference this transcript with emotion data above. Note any incongruence between what the patient SAYS vs their emotional TONE and FACIAL expression.
"""
    
    # Build prompt
    prompt = f"""{SYSTEM_CONTEXT}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATIENT ANALYSIS REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PATIENT ID: {patient_id}

AUDIO EMOTION ANALYSIS:
• Primary: {audio_primary} ({audio_confidence:.1f}% confidence)
• Distribution: {audio_emotions}

FACIAL EMOTION ANALYSIS:
• Face Detected: {'Yes' if face_detected else 'No'}
• Primary: {face_primary} ({face_confidence:.1f}% confidence)
• Distribution: {face_emotions}{incongruence_note}

MEDICATION COMPLIANCE:
• Pill Detected: {'Yes' if pill_detected else 'No'}
• Compliance Score: {compliance_score:.1f}%
• Status: {compliance_status}
{transcript_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK: Generate a clinical summary in this EXACT JSON format:

{{
  "emotional_state": "2-3 sentence clinical narrative describing the patient's emotional state. Cross-reference what they SAY (transcript) with their emotional TONE (audio) and FACIAL expression. Note any incongruence or concerning patterns.",
  
  "verbal_content_analysis": "1-2 sentences analyzing key themes, concerns, or clinical indicators from patient's speech. Note medication mentions, symptom descriptions, or concerning language.",
  
  "medication_adherence": "1-2 sentences on medication compliance based on video evidence and verbal statements.",
  
  "risk_assessment": "low|moderate|high",
  
  "risk_factors": [
    "List 2-4 specific concerning patterns if risk is moderate/high",
    "Include both behavioral AND verbal indicators",
    "Examples: 'Elevated anger with aggressive language', 'Reports feeling hopeless', 'Emotional masking behavior'"
  ],
  
  "recommendations": [
    "3-4 specific, actionable clinical recommendations",
    "Each should be evidence-based and time-specific",
    "Consider both emotion data AND verbal content",
    "Examples: 'Schedule follow-up within 48 hours to address reported side effects', 'Assess for medication adjustment'"
  ],
  
  "clinical_notes": "1-2 sentences with additional observations about emotional patterns, verbal themes, potential triggers, or clinical significance.",
  
  "confidence": 0.85
}}

IMPORTANT:
- Respond with ONLY valid JSON
- No markdown code blocks (no ```json)
- No additional commentary
- Use exact field names above
- risk_assessment must be: low, moderate, or high
- confidence should be 0.0 to 1.0

RESPOND NOW:"""
    
    return prompt


def build_minimal_prompt(emotion_data: Dict[str, Any], patient_id: str) -> str:
    """
    Build ultra-minimal prompt for cost optimization (use if token budget tight)
    
    Args:
        emotion_data: Emotion analysis data
        patient_id: Patient ID
        
    Returns:
        Minimal prompt string
    """
    audio = emotion_data.get('audio_emotion', {})
    face = emotion_data.get('facial_emotion', {})
    compliance = emotion_data.get('compliance', {})
    
    prompt = f"""Psychiatric AI: Analyze patient {patient_id}

Audio: {audio.get('primary_emotion')} ({audio.get('confidence', 0)*100:.0f}%)
Face: {face.get('primary_emotion')} ({face.get('confidence', 0)*100:.0f}%)
Meds: {'Taken' if compliance.get('pill_detected') else 'Not taken'}

Generate JSON:
{{
  "emotional_state": "brief description",
  "medication_adherence": "assessment",
  "risk_assessment": "low|moderate|high",
  "risk_factors": ["if any"],
  "recommendations": ["3-4 items"],
  "clinical_notes": "notes",
  "confidence": 0.8
}}

JSON only:"""
    
    return prompt


def validate_prompt_length(prompt: str, max_tokens: int = 2000) -> bool:
    """
    Validate prompt is within token budget (rough estimate)
    
    Args:
        prompt: Prompt string
        max_tokens: Maximum allowed tokens
        
    Returns:
        True if within budget, False otherwise
    """
    # Rough estimate: 1 token ≈ 4 characters
    estimated_tokens = len(prompt) / 4
    
    if estimated_tokens > max_tokens:
        return False
    
    return True
