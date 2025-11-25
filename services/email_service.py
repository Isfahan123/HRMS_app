"""
Email Service module for HRMS
Re-exports the email service from core module for backwards compatibility
"""

# Import and re-export the email_service instance from core
from core.email_service import email_service, HRMSEmailService

__all__ = ['email_service', 'HRMSEmailService']
