from urllib.parse import urlparse

from . import logger, config
from .message_queues import RabbitMQ

mq_handlers = {'rabbitmq': RabbitMQ}


def parser_service(result_name, mq_url=config['mq']['default_url']):
    """
    run the parser as a long-term service that consumes from a message queue (mq_url), calls the parser of type
    result_name and sends it to saver via the message queue.
    """
    MQ = mq_handlers.get(urlparse(mq_url).scheme, None)
    if MQ is None:
        raise ValueError(f"MQ type {urlparse(mq_url).scheme} is not supported")
    MQ(result_name, mq_url).run()
