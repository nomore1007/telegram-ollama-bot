"""Multi-modal AI processing for images, voice, and files"""

import asyncio
import logging
import base64
import io
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import tempfile
import os

from PIL import Image
import speech_recognition as sr
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Process and analyze images"""

    def __init__(self):
        self.max_image_size = (1024, 1024)  # Max dimensions
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.supported_formats = ['JPEG', 'PNG', 'GIF', 'WEBP']

    async def process_image(self, image_data: bytes, filename: str = "") -> Dict[str, Any]:
        """Process uploaded image and extract information"""
        try:
            # Validate file size
            if len(image_data) > self.max_file_size:
                return {
                    "success": False,
                    "error": f"Image too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
                }

            # Open image
            image = Image.open(io.BytesIO(image_data))

            # Validate format
            if image.format not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"Unsupported format: {image.format}. Supported: {', '.join(self.supported_formats)}"
                }

            # Get basic image info
            info = {
                "success": True,
                "filename": filename,
                "format": image.format,
                "size": image.size,
                "mode": image.mode,
                "file_size_bytes": len(image_data)
            }

            # Convert to RGB if necessary for processing
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large
            if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                info["resized"] = True
                info["original_size"] = info["size"]
                info["size"] = image.size

            # Convert to base64 for AI processing
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            info["base64_data"] = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return info

        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return {
                "success": False,
                "error": f"Failed to process image: {type(e).__name__}"
            }

    async def generate_image_description(self, ollama_client, image_info: Dict[str, Any]) -> str:
        """Generate AI description of the image"""
        try:
            prompt = f"""Analyze this image and provide a detailed description. Include:
1. Main subjects and objects visible
2. Colors and overall mood/tone
3. Setting or environment
4. Any text visible in the image
5. Notable features or details

Image details: {image_info.get('format', 'Unknown')} format, {image_info.get('size', 'Unknown')} resolution

Please provide a comprehensive but concise description."""

            # For now, return a placeholder since we don't have vision models
            # In production, this would use a vision-capable model
            return "Image analysis feature coming soon! This will use vision-capable AI models to describe images."

        except Exception as e:
            logger.error(f"Image description generation error: {e}")
            return "❌ Failed to analyze image."

class VoiceProcessor:
    """Process voice messages and convert to text"""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.max_duration = 300  # 5 minutes max
        self.supported_formats = ['ogg', 'mp3', 'wav', 'flac', 'm4a']

    async def process_voice(self, voice_data: bytes, mime_type: str = "audio/ogg") -> Dict[str, Any]:
        """Process voice message and convert to text"""
        try:
            # Save voice data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file.write(voice_data)
                temp_path = temp_file.name

            try:
                # Convert audio if needed
                audio_path = await self._convert_audio(temp_path, mime_type)

                # Perform speech recognition
                with sr.AudioFile(audio_path) as source:
                    audio = self.recognizer.record(source)

                    # Try different recognition engines
                    text = ""
                    try:
                        text = self.recognizer.recognize_google(audio)
                    except sr.UnknownValueError:
                        text = "Could not understand audio"
                    except sr.RequestError as e:
                        logger.error(f"Speech recognition service error: {e}")
                        text = "Speech recognition service unavailable"

                    # Get audio duration
                    audio_segment = AudioSegment.from_file(audio_path)
                    duration = len(audio_segment) / 1000  # Convert to seconds

                    return {
                        "success": True,
                        "text": text,
                        "duration_seconds": duration,
                        "confidence": getattr(audio, '_confidence', None)
                    }

            finally:
                # Clean up temporary files
                for path in [temp_path, audio_path]:
                    if os.path.exists(path):
                        os.unlink(path)

        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            return {
                "success": False,
                "error": f"Failed to process voice message: {type(e).__name__}"
            }

    async def _convert_audio(self, input_path: str, mime_type: str) -> str:
        """Convert audio to WAV format for speech recognition"""
        try:
            # Load audio with pydub
            if mime_type == "audio/ogg":
                audio = AudioSegment.from_ogg(input_path)
            elif mime_type in ["audio/mp3", "audio/mpeg"]:
                audio = AudioSegment.from_mp3(input_path)
            elif mime_type == "audio/wav":
                return input_path  # Already WAV
            else:
                # Try to detect format automatically
                audio = AudioSegment.from_file(input_path)

            # Convert to WAV
            output_path = input_path + '.wav'
            audio.export(output_path, format='wav')

            return output_path

        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return input_path  # Return original if conversion fails

class FileProcessor:
    """Process uploaded files and documents"""

    def __init__(self):
        self.max_file_size = 25 * 1024 * 1024  # 25MB
        self.allowed_extensions = {
            'text': ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml'],
            'document': ['.pdf', '.doc', '.docx'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
            'video': ['.mp4', '.avi', '.mov', '.mkv']
        }

    async def process_file(self, file_data: bytes, filename: str, mime_type: str = "") -> Dict[str, Any]:
        """Process uploaded file and extract information"""
        try:
            file_size = len(file_data)
            file_ext = Path(filename).suffix.lower()

            # Check file size
            if file_size > self.max_file_size:
                return {
                    "success": False,
                    "error": f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
                }

            # Determine file type
            file_type = self._get_file_type(file_ext)

            if not file_type:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}"
                }

            # Basic file info
            result = {
                "success": True,
                "filename": filename,
                "file_type": file_type,
                "file_size": file_size,
                "mime_type": mime_type,
                "extension": file_ext
            }

            # For text files, try to extract content
            if file_type == 'text' and file_size < 1024 * 1024:  # 1MB limit for text extraction
                try:
                    text_content = file_data.decode('utf-8', errors='ignore')
                    if len(text_content) > 5000:  # Truncate long files
                        text_content = text_content[:5000] + "...\n[Content truncated]"
                    result["content"] = text_content
                    result["content_length"] = len(text_content)
                except UnicodeDecodeError:
                    result["content"] = "[Binary file - cannot display as text]"

            return result

        except Exception as e:
            logger.error(f"File processing error: {e}")
            return {
                "success": False,
                "error": f"Failed to process file: {type(e).__name__}"
            }

    def _get_file_type(self, extension: str) -> Optional[str]:
        """Determine file type from extension"""
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return file_type
        return None

    async def summarize_file(self, ollama_client, file_info: Dict[str, Any]) -> str:
        """Generate AI summary of file content"""
        try:
            file_type = file_info.get('file_type', 'unknown')
            filename = file_info.get('filename', 'Unknown file')

            if file_type == 'text' and 'content' in file_info:
                content = file_info['content']
                prompt = f"""Please analyze and summarize this file:

Filename: {filename}
File type: {file_type}
Content length: {file_info.get('content_length', 'Unknown')} characters

Content:
{content}

Please provide:
1. A brief summary of what this file contains
2. Key information or code structure
3. Any notable features or patterns
4. Purpose or intended use (if detectable)

Keep the summary concise but informative."""

                summary = await ollama_client.generate(prompt)
                return summary

            else:
                # For binary files, just describe the file
                return f"📁 **{filename}**\n\n" \
                       f"- **Type:** {file_type}\n" \
                       f"- **Size:** {file_info.get('file_size', 'Unknown')} bytes\n" \
                       f"- **MIME Type:** {file_info.get('mime_type', 'Unknown')}\n\n" \
                       f"This is a {file_type} file. Content analysis available for text files only."

        except Exception as e:
            logger.error(f"File summarization error: {e}")
            return "❌ Failed to analyze file content."

# Global instances
image_processor = ImageProcessor()
voice_processor = VoiceProcessor()
file_processor = FileProcessor()

__all__ = [
    'ImageProcessor',
    'VoiceProcessor',
    'FileProcessor',
    'image_processor',
    'voice_processor',
    'file_processor'
]