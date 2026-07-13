import json
from unittest.mock import Mock, patch

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Everyone

from palm_app import RootFactory
from palm_app.utils.auth import hash_password, verify_password
from palm_app.views.api_views import AuthViews, _json_error


def test_root_factory_allows_admin_principal():
    policy = ACLAuthorizationPolicy()
    principals = ['system.Everyone', 'system.Authenticated', 'admin@gmail.com', 'admin']

    assert policy.permits(RootFactory(), principals, 'admin')
    assert policy.permits(RootFactory(), principals, 'view')
    assert not policy.permits(RootFactory(), [Everyone], 'admin')


def test_json_error_returns_json_not_500():
    response = _json_error('Invalid credentials', 401)

    assert response.status_code == 401
    assert response.content_type == 'application/json'
    assert response.charset == 'utf-8'
    assert json.loads(response.text) == {'error': 'Invalid credentials'}


def test_login_sets_auth_cookie_headerlist():
    request = Mock()
    request.json_body = {'email': 'admin@gmail.com', 'password': 'Admin123'}
    request.registry.settings = {}

    user = Mock()
    user.email = 'admin@gmail.com'
    user.is_admin = True

    with patch('palm_app.views.api_views.AuthService') as auth_service_cls:
        auth_service = auth_service_cls.return_value
        auth_service.authenticate.return_value = user
        with patch('palm_app.views.api_views.remember', return_value=[('Set-Cookie', 'auth_tkt=test')]) as remember:
            with patch('palm_app.views.api_views.user_to_dict', return_value={'email': 'admin@gmail.com'}):
                response = AuthViews(request).login()

    remember.assert_called_once_with(request, 'admin@gmail.com')
    assert response.status_code == 200
    assert response.headers.get('Set-Cookie') == 'auth_tkt=test'
    assert json.loads(response.text)['success'] is True


def test_hash_and_verify_password():
    password = 'Admin123'
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password('wrong', hashed)
