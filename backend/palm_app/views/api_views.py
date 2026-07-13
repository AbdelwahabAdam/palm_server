import json
import logging
from pathlib import Path

from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPUnauthorized
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import view_config, view_defaults
from sqlalchemy import text

from ..models.site_visit import SiteVisit
from ..services.auth_service import AuthService
from ..services.palm_service import PalmService
from ..services.storage_service import StorageService
from ..utils.serializers import palm_to_dict, site_visit_to_dict, user_to_dict

logger = logging.getLogger(__name__)

JSON_CONTENT_TYPE = 'application/json; charset=utf-8'


def _json_response(payload, status=200, headerlist=None):
    kwargs = {
        'body': json.dumps(payload),
        'status': status,
        'content_type': JSON_CONTENT_TYPE,
        'charset': 'utf-8',
    }
    if headerlist is not None:
        kwargs['headerlist'] = headerlist
    return Response(**kwargs)


def _json_error(message, status=400):
    return _json_response({'error': message}, status=status)


def _get_json_body(request):
    try:
        return request.json_body
    except json.JSONDecodeError:
        return {}


def _is_multipart(request):
    content_type = request.content_type or ''
    return 'multipart/form-data' in content_type


def _parse_palm_request(request):
    if _is_multipart(request):
        data = {
            'palm_id': request.POST.get('palm_id', '').strip(),
            'palm_code': request.POST.get('palm_code', '').strip(),
            'plant_date': request.POST.get('plant_date', '').strip(),
            'donner_name': request.POST.get('donner_name'),
            'donner_phone_number': request.POST.get('donner_phone_number'),
            'harvest_amount': request.POST.get('harvest_amount'),
            'last_harvest': request.POST.get('last_harvest'),
            'age': request.POST.get('age'),
            'area': request.POST.get('area'),
            'section': request.POST.get('section'),
        }
        images = request.POST.getall('images') if hasattr(request.POST, 'getall') else []
        return data, images

    body = _get_json_body(request)
    return body, []


def _storage_for_request(request):
    return StorageService(request.registry.settings)


def _record_visit(request, page):
    try:
        visit = SiteVisit(
            ip_address=request.client_addr,
            user_agent=request.headers.get('User-Agent', '')[:255],
            page_visited=page,
        )
        request.dbsession.add(visit)
        request.dbsession.flush()
    except Exception as exc:
        logger.warning('Failed to record site visit: %s', exc)


@view_config(route_name='health', renderer='json', request_method='GET')
def health(request):
    return {'status': 'ok'}


@view_config(route_name='ready', renderer='json', request_method='GET')
def ready(request):
    try:
        request.dbsession.execute(text('SELECT 1'))
        return {'status': 'ready', 'database': 'connected'}
    except Exception as exc:
        return _json_response(
            {'status': 'not_ready', 'database': str(exc)},
            status=503,
        )


def _normalize_subpath(subpath):
    if not subpath:
        return ''
    if isinstance(subpath, (list, tuple)):
        return '/'.join(str(part) for part in subpath if part)
    return str(subpath)


def _binary_image_response(body, content_type):
    return Response(
        body=body,
        content_type=content_type,
        headerlist=[('Cache-Control', 'public, max-age=86400')],
    )


@view_config(route_name='upload_file', request_method='GET')
def upload_file(request):
    subpath = _normalize_subpath(request.matchdict.get('subpath', ''))
    storage = _storage_for_request(request)
    path = storage.resolve_local_path(subpath)
    if not path:
        raise HTTPNotFound()

    content_type = _content_type_for_path(path)

    with open(path, 'rb') as image_file:
        return _binary_image_response(image_file.read(), content_type)


@view_config(route_name='s3_image', request_method='GET')
def s3_image(request):
    subpath = _normalize_subpath(request.matchdict.get('subpath', ''))
    storage = _storage_for_request(request)
    try:
        obj = storage.get_s3_object(subpath)
        content_type = obj.get('ContentType') or _content_type_for_path(Path(subpath))
        return _binary_image_response(obj['Body'].read(), content_type)
    except Exception as exc:
        logger.warning('Failed to fetch S3 image %s: %s', subpath, exc)
        raise HTTPNotFound()


def _content_type_for_path(path):
    suffix = Path(path).suffix.lower()
    if suffix in {'.jpg', '.jpeg'}:
        return 'image/jpeg'
    if suffix == '.png':
        return 'image/png'
    if suffix == '.webp':
        return 'image/webp'
    if suffix == '.gif':
        return 'image/gif'
    return 'application/octet-stream'


@view_defaults(renderer='json')
class PublicApiViews:
    def __init__(self, request):
        self.request = request
        self.palm_service = PalmService(request)

    @view_config(route_name='api_statistics', request_method='GET')
    def statistics(self):
        _record_visit(self.request, '/api/statistics')
        return self.palm_service.get_statistics()

    @view_config(route_name='api_search', request_method='GET')
    def search(self):
        _record_visit(self.request, '/api/search')
        palm_code = self.request.params.get('palm_code')
        donner_name = self.request.params.get('donner_name')
        donner_phone = self.request.params.get('donner_phone')
        area = self.request.params.get('area')
        section = self.request.params.get('section')
        page = int(self.request.params.get('page', 1))
        per_page = int(self.request.params.get('per_page', 20))

        results = self.palm_service.search_palms(
            palm_code=palm_code,
            donner_name=donner_name,
            donner_phone=donner_phone,
            area=area,
            section=section,
            page=page,
            per_page=per_page,
        )

        return {
            'palms': [palm_to_dict(p, _storage_for_request(self.request)) for p in results['palms']],
            'total': results['total'],
            'page': results['page'],
            'per_page': results['per_page'],
            'pages': results['pages'],
        }

    @view_config(route_name='api_palm_detail', request_method='GET')
    def palm_detail(self):
        palm_id = int(self.request.matchdict['id'])
        _record_visit(self.request, f'/api/palms/{palm_id}')
        palm = self.palm_service.get_palm_by_id(palm_id)
        if not palm:
            raise HTTPNotFound(json_body={'error': 'Palm not found'})
        return palm_to_dict(palm, _storage_for_request(self.request))


@view_defaults(renderer='json')
class AuthViews:
    def __init__(self, request):
        self.request = request
        self.auth_service = AuthService(request)

    @view_config(route_name='admin_login', request_method='POST')
    def login(self):
        body = _get_json_body(self.request)
        email = body.get('email', '').strip()
        password = body.get('password', '')

        if not email or not password:
            return _json_error('Email and password are required')

        user = self.auth_service.authenticate(email, password)
        if not user:
            return _json_error('Invalid credentials', 401)

        if not user.is_admin:
            return _json_error('Admin access required', 403)

        headerlist = remember(self.request, user.email)
        return _json_response(
            {'success': True, 'user': user_to_dict(user)},
            headerlist=headerlist,
        )

    @view_config(route_name='admin_logout', request_method='POST')
    def logout(self):
        headerlist = forget(self.request)
        return _json_response({'success': True}, headerlist=headerlist)

    @view_config(route_name='admin_me', request_method='GET')
    def me(self):
        from .. import groupfinder

        userid = self.request.authenticated_userid
        groups = groupfinder(userid, self.request) if userid else []
        return {
            'authenticated_userid': userid,
            'effective_principals': list(self.request.effective_principals),
            'groups': groups,
        }

    @view_config(route_name='admin_password_reset_request', request_method='POST')
    def password_reset_request(self):
        body = _get_json_body(self.request)
        email = body.get('email', '').strip()
        if not email:
            return _json_error('Email is required')

        self.auth_service.request_password_reset(email)
        return {
            'success': True,
            'message': 'If the email exists, a reset link has been sent.',
        }

    @view_config(route_name='admin_password_reset_confirm', request_method='POST')
    def password_reset_confirm(self):
        body = _get_json_body(self.request)
        token = body.get('token', '').strip()
        password = body.get('password', '')

        if not token or not password:
            return _json_error('Token and password are required')

        if len(password) < 6:
            return _json_error('Password must be at least 6 characters')

        try:
            self.auth_service.reset_password(token, password)
            return {'success': True, 'message': 'Password has been reset.'}
        except ValueError as exc:
            return _json_error(str(exc))


@view_defaults(renderer='json')
class AdminViews:
    def __init__(self, request):
        self.request = request
        self.palm_service = PalmService(request)

    @view_config(route_name='admin_dashboard', request_method='GET', permission='admin')
    def dashboard(self):
        stats = self.palm_service.get_statistics()
        recent_visits = (
            self.request.dbsession.query(SiteVisit)
            .order_by(SiteVisit.visited_at.desc())
            .limit(10)
            .all()
        )
        return {
            'stats': stats,
            'recent_visits': [site_visit_to_dict(v) for v in recent_visits],
        }

    @view_config(route_name='admin_palms', request_method='GET', permission='admin')
    def list_palms(self):
        page = int(self.request.params.get('page', 1))
        per_page = int(self.request.params.get('per_page', 50))
        results = self.palm_service.search_palms(
            palm_code=self.request.params.get('palm_code'),
            donner_name=self.request.params.get('donner_name'),
            donner_phone=self.request.params.get('donner_phone'),
            area=self.request.params.get('area'),
            section=self.request.params.get('section'),
            page=page,
            per_page=per_page,
        )
        return {
            'palms': [palm_to_dict(p, _storage_for_request(self.request)) for p in results['palms']],
            'total': results['total'],
            'page': results['page'],
            'per_page': results['per_page'],
            'pages': results['pages'],
        }

    @view_config(route_name='admin_palms', request_method='POST', permission='admin')
    def add_palm(self):
        try:
            data, images = _parse_palm_request(self.request)

            if not data.get('palm_id') or not data.get('palm_code') or not data.get('plant_date'):
                return _json_error('palm_id, palm_code, and plant_date are required')

            palm = self.palm_service.create_palm(data, images)
            return {'success': True, 'palm': palm_to_dict(palm, _storage_for_request(self.request))}
        except ValueError as exc:
            return _json_error(str(exc))
        except Exception as exc:
            logger.exception('Error creating palm')
            return _json_error(str(exc))

    @view_config(route_name='admin_palm_detail', request_method='GET', permission='admin')
    def get_palm(self):
        palm_id = int(self.request.matchdict['id'])
        palm = self.palm_service.get_palm_by_id(palm_id)
        if not palm:
            raise HTTPNotFound(json_body={'error': 'Palm not found'})
        return palm_to_dict(palm, _storage_for_request(self.request))

    @view_config(route_name='admin_palm_detail', request_method='PUT', permission='admin')
    def update_palm(self):
        palm_id = int(self.request.matchdict['id'])
        try:
            data, images = _parse_palm_request(self.request)
            palm = self.palm_service.update_palm(palm_id, data, images)
            return {'success': True, 'palm': palm_to_dict(palm, _storage_for_request(self.request))}
        except ValueError as exc:
            return _json_error(str(exc))

    @view_config(route_name='admin_palm_update', request_method='POST', permission='admin')
    def update_palm_multipart(self):
        palm_id = int(self.request.matchdict['id'])
        try:
            data, images = _parse_palm_request(self.request)
            palm = self.palm_service.update_palm(palm_id, data, images)
            return {'success': True, 'palm': palm_to_dict(palm, _storage_for_request(self.request))}
        except ValueError as exc:
            return _json_error(str(exc))
        except Exception as exc:
            logger.exception('Error updating palm with images')
            return _json_error(str(exc))

    @view_config(route_name='admin_palm_detail', request_method='DELETE', permission='admin')
    def delete_palm(self):
        palm_id = int(self.request.matchdict['id'])
        try:
            self.palm_service.delete_palm(palm_id)
            return {'success': True}
        except ValueError as exc:
            return _json_error(str(exc))

    @view_config(route_name='admin_reports', request_method='GET', permission='admin')
    def reports(self):
        start_date = self.request.params.get('start_date')
        end_date = self.request.params.get('end_date')
        section = self.request.params.get('section')

        report_data = self.palm_service.generate_report(
            start_date=start_date,
            end_date=end_date,
            section=section,
        )

        return {
            'report_data': report_data,
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'section': section,
            },
        }

    @view_config(route_name='admin_visits', request_method='GET', permission='admin')
    def visits(self):
        page = int(self.request.params.get('page', 1))
        per_page = int(self.request.params.get('per_page', 50))
        query = self.request.dbsession.query(SiteVisit).order_by(SiteVisit.visited_at.desc())
        total = query.count()
        visits = query.offset((page - 1) * per_page).limit(per_page).all()
        return {
            'visits': [site_visit_to_dict(v) for v in visits],
            'total': total,
            'page': page,
            'per_page': per_page,
        }
