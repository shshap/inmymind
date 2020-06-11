"""
To add a parse method
Every parse_method gets a dict of the form: {'user_id': ,'datetime': , <result_name>: {..}}, as the rresult_name
is the parser's type (options can be found in the configurations file).
Every such method returns the json dict that will be sent to the RESTful API.
"""

import json
from pathlib import Path
import PIL
import struct

import matplotlib.pyplot as plt
import numpy as np

from . import logger

PATH_LARGE_DATA = str(Path('inmymind/data/inmymind_%d_%d_%s_data.%s').resolve())


def parse_pose(dict_pose: dict) -> str:
    return json.dumps(dict_pose)


def parse_feelings(dict_feelings: dict) -> str:
    return json.dumps(dict_feelings)


def _parse_rgb_color_image_helper(dict_color: dict) -> str:
    dimensions = dict_color['color_image']['width'], dict_color['color_image']['height']
    size = dimensions[0] * dimensions[1] * 3
    pixels = struct.unpack(f'{size}B', dict_color['color_image']['data'])
    pixels = [pixels[i:i + 3] for i in range(0, size, 3)]
    image = PIL.Image.new('RGB', dimensions)
    image.putdata(pixels)
    path = PATH_LARGE_DATA % (dict_color['user_id'], dict_color['datetime'], "color", "jpg")
    image.save(path)
    return path


def parse_color_image(dict_color: dict) -> str:
    path = _parse_rgb_color_image_helper(dict_color)
    dict_color['color_image'].pop('data')
    dict_color['color_image'].update({'path': path, 'content_type': 'image/jpg'})
    return json.dumps(dict_color)


def _parse_depth_image_helper(dict_depth: dict) -> str:
    dimensions = dict_depth['depth_image']['height'], dict_depth['depth_image']['width']
    pixels = np.asarray(dict_depth['depth_image']['data'])
    array_data = pixels.reshape(dimensions)
    path = PATH_LARGE_DATA % (dict_depth['user_id'], dict_depth['datetime'], "depth", "jpg")
    plt.imsave(path, array_data, cmap="hot")
    # plt.show()
    return path


def parse_depth_image(dict_depth: dict) -> str:
    path = _parse_depth_image_helper(dict_depth)
    dict_depth['depth_image'].pop('data')
    dict_depth['depth_image'].update({'path': path, 'content_type': 'image/jpg'})
    return json.dumps(dict_depth)
