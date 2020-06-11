import threading
import time

import pytest
from flask import Flask, request

from inmymind.client import upload_sample

app = Flask(__name__)
app.user = None
app.snapshot = None
host = '127.0.0.1'
port = 8000


@app.route('/', methods=['POST'])
def index():
    if request.content_type == 'mind/user':
        app.user = request.data
    else:
        app.snapshot = request.data
    return '', 200


@pytest.fixture
def server():
    t = threading.Thread(target=app.run, args=(host, port))
    t.daemon = True
    t.start()


def test_client(server):
    upload_sample(path='tests/onesnap.mind.gz')
    time.sleep(1)
    assert app.user
    print("after assert user")
    assert app.snapshot
