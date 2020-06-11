import json
import threading
import time

import pytest
from flask import Flask, request

from inmymind.saver import Saver

app = Flask(__name__)
app.user = None
app.snapshot = None
host = '127.0.0.1'
port = 5001


@app.route('/users/', methods=['POST'])
def users():
    app.user = request.data
    return '', 200


@app.route('/users/21/snapshots/', methods=['POST'])
def snapshots():
    app.snapshot = request.data
    return '', 200


@pytest.fixture
def api():
    t = threading.Thread(target=app.run, args=(host, port))
    t.daemon = True
    t.start()


def test_saver(api):
    saver = Saver(f'http://{host}:{port}')
    saver.save_all_types('user', json.dumps({'user_id': 21, 'username': 'Amit'}))
    saver.save('feelings', json.dumps({'user_id': 21, 'datetime': 120520, 'feelings': {}}))
    time.sleep(1)
    assert app.user
    assert app.snapshot
