"""
General purpose cloud function 
"""
import os
import base64
import json
import time
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from auxiliary import process_data


def return_pubsub_message(data):
    """
    Send pub/sub message to the return topic from within the cloud function
    """
    service_account_info = json.loads(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    project_id = service_account_info["project_id"]
    return_topic_name = os.environ["RETURN_TOPIC"]
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    topic_path = publisher.topic_path(project_id,
                                      return_topic_name)

    tmp = data.pop('data')
    for key in tmp:
        data[key] = tmp[key]

    data["result"] = process_data(data["data_into_cloud_function"])
    data = json.dumps(data).encode('utf-8')
    max_ntrials = 10
    for j in range(max_ntrials):
        try:
            response = publisher.publish(topic_path, data=data)
            print("publish", response.result())
            return response
        except:
            time.sleep(1)
            continue
    raise RuntimeError('max trials exceeded')


def run(event, context):
    """
Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata. The `event_id` field contains the Pub/Sub message ID. The
         `timestamp` field contains the publish time.
    """

    print("""This Function was triggered by messageId {} published at {}
    """.format(context.event_id, context.timestamp))
    # print("keys %s" % str(event.keys())) # key data
    obj = base64.b64decode(event['data']).decode('utf-8')
    obj = json.loads(obj)
    print(context.resource, context.event_type,
          context.timestamp, context.event_id)
    return_pubsub_message(
        data={'data': obj, 'return message': context.event_id})
    return 0
