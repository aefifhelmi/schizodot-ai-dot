"""
Audio extraction utilities for transcription
Extracts audio from video files using ffmpeg
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_audio_from_video(
    video_path: str,
    output_path: Optional[str] = None,
    audio_format: str = "mp3",
    audio_bitrate: str = "128k",
    sample_rate: int = 16000
) -> str:
    """
    Extract audio from video file using ffmpeg
    
    Args:
        video_path: Path to input video file
        output_path: Path for output audio (auto-generated if None)
        audio_format: Output audio format (mp3, wav, etc.)
        audio_bitrate: Audio bitrate for compression
        sample_rate: Audio sample rate in Hz
        
    Returns:
        Path to extracted audio file
        
    Raises:
        Exception: If extraction fails
    """
    video_file = Path(video_path)
    
    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Generate output path if not provided
    if not output_path:
        output_path = str(video_file.parent / f"{video_file.stem}_audio.{audio_format}")
    
    logger.info(f"Extracting audio from {video_file.name} -> {Path(output_path).name}")
    
    try:
        # FFmpeg command to extract audio
        command = [
            'ffmpeg',
            '-i', str(video_path),           # Input video
            '-vn',                            # No video
            '-acodec', 'libmp3lame' if audio_format == 'mp3' else 'pcm_s16le',  # Audio codec
            '-ab', audio_bitrate,             # Audio bitrate
            '-ar', str(sample_rate),          # Sample rate
            '-ac', '1',                       # Mono channel
            '-y',                             # Overwrite output
            str(output_path)
        ]
        
        # Run ffmpeg
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=120  # 2 minute timeout
        )
        
        # Verify output file exists
        if not Path(output_path).exists():
            raise Exception("Audio extraction failed: output file not created")
        
        # Get file size
        file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        
        logger.info(f"✅ Audio extracted: {Path(output_path).name} ({file_size_mb:.2f} MB)")
        
        return str(output_path)
        
    except subprocess.TimeoutExpired:
        logger.error("Audio extraction timeout (>120s)")
        raise Exception("Audio extraction timeout")
        
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('utf-8') if e.stderr else 'Unknown error'
        logger.error(f"FFmpeg error: {error_output}")
        raise Exception(f"Audio extraction failed: {error_output}")
        
    except Exception as e:
        logger.error(f"Unexpected error during audio extraction: {str(e)}")
        raise


def get_audio_duration(audio_path: str) -> float:
    """
    Get duration of audio file in seconds using ffprobe
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=10
        )
        
        duration = float(result.stdout.decode('utf-8').strip())
        return duration
        
    except Exception as e:
        logger.error(f"Failed to get audio duration: {e}")
        return 0.0


def validate_audio_file(audio_path: str) -> bool:
    """
    Validate that audio file is readable and has content
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        True if valid, False otherwise
    """
    audio_file = Path(audio_path)
    
    # Check file exists
    if not audio_file.exists():
        logger.error(f"Audio file does not exist: {audio_path}")
        return False
    
    # Check file size (should be > 1KB)
    file_size = audio_file.stat().st_size
    if file_size < 1024:
        logger.error(f"Audio file too small: {file_size} bytes")
        return False
    
    # Check duration
    duration = get_audio_duration(audio_path)
    if duration < 0.1:
        logger.error(f"Audio duration too short: {duration}s")
        return False
    
    logger.info(f"✅ Audio file validated: {audio_file.name} ({duration:.1f}s, {file_size/1024:.1f}KB)")
    return True


def cleanup_audio_file(audio_path: str) -> bool:
    """
    Delete audio file after processing
    
    Args:
        audio_path: Path to audio file to delete
        
    Returns:
        True if deleted successfully
    """
    try:
        audio_file = Path(audio_path)
        if audio_file.exists():
            audio_file.unlink()
            logger.info(f"✅ Cleaned up audio file: {audio_file.name}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to cleanup audio file: {e}")
        return False
