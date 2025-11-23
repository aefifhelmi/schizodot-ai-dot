# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SchizoDot Backend"
    ENV: str = "local"

    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "schizodot-backend-storage"
    DYNAMO_TABLE: str = "SchizodotUsers"
    DYNAMO_TABLE_JOBS: str = "SchizodotJobs"

    # AWS Bedrock
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_ENABLE: bool = False
    BEDROCK_MODEL_ID: str = "anthropic.claude-v2"
    
    # AWS Transcribe
    ENABLE_TRANSCRIPTION: bool = True
    AWS_TRANSCRIBE_REGION: str = "us-east-1"
    TRANSCRIBE_LANGUAGE_CODE: str = "ms-MY"
    TRANSCRIBE_OUTPUT_BUCKET: str = "schizodot-transcriptions"
    TRANSCRIBE_MAX_SPEAKERS: int = 2

    # Redis & Celery
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000"

    # Internal Services
    AI_PIPELINE_URL: str = "http://ai-pipeline:8001"
    EMOTION_SERVICE_URL: str = "http://localhost:8004"  # Emotion recognition service (local port 8004)
    OBJECT_DETECTION_SERVICE_URL: str = "http://pill-detection:8003"  # Pill detection service
    
    # Feature Flags for AI Services
    ENABLE_EMOTION_SERVICE: bool = True  # Toggle for emotion detection (NOW ENABLED)
    ENABLE_COMPLIANCE_SERVICE: bool = True  # Toggle for pill/medication detection (NOW ENABLED)
    ENABLE_MULTIMODAL_FUSION: bool = True  # Always enabled (rule-based)
    ENABLE_BEDROCK_SERVICE: bool = True  # Toggle for Bedrock LLM clinical summaries
    
    # Service Timeouts
    AI_SERVICE_TIMEOUT: int = 120  # seconds
    EMOTION_SERVICE_TIMEOUT: int = 120  # seconds for emotion detection
    OBJECT_DETECTION_TIMEOUT: int = 60  # seconds for pill detection
    S3_DOWNLOAD_TIMEOUT: int = 300  # seconds

    # pydantic v2 config:
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()
