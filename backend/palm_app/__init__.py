import os

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import (
    ALL_PERMISSIONS,
    ACLAuthorizationPolicy,
    Allow,
    Authenticated,
    Deny,
    Everyone,
)
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register

from .models.base import Base

_ENV_SETTING_MAP = (
    ('DATABASE_URL', 'sqlalchemy.url'),
    ('SECRET_KEY', 'secret_key'),
    ('S3_BUCKET', 's3_bucket'),
    ('AWS_ACCESS_KEY_ID', 'aws_access_key_id'),
    ('AWS_SECRET_ACCESS_KEY', 'aws_secret_access_key'),
    ('AWS_REGION', 'aws_region'),
    ('SMTP_HOST', 'smtp_host'),
    ('SMTP_PORT', 'smtp_port'),
    ('SMTP_USER', 'smtp_user'),
    ('SMTP_PASSWORD', 'smtp_password'),
    ('SMTP_FROM', 'smtp_from'),
    ('SMTP_USE_TLS', 'smtp_use_tls'),
    ('FRONTEND_URL', 'frontend_url'),
    ('UPLOAD_DIR', 'upload_dir'),
)


def _apply_env_settings(settings):
    settings = dict(settings)
    for env_var, setting_key in _ENV_SETTING_MAP:
        value = os.environ.get(env_var)
        if value is not None:
            settings[setting_key] = value
    return settings


def groupfinder(userid, request):
    from .models.user import User

    groups = []
    if userid:
        user = request.dbsession.query(User).filter_by(email=userid).first()
        if user and user.is_admin:
            groups.append('admin')
    return groups


def main(global_config, **settings):
    settings = _apply_env_settings(settings)
    secret_key = settings.get('secret_key', 'change-me-in-production')

    session_factory = SignedCookieSessionFactory(secret_key)
    authn_policy = AuthTktAuthenticationPolicy(
        secret_key,
        hashalg='sha512',
        callback=groupfinder,
        secure=False,
        http_only=True,
        samesite='Lax',
        include_ip=False,
    )
    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(settings=settings, session_factory=session_factory)
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.set_root_factory(lambda request: RootFactory())

    config.include('pyramid_tm')
    config.include('.routes')

    engine = engine_from_config(settings, 'sqlalchemy.')
    Base.metadata.bind = engine
    session_factory_db = sessionmaker(bind=engine, expire_on_commit=False)
    register(session_factory_db)
    config.registry['db_session_factory'] = session_factory_db

    config.add_request_method(
        lambda request: session_factory_db(),
        'dbsession',
        reify=True,
    )

    config.scan(ignore='palm_app.tests')

    return config.make_wsgi_app()


class RootFactory:
    __acl__ = [
        (Allow, 'admin', 'admin'),
        (Allow, Authenticated, 'view'),
        (Deny, Everyone, ALL_PERMISSIONS),
    ]
