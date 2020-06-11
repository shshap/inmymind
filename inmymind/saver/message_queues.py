import json
from urllib.parse import urlparse

import pika

from . import logger, config


class RabbitMQ:
    def __init__(self, rabbit_url, saver):
        """
        declares the exchange and all the queues.
        :param rabbit_url: url of the form rabbitmq://<host>:<port>.
        :param saver: Saver object, that handles the saving logic.
        """

        logger.debug("start settings")

        self.saver = saver
        url = urlparse(rabbit_url)
        parameters = pika.ConnectionParameters(host=url.hostname, port=url.port)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.x_name = config['rabbitmq']['exchange']
        self.channel.exchange_declare(exchange=self.x_name, exchange_type=config['rabbitmq']['exchange_type'])
        logger.debug("exchange declared")

        durable = config['rabbitmq']['durable']
        q_name = config['rabbitmq']['saver_queue']
        self.channel.queue_declare(queue=q_name, durable=durable)
        self.channel.queue_bind(exchange=self.x_name, queue=q_name,
                                routing_key=config['rabbitmq']['routing_key_saver'])
        for name in config['rabbitmq']['parsers_queues'].values():
            self.channel.queue_declare(queue=name, durable=durable)
            self.channel.queue_bind(exchange=self.x_name, queue=name,
                                    routing_key=config['rabbitmq']['routing_key_parsers'])

        self.channel.basic_consume(queue=q_name, on_message_callback=self.callback)
        self.channel.basic_qos(prefetch_count=1)

    def run(self):
        try:
            logger.debug('start consuming')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.debug('stop consuming')
            self.channel.stop_consuming()
        self.connection.close()

    def callback(self, ch, method, properties, body):
        logger.debug(f'dedicated a body! {json.loads(body)}')
        logger.debug('got type %r and content %r' % (type(body), body))
        body = body.decode('utf-8')
        item_type = properties.headers.get('type', None)
        if item_type is None:
            logger.warning('message not contains a type header, skip this message')
        else:
            self.saver.save_all_types(properties.headers['type'], body)
        logger.debug('ack')
        ch.basic_ack(delivery_tag=method.delivery_tag)
