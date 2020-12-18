# set up celery for syncing runcards on a schedule
import os
from main import create_app
from datetime import timedelta
from extensions import celery

# celery.config_from_object(__name__)
# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#beat-entries
# celery.conf.beat_schedule = {'start-work': {'task': 'tasks.celery_add_ex',
#                                            'schedule': timedelta(seconds=10)}}

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


from celery_jobs import *  # noqa
# @celery.task
# def celery_delay_method():
#    import datetime
#    f = open("tmp.txt", "a")
#    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
#    f.write("%s" % now)
#    f.close()
#    print("now", now)
#    return 0
