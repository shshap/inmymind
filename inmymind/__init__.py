import logging
import sys

import yaml

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(module)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

pika_logger = logging.getLogger('pika')
pika_logger.setLevel(logging.WARN)

with open('inmymind/conf.yaml', 'r') as reader:
    config = yaml.safe_load(reader)
