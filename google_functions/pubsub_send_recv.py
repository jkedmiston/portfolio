import json
import os
from google.cloud import pubsub_v1
from google.oauth2 import service_account


class MPISendRecv:
    """

    """

    def __init__(self, service_account_info, topic_name, subscription_name):
        # https://github.com/googleapis/google-cloud-python/issues/4477
        self.project_id = service_account_info["project_id"]

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info)
        self.credentials = credentials
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        self.topic_path = self.publisher.topic_path(self.project_id,
                                                    topic_name)
        self.subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name)

    @classmethod
    def init_from_env(cls, topic_name, subscription_name):
        service_account_info = json.loads(
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        return cls(service_account_info, topic_name=topic_name, subscription_name=subscription_name)

    def mpi_send(self, data):
        """
        Send data to topic
        """
        data = json.dumps(data).encode('utf-8')
        response = self.publisher.publish(self.topic_path, data=data)
        return response

    def mpi_recv(self, callback):
        self.local_callback = callback
        return self._mpi_recv(self.callback_wrapper)

    def callback_wrapper(self, *args, **kwargs):
        self.callback_args = args
        self.callback_kwargs = kwargs
        self.retval = self.local_callback(*args)

    def _mpi_recv(self, callback):
        """
        Return data from pubsub comm
        """
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path, callback=callback)
        print(f"Listening for messages on {self.subscription_path}..\n")
        # Wrap subscriber in a 'with' block to automatically call close() when done.
        timeout = 5
        with self.subscriber:
            try:
                # When `timeout` is not set, result() will block indefinitely,
                # unless an exception is encountered first.
                streaming_pull_future.result(timeout=timeout)
            except TimeoutError:
                streaming_pull_future.cancel()
