import json
import time

import pytest
from flask import Flask, request

from inmymind.client import upload_sample

app = Flask(__name__)
user = None
snapshot = None
host = '127.0.0.1'
port = 8000


@app.route('/')
def index():
    global user, snapshot
    if request.content_type == 'mind/user':
        user = request.data
    else:
        snapshot = request.data
    return '', 200


@pytest.fixture
def mock_server():
    app.run(host, port)


def test_client(mock_server):
    global user, snapshot
    upload_sample('mini-sample.mind.gz')
    time.sleep(3)
    assert user
    assert snapshot

print('handling user')
handle_user(json.dumps({'user_id': 19, 'username': 'amit',
                        'gender': 0, 'birthday': 80299}))
print('done handling user')
print('handling snapshot')
handle_snapshot(json.dumps({'user_id': 19, 'datetime': 120520,
                            'color_image': {'path': './data/color_image_example.jpg', 'width': 1920, 'height': 1080,
                                            'content_type': 'image/jpg'}}))

print('done handling snapshot')
