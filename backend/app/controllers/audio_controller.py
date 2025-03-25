import os
import logging
import requests
import io
import tempfile
from openai import OpenAI
from fastapi import HTTPException
from dotenv import load_dotenv
from requests.exceptions import RequestException
from pydub import AudioSegment

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioController:
    def __init__(self):
        self.client = OpenAI()  # Automatically reads API key from env
        logger.info("AudioController initialized")
    
    async def download_audio(self, audio_url):
        """Download audio from URL"""
        try:
            logger.info(f"Downloading audio from: {audio_url}")
            response = requests.get(audio_url)
            response.raise_for_status()  # Raises error for HTTP codes >= 400
            return response.content
        except RequestException as req_err:
            logger.error(f"Network error while downloading audio: {req_err}")
            raise HTTPException(status_code=500, detail="Network error while downloading audio")
        except Exception as e:
            logger.error(f"Unexpected error downloading audio: {str(e)}")
            raise HTTPException(status_code=500, detail="Unexpected error downloading audio")

    async def transcribe_audio(self, audio_content):
        """Transcribe audio using OpenAI Whisper"""
        try:
            if not audio_content:
                logger.error("Empty audio content received")
                raise HTTPException(status_code=400, detail="Empty audio content received")
            
            logger.info(f"Processing audio content, size: {len(audio_content)} bytes")
            
            # Create a temporary directory to work with the audio files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save the original audio content to a temporary file
                original_file = os.path.join(temp_dir, "original_audio")
                with open(original_file, "wb") as f:
                    f.write(audio_content)
                
                try:
                    # Convert to a format that Whisper definitely supports (mp3)
                    logger.info("Converting audio to MP3 format")
                    audio = AudioSegment.from_file(original_file)
                    mp3_file = os.path.join(temp_dir, "converted_audio.mp3")
                    audio.export(mp3_file, format="mp3")
                    
                    # Transcribe with OpenAI Whisper using the converted file
                    logger.info("Transcribing audio with Whisper API...")
                    with open(mp3_file, "rb") as audio_file:
                        try:
                            transcript_response = self.client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format="text"
                            )
                            logger.info(f"Transcription successful: {transcript_response[:100] if transcript_response else 'Empty response'}...")
                            return transcript_response  # Response is already a string
                        except Exception as api_err:
                            logger.error(f"Whisper API error: {str(api_err)}")
                            raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI API: {str(api_err)}")
                except Exception as convert_err:
                    logger.error(f"Error converting audio: {str(convert_err)}")
                    
                    # Fallback: Try sending the original file directly
                    logger.info("Conversion failed, trying with original file...")
                    with open(original_file, "rb") as audio_file:
                        try:
                            transcript_response = self.client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format="text"
                            )
                            logger.info(f"Transcription successful: {transcript_response[:100] if transcript_response else 'Empty response'}...")
                            return transcript_response
                        except Exception as api_err:
                            logger.error(f"Whisper API error with original file: {str(api_err)}")
                            raise HTTPException(status_code=500, detail=f"Error processing audio: {str(api_err)}")
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error transcribing audio: {str(e)}")
