"""
This one-off script code demonstrates POC for uploading a custom function definition
as a cloud function, and then aggregating results from the cloud functions
via a subscriber pull. A data array is split up into chunks (row-wise) and
the cloud function is deployed on each chunk. The results are sent back to this central processing unit via Pub/Sub publish/pulls.

This mimics the action of a HPC cluster's MPI_Send to workers, and MPI_Recv from the workers, but by using Cloud functions. 

To run:
docker-compose run --rm web python -i scripts/upload_to_cloud_function_and_aggregate.py

The output is:

Message 0 2263504105992601 published
Message 1 2263504730788492 published
Message 2 2263498282453856 published
Message 3 2263487806408384 published
Cloud function results......
cloud function's process_data([1, 10, 100]) -> 74.0
local process_data([1, 10, 100]) -> 74.0
cloud function's process_data([4, 5, 6]) -> 10.0
local process_data([4, 5, 6]) -> 10.0
cloud function's process_data([10, 11, 12]) -> 22.0
local process_data([10, 11, 12]) -> 22.0
cloud function's process_data([3, 5, 10]) -> 12.0
local process_data([3, 5, 10]) -> 12.0

"""

import os
import json
import subprocess
from google.cloud import pubsub_v1
from google.oauth2 import service_account


def write_function_to_file(funcdef, target):
    fobj = open(target, "w")
    fobj.write(funcdef)
    fobj.close()


def process_data(x):
    import numpy as np
    return 2 * np.mean(x)


def parse_file_for_function(fname, funcname):
    """
    Look for a simple function definition in the source file:
    def funcname:
        return
    """
    f = open(fname, "r")
    lines = f.readlines()
    start = 0
    for i, line in enumerate(lines):
        if line.count(f"def {funcname}"):
            start = i
        if line.count("return"):
            end = i
            if start > 0:
                break

    func = ''.join(lines[start:end+1])
    return func


def callback(message, agg_struct):
    """
    Meant to pulling one chunk of work from cloud function.
    """
    data = json.loads(message)
    index = data["index"]
    result = data["result"]
    agg_struct[index] = result
    return 0


# GCP Pub/Sub
topic_name = "mpi-cloud-function-topic"
return_subscription_name = "m-retval-subscription"
return_topic_name = "m-retval"

service_account_info = json.loads(
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
project_id = service_account_info["project_id"]

credentials = service_account.Credentials.from_service_account_info(
    service_account_info)
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path(project_id,
                                  topic_name)

# build command for the cloud function,
# pubsub topic/subscription for the return message
pub_sub_info = {"project_id": project_id,
                "trigger_topic": topic_name,
                "return_topic_name": return_topic_name,
                "return_subscription_name": return_subscription_name}

redeploy_cloud_build = 0
gcloud_init = """gcloud config set project %(project_id)s""" % pub_sub_info
gcloud_build = """gcloud functions deploy mpi-cloud-function --runtime python38 --trigger-topic = %(trigger_topic)s --memory = 1GB --source = ./google_functions/deployment/mpi_cloud_function --entry-point = run --timeout = 540 --env-vars-file = ./google_functions/deployment/mpi_cloud_function/.env.yaml""" % pub_sub_info
gcloud_topic = """gcloud pubsub topics create %(return_topic_name)s""" % pub_sub_info
gcloud_subscription = """gcloud pubsub subscriptions create %(return_subscription_name)s --topic = %(return_topic_name)s --ack-deadline = 10 --expiration-period = never""" % pub_sub_info

# this is a custom function which the cloud function calls
function_to_upload = parse_file_for_function(__file__, "process_data")

write_function_to_file(
    function_to_upload,
    "google_functions/deployment/mpi_cloud_function/auxiliary.py")

if redeploy_cloud_build:
    commands = [gcloud_init,
                gcloud_topic,
                gcloud_subscription,
                gcloud_build]
    for command in commands:
        p = subprocess.Popen([command],
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        a, b = p.communicate()
        err = b.decode('utf-8')
        out = a.decode('utf-8')
        print(out, err)

# MPI_Send:
# chunks of data to send to the cloud function
chunks = ([1, 10, 100],
          [4, 5, 6],
          [10, 11, 12],
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

# MPI_Recv, until the correct number of data pulls is found.
cloud_func = {}
max_trials = 10
for j in range(max_trials):
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    pulls = subscriber.pull(subscription=subscription_path, max_messages=100)
    for msg in pulls.received_messages:
        message = msg.message.data.decode('utf-8')
        subscriber.acknowledge(subscription_path, [msg.ack_id])
        callback(message, cloud_func)

    subscriber.close()
    if len(cloud_func.keys()) == len(chunks):
        break

print("Cloud function results......")
for i, c in enumerate(chunks):
    print("cloud function's process_data(%s) -> %s" % (c, cloud_func[i]))
    print("local process_data(%s) -> %s" % (c, process_data(c)))
    assert cloud_func[i] == process_data(c)
