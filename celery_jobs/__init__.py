import os
import json
import datetime
from google.oauth2 import service_account
from extensions import celery


@celery.task
def catch_pubsub_message(subscription_id):
    """
    Pulls messages from the channel @subscription_id, and executes a basic DB write of the message to demonstrate its retreival by viewing in admin panel. 
    """

    from google.cloud import pubsub_v1
    from concurrent.futures import TimeoutError

    from database.schema import PubSubMessage
    from extensions import db
    from main import create_app

    service_account_info = json.loads(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    project_id = service_account_info["project_id"]

    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)

    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

    def callback(message):
        message.ack()
        app = create_app()
        with app.app_context():
            data = json.loads(message.data.decode('utf-8'))
            publish_time = message.publish_time
            record = PubSubMessage(data=data,
                                   unique_tag=data["unique_tag"],
                                   publish_time=publish_time)
            db.session.add(record)
            db.session.commit()

    subscription_path = subscriber.subscription_path(
        project_id, subscription_id)

    streaming_pull_future = subscriber.subscribe(
        subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    timeout = 5
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            streaming_pull_future.cancel()
    return 0
