import base64
import gzip

from google.protobuf.json_format import MessageToDict

from . import logger
from ..mind_pb2 import Snapshot
from .parse_methods import *


################ FORMAT HANDLERS #####################

def handler_format_mind(result_name, path):
    """
    The data is a path to the file that the contains the snapshot (in bytes in the format: user_id + datetime
    of the snapshot + the snapshot itself).
    Parses it and extracts from it the dict of the current parser (result_name).
    """
    with gzip.open(path, 'rb') as reader:
        user_id, = struct.unpack('I', reader.read(4))
        datetime, = struct.unpack('L', reader.read(8))
        snapshot = Snapshot()
        snapshot.ParseFromString(reader.read())
    result = getattr(snapshot, result_name)
    dict_result_fields = MessageToDict(result, preserving_proto_field_name=True)
    if result_name == 'color_image':
        dict_result_fields['data'] = base64.b64decode(dict_result_fields.pop('data'))
    dict_result = {result_name: dict_result_fields, 'user_id': user_id, 'datetime': datetime}
    return dict_result


####################### PARSER ########################

format_handlers = {'mind': handler_format_mind}

parse = {'pose': parse_pose, 'feelings': parse_feelings,
         'color_image': parse_color_image, 'depth_image': parse_depth_image}


def run_parser(result_name, data, format='mind'):
    """
    One-time running parser.
    :param result_name: the type of the parser (options can be found in the configuration file).
    :param data: data as consumed from the message queue.
    :param format: what is the format/protocol of the data, for example, mind (more info in the handler_format_mind function).
    :return:
    """
    data = data.decode('utf-8')
    format_handler = format_handlers.get(format, None)
    if format_handler is None:
        raise ValueError(f'do not know to handle {format} format')
    dict_result = format_handler(result_name, data)
    return parse[result_name](dict_result)
