# app/config.py
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://support_user:support_pass_2024@localhost:5433/support_tickets_db"
    POSTGRES_USER: str = "support_user"
    POSTGRES_PASSWORD: str = "support_pass_2024"
    POSTGRES_DB: str = "support_tickets_db"
    
    # Google Vertex AI Configuration
    GOOGLE_PROJECT_ID: str = "your-project-id"
    GOOGLE_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-001"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_AGENT_ID: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # FastAPI Configuration
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 9000
    
    # CORS Configuration
    FRONTEND_URL: str = "http://localhost:3001"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Ignore extra env vars like old CHROMA_* settings
    }

settings = Settings()
