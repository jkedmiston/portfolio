# set up celery for syncing runcards on a schedule
import os
from main import create_app
from datetime import timedelta
import datetime
from extensions import celery
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


def send_email(email, subject="", message_text=""):
    """
    Sends the log file to me
    """
    message = MIMEMultipart()
    sender_email = os.environ["APP_EMAIL"]
    sender_password = os.environ["FOG_APP_PW"]
    message['From'] = sender_email
    message['To'] = email
    message['Subject'] = subject
    message.attach(
        MIMEText(message_text, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        return 'Email Sent!'
    except Exception as e:
        return str(e)


# celery.config_from_object(__name__)
# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#beat-entries
celery.conf.beat_schedule = {'start-work': {'task': 'tasks.celery_add_ex',
                                            'schedule': timedelta(seconds=10)},
                             'healthcheck': {'task': 'tasks.healthcheck',
                                             'schedule': timedelta(seconds=2 * 60)}}

celery.conf.timezone = 'UTC'
flask_app = create_app()
celery.conf.update(flask_app.config)
flask_app.app_context().push()
from extensions import db  # noqa


@celery.task
def healthcheck():
    """
    Check for last contact with local hardware 
    """
    from database.schema import Healthcheck
    hcs = Healthcheck.query.all()
    interval = None
    if len(hcs) == 1:
        hc = hcs[0]
        now = datetime.datetime.utcnow()
        interval = (now - hc.last_hit).total_seconds()
        print(f"interval {interval}")
        if interval > 12 * 60:
            send_email(email=os.environ["HEALTHCHECK_FAIL_NOTIFY_EMAIL"],
                       subject="Serverside healthcheck failed",
                       message_text="No contact in 60 minutes")
        else:
            return
    else:
        send_email(email=os.environ["HEALTHCHECK_FAIL_NOTIFY_EMAIL"],
                   subject="Serverside healthcheck failed",
                   message_text="No healthcheck entries")


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
from celery_jobs.background_analyze_user_sheet import *  # noqa
