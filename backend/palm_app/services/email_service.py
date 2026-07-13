import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings):
        self.smtp_host = settings.get('smtp_host', '')
        self.smtp_port = int(settings.get('smtp_port', 587))
        self.smtp_user = settings.get('smtp_user', '')
        self.smtp_password = settings.get('smtp_password', '')
        self.smtp_from = settings.get('smtp_from', self.smtp_user)
        self.smtp_use_tls = settings.get('smtp_use_tls', 'true').lower() == 'true'
        self.frontend_url = settings.get('frontend_url', 'http://localhost')

    def is_configured(self):
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    def send_email(self, to_email, subject, body_html, body_text=None):
        if not self.is_configured():
            logger.warning('SMTP not configured; email not sent to %s', to_email)
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.smtp_from
        msg['To'] = to_email

        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_from, [to_email], msg.as_string())
            return True
        except Exception as exc:
            logger.error('Failed to send email to %s: %s', to_email, exc)
            return False

    def send_password_reset_email(self, to_email, reset_token):
        reset_url = f'{self.frontend_url}/admin/reset-password?token={reset_token}'
        subject = 'Palm Management System - Password Reset'
        body_html = f"""
        <html>
          <body>
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for your Palm Management System account.</p>
            <p><a href="{reset_url}">Click here to reset your password</a></p>
            <p>This link expires in 1 hour.</p>
            <p>If you did not request this, please ignore this email.</p>
          </body>
        </html>
        """
        body_text = (
            f'Password Reset Request\n\n'
            f'Reset your password: {reset_url}\n\n'
            f'This link expires in 1 hour.'
        )
        return self.send_email(to_email, subject, body_html, body_text)
