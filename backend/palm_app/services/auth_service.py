from datetime import datetime, timedelta

from ..models.user import User
from ..utils.auth import generate_reset_token, hash_password, is_token_expired, verify_password
from .email_service import EmailService


class AuthService:
    def __init__(self, request):
        self.request = request
        self.db = request.dbsession
        self.email_service = EmailService(request.registry.settings)

    def authenticate(self, email, password):
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    def request_password_reset(self, email):
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return True

        token = generate_reset_token()
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        self.db.flush()

        self.email_service.send_password_reset_email(user.email, token)
        return True

    def reset_password(self, token, new_password):
        user = self.db.query(User).filter(User.reset_token == token).first()
        if not user or is_token_expired(user.reset_token_expires):
            raise ValueError('Invalid or expired reset token')

        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        self.db.flush()
        return user

    def create_user(self, email, password, full_name=None, is_admin=False):
        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_admin=is_admin,
        )
        self.db.add(user)
        self.db.flush()
        return user
