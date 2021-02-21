import sys
import os
import pytest
import tempfile
import json


@pytest.fixture
def app(monkeypatch):
    from main import create_app
    from extensions import db
    db_fd, database = tempfile.mkstemp()
    database = database + "_c"

    database_url = 'sqlite:///%s' % database
    os.environ["DATABASE_URL"] = database_url
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = """{  "type": "service_account",  "project_id": "testproject",  "private_key_id": "f1", "private_key": "f2", "client_email": "na", "client_id": "a", "auth_uri": "a"}"""
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
    # See https://flask.palletsprojects.com/en/1.1.x/testing/
    os.close(db_fd)
    os.unlink(database)


@pytest.fixture
def service_env(app):
    service_account_info = json.loads(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    return service_account_info


def pytest_configure(config):
    # see https://docs.pytest.org/_/downloads/en/3.0.1/pdf/
    # detect if running from pytest
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test
