"""
Message queues handlers for the server.
A message queue is configured by the conf.yaml and the url given as argument.
It gets the data (from the app) in the format: tuple of (data, content_type), and sends via the message queue, managing the messages by the content_type in the data.
"""

import gzip
import json
import os
import struct
from pathlib import Path
from stat import S_IREAD
from urllib.parse import urlparse

import pika

from . import logger, config


class RabbitMQ:
    def __init__(self, url):
        """
        declares the exchange and all the queues.
        :param url: url of the form rabbitmq://<host>:<port>
        """

        logger.debug("start settings")

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
        self.channel.queue_bind(exchange=self.x_name, queue=saver_queue, routing_key=config['rabbitmq']['routing_key_saver'])
        for name in config['rabbitmq']['parsers_queues'].values():
            self.channel.queue_declare(queue=name, durable=durable)
            self.channel.queue_bind(exchange=self.x_name, queue=name, routing_key=config['rabbitmq']['routing_key_parsers'])

    def close(self):
        self.connection.close()

    def handle_message(self, message: tuple):
        """
        Gets a tuple contains the data and the content_type and calls the method that matches the content_type
        """

        logger.debug('in handle_mind')
        data = message[0]
        content_type = message[1]
        obj = content_type.split('/')[1]
        if obj == 'user':
            self._send_user_to_saver(data)
        elif obj == 'snapshot':
            self._send_snapshot_to_parsers(data, content_type)
        else:
            raise ValueError("Do not know to handle {obj} object type in mind protocol")

    def _send_user_to_saver(self, json_user):
        """
        Gets a json dict of the user {'user_id': , 'username':, 'birthday':, 'datetime': }
        and sends it to the the saver by the message queue.
        """
        logger.debug(f'send user to saver {json.loads(json_user)}')
        self.channel.basic_publish(
            exchange=self.x_name,
            routing_key=config['rabbitmq']['routing_key_saver'],
            body=json_user,
            properties=pika.BasicProperties(headers={'type': 'user'},
                                            delivery_mode=2,
                                            content_type='application/json')
        )
        logger.debug('sent user to saver')

    def _send_snapshot_to_parsers(self, data, content_type):
        """
        Gets a the snapshot in bytes: user_id + datetime of snapshot + snapshot itself.
        Write it to a gz file and sends it via the message queue to the parsers.
        """
        user_id, = struct.unpack('I', data[:4])
        datetime, = struct.unpack('L', data[4:12])
        path = str(Path(config['rabbitmq']['snapshot_file_path'] % (user_id, datetime)).resolve())
        try:
            with gzip.open(path, 'wb+') as writer:
                writer.write(data)
        except Exception as error:
            logger.debug(str(error))
        os.chmod(path, S_IREAD)
        logger.debug(content_type)
        self.channel.basic_publish(
            exchange=self.x_name,
            routing_key=config['rabbitmq']['routing_key_parsers'],
            body=path,
            properties=pika.BasicProperties(delivery_mode=2,
                                            headers={'content_type': content_type})
        )
        logger.debug('sent to parsers')
