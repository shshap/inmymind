import json
from pathlib import Path

import pytest

from inmymind.parsers import run_parser

path = 'tests/snapshot_file_for_test.gz'


@pytest.mark.parametrize("result_name", [
    'pose',
    'feelings',
    'color_image',
    'depth_image',
],)
def test_parser_large_data(result_name):
    result = run_parser(result_name, path.encode('utf-8'))
    result = json.loads(result)
    assert set(result.keys()) == {'user_id', 'datetime', result_name}
    if result_name in ['pose', 'feelings']:
        assert isinstance(result[result_name], dict)
    else:
        assert Path(result[result_name]['path']).suffix == '.jpg'
