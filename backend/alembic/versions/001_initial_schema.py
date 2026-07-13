"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'palm_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('palm_id', sa.String(50), nullable=False),
        sa.Column('palm_code', sa.String(50), nullable=False),
        sa.Column('plant_date', sa.DateTime(), nullable=False),
        sa.Column('donner_name', sa.String(100)),
        sa.Column('donner_phone_number', sa.String(20)),
        sa.Column('harvest_amount', sa.Float()),
        sa.Column('last_harvest', sa.DateTime()),
        sa.Column('age', sa.Integer()),
        sa.Column('images', sa.JSON()),
        sa.Column('area', sa.String(100)),
        sa.Column('section', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('palm_id'),
        sa.UniqueConstraint('palm_code'),
    )
    op.create_index('ix_palm_profiles_palm_code', 'palm_profiles', ['palm_code'])
    op.create_index('ix_palm_profiles_donner_name', 'palm_profiles', ['donner_name'])
    op.create_index('ix_palm_profiles_donner_phone_number', 'palm_profiles', ['donner_phone_number'])

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100)),
        sa.Column('is_admin', sa.Boolean(), server_default='false'),
        sa.Column('reset_token', sa.String(255)),
        sa.Column('reset_token_expires', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    op.create_table(
        'site_visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(255)),
        sa.Column('page_visited', sa.String(255)),
        sa.Column('visited_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('site_visits')
    op.drop_table('users')
    op.drop_index('ix_palm_profiles_donner_phone_number', table_name='palm_profiles')
    op.drop_index('ix_palm_profiles_donner_name', table_name='palm_profiles')
    op.drop_index('ix_palm_profiles_palm_code', table_name='palm_profiles')
    op.drop_table('palm_profiles')
