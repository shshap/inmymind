"""
The Client's writer handles the publishing of the data.
Every writer must be writer_conf (configurations for the writer if needed, such as, host and port),
and item (the item to be published) in initialization.
A writer is assumed to be a function, but it is possible to implement it as a class that has a write method,
that the manager will use.
The write method returns 0 on success and 2 on failure (if there is any chance to success on resend, do it
in the method and to not return 1. The manager will not try to recall the write method later).
"""

import time

import requests

from . import logger


def writer_http(writer_conf, item):
    """
    Sends the item to the address written in the writer_conf (host, port).
    It gets a dict with the fields 'data' and 'content_type' and write them in the matching fields in the requests.
    """
    logger.debug('in writer http')
    while True:
        try:
            r = requests.post(f"http://{writer_conf['host']}:{writer_conf['port']}/",
                              data=item['data'],
                              headers={'content_type': item['content_type']})
            break
        except requests.exceptions.ConnectionError:
            logger.info('connection error, try again in 5 sec')
            time.sleep(5)
    logger.debug('send request')
    if r.status_code != 200:
        logger.info(f'server rejected: {r.text}')
        return 2
    return 0
