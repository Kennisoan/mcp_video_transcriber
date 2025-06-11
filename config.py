"""
Centralized configuration management for MCP Video Transcriber
"""

import os
import secrets
from typing import Optional


class Config:
    """Application configuration"""

    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "").rstrip("/")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    SERVER_URL: str = os.getenv("SERVER_URL", f"http://localhost:{PORT}")

    # Security Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))
    AUTH_CODE_EXPIRES_MINUTES: int = int(
        os.getenv("AUTH_CODE_EXPIRES_MINUTES", "10"))

    # Database Configuration
    DATABASE_PATH: Optional[str] = os.getenv("DATABASE_PATH", None)

    # OAuth Scopes
    SUPPORTED_SCOPES = [
        "video:transcribe",
        "projects:read",
        "projects:write",
        "videos:read"
    ]

    # Default OAuth Client Settings
    DEFAULT_REDIRECT_URIS = ["http://localhost:3334/callback"]
    DEFAULT_GRANT_TYPES = ["authorization_code", "client_credentials"]
    DEFAULT_SCOPE = "video:transcribe projects:read projects:write videos:read"

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        if not cls.API_BASE_URL:
            raise ValueError("API_BASE_URL environment variable is required")

        if not cls.JWT_SECRET or len(cls.JWT_SECRET) < 16:
            raise ValueError("JWT_SECRET must be at least 16 characters long")

    @classmethod
    def get_cors_settings(cls) -> dict:
        """Get CORS middleware settings"""
        return {
            "allow_origins": ["*"],  # In production, specify exact origins
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }


# Validate configuration on import
Config.validate()
