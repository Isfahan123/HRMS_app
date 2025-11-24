"""
Configuration module for HRMS Application
Centralizes all configuration and provides context for templates
"""
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Application Info
    APP_NAME = "HRMS Application"
    APP_VERSION = "2.0.0"
    APP_DESCRIPTION = "Human Resource Management System"
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
    
    # Web Server
    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
    WEB_RELOAD = os.getenv("WEB_RELOAD", "false").lower() == "true"
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    # API Configuration
    API_PREFIX = "/api"
    API_VERSION = "v1"
    
    # Features
    FEATURE_CALENDAR = True
    FEATURE_BONUS = True
    FEATURE_PAYROLL = True
    FEATURE_ENGAGEMENTS = True
    
    @classmethod
    def get_template_context(cls, **kwargs):
        """
        Get context dictionary for templates
        Returns common variables that should be available in all templates
        """
        context = {
            # App info
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "app_description": cls.APP_DESCRIPTION,
            
            # Environment
            "environment": cls.ENVIRONMENT,
            "debug": cls.DEBUG,
            "is_production": cls.ENVIRONMENT == "production",
            "is_development": cls.ENVIRONMENT == "development",
            
            # API info
            "api_prefix": cls.API_PREFIX,
            "api_version": cls.API_VERSION,
            
            # Features
            "features": {
                "calendar": cls.FEATURE_CALENDAR,
                "bonus": cls.FEATURE_BONUS,
                "payroll": cls.FEATURE_PAYROLL,
                "engagements": cls.FEATURE_ENGAGEMENTS,
            },
            
            # Current year (useful for copyright, etc.)
            "current_year": datetime.now().year,
        }
        
        # Merge with any additional kwargs
        context.update(kwargs)
        
        return context

# Create a singleton instance
config = Config()
