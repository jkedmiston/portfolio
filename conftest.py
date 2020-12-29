import sys
import os
import pytest
import tempfile


@pytest.fixture
def app(monkeypatch):
    from main import create_app
    from extensions import db
    db_fd, database = tempfile.mkstemp()
    database = database + "_c"

    database_url = 'sqlite:///%s' % database
    os.environ["DATABASE_URL"] = database_url
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
    # See https://flask.palletsprojects.com/en/1.1.x/testing/
    os.close(db_fd)
    os.unlink(database)


def pytest_configure(config):
    # see https://docs.pytest.org/_/downloads/en/3.0.1/pdf/
    # detect if running from pytest
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test
