from concurrent.futures._base import TimeoutError
import time
import os
import json
from google_functions.pubsub_send_recv import MPISendRecv
import numpy as np
from google.cloud import pubsub_v1
from google.oauth2 import service_account
arr = np.random.random((1000, 1000, 3))
np.save("np.t", arr)
np.load("np.t.npy")

# gcp pub sub
"""
# /home/jedmiston/projects/portfolio/google_functions/deployment/mpi_cloud_function
gcloud pubsub topics create mpi-cloud-function-topic
gcloud pubsub topics create mpi-cloud-function-topic-retval
cd /home/jedmiston/projects/portfolio/google_functions/deployment/mpi_cloud_function
gcloud functions deploy mpi-cloud-function --runtime python38 --trigger-topic=mpi-cloud-function-topic --memory=1GB --source=/home/jedmiston/projects/portfolio/google_functions/deployment/mpi_cloud_function --entry-point=run --timeout=540 --env-vars-file=/home/jedmiston/projects/portfolio/google_functions/deployment/mpi_cloud_function/app.yaml
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
# divide up into chunks and publish the result
chunks = ([1, 10, 100],)
#          [4, 20, 200],
#         [5, 30, 300])
for i, chunk in enumerate(chunks):
    # funcname in library
    data = {"index": i, "datain": chunk}
    data = json.dumps(data).encode('utf-8')
    response = publisher.publish(topic_path, data=data)
    result = response.result()
    print("Message %s %s published" % (i, result))


# collect messages on the pubsub channel
received_messages = []
subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
subscription_name = "m-retval-subscription"
subscription_path = subscriber.subscription_path(
    project_id, subscription_name)


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
for j in range(10):
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    pulls = subscriber.pull(subscription=subscription_path, max_messages=100)
    for msg in pulls.received_messages:
        message = msg.message.data.decode('utf-8')
        subscriber.acknowledge(subscription_path, [msg.ack_id])
        callback(message, func)

    subscriber.close()
    if len(func.keys()) == 1:
        break

for i, c in enumerate(chunks):
    print("%s -> %s" % (c, func[i]))
