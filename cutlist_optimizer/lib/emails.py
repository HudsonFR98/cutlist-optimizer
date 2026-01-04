import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import traceback
import sys
from datetime import datetime

from cutlist_optimizer.lib import config

logger = logging.getLogger(__name__)


def send_error_notification(exception, request_info=None, context_info=None):
    """
    Send error notification email to the developer.
    
    Args:
        exception: The exception that occurred
        request_info: Optional dict containing request information (URL, method, etc.)
        context_info: Optional dict containing additional context information
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = config.ERROR_EMAIL_FROM
        msg['To'] = config.ERROR_EMAIL_TO
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = f'[cutlist_optimizer] Error 500 - {config.CONTEXT.upper()} Environment'
        
        # Build email body
        body_parts = []
        
        # Header
        body_parts.append("=" * 80)
        body_parts.append("cutlist_optimizer - ERROR NOTIFICATION")
        body_parts.append("=" * 80)
        body_parts.append(f"Environment: {config.CONTEXT.upper()}")
        body_parts.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        body_parts.append("")
        
        # Exception details
        body_parts.append("EXCEPTION DETAILS:")
        body_parts.append("-" * 40)
        body_parts.append(f"Exception Type: {type(exception).__name__}")
        body_parts.append(f"Exception Message: {str(exception)}")
        body_parts.append("")
        
        # Full traceback
        body_parts.append("FULL TRACEBACK:")
        body_parts.append("-" * 40)
        body_parts.append(traceback.format_exc())
        body_parts.append("")
        
        # Request information (if available)
        if request_info:
            body_parts.append("REQUEST INFORMATION:")
            body_parts.append("-" * 40)
            for key, value in request_info.items():
                body_parts.append(f"{key}: {value}")
            body_parts.append("")
        
        # Context information (if available)
        if context_info:
            body_parts.append("ADDITIONAL CONTEXT:")
            body_parts.append("-" * 40)
            for key, value in context_info.items():
                body_parts.append(f"{key}: {value}")
            body_parts.append("")
        
        # System information
        body_parts.append("SYSTEM INFORMATION:")
        body_parts.append("-" * 40)
        body_parts.append(f"Python Version: {sys.version}")
        body_parts.append(f"Platform: {sys.platform}")
        body_parts.append("")
        
        # Footer
        body_parts.append("=" * 80)
        body_parts.append("This is an automated error notification from the cutlist_optimizer application.")
        body_parts.append("Please investigate and resolve the issue.")
        body_parts.append("=" * 80)
        
        # Combine all parts
        email_body = "\n".join(body_parts)
        
        # Attach body to message
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # Send email
        with smtplib.SMTP(config.ERROR_EMAIL_SMTP_SERVER, config.ERROR_EMAIL_SMTP_PORT) as server:
            server.starttls()  # Enable TLS
            server.login(config.ERROR_EMAIL_SMTP_USER, config.ERROR_EMAIL_SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Error notification email sent successfully to {config.ERROR_EMAIL_TO}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send error notification email: {e}")
        return False


def send_simple_email(to_email, subject, body, from_email=None):
    """
    Send a simple email message.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body
        from_email: Sender email address (defaults to config.ERROR_EMAIL_FROM)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        if from_email is None:
            from_email = config.ERROR_EMAIL_FROM
            
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP(config.ERROR_EMAIL_SMTP_SERVER, config.ERROR_EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(config.ERROR_EMAIL_SMTP_USER, config.ERROR_EMAIL_SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
