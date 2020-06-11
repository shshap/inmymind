"""
The Client's reader handles processing of the data, according the the its format.
Uses a driver (given as parameter) to get the data, and outputs the data that will be sent to the server.
The format of the data is a json dict {'data': `jsonify data`, 'content_type': `protocol`/`item type`.
A reader is assumed to be a function, but it is possible to implement it as a class that has a read method,
that the manager will use.
"""

import json
import struct

from google.protobuf.json_format import MessageToDict

from . import logger
from ..mind_pb2 import User, Snapshot


def reader_mind(driver):
    """
    A reader that handles data in mind format (that means, as the specifications in mind_pb2.py,
    and the format: user size - user - snapshot size - snapshot - snapshot size - snapshot and so on.
    :param driver: the driver that gets the data
    """
    logger.debug('in reader_mind start')
    try:
        logger.debug('in reader_mind going to read size')
        raw_user_size = driver.read(4)
        if raw_user_size == b'':
            print("File is empty, Job is done")
            yield None
        user_size, = struct.unpack('I', raw_user_size)
        user = User()
        user.ParseFromString(driver.read(user_size))
        dict_user = MessageToDict(user, preserving_proto_field_name=True, use_integers_for_enums=True)
        dict_user['user_id'] = int(dict_user.pop('user_id'))
        logger.debug('yielding user')
        yield {'data': json.dumps(dict_user), 'content_type': 'mind/user'}

        logger.debug('start reading snapshots')
        raw_user_id = struct.pack('I', user.user_id)
        while True:
            logger.debug('in reader_mind_mind going to read snapshot')
            raw_snap_size = driver.read(4)
            if raw_snap_size == b'':
                print("Done reading snapshots")
                yield None
            snap_size, = struct.unpack('I', raw_snap_size)
            raw_snapshot = driver.read(snap_size)
            snap = Snapshot()
            snap.ParseFromString(raw_snapshot)
            logger.debug(f'{snap.datetime=}')
            raw_datetime = struct.pack('L', snap.datetime)
            yield {'data': raw_user_id + raw_datetime + raw_snapshot,
                   'content_type': 'mind/snapshot'}
            logger.debug('going to yield None')
            yield None
    except TypeError:
        raise TypeError("The given file has not the right form")
