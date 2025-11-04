"""
Configuration module for FlyMind API.
Loads settings from environment variables with sensible defaults.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# API Configuration
API_PORT = int(os.getenv("PORT", 8001))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
APP_NAME = os.getenv("APP_NAME", "FlyMind")

# CORS Configuration
ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "*")
if ALLOWED_ORIGINS_STR == "*" or ENVIRONMENT == "development":
    ALLOWED_ORIGINS: List[str] = ["*"]
else:
    ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",") if origin.strip()]

# API Key Configuration (for authentication)
API_KEY = os.getenv("API_KEY", None)
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"

# Rate Limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./flymind.db")

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"

# AI API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", None)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or text

# External Services
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", None)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", None)
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", None)


