def includeme(config):
    # Health checks
    config.add_route('health', '/health')
    config.add_route('ready', '/ready')

    # Public API
    config.add_route('api_statistics', '/api/statistics')
    config.add_route('api_search', '/api/search')
    config.add_route('api_palm_detail', '/api/palms/{id}')
    config.add_route('upload_file', '/api/uploads/*subpath')
    config.add_route('s3_image', '/api/images/*subpath')

    # Admin API (under /api/admin to avoid conflicting with React /admin/* pages)
    config.add_route('admin_login', '/api/admin/login')
    config.add_route('admin_logout', '/api/admin/logout')
    config.add_route('admin_me', '/api/admin/me')
    config.add_route('admin_password_reset_request', '/api/admin/password-reset/request')
    config.add_route('admin_password_reset_confirm', '/api/admin/password-reset/confirm')
    config.add_route('admin_dashboard', '/api/admin/dashboard')
    config.add_route('admin_palms', '/api/admin/palms')
    config.add_route('admin_palm_detail', '/api/admin/palms/{id}')
    config.add_route('admin_palm_update', '/api/admin/palms/{id}/update')
    config.add_route('admin_reports', '/api/admin/reports')
    config.add_route('admin_visits', '/api/admin/visits')
