# set up celery for syncing runcards on a schedule
from main import create_app
import os
from celery.signals import task_prerun, task_postrun
from celery import Celery
from datetime import timedelta

# DATABASE_URL is from the EBR
redis_url = os.getenv('REDIS_URL')
redis_db_0 = redis_url + '/0'
app = Celery(__name__, broker=redis_db_0)
app.config_from_object(__name__)

# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#beat-entries
app.conf.beat_schedule = {'start-work': {'task': 'tasks.celery_add_ex',
                                         'schedule': timedelta(seconds=10)}}

app.conf.timezone = 'UTC'
flask_app = create_app()
app.conf.update(flask_app.config)
flask_app.app_context().push()
from extensions import db  # noqa


@task_prerun.connect
def on_task_init(*args, **kwargs):
    # See: https://stackoverflow.com/questions/45215596
    from extensions import db  # noqa
    db.engine.dispose()


@task_postrun.connect
def close_session(*args, **kwargs):
    # - https://docs.sqlalchemy.org/en/13/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session.remove # noqa
    # - https://github.com/pallets/flask-sqlalchemy/blob/master/flask_sqlalchemy/__init__.py#L845-L851 # noqa
    # - https://stackoverflow.com/questions/12044776
    db.session.remove()


@app.task
def celery_add_ex():
    import numpy as np
    from extensions import db  # noqa
    from database.schema import RandomData
    rd = RandomData.query.get(1)
    if rd is None:
        rd = RandomData(value=np.random.random())
        db.session.add(rd)
    else:
        rd.value = np.random.random()
    db.session.commit()
    return 0
