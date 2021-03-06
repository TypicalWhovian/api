from setuptools import setup

setup(
    name='api',
    packages=['api'],
    include_package_data=True,
    install_requires=[
        'flask',
        'mimesis',
        'peewee',
        'psycopg2',
        'PyJWT',
        'PyYAML',
    ],
)
