import os
import datetime
import sqlalchemy
from celery.signals import task_prerun, task_postrun
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import Model
from sqlalchemy.ext.declarative import declared_attr


class BaseModel(Model):
    """
    The base model for all database models. This will include some common
    columns for all tables:
    """

    @declared_attr
    def id(self):
        return sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, nullable=False)

    @declared_attr
    def created_at(self):
        return sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.utcnow, nullable=True)


db = SQLAlchemy(model_class=BaseModel)
migrate = Migrate()
csrf = CSRFProtect()


redis_url = os.getenv('REDIS_URL')
redis_db_0 = redis_url + '/0?ssl_cert_reqs=CERT_NONE'
celery = Celery(__name__, broker=redis_db_0, backend=redis_db_0)
celery.conf.update(task_ignore_result=True,
                   result_expires=600,
                   )

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
