import os
import json
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# https://github.com/googleapis/google-cloud-python/issues/4477


def publish_message(topic_name, data):
    """
    Push data to the GCP PubSub topic
    """
    service_account_info = json.loads(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    project_id = service_account_info["project_id"]

    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)
    publisher = pubsub_v1.PublisherClient(credentials=credentials)

    topic_path = publisher.topic_path(project_id, topic_name)

    data = json.dumps(data).encode('utf-8')

    response = publisher.publish(topic_path, data=data)
    print(response.result())
    #logger = logging.getLogger(__name__)
    #logger.info('PubSub: %s %s' % (topic_name, data))
    return response
