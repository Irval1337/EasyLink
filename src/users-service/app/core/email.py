import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import base64
import json
from passlib.context import CryptContext
from jinja2 import Environment, FileSystemLoader
import os
import logging

from app.config import (
    SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, 
    SMTP_USE_TLS, FROM_EMAIL, SECRET_KEY, ALGORITHM,
    EMAIL_ACTIVATION_TOKEN_EXPIRE_HOURS, FRONTEND_URL
)

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.smtp_use_tls = SMTP_USE_TLS
        self.from_email = FROM_EMAIL
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured - email sending will be unavailable")
        
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        if not os.path.exists(template_dir):
            logger.warning(f"Template directory not found: {template_dir}")
    
    def create_email_activation_token(self, email: str) -> str:
        expire = datetime.utcnow() + timedelta(hours=EMAIL_ACTIVATION_TOKEN_EXPIRE_HOURS)
        payload = {
            "email": email,
            "exp": expire,
            "purpose": "email_activation"
        }
        
        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_email_activation_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = payload.get("exp")
            if exp is None:
                return None
            if datetime.now(timezone.utc).timestamp() > float(exp):
                logger.warning("Email activation token expired")
                return None
            if payload.get("purpose") != "email_activation":
                logger.warning("Token purpose mismatch")
                return None
            email = payload.get("email")
            if not email:
                logger.warning("No email in token payload")
                return None
            return email
        except JWTError as e:
            logger.warning(f"JWT error verifying email activation token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying email activation token: {e}")
            return None
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls(context=context)
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            return True
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_activation_email(self, email: str, username: str) -> bool:
        token = self.create_email_activation_token(email)
        activation_url = f"{FRONTEND_URL}/activate-email?token={token}"
        
        try:
            template = self.jinja_env.get_template("activation_email.html")
            html_content = template.render(
                username=username,
                activation_url=activation_url,
                frontend_url=FRONTEND_URL
            )
        except Exception as e:
            logger.error(f"Error rendering email template for {email}: {e}")
            return False
        
        subject = "Подтвердите ваш email - EasyLink"
        return self.send_email(email, subject, html_content)

email_service = EmailService()
