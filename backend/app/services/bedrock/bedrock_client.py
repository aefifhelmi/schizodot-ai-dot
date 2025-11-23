"""
AWS Bedrock Client for Clinical Summary Generation
Uses Claude 3 Haiku for cost-effective MVP
Cost: ~$0.0007 per request
"""
import json
import logging
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger(__name__)


class BedrockClient:
    """
    AWS Bedrock client for generating clinical summaries using Claude 3 Haiku
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
        max_tokens: int = 1500,
        temperature: float = 0.7,
        timeout: int = 30
    ):
        """
        Initialize Bedrock client
        
        Args:
            region: AWS region (default: us-east-1)
            model_id: Claude model ID (default: Haiku)
            max_tokens: Maximum output tokens (default: 1500)
            temperature: Sampling temperature (default: 0.7)
            timeout: Request timeout in seconds (default: 30)
        """
        self.region = region
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        # Initialize Bedrock runtime client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region,
            config=boto3.session.Config(
                read_timeout=timeout,
                connect_timeout=10,
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )
        )
        
        logger.info(f"Bedrock client initialized: {model_id} in {region}")
    
    def generate_clinical_summary(
        self,
        emotion_data: Dict[str, Any],
        patient_id: str,
        transcript: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate clinical summary using Claude 3 Haiku
        
        Args:
            emotion_data: Dict containing audio_emotion, facial_emotion, compliance
            patient_id: Patient identifier
            transcript: Optional patient speech transcript from video
            max_tokens: Override default max tokens
            temperature: Override default temperature
            
        Returns:
            Dict containing clinical summary with all required fields
            
        Raises:
            Exception: If Bedrock API fails or response is invalid
        """
        from .prompt_builder import build_clinical_prompt
        from .response_parser import parse_bedrock_response
        
        # Build prompt with optional transcript
        prompt = build_clinical_prompt(emotion_data, patient_id, transcript)
        
        # Use provided or default values
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        logger.info(f"Generating clinical summary for patient {patient_id}")
        
        try:
            # Call Bedrock
            response = self._invoke_model(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Parse and validate response
            clinical_summary = parse_bedrock_response(response)
            
            logger.info(f"✅ Clinical summary generated for {patient_id}")
            
            return clinical_summary
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ThrottlingException':
                logger.error(f"Bedrock rate limit exceeded: {error_message}")
                raise Exception("Bedrock API rate limit exceeded. Please retry.")
            elif error_code == 'AccessDeniedException':
                logger.error(f"Bedrock access denied: {error_message}")
                raise Exception("Bedrock access denied. Check IAM permissions.")
            else:
                logger.error(f"Bedrock API error [{error_code}]: {error_message}")
                raise Exception(f"Bedrock API error: {error_message}")
                
        except Exception as e:
            logger.error(f"Failed to generate clinical summary: {str(e)}")
            raise
    
    def _invoke_model(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """
        Invoke Claude 3 Haiku via Bedrock Runtime API
        
        Args:
            prompt: Formatted clinical prompt
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            
        Returns:
            Raw response from Bedrock API
        """
        # Build request body for Claude 3
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        # Invoke model
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        # Log token usage for cost tracking
        usage = response_body.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        
        # Calculate cost (Haiku pricing: $0.25/1M input, $1.25/1M output)
        input_cost = (input_tokens / 1_000_000) * 0.25
        output_cost = (output_tokens / 1_000_000) * 1.25
        total_cost = input_cost + output_cost
        
        logger.info(
            f"Bedrock usage - Input: {input_tokens} tokens, "
            f"Output: {output_tokens} tokens, Cost: ${total_cost:.6f}"
        )
        
        return response_body
    
    def test_connection(self) -> bool:
        """
        Test Bedrock connection with a simple request
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self._invoke_model(
                prompt="Respond with 'OK' if you can hear me.",
                max_tokens=10,
                temperature=0.5
            )
            
            content = response.get('content', [])
            if content and 'OK' in content[0].get('text', ''):
                logger.info("✅ Bedrock connection test successful")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Bedrock connection test failed: {str(e)}")
            return False
