"""
AWS Bedrock Service for Clinical Summary Generation
Using Claude 3 Haiku for cost-effective AI-generated insights
"""
from .bedrock_client import BedrockClient
from .prompt_builder import build_clinical_prompt
from .response_parser import parse_bedrock_response

__all__ = [
    'BedrockClient',
    'build_clinical_prompt',
    'parse_bedrock_response',
]
