from datetime import datetime


def palm_to_dict(palm, storage=None):
    images = palm.images or []
    if storage:
        images = [storage.get_view_url(url) for url in images if storage.get_view_url(url)]

    return {
        'id': palm.id,
        'palm_id': palm.palm_id,
        'palm_code': palm.palm_code,
        'plant_date': palm.plant_date.isoformat() if palm.plant_date else None,
        'donner_name': palm.donner_name,
        'donner_phone_number': palm.donner_phone_number,
        'harvest_amount': palm.harvest_amount,
        'last_harvest': palm.last_harvest.isoformat() if palm.last_harvest else None,
        'age': palm.age,
        'images': images,
        'area': palm.area,
        'section': palm.section,
        'created_at': palm.created_at.isoformat() if palm.created_at else None,
        'updated_at': palm.updated_at.isoformat() if palm.updated_at else None,
    }


def user_to_dict(user):
    return {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def site_visit_to_dict(visit):
    return {
        'id': visit.id,
        'ip_address': visit.ip_address,
        'user_agent': visit.user_agent,
        'page_visited': visit.page_visited,
        'visited_at': visit.visited_at.isoformat() if visit.visited_at else None,
    }
