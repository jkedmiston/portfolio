import pytest
import json
from unittest import mock
from google_functions.pubsub_send_recv import MPISendRecv
import functools


class FakePublisherClient:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.args = args

    @classmethod
    def init(cls, *args, **kwargs):
        cls(*args, **kwargs)

    def fake_publish_message(self, *args, **kwargs):
        self.publish_args = args
        self.publish_kwargs = kwargs.copy()
        return 0


class FakeStreamingPullFuture:
    def __init__(self, callback):
        self.callback = callback

    def result(self, *args, **kwargs):
        self.callback()


class FakeSubscriberClient:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.args = args

    @classmethod
    def init(cls, *args, **kwargs):
        cls(*args, **kwargs)

    def fake_subscribe(self, subscription_path, callback):
        """
        store the callback in a Fake
        """
        self.subscription_path = subscription_path
        self.callback = callback
        return FakeStreamingPullFuture(callback=callback)


def test_pubsub_dispatch(app, service_env):
    local_publisher = FakePublisherClient()
    local_subscriber = FakeSubscriberClient()
    mocked_publisher = mock.patch(
        'google.cloud.pubsub_v1.PublisherClient.__init__', side_effect=FakePublisherClient.init)
    mocked_subscriber = mock.patch(
        'google.cloud.pubsub_v1.SubscriberClient.__init__', side_effect=FakeSubscriberClient.init)
    mocked_publish = mock.patch(
        'google.cloud.pubsub_v1.PublisherClient.publish', side_effect=local_publisher.fake_publish_message)
    mocked_subscribe = mock.patch(
        'google.cloud.pubsub_v1.SubscriberClient.subscribe', side_effect=local_subscriber.fake_subscribe)
    mocked_subscribe_close = mock.patch(
        'google.cloud.pubsub_v1.SubscriberClient.close')
    mocked_credentials = mock.patch(
        'google.oauth2.service_account.Credentials.from_service_account_info', return_value=None)
    with app.test_request_context():
        with mocked_publisher as mocked_publisher_t, \
                mocked_subscriber as mocked_subscriber_t, \
                mocked_credentials as mocked_credentials_t, \
                mocked_publish as mocked_publish_t, \
                mocked_subscribe as mocked_subscribe_t,\
                mocked_subscribe_close as mocked_subscribe_close_t:
            topic_name = "mytopic"
            subscription_name = "mysubscription"
            data_to_send = {'mydata': 5}

            mpi_obj = MPISendRecv.init_from_env(
                topic_name=topic_name,
                subscription_name=subscription_name)
            mpi_obj.mpi_send(data_to_send)
            called_kwargs = json.loads(
                local_publisher.publish_kwargs["data"].decode('utf-8'))
            assert called_kwargs == data_to_send

            message_called_args = local_publisher.publish_args
            assert message_called_args == (
                'projects/%(project_id)s/topics/%(topic_name)s' % dict(project_id=service_env["project_id"],
                                                                       topic_name=topic_name),
            )

            def local_callback(msg):
                return msg
            # the use of functools partial is to force a workaround
            # since the pubsub callback can't call the message from the
            # pull in this test.
            cb = functools.partial(local_callback, msg=data_to_send)
            mpi_obj.mpi_recv(callback=cb)
            assert mpi_obj.retval == data_to_send
            mocked_publisher_t.assert_called()
            mocked_subscriber_t.assert_called()
            mocked_publish_t.assert_called()
            mocked_subscribe_t.assert_called()
            mocked_subscribe_close_t.assert_called()
