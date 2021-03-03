"""
This code demonstrates POC for uploading a custom function definition
as a cloud function, and then aggregating results from the cloud functions
via a subscriber pull.
"""
import subprocess
import os
import json
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# GCP Pub/Sub
"""
gcloud pubsub topics create mpi-cloud-function-topic
gcloud pubsub topics create mpi-cloud-function-topic-retval
cd /home/jedmiston/projects/portfolio/ \
    google_functions/deployment/mpi_cloud_function
gcloud functions deploy mpi-cloud-function --runtime python38 --trigger-topic=mpi-cloud-function-topic --memory=1GB --source=/home/jedmiston/projects/portfolio/google_functions/deployment/mpi_cloud_function --entry-point=run --timeout=540 --env-vars-file=/home/jedmiston/projects/portfolio/google_functions/deployment/mpi_cloud_function/.env.yaml
"""

service_account_info = json.loads(
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
project_id = service_account_info["project_id"]
topic_name = "mpi-cloud-function-topic"
credentials = service_account.Credentials.from_service_account_info(
    service_account_info)
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path(project_id,
                                  topic_name)

# build command for the cloud function,
# pubsub topic/subscription for the return message
return_subscription_name = "m-retval-subscription"
return_topic_name = "m-retval"
pub_sub_info = {"project_id": project_id,
                "trigger_topic": topic_name,
                "return_topic_name": return_topic_name,
                "return_subscription_name": return_subscription_name}

gcloud_init = """gcloud config set project %(project_id)s""" % pub_sub_info
gcloud_build = """gcloud functions deploy mpi-cloud-function --runtime python38 --trigger-topic=%(trigger_topic)s --memory=1GB --source=./google_functions/deployment/mpi_cloud_function --entry-point=run --timeout=540 --env-vars-file=./google_functions/deployment/mpi_cloud_function/.env.yaml""" % pub_sub_info
gcloud_topic = """gcloud pubsub topics create %(return_topic_name)s""" % pub_sub_info
gcloud_subscription = """gcloud pubsub subscriptions create %(return_subscription_name)s --topic=%(return_topic_name)s --ack-deadline=10 --expiration-period=never""" % pub_sub_info


function_to_upload = """
import numpy as np
def process_data(x):
    return 2 * np.mean(x)
"""


def write_function_to_file(funcdef, target):
    fobj = open(target, "w")
    fobj.write(funcdef)
    fobj.close()


write_function_to_file(
    function_to_upload, "google_functions/deployment/mpi_cloud_function/auxiliary.py")

commands = [gcloud_init, gcloud_topic, gcloud_subscription, gcloud_build]
for command in commands:
    p = subprocess.Popen([command],
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    a, b = p.communicate()
    err = b.decode('utf-8')
    out = a.decode('utf-8')
    print(out, err)


chunks = ([1, 10, 100],
          [4, 5, 6],
          [3, 5, 10])
# each chunk is submitted as a message to a cloud function, where the function
# in process_data() is applied to the entry.
for i, chunk in enumerate(chunks):
    data = {"index": i, "data_into_cloud_function": chunk}
    data = json.dumps(data).encode('utf-8')
    response = publisher.publish(topic_path, data=data)
    result = response.result()
    print("Message %s %s published" % (i, result))


# collect return messages on the pubsub return subscription
received_messages = []
subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
subscription_path = subscriber.subscription_path(
    project_id, return_subscription_name)


def callback(message, agg):
    data = json.loads(message)
    try:
        x = data["return message"]
        index = data["index"]
        result = data["result"]
        agg[index] = result
    except:
        print("error")

    return 0


func = {}
max_trials = 10
for j in range(max_trials):
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    pulls = subscriber.pull(subscription=subscription_path, max_messages=100)
    for msg in pulls.received_messages:
        message = msg.message.data.decode('utf-8')
        subscriber.acknowledge(subscription_path, [msg.ack_id])
        callback(message, func)

    subscriber.close()
    if len(func.keys()) == len(chunks):
        break

print("Cloud function results!")
for i, c in enumerate(chunks):
    print("process_data(%s) -> %s" % (c, func[i]))
