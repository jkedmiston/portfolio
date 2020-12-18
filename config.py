'''App config.'''
import os


def fetch_from_env_or_warn(key):
    value = os.environ.get(key)
    if not value:
        print('"%s" environment variable seems to be missing.' % key)
    return value


def fetch_from_env_or_fail(key):
    value = os.environ.get(key)
    if value:
        return value
    else:
        raise KeyError('"%s" must be present in host environment.' % key)


class Config:
    '''Global configuration variables.'''
    DB_PASSWORD = fetch_from_env_or_fail("DB_PASSWORD")
    FLASK_DEBUG = fetch_from_env_or_fail("FLASK_DEBUG")
    SQLALCHEMY_DATABASE_URI = fetch_from_env_or_fail('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = fetch_from_env_or_fail('SECRET_KEY')
    GOOGLE_APPLICATION_CREDENTIALS = fetch_from_env_or_fail(
        'GOOGLE_APPLICATION_CREDENTIALS')
    UPLOAD_FOLDER = "tmp"
    # LOG_LEVEL = 'debug'  # fetch_from_env_or_fail('LOG_LEVEL')
