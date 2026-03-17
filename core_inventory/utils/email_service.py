"""Email service for sending notifications."""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class EmailError(Exception):
    """Exception raised for email sending errors."""
    pass


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        """Initialize email service with configuration from environment variables."""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'CoreInventory')
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if email sent successfully
            
        Raises:
            EmailError: If email sending fails
        """
        if not self.smtp_user or not self.smtp_password:
            raise EmailError(
                "Email configuration missing. Please set SMTP_USER and SMTP_PASSWORD environment variables."
            )
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Attach plain text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Attach HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            raise EmailError("SMTP authentication failed. Check your email credentials.")
        except smtplib.SMTPException as e:
            raise EmailError(f"Failed to send email: {str(e)}")
        except Exception as e:
            raise EmailError(f"Unexpected error sending email: {str(e)}")
    
    def send_password_reset_email(self, to_email: str, otp: str) -> bool:
        """Send password reset OTP email.
        
        Args:
            to_email: Recipient email address
            otp: 6-digit OTP code
            
        Returns:
            True if email sent successfully
        """
        subject = "CoreInventory - Password Reset Code"
        
        # Plain text version
        body = f"""
Hello,

You requested to reset your password for CoreInventory.

Your password reset code is: {otp}

This code will expire in 15 minutes and can only be used once.

If you did not request this password reset, please ignore this email.

Best regards,
CoreInventory Team
"""
        
        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #0f1419 0%, #1a2a3a 100%);
            color: #00d4ff;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .otp-box {{
            background: #fff;
            border: 2px solid #00d4ff;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        }}
        .otp-code {{
            font-size: 32px;
            font-weight: bold;
            color: #00d4ff;
            letter-spacing: 8px;
            font-family: 'Courier New', monospace;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffa500;
            padding: 15px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CoreInventory</h1>
            <p>Password Reset Request</p>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>You requested to reset your password for CoreInventory.</p>
            
            <div class="otp-box">
                <p style="margin: 0; color: #666;">Your password reset code is:</p>
                <div class="otp-code">{otp}</div>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important:</strong>
                <ul style="margin: 10px 0 0 0;">
                    <li>This code will expire in <strong>15 minutes</strong></li>
                    <li>This code can only be used <strong>once</strong></li>
                    <li>Do not share this code with anyone</li>
                </ul>
            </div>
            
            <p>If you did not request this password reset, please ignore this email and your password will remain unchanged.</p>
            
            <p>Best regards,<br>CoreInventory Team</p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_email, subject, body, html_body)
