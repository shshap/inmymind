from urllib.parse import urlparse

import pika

from . import logger, config
from .parser import run_parser


class RabbitMQ:
    def __init__(self, result_name, url):
        """
        declares the exchange and all the queues.
        :param url: url of the form rabbitmq://<host>:<port>.
        :param result_name: what is the type of parser that is running
        """

        logger.debug("start settings")

        self.result_name = result_name
        url = urlparse(url)
        parameters = pika.ConnectionParameters(host=url.hostname, port=url.port)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.x_name = config['rabbitmq']['exchange']
        self.channel.exchange_declare(exchange=self.x_name, exchange_type=config['rabbitmq']['exchange_type'])
        logger.debug("exchange declared")

        durable = config['rabbitmq']['durable']
        saver_queue = config['rabbitmq']['saver_queue']
        self.channel.queue_declare(queue=saver_queue, durable=durable)
        self.channel.queue_bind(exchange=self.x_name, queue=saver_queue,
                                routing_key=config['rabbitmq']['routing_key_saver'])
        for name in config['rabbitmq']['parsers_queues'].values():
            self.channel.queue_declare(queue=name, durable=durable)
            self.channel.queue_bind(exchange=self.x_name, queue=name,
                                    routing_key=config['rabbitmq']['routing_key_parsers'])

        q_name = config['rabbitmq']['parsers_queues'][result_name]
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
        logger.debug(f'{body=}')
        logger.debug("callback got %r" % body)
        logger.debug(f"{properties}")
        format = properties.headers['content_type'].split('/')[0]
        res = run_parser(self.result_name, body, format)
        logger.debug(f'sending from parser to saver {res}')
        self.send_to_saver(res)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def send_to_saver(self, res):
        self.channel.basic_publish(
            exchange=self.x_name,
            routing_key=config['rabbitmq']['routing_key_saver'],
            body=res,
            properties=pika.BasicProperties(headers={'type': 'snapshot'},
                                            delivery_mode=2,
                                            content_type='application/json')
        )
