"""
Configuration settings for the Digital Inspector application
"""

class Config:
    """Application configuration"""
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024  # 64MB max file size
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
