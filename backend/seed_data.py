#!/usr/bin/env python
"""Seed the database with admin user and sample palm profiles."""

import os
import random
import sys
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from palm_app.models.palm import PalmProfile
from palm_app.models.user import User
from palm_app.utils.auth import hash_password

ADMIN_EMAIL = 'admin@gmail.com'
ADMIN_PASSWORD = 'Admin123'

AREAS = ['Area A', 'Area B', 'Area C', 'Area D']
SECTIONS = ['North', 'South', 'East', 'West']
DONNER_NAMES = [
    'Ahmed Hassan', 'Fatima Al-Rashid', 'Mohammed Saleh', 'Layla Ibrahim',
    'Omar Khalil', 'Noura Mansour', 'Youssef Nasser', 'Sara Al-Farsi',
    'Khalid Barakat', 'Rania Haddad', 'Tariq Zayed', 'Hana Qasim',
]


def get_session():
    database_url = os.environ.get(
        'DATABASE_URL',
        'postgresql://palmuser:palmpass@localhost:5432/palmdb',
    )
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()


def seed_admin(session):
    existing = session.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing:
        print(f'Admin user {ADMIN_EMAIL} already exists, skipping.')
        return existing

    admin = User(
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        full_name='System Administrator',
        is_admin=True,
    )
    session.add(admin)
    session.flush()
    print(f'Created admin user: {ADMIN_EMAIL}')
    return admin


def seed_palms(session, count=75):
    existing_count = session.query(PalmProfile).count()
    if existing_count >= count:
        print(f'Database already has {existing_count} palms, skipping seed.')
        return

    to_create = count - existing_count
    print(f'Seeding {to_create} palm profiles...')

    for i in range(existing_count, existing_count + to_create):
        plant_date = datetime.utcnow() - timedelta(days=random.randint(365, 3650))
        age = max(1, (datetime.utcnow() - plant_date).days // 365)
        last_harvest = None
        harvest_amount = None
        if random.random() > 0.3:
            last_harvest = datetime.utcnow() - timedelta(days=random.randint(30, 365))
            harvest_amount = round(random.uniform(50, 1200), 2)

        palm = PalmProfile(
            palm_id=f'P{i:04d}',
            palm_code=f'CODE{i:04d}',
            plant_date=plant_date,
            donner_name=random.choice(DONNER_NAMES),
            donner_phone_number=f'05{random.randint(10000000, 99999999)}',
            harvest_amount=harvest_amount,
            last_harvest=last_harvest,
            age=age,
            images=[],
            area=random.choice(AREAS),
            section=random.choice(SECTIONS),
        )
        session.add(palm)

    session.flush()
    print(f'Seeded {to_create} palm profiles.')


def main():
    session = get_session()
    try:
        seed_admin(session)
        seed_palms(session)
        session.commit()
        print('Seed completed successfully.')
    except Exception as exc:
        session.rollback()
        print(f'Seed failed: {exc}', file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == '__main__':
    main()
