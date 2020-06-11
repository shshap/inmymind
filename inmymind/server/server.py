from urllib.parse import urlparse

from flask import Flask, request, Response

from . import logger, config
from .message_queues import RabbitMQ

mq_handlers = {'rabbitmq': RabbitMQ}


def run_server(host=config['server']['default_host'], port=config['server']['default_port'],
               publish=None, mq_url=config['mq']['default_url']):
    """
    main method of the server. Gets the data from the client and forwards it to the handler, which
    is a custom publish method (if the publish argument is not None) or a message queue (defined by the url).
    """
    app = Flask(__name__)
    if publish:
        app.config['handler'] = publish
    else:
        Handler = mq_handlers.get(urlparse(mq_url).scheme, None)
        if Handler is None:
            raise ValueError(f"MQ type {urlparse(mq_url).scheme} is not supported")
        app.config['handler'] = Handler(mq_url).handle_message

    @app.route('/', methods=['POST'])
    def get_message():
        try:
            handler = app.config.get('handler')
            logger.debug(request.headers['content_type'])
            handler((request.data, request.headers['content_type']))
        except Exception as e:
            return Response(str(e), 400)
        return '', 200

    try:
        app.run(host, port, debug=config['server']['debug'], use_reloader=config['server']['use_reloader'])
    except (Exception, KeyboardInterrupt) as error:
        logger.warning(str(error))
        if isinstance(app.config['handle'], RabbitMQ):
            app.config['handle'].close()
