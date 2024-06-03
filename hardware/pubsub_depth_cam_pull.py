"""
Pulls messages from the channel to trigger a depth camera event
"""
import time
import os
import json
import subprocess
from subprocess import TimeoutExpired
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError
from misc_utilities import generate_uuid
from google.oauth2 import service_account
from google_functions.google_storage import upload_file
from google_functions.pubsub import publish_message
topic = os.environ["DEPTH_CAM_TO_SERVER_TOPIC"]
subscription_id = os.environ["SERVER_TO_DEPTH_CAM_SUBSCRIPTION"]

service_account_info = json.loads(
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
project_id = service_account_info["project_id"]

credentials = service_account.Credentials.from_service_account_info(
    service_account_info)


def reset_camera():
    """
    USB port reset. 
    The realsense cam is finicky and not reliable on reuse. This resets the USB. Functionality from https://askubuntu.com/questions/645/how-do-you-reset-a-usb-device-from-the-command-line
    """
    cmd = 'python r2.py'
    cmd = 'python reset_usb.py search "RealSense"'
    proc = subprocess.Popen([cmd],
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    print("stdout %s" % stdout)
    print("stderr %s" % stderr)
    return


def reset_camera1():
    """
    USB port reset. 
    The realsense cam is finicky and not reliable on reuse. This resets the USB. Functionality from https://askubuntu.com/questions/645/how-do-you-reset-a-usb-device-from-the-command-line
    """
    cmd = 'python r2.py'
    proc = subprocess.Popen([cmd],
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    print("stdout %s" % stdout)
    print("stderr %s" % stderr)
    return


def callback(message):
    """
    Take the triggered photo 
    """
    print("callback on message %s" % message)
    message.ack()
    data = json.loads(message.data.decode('utf-8'))
    publish_time = message.publish_time

    reset_camera1()
    ntrials = 10
    for j in range(ntrials):
        print("trial %s" % j)
        proc = subprocess.Popen(["run_d435"],
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate(timeout=2)

            # push up result of depth cam to storage and send path in
            # the return message
            unique_tag = data["unique_tag"]
            fname_target = "depth_cam_%s.txt" % unique_tag
            bmp_target = "depth_cam_image_%s.bmp" % unique_tag

            if os.path.isfile("depth0.txt") and os.path.isfile("depth0.bmp"):
                upload_file("depth0.txt", fname_target)
                upload_file("depth0.bmp", bmp_target)

            # send info on the file location in storage

            publish_message(
                topic_name=os.environ["DEPTH_CAM_TO_SERVER_TOPIC"],
                data={"fname": fname_target,
                      "colormap": bmp_target,
                      "unique_tag": unique_tag,
                      "initial_publish_time": publish_time.strftime("%Y-%m-%d %H:%M:%S"),
                      }
            )

            return
        except TimeoutExpired:
            print("timeout expired")
            proc.kill()
            # stdout, stderr = proc.communicate()
            reset_camera()
            time.sleep(1)

    publish_message(
        topic_name=os.environ["DEPTH_CAM_TO_SERVER_TOPIC"],
        data={}
    )
    raise Exception("Proc communication error")


while True:
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    subscription_path = subscriber.subscription_path(
        project_id, subscription_id)

    streaming_pull_future = subscriber.subscribe(
        subscription_path, callback=callback)
    #print(f"Listening for messages on {subscription_path}..\n")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        timeout = 2
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            streaming_pull_future.cancel()

        # print("looping")
