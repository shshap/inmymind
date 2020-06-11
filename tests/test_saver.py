import time

import pytest
from flask import Flask, request

from inmymind.saver import Saver

app = Flask(__name__)
user = None
snapshot = None
host = '127.0.0.1'
port = 8000


@app.route('/users')
def users():
    global user
    user = request.data
    return '', 200


@app.route('/users/42/snapshots')
def snapshots():
    global snapshot
    snapshot = request.data
    return '', 200


@pytest.fixture
def mock_api():
    app.run(host, port)


def test_saver(mock_api):
    saver = Saver()
    saver.save_all_types('user', {'user_id': 21, 'username': 'Amit'})
    saver.save({'feelings': {}})
    time.sleep(3)
    assert user
    assert snapshot
