# app/services/elevenlabs_service.py
import aiohttp
import asyncio
import base64
import json
from typing import Dict, Any, Optional, List
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class ElevenLabsService:
    """Service for integrating with ElevenLabs text-to-speech and ConvAI"""
    
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.agent_id = settings.ELEVENLABS_AGENT_ID
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.model_id = settings.ELEVENLABS_MODEL_ID
        self.base_url = "https://api.elevenlabs.io/v1"
        
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Convert text to speech using ElevenLabs TTS"""
        
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured")
        
        voice_id = voice_id or self.voice_id
        model_id = model_id or self.model_id
        
        # Default voice settings for clear technical support speech
        default_voice_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.5,
            "use_speaker_boost": True
        }
        
        voice_settings = voice_settings or default_voice_settings
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        error_text = await response.text()
                        raise Exception(f"ElevenLabs TTS error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            raise
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech to text (using Whisper API as fallback)"""
        # ElevenLabs doesn't have native STT, so we'll use OpenAI Whisper
        from openai import AsyncOpenAI
        
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key required for speech-to-text")
        
        openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        try:
            # Create a temporary file-like object for the audio
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            response = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {str(e)}")
            raise
    
    async def create_conversation_agent(
        self, 
        agent_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update a conversation agent"""
        
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured")
        
        url = f"{self.base_url}/convai/agents"
        
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        # Default agent configuration for IT support
        default_config = {
            "name": "IT Support Assistant",
            "prompt": """You are a professional IT support assistant for a company's internal helpdesk. Your role is to:

1. Help employees with technical issues in a friendly, professional manner
2. Provide step-by-step troubleshooting guidance
3. Reference knowledge base articles when appropriate
4. Escalate complex issues to human technicians
5. Collect necessary information for ticket creation

Always:
- Speak clearly and at an appropriate pace
- Ask clarifying questions when needed
- Provide specific, actionable steps
- Be patient and understanding
- Confirm understanding before proceeding

If you cannot resolve an issue, offer to create a support ticket with the information gathered.""",
            "language": "en",
            "conversation_config": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "suffix_padding_ms": 200
                }
            },
            "platform_settings": {
                "widget": {
                    "variant": "embed_large"
                }
            }
        }
        
        # Merge with provided config
        final_config = {**default_config, **agent_config}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=final_config) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"ElevenLabs agent creation error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Error creating conversation agent: {str(e)}")
            raise
    
    async def get_agent_conversations(
        self, 
        agent_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversations for an agent"""
        
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured")
        
        agent_id = agent_id or self.agent_id
        
        if not agent_id:
            raise Exception("Agent ID not provided")
        
        url = f"{self.base_url}/convai/agents/{agent_id}/conversations"
        
        headers = {
            "xi-api-key": self.api_key
        }
        
        params = {"limit": limit}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"ElevenLabs conversations error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Error getting agent conversations: {str(e)}")
            raise
    
    async def create_voice_enabled_response(
        self, 
        text_response: str,
        include_audio: bool = True
    ) -> Dict[str, Any]:
        """Create a response that includes both text and audio"""
        
        response_data = {
            "text": text_response,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        if include_audio and self.api_key:
            try:
                # Generate audio for the response
                audio_data = await self.text_to_speech(text_response)
                
                # Convert to base64 for JSON transmission
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                response_data.update({
                    "audio": {
                        "format": "mp3",
                        "data": audio_base64,
                        "duration_estimate": len(text_response) * 0.1  # Rough estimate
                    },
                    "voice_enabled": True
                })
                
            except Exception as e:
                logger.warning(f"Could not generate audio: {str(e)}")
                response_data["voice_enabled"] = False
        else:
            response_data["voice_enabled"] = False
        
        return response_data
    
    def get_agent_embed_code(self, agent_id: Optional[str] = None) -> str:
        """Get the HTML embed code for the ElevenLabs ConvAI widget"""
        
        agent_id = agent_id or self.agent_id
        
        if not agent_id:
            return "<!-- ElevenLabs Agent ID not configured -->"
        
        return f'''<script src="https://elevenlabs.io/convai-widget/index.js" async></script>
<elevenlabs-convai agent-id="{agent_id}"></elevenlabs-convai>'''
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured")
        
        url = f"{self.base_url}/voices"
        
        headers = {
            "xi-api-key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("voices", [])
                    else:
                        error_text = await response.text()
                        raise Exception(f"ElevenLabs voices error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
            raise

# Global instance
elevenlabs_service = ElevenLabsService()
