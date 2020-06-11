import json
import requests
import time

from . import logger

###################### HANDLE USER ##########################


def handle_user(data_user, url):
    """
    Gets the user data in json format, and the url of the RESTful API, and sends the data to the API.
    """
    logger.debug("Handling user...")
    dict_user = json.loads(data_user)
    while True:
        try:
            r_post = _post_user(dict_user, url)
            logger.debug('got status code from post: %d' % r_post.status_code)

            if r_post.status_code == 201:
                logger.debug('successsssss')
                print(r_post.json())
                return
            if r_post.status_code == 409:
                # resource already exists, that means other parts of the snapshot are already in the db
                # so, the request should be 'post' and not 'put'
                r_put = _put_user(dict_user, url)
                if r_put.status_code == 200:
                    print(r_put.json())
                    return
                else:
                    raise Exception(r_put.text)
            else:
                logger.debug('raising an exception')
                raise Exception(r_post.text)
        except requests.exceptions.ConnectionError as error:
            logger.debug(str(error))
            time.sleep(5)


def _post_user(dict_user, url):
    logger.debug(f"send post request for user {dict_user}")
    return requests.post(url + '/users/',
                         data=json.dumps({'user': dict_user}),
                         headers={'Content-type': 'application/json'})


def _put_user(dict_user, url):
    logger.debug(f"send put request for user {dict_user}")
    user_id = dict_user['user_id']
    return requests.put(url + f'/users/{user_id}/',
                        data=json.dumps({'user': dict_user}),
                        headers={'Content-type': 'application/json'})


###################### HANDLE SNAPSHOT ##########################

def handle_snapshot(data_snap, url):
    """
    Gets the user snapshot in json format, and the url of the RESTful API, and sends the data to the API.
    """
    logger.debug("Handling snapshot...")
    dict_snap = json.loads(data_snap)
    while True:
        try:
            r_post = _post_snapshot(dict_snap, url)
            logger.debug('got status code from post: %d' % r_post.status_code)
            if r_post.status_code == 201:
                logger.debug('successss')
                return
            elif r_post.status_code == 409:
                # resource already exists, that means other parts of the snapshot are already in the db
                # so, the request should be 'post' and not 'put'
                snap_id = r_post.json()
                logger.debug(f'snap_id for put is {snap_id} of type {type(snap_id)}')
                r_put = _put_snapshot(dict_snap, snap_id, url)
                logger.debug(f'got r_put {r_put}')
                if r_put.status_code == 200:
                    return
                else:
                    raise Exception(r_put.json())
            else:
                logger.debug('raising an exception')
                raise Exception(r_post.json())

        except requests.exceptions.ConnectionError as error:
            logger.debug(str(error))
            time.sleep(5)


# the form of dict_snap is {'user_id': 21, 'username: 'Amit', '<field>': {...}, '<field>': {...}}
def _post_snapshot(dict_snap, url):
    logger.debug(f"send post request for snap {dict_snap['user_id']}")
    user_id = dict_snap['user_id']
    return requests.post(url + f'/users/{user_id}/snapshots/',
                         data=json.dumps({'snapshot': dict_snap}),
                         headers={'Content-type': 'application/json'})


def _put_snapshot(dict_snap, snap_id, url):
    logger.debug(f"send put request for snap {dict_snap['user_id']}")
    user_id = dict_snap['user_id']
    return requests.put(url + f'/users/{user_id}/snapshots/{snap_id}/',
                        data=json.dumps({'snapshot': dict_snap}),
                        headers={'Content-type': 'application/json'})
