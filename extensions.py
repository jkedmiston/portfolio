from celery.signals import task_prerun, task_postrun
from celery import Celery
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


redis_url = os.getenv('REDIS_URL')
redis_db_0 = redis_url + '/0'
celery = Celery(__name__, broker=redis_db_0)


@task_prerun.connect
def on_task_init(*args, **kwargs):
    # https://stackoverflow.com/questions/45215596
    from extensions import db  # noqa
    db.engine.dispose()


@task_postrun.connect
def close_session(*args, **kwargs):
    # https://docs.sqlalchemy.org/en/13/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session.remove # noqa
    # https://github.com/pallets/flask-sqlalchemy/blob/master/flask_sqlalchemy/__init__.py#L845-L851 # noqa
    # https://stackoverflow.com/questions/12044776
    db.session.remove()
