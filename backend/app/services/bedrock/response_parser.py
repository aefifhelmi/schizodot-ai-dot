"""
Parse and validate AWS Bedrock responses
Handles Claude 3 output and converts to DynamoDB-compatible format
"""
import json
import re
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal

logger = logging.getLogger(__name__)


def parse_bedrock_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Bedrock Claude response and extract clinical summary
    
    Args:
        response: Raw response from Bedrock API
        
    Returns:
        Validated clinical summary dict
        
    Raises:
        ValueError: If response is invalid or missing required fields
    """
    # Extract content from Claude response
    content = response.get('content', [])
    if not content:
        raise ValueError("Empty response from Bedrock")
    
    # Get text from first content block
    text = content[0].get('text', '')
    if not text:
        raise ValueError("No text content in Bedrock response")
    
    logger.debug(f"Raw Bedrock response: {text[:200]}...")
    
    # Extract JSON from response
    json_text = extract_json_from_text(text)
    
    # Parse JSON
    try:
        summary = json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Bedrock: {str(e)}")
        logger.error(f"Problematic text: {json_text[:500]}")
        raise ValueError(f"Invalid JSON in Bedrock response: {str(e)}")
    
    # Validate and convert to DynamoDB format
    validated = validate_clinical_summary(summary)
    
    # Add usage metadata
    usage = response.get('usage', {})
    validated['_metadata'] = {
        'input_tokens': usage.get('input_tokens', 0),
        'output_tokens': usage.get('output_tokens', 0),
        'model': 'claude-3-haiku',
        'stop_reason': response.get('stop_reason', 'unknown')
    }
    
    logger.info(f"✅ Parsed clinical summary: {validated.get('risk_assessment')} risk")
    
    return validated


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text that may contain markdown or extra content
    
    Args:
        text: Raw text from LLM
        
    Returns:
        Extracted JSON string
    """
    # Try to find JSON in markdown code block
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # Try to find JSON in plain code block
    json_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        potential_json = json_match.group(1).strip()
        if potential_json.startswith('{'):
            return potential_json
    
    # Try to find raw JSON (starts with { and ends with })
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # If no JSON structure found, return text as-is and let JSON parser fail
    return text.strip()


def validate_clinical_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and format clinical summary for DynamoDB
    
    Args:
        summary: Parsed summary dict from LLM
        
    Returns:
        Validated and formatted summary
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Required fields
    required_fields = [
        'emotional_state',
        'medication_adherence',
        'risk_assessment',
        'recommendations'
    ]
    
    # Check for missing fields
    missing_fields = [field for field in required_fields if field not in summary]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate risk_assessment
    risk = summary['risk_assessment'].lower().strip()
    if risk not in ['low', 'moderate', 'high']:
        logger.warning(f"Invalid risk_assessment: {risk}, defaulting to 'moderate'")
        summary['risk_assessment'] = 'moderate'
    else:
        summary['risk_assessment'] = risk
    
    # Ensure recommendations is a list
    if not isinstance(summary['recommendations'], list):
        if isinstance(summary['recommendations'], str):
            summary['recommendations'] = [summary['recommendations']]
        else:
            summary['recommendations'] = []
    
    # Ensure risk_factors is a list (optional field)
    if 'risk_factors' in summary:
        if not isinstance(summary['risk_factors'], list):
            if isinstance(summary['risk_factors'], str):
                summary['risk_factors'] = [summary['risk_factors']]
            else:
                summary['risk_factors'] = []
    else:
        summary['risk_factors'] = []
    
    # Validate and convert confidence to Decimal for DynamoDB
    if 'confidence' in summary:
        try:
            confidence = float(summary['confidence'])
            if not 0.0 <= confidence <= 1.0:
                logger.warning(f"Confidence {confidence} out of range, clamping")
                confidence = max(0.0, min(1.0, confidence))
            summary['confidence'] = Decimal(str(round(confidence, 2)))
        except (ValueError, TypeError):
            logger.warning("Invalid confidence value, defaulting to 0.80")
            summary['confidence'] = Decimal('0.80')
    else:
        summary['confidence'] = Decimal('0.80')
    
    # Ensure clinical_notes exists (optional)
    if 'clinical_notes' not in summary or not summary['clinical_notes']:
        summary['clinical_notes'] = "No additional notes."
    
    # Add generation metadata
    summary['generated_by'] = 'aws_bedrock_claude_3_haiku'
    summary['model_version'] = 'anthropic.claude-3-haiku-20240307-v1:0'
    
    # Truncate overly long fields (safety measure)
    max_lengths = {
        'emotional_state': 1000,
        'medication_adherence': 500,
        'clinical_notes': 1000
    }
    
    for field, max_len in max_lengths.items():
        if field in summary and len(summary[field]) > max_len:
            logger.warning(f"Truncating {field} from {len(summary[field])} to {max_len} chars")
            summary[field] = summary[field][:max_len] + "..."
    
    # Limit recommendations to 10 items
    if len(summary['recommendations']) > 10:
        logger.warning(f"Truncating recommendations from {len(summary['recommendations'])} to 10")
        summary['recommendations'] = summary['recommendations'][:10]
    
    # Limit risk_factors to 10 items
    if len(summary['risk_factors']) > 10:
        logger.warning(f"Truncating risk_factors from {len(summary['risk_factors'])} to 10")
        summary['risk_factors'] = summary['risk_factors'][:10]
    
    return summary


def format_for_dynamodb(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert summary to DynamoDB-compatible format
    
    Args:
        summary: Validated summary dict
        
    Returns:
        DynamoDB-compatible dict (all floats converted to Decimal)
    """
    dynamodb_summary = {}
    
    for key, value in summary.items():
        if isinstance(value, float):
            # Convert float to Decimal for DynamoDB
            dynamodb_summary[key] = Decimal(str(value))
        elif isinstance(value, dict):
            # Recursively convert nested dicts
            dynamodb_summary[key] = format_for_dynamodb(value)
        elif isinstance(value, list):
            # Convert list items if needed
            dynamodb_summary[key] = [
                Decimal(str(item)) if isinstance(item, float) else item
                for item in value
            ]
        else:
            dynamodb_summary[key] = value
    
    return dynamodb_summary
