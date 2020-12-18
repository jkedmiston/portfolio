# set up celery for syncing runcards on a schedule
from main import create_app
import os
from datetime import timedelta
from extensions import celery

# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#beat-entries
celery.conf.beat_schedule = {'start-work': {'task': 'tasks.celery_add_ex',
                                            'schedule': timedelta(seconds=10)}}

celery.conf.timezone = 'UTC'
flask_app = create_app()
celery.conf.update(flask_app.config)
flask_app.app_context().push()
from extensions import db  # noqa


@celery.task
def celery_add_ex():
    """adds a random number to a database"""
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
