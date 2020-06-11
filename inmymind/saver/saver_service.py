from urllib.parse import urlparse

from .message_queues import RabbitMQ
from .saver import Saver

mqs = {'rabbitmq': RabbitMQ}


def saver_service(api_url, mq_url):
    """
    run the saver as a long-term service that gets the messages from a message queue (mq_url) and send them
    to the RESTful API (api_url) that will save them to the db.
    """
    MQ = mqs.get(urlparse(mq_url).scheme, None)
    if MQ is None:
        raise ValueError(f"MQ type {urlparse(mq_url).scheme} is not supported")
    MQ(mq_url, Saver(api_url)).run()
