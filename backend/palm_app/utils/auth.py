import secrets
from datetime import datetime

import bcrypt


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_reset_token():
    return secrets.token_urlsafe(32)


def is_token_expired(expires_at):
    if expires_at is None:
        return True
    return datetime.utcnow() > expires_at
