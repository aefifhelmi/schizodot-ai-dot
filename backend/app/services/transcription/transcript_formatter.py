"""
Transcript formatting utilities for LLM consumption
Formats AWS Transcribe output for clinical analysis
"""
import re
from typing import Dict, Any, List, Optional


def format_transcript_for_llm(
    transcript_data: Dict[str, Any],
    include_timestamps: bool = False,
    include_speakers: bool = True,
    max_length: Optional[int] = None
) -> str:
    """
    Format transcript for LLM input
    
    Args:
        transcript_data: Transcript dict from TranscribeClient
        include_timestamps: Include time markers (default: False)
        include_speakers: Include speaker labels (default: True)
        max_length: Maximum character length (truncate if longer)
        
    Returns:
        Formatted transcript string for LLM
    """
    # Get full transcript
    full_transcript = transcript_data.get('transcript', '')
    segments = transcript_data.get('segments', [])
    
    # If no segments, return full transcript
    if not segments or not include_speakers:
        formatted = full_transcript
    else:
        # Format with speakers
        formatted_segments = []
        
        for segment in segments:
            speaker = segment.get('speaker', 'Unknown')
            text = segment.get('text', '').strip()
            
            if not text:
                continue
            
            # Format based on options
            if include_timestamps:
                start_time = segment.get('start_time', 0)
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                time_str = f"[{minutes:02d}:{seconds:02d}]"
                line = f"{time_str} {speaker}: {text}"
            else:
                line = f"{speaker}: {text}"
            
            formatted_segments.append(line)
        
        formatted = '\n'.join(formatted_segments)
    
    # Clean up transcript
    formatted = clean_transcript(formatted)
    
    # Truncate if needed
    if max_length and len(formatted) > max_length:
        formatted = formatted[:max_length] + "... [transcript truncated]"
    
    return formatted


def clean_transcript(text: str) -> str:
    """
    Clean transcript text for LLM consumption
    
    Args:
        text: Raw transcript text
        
    Returns:
        Cleaned transcript
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove repeated words (common in speech)
    text = re.sub(r'\b(\w+)(\s+\1\b)+', r'\1', text, flags=re.IGNORECASE)
    
    # Fix common transcription artifacts
    text = text.replace('  ', ' ')
    text = text.replace(' .', '.')
    text = text.replace(' ,', ',')
    text = text.replace(' ?', '?')
    text = text.replace(' !', '!')
    
    # Capitalize first letter of sentences
    text = '. '.join(s.capitalize() for s in text.split('. '))
    
    return text.strip()


def extract_key_phrases(transcript: str) -> List[str]:
    """
    Extract key medical/emotional phrases from transcript
    
    Args:
        transcript: Transcript text
        
    Returns:
        List of key phrases
    """
    key_phrases = []
    
    # Medical terms and symptoms
    medical_terms = [
        r'feel(?:ing)?\s+(?:depressed|anxious|angry|sad|happy|frustrated)',
        r'(?:can\'t|cannot|unable to)\s+(?:sleep|eat|focus|concentrate)',
        r'(?:medication|medicine|pills?|drugs?)',
        r'side\s+effects?',
        r'(?:hurt|harm|kill)\s+(?:myself|themselves)',
        r'suicidal?\s+(?:thoughts?|ideation)',
        r'panic\s+attacks?',
        r'(?:hear|see)\s+(?:voices|things)',
        r'hallucinations?',
        r'mood\s+(?:swings?|changes?)',
    ]
    
    for pattern in medical_terms:
        matches = re.finditer(pattern, transcript, re.IGNORECASE)
        for match in matches:
            phrase = match.group(0)
            if phrase.lower() not in [p.lower() for p in key_phrases]:
                key_phrases.append(phrase)
    
    return key_phrases


def summarize_transcript(
    transcript_data: Dict[str, Any],
    max_words: int = 200
) -> str:
    """
    Create a brief summary of transcript for quick review
    
    Args:
        transcript_data: Transcript dict from TranscribeClient
        max_words: Maximum words in summary
        
    Returns:
        Brief summary string
    """
    full_transcript = transcript_data.get('transcript', '')
    word_count = transcript_data.get('word_count', 0)
    speaker_count = transcript_data.get('speaker_count', 1)
    duration = transcript_data.get('duration_seconds', 0)
    
    # Extract key phrases
    key_phrases = extract_key_phrases(full_transcript)
    
    # Get first portion of transcript
    words = full_transcript.split()
    preview = ' '.join(words[:max_words])
    
    if len(words) > max_words:
        preview += "..."
    
    summary = f"""
Transcript Summary:
- Duration: {duration:.0f} seconds
- Word Count: {word_count}
- Speakers: {speaker_count}
- Key Phrases: {', '.join(key_phrases[:5]) if key_phrases else 'None detected'}

Preview:
{preview}
""".strip()
    
    return summary


def format_for_clinical_prompt(transcript_data: Dict[str, Any]) -> str:
    """
    Format transcript specifically for clinical LLM prompt
    
    Args:
        transcript_data: Transcript dict from TranscribeClient
        
    Returns:
        Formatted string optimized for clinical analysis
    """
    full_transcript = transcript_data.get('transcript', '')
    key_phrases = extract_key_phrases(full_transcript)
    word_count = transcript_data.get('word_count', 0)
    
    # Format for LLM
    formatted = f"""PATIENT TRANSCRIPT ({word_count} words):
"{full_transcript}"

KEY CLINICAL PHRASES DETECTED:
{chr(10).join(f"- {phrase}" for phrase in key_phrases[:10]) if key_phrases else "- None"}
"""
    
    return formatted.strip()


def detect_concerning_content(transcript: str) -> Dict[str, Any]:
    """
    Detect concerning or high-risk content in transcript
    
    Args:
        transcript: Transcript text
        
    Returns:
        Dict with flags and detected phrases
    """
    concerns = {
        'suicide_risk': False,
        'self_harm_risk': False,
        'violence_risk': False,
        'substance_use': False,
        'detected_phrases': []
    }
    
    # Suicide/self-harm patterns
    suicide_patterns = [
        r'(?:want|going)\s+to\s+(?:kill|end)\s+(?:myself|my\s+life)',
        r'suicidal?\s+(?:thoughts?|ideation)',
        r'better\s+off\s+dead',
        r'no\s+reason\s+to\s+live',
    ]
    
    self_harm_patterns = [
        r'hurt(?:ing)?\s+myself',
        r'cut(?:ting)?\s+myself',
        r'self-harm',
    ]
    
    violence_patterns = [
        r'(?:want|going)\s+to\s+hurt\s+(?:someone|them|him|her)',
        r'kill\s+(?:someone|them|him|her)',
        r'violent\s+thoughts',
    ]
    
    substance_patterns = [
        r'(?:using|taking|drinking)\s+(?:drugs|alcohol|cocaine|heroin)',
        r'relapsed?',
        r'addiction',
    ]
    
    # Check for patterns
    for pattern in suicide_patterns:
        if re.search(pattern, transcript, re.IGNORECASE):
            concerns['suicide_risk'] = True
            match = re.search(pattern, transcript, re.IGNORECASE)
            concerns['detected_phrases'].append(match.group(0))
    
    for pattern in self_harm_patterns:
        if re.search(pattern, transcript, re.IGNORECASE):
            concerns['self_harm_risk'] = True
            match = re.search(pattern, transcript, re.IGNORECASE)
            concerns['detected_phrases'].append(match.group(0))
    
    for pattern in violence_patterns:
        if re.search(pattern, transcript, re.IGNORECASE):
            concerns['violence_risk'] = True
            match = re.search(pattern, transcript, re.IGNORECASE)
            concerns['detected_phrases'].append(match.group(0))
    
    for pattern in substance_patterns:
        if re.search(pattern, transcript, re.IGNORECASE):
            concerns['substance_use'] = True
            match = re.search(pattern, transcript, re.IGNORECASE)
            concerns['detected_phrases'].append(match.group(0))
    
    concerns['has_concerns'] = any([
        concerns['suicide_risk'],
        concerns['self_harm_risk'],
        concerns['violence_risk']
    ])
    
    return concerns
