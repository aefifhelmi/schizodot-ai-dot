"""
AWS Transcribe Client for Video Transcription
Handles asynchronous transcription jobs with S3 integration
Cost: ~$0.024 per minute (standard), ~$0.015 per minute (batch)
"""
import json
import time
import logging
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class TranscribeClient:
    """
    AWS Transcribe client for converting speech to text
    Handles long videos with async processing
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        s3_bucket: str = None,
        language_code: str = "en-US",
        max_speakers: int = 2,
        output_bucket: str = None
    ):
        """
        Initialize Transcribe client
        
        Args:
            region: AWS region (default: us-east-1)
            s3_bucket: S3 bucket for audio uploads
            language_code: Language for transcription (default: en-US)
            max_speakers: Max speakers for diarization (default: 2)
            output_bucket: S3 bucket for transcription results
        """
        self.region = region
        self.s3_bucket = s3_bucket
        self.output_bucket = output_bucket or s3_bucket
        self.language_code = language_code
        self.max_speakers = max_speakers
        
        # Initialize AWS clients
        self.transcribe = boto3.client('transcribe', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        
        logger.info(f"Transcribe client initialized: {region}, bucket: {s3_bucket}")
    
    def transcribe_audio(
        self,
        audio_path: str,
        job_name: Optional[str] = None,
        wait_for_completion: bool = True,
        max_wait_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using AWS Transcribe
        
        Args:
            audio_path: Path to audio file (mp3, wav, mp4, etc.)
            job_name: Custom job name (auto-generated if None)
            wait_for_completion: Wait for job to complete (default: True)
            max_wait_seconds: Maximum wait time in seconds (default: 300)
            
        Returns:
            Dict containing transcript and metadata
            
        Raises:
            Exception: If transcription fails
        """
        # Generate unique job name
        if not job_name:
            job_name = f"transcribe-{uuid.uuid4().hex[:12]}"
        
        logger.info(f"Starting transcription job: {job_name}")
        
        try:
            # Step 1: Upload audio to S3
            s3_uri = self._upload_to_s3(audio_path, job_name)
            
            # Step 2: Start transcription job
            self._start_transcription_job(job_name, s3_uri)
            
            # Step 3: Wait for completion (if requested)
            if wait_for_completion:
                result = self._wait_for_job(job_name, max_wait_seconds)
                return result
            else:
                return {
                    'job_name': job_name,
                    'status': 'IN_PROGRESS',
                    'message': 'Transcription job started'
                }
                
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _upload_to_s3(self, audio_path: str, job_name: str) -> str:
        """Upload audio file to S3"""
        audio_file = Path(audio_path)
        s3_key = f"transcribe-inputs/{job_name}/{audio_file.name}"
        
        logger.info(f"Uploading audio to S3: s3://{self.s3_bucket}/{s3_key}")
        
        try:
            self.s3.upload_file(
                str(audio_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs={'ContentType': 'audio/mpeg'}
            )
            
            s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
            logger.info(f"✅ Upload complete: {s3_uri}")
            return s3_uri
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise Exception(f"Failed to upload audio to S3: {str(e)}")
    
    def _start_transcription_job(self, job_name: str, media_uri: str) -> None:
        """Start AWS Transcribe job"""
        logger.info(f"Starting Transcribe job: {job_name}")
        
        # Job settings
        settings = {
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': self.max_speakers,
            'ChannelIdentification': False,
        }
        
        try:
            self.transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': media_uri},
                MediaFormat='mp3',  # Auto-detected by AWS
                LanguageCode=self.language_code,
                Settings=settings,
                OutputBucketName=self.output_bucket
            )
            
            logger.info(f"✅ Transcription job started: {job_name}")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ConflictException':
                logger.warning(f"Job {job_name} already exists, checking status...")
            else:
                logger.error(f"Failed to start transcription: {e}")
                raise Exception(f"Transcribe job failed: {str(e)}")
    
    def _wait_for_job(self, job_name: str, max_wait_seconds: int) -> Dict[str, Any]:
        """Wait for transcription job to complete"""
        logger.info(f"Waiting for job {job_name} to complete (max {max_wait_seconds}s)...")
        
        start_time = time.time()
        poll_interval = 5  # seconds
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait_seconds:
                raise TimeoutError(f"Transcription timeout after {max_wait_seconds}s")
            
            # Check job status
            status = self._get_job_status(job_name)
            
            if status == 'COMPLETED':
                logger.info(f"✅ Transcription complete: {job_name}")
                return self._get_transcript(job_name)
            
            elif status == 'FAILED':
                raise Exception(f"Transcription job failed: {job_name}")
            
            elif status in ['IN_PROGRESS', 'QUEUED']:
                logger.debug(f"Job {status}, waiting... ({elapsed:.0f}s elapsed)")
                time.sleep(poll_interval)
            
            else:
                raise Exception(f"Unknown job status: {status}")
    
    def _get_job_status(self, job_name: str) -> str:
        """Get transcription job status"""
        try:
            response = self.transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )
            return response['TranscriptionJob']['TranscriptionJobStatus']
        except ClientError as e:
            logger.error(f"Failed to get job status: {e}")
            raise
    
    def _get_transcript(self, job_name: str) -> Dict[str, Any]:
        """Retrieve and parse completed transcript"""
        try:
            # Get job details
            response = self.transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            job = response['TranscriptionJob']
            transcript_uri = job['Transcript']['TranscriptFileUri']
            
            # Download transcript JSON using boto3 (authenticated)
            logger.info(f"Downloading transcript from: {transcript_uri}")
            
            # Parse S3 URI to get bucket and key
            # Format: https://s3.region.amazonaws.com/bucket/key or s3://bucket/key
            if transcript_uri.startswith('s3://'):
                # s3://bucket/key format
                parts = transcript_uri[5:].split('/', 1)
                bucket = parts[0]
                key = parts[1]
            else:
                # https://s3.region.amazonaws.com/bucket/key format
                import re
                match = re.search(r's3[.-]([^.]+)\.amazonaws\.com/([^/]+)/(.+)', transcript_uri)
                if match:
                    bucket = match.group(2)
                    key = match.group(3)
                else:
                    # Try alternative format: https://bucket.s3.region.amazonaws.com/key
                    match = re.search(r'https://([^.]+)\.s3[.-]([^.]+)\.amazonaws\.com/(.+)', transcript_uri)
                    if match:
                        bucket = match.group(1)
                        key = match.group(3)
                    else:
                        raise Exception(f"Unable to parse S3 URI: {transcript_uri}")
            
            logger.info(f"Downloading from S3: bucket={bucket}, key={key}")
            
            # Download using boto3 with credentials
            response = self.s3.get_object(Bucket=bucket, Key=key)
            transcript_data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Parse transcript
            full_transcript = transcript_data['results']['transcripts'][0]['transcript']
            
            # Extract segments with timestamps and speakers
            segments = []
            if 'speaker_labels' in transcript_data['results']:
                speaker_labels = transcript_data['results']['speaker_labels']
                
                # Get all items (words) with their timestamps
                all_items = transcript_data['results'].get('items', [])
                
                for segment in speaker_labels.get('segments', []):
                    speaker = segment.get('speaker_label', 'Unknown')
                    start_time = float(segment.get('start_time', 0))
                    end_time = float(segment.get('end_time', 0))
                    
                    # Get items (words) for this segment
                    # Items in segment only have start_time and end_time, no content
                    # We need to match with main items list
                    segment_items = segment.get('items', [])
                    
                    # Collect words for this segment by matching timestamps
                    words = []
                    for seg_item in segment_items:
                        seg_start = float(seg_item.get('start_time', 0))
                        seg_end = float(seg_item.get('end_time', 0))
                        
                        # Find matching word in main items
                        for item in all_items:
                            if item.get('type') == 'pronunciation':
                                item_start = float(item.get('start_time', 0))
                                # Match by start time (with small tolerance)
                                if abs(item_start - seg_start) < 0.01:
                                    words.append(item.get('alternatives', [{}])[0].get('content', ''))
                                    break
                    
                    text = ' '.join(words) if words else ''
                    
                    if text:  # Only add segments with actual text
                        segments.append({
                            'speaker': speaker,
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text
                        })
            
            # Calculate duration and stats
            duration_seconds = float(job['MediaSampleRateHertz']) if 'MediaSampleRateHertz' in job else 0
            word_count = len(full_transcript.split())
            
            result = {
                'job_name': job_name,
                'status': 'COMPLETED',
                'transcript': full_transcript,
                'segments': segments,
                'language_code': job['LanguageCode'],
                'duration_seconds': duration_seconds,
                'word_count': word_count,
                'speaker_count': len(set(s['speaker'] for s in segments)) if segments else 1,
                'created_at': job['CreationTime'].isoformat(),
                'completed_at': job['CompletionTime'].isoformat()
            }
            
            logger.info(f"✅ Transcript retrieved: {word_count} words, {len(segments)} segments")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve transcript: {e}")
            raise Exception(f"Failed to get transcript: {str(e)}")
    
    def get_job_result(self, job_name: str) -> Dict[str, Any]:
        """
        Get result of previously started job
        
        Args:
            job_name: Transcription job name
            
        Returns:
            Job result with transcript if complete
        """
        status = self._get_job_status(job_name)
        
        if status == 'COMPLETED':
            return self._get_transcript(job_name)
        else:
            return {
                'job_name': job_name,
                'status': status,
                'message': f'Job is {status}'
            }
    
    def delete_job(self, job_name: str) -> bool:
        """
        Delete transcription job
        
        Args:
            job_name: Job to delete
            
        Returns:
            True if successful
        """
        try:
            self.transcribe.delete_transcription_job(
                TranscriptionJobName=job_name
            )
            logger.info(f"✅ Deleted transcription job: {job_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete job: {e}")
            return False
