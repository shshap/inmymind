![build status](https://travis-ci.org/shshap/inmymind.svg?branch=master)
![coverage](https://codecov.io/gh/shshap/inmymind/branch/master/graph/badge.svg)

# inmymind

inmymind is a Python package for dealing with snapshots 
from your brain. [Full documentation](https://shshap-inmymind.readthedocs.io/en/latest/)

## Installation

Clone the repository, install its dependencies, virtual environment 
and requirements, and activate it:
```bash
$ git clone git@github.com:shanish77/inmymind.git
$ cd inmymind/
$ ./script/install.sh
$ source .enc/bin/activate
```
## USAGE

inmymind's subpackages have some subpackages: client, server, parsers, saver, api, cli, gui.

###client
Uploads the sample to the server, snapshot by snapshot.
The client is available as inmymind.client and expose the following API: 

```python
from inmymind.client import upload_sample
>>> upload_sample(host='127.0.0.1', port=8000, path='sample.mind.gz')
```
Note: the sample's path should have the extensions: .<sample format>.<file format>.
And the following CLI:

```bash
$ python -m cortex.client upload-smaple \
    -h/--host '127.0.0.1'             \
    -p/--port 8000                    \
    'snapshot.mind.gz'
```

###server
Accepts connections from clients and publishes the messages.  
The server connects to a message queue and to publish the messages to the **saver**
and **parsers**. 
The server is available as inmymind.server and exposes the following CLI:

```bash
$ python -m cortex.server run-server  \
    -h/--host '127.0.0.1'           \
    -p/--port 8000                  \
    'rabbitmq://127.0.0.1:5672/' #only a url is accepted here
```

And the following API:

```python
from inmymind.server import run_server
>>> def print_message(message):
...     print(message)
>>> run_server(host='127.0.0.1', port=8000, publish=print_message)
```
That is, the server can get a publish method as an argument, and to use it rather
then publish the result to a message queue. 

###parsers
A parser handles a specific result of the snapshot. The available parsers are:
pose, feelings, color_image, depth_image. \
The parsers are available as inmymind.parsers and expose the following CLI:

```bash
$ python -m cortex.parsers run-parser 'pose' 'rabbitmq://127.0.0.1:5672/'
```
Runs the parser as a service, that connects to the message queue, consumes messages 
and publishes the results to the **saver**. \
And the following command:

```bash
$ python -m cortex.parsers parse 'pose' 'snapshot.raw' > 'pose.result'
```
Accepts a path to some raw data, as consumed from the message queue, that is,
a path to a file in mind format: user_id encoded in bytes + datetime of the snapshot 
(encoded in bytes) + raw snapshot (as in the sample). \
It also exposes the following API: 

```python
from inmymind.parsers import run_parser
>>> data = ...
>>> result = run_parser('pose', data)
```
Here only the parse logic is performed. The data is as consumed from the message queue
(assumed to be in mind format).


###saver
Uploads the data to **the API**, that will save it to the database.
The saver is available as inmymind.saver and expose the following CLI:

```bash
$ python -m cortex.saver run-saver 'http://127.0.0.1:5000' 'rabbitmq://127.0.0.1:5672/'
```
Runs the saver as a service, that connects to the message queue, consumes messages
and uploads then to the **the API**. \
And the following command:

```bash
$ python -m cortex.saver save                 \
    -r/--restapi 'http://localhost:5000' \
    'pose'                                  \
    'pose.result'
```
Accepts a path to some raw data, as consumed from the message queue, that is,
a JSON serialization of a dictionary that contains the keys: user_id, datetime and 
<result_name> (In this example, it is 'pose'). \
It also exposes the following API: 

```python
from inmymind.saver import Saver
>>> saver = Saver(the_api_url)
>>> data = ...
>>> saver.save('pose', data)
```
Here, the data is as consumed from the message queue.

###the API
A RESTful API, that wraps the database. It handles all the CRUD operations, as listed below.
If one would like to use another database, he would just need to write a simple
service for the database. see more in the full documentation.
The saver is available as inmymind.api and expose the following API:
```python
from inmymind.api import run_api_server
>>> run_api_server(
    host = '127.0.0.1',
    port = 5000,
    database_url = 'mongo://127.0.0.1:27017'
)
```
And the following CLI:

```bash
python -m cortex.api run-server \
    -h/--host '127.0.0.1'       \
    -p/--port 5000              \
    -d/--database 'mongo://127.0.0.1:27017
```

The endpoints are:

#####GET /users
Returns the list of all the supported users, including their IDs and names only.

#####POST /users
Saves a new user to the database. Note, that it will not save the user if the user_id already 
exists in the database. In that case, a status code of 409 will be returned, and it is recommended
to put this user by the **PUT /users/user-id** request.

**DELETE /users** \
Deletes all the users and all the snapshots from the database.


**GET /users/user-id** \ 
Returns the specified user's details: ID, name, birthday and gender.

**PUT /users/user-id** \
Saves a the user to the database. Will create a new user if the user-id id not
already exists does not already exists.

**DELETE /users/user-id** \
Deletes the user and all of its snapshots from the database.


**GET /users/user-id/snapshots** \
Returns the list of the specified user's snapshot IDs and datetimes only.

**POST /users/user-id/snapshots** \
Saves a new snapshot of the given user to the database. Note, that it will not save
the snapshot if the snapshot's datetime already exists in the database. 
In that case, a status code of 409 will be returned, and it is recommended
to put this user by the **PUT /users/user_id** request.

**DELETE /users/user-id/snapshots** \
Deletes all the snapshots of the given user from the database.


**GET /users/user-id/snapshots/snapshot-id** \
Returns the specified snapshot's details: ID, datetime, and the available results' names only (e.g. pose).

**PUT /users/user-id/snapshots/snapshot-id** \
Saves a the snapshot to the database. Will create a new snapshot if the user-id id not
already exists does not already exists.

**DELETE /users/user-id/snapshots/snapshot-id** \
Deletes the snapshot from the database.


**GET /users/user-id/snapshots/snapshot-id/result-name** \
Returns the specified snapshot's result in a reasonable format.  
Supported results are: pose, color-image, depth-image and feelings.  
color-image and depth-image have large binary data, so the return data contains metadata only, with their data
being available via: **GET /users/user-id/snapshots/snapshot-id/result-name/data**

**DELETE /users/user-id/snapshots/snapshot-id/result-name** \
Deletes the result from the snapshot, in the database.


**GET /users/user-id/snapshots/snapshot-id/result-name/data** \
Returns the large binary data.


###the CLI
Consumes **the API** and reflects it. 
The cli is available as inmymind.cli and expose the following commands:

```bash
$ python -m cortex.cli get-users 
$ python -m cortex.cli get-user 1
$ python -m cortex.cli get-snapshots 1
$ python -m cortex.cli get-snapshot 1 2 
$ python -m cortex.cli get-result 1 2 'pose'
```

###the GUI
The GUI consumes the API and reflects it.
The cli is available as inmymind.cli and expose the following API:

```python
from inmymind.gui import run_server
>>> run_server(
    host = '127.0.0.1',
    port = 8080,
    api_host='127.0.0.1',    
    api_port = 5000
)
```
And the following CLI:

```bash
$ python -m cortex.api run-server \
    -h/--host '127.0.0.1'       \
    -p/--port 8080              \
    -H/--api-host '127.0.0.1'   \
    -P/--api-port 5000
```

## Deployment

```bash
$ ./scripts/run-pipline.sh
```

HAVE FUN!


