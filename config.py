import os


def fetch_from_env_or_warn(key):
    value = os.environ.get(key)
    if not value:
        print('"%s" environment variable is missing.' % key)
    return value


def fetch_from_env_or_fail(key):
    value = os.environ.get(key)
    if value:
        return value
    else:
        raise KeyError('"%s" is required. ' % key)


class Config:
    '''Global configuration variables.'''
    FLASK_DEBUG = fetch_from_env_or_fail("FLASK_DEBUG")
    GOOGLE_APPLICATION_CREDENTIALS = fetch_from_env_or_warn(
        'GOOGLE_APPLICATION_CREDENTIALS')
    REDIS_URL = fetch_from_env_or_fail('REDIS_URL')
    SQLALCHEMY_DATABASE_URI = fetch_from_env_or_fail('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = fetch_from_env_or_fail('SECRET_KEY')
    UPLOAD_FOLDER = "tmp"
