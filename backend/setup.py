from setuptools import setup, find_packages

setup(
    name='palm_app',
    version='1.0.0',
    description='Palm Management System Backend',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pyramid',
        'pyramid_tm',
        'SQLAlchemy',
        'alembic',
        'psycopg2-binary',
        'boto3',
        'waitress',
        'bcrypt',
        'transaction',
        'zope.sqlalchemy',
    ],
    entry_points={
        'paste.app_factory': [
            'main = palm_app:main',
        ],
    },
)
