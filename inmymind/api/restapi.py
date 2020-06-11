import json
from urllib.parse import urlparse

from flask import Flask, make_response, send_file
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse

from . import logger
from . import config


class RestfulApi:
    """
    A RESTful API that wraps the DB. Every action that ones willing to perform on the DB, must pass throw the API.
    In that way, the DB type is not matters. Every DB can be in use, it just need to expose a DB service (all the methods
    that were implemented in the MongoService class), and the API will remain the same.
    """

    def __init__(self, host, port):
        """
        Gets the url of the API, that has the form: http://<host>:<port>.
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.parser = reqparse.RequestParser()
        self.parser.add_argument('user', type=dict, location='json')
        self.parser.add_argument('snapshot', type=dict, location='json')

    def run(self, db_service):
        if db_service is None:
            logger.fatal('no thought service is available')
            return 1
        try:
            self._add_resources(db_service)
            cors = CORS(self.app)
            self.app.run(host=self.host, port=self.port, debug=config['api']['flask_debug'],
                         use_reloader=config['api']['flask_debug'])
        except KeyboardInterrupt:
            return 0
        except Exception as error:
            logger.fatal(str(error))
            return 1

    def _add_resources(self, db_service):
        flds = {'db_service': db_service, 'parser': self.parser}
        # resource_class_kwargs will pass the kwargs to the __init__ of the Resource
        self.api.add_resource(Users,
                              '/users/',
                              resource_class_kwargs=flds)
        self.api.add_resource(UserById,
                              '/users/<int:user_id>/',
                              resource_class_kwargs=flds)
        self.api.add_resource(SnapshotsByUserId,
                              '/users/<int:user_id>/snapshots/',
                              resource_class_kwargs=flds)
        self.api.add_resource(SnapshotByUserIdSnapshotId,
                              '/users/<int:user_id>/snapshots/<string:snap_id>/',
                              resource_class_kwargs=flds)
        self.api.add_resource(ResultByUserIdSnapIdResultName,
                              '/users/<int:user_id>/snapshots/<string:snap_id>/<string:result_name>/',
                              resource_class_kwargs=flds)
        self.api.add_resource(DataByUserIdSnapIdResultName,
                              '/users/<int:user_id>/snapshots/<string:snap_id>/<string:result_name>/data/',
                              resource_class_kwargs=flds)


############################ RESOURCES #############################

def api_init(cls):
    setattr(cls, '__init__', new_init)
    return cls


def new_init(self, db_service, parser):
    self.db_service = db_service
    self.parser = parser


@api_init
class Users(Resource):
    def get(self):
        print('get request to /')
        items = self.db_service.get_users_list()
        return [self.db_service.utils_get_user_dict(item) for item in items], 200

    def post(self):
        logger.debug("Inside post in Users")
        self.parser.add_argument('user', type=dict, location='json')
        args = self.parser.parse_args()
        try:
            user = self.db_service.set_user(args.user)
        except ResourceWarning as error:
            return str(error), 409  # user already exists
        except TypeError as error:
            return str(error), 400  # invalid fields
        logger.debug(f"in Users post returns {user.to_json()}")
        return self.db_service.utils_get_user_dict(user), 201

    def delete(self):
        try:
            self.db_service.delete_all()
        except ResourceWarning as e:
            return str(e), 204
        return '', 200


@api_init
class UserById(Resource):

    def get(self, user_id):
        logger.debug("Inside get in UserById")
        user = self.db_service.get_user_by_id(user_id)
        if not user:
            return f"user {user_id} doesn't exist", 404
        return self.db_service.utils_get_user_dict(user), 200

    def put(self, user_id):
        logger.debug(f"Inside put in UserById")
        self.parser.add_argument('user', type=dict, location='json')
        args = self.parser.parse_args()
        cur_user = self.db_service.get_user_by_id(user_id)
        status = 201 if not cur_user else 200
        logger.debug(f"status is set to {status}")
        try:
            user = self.db_service.set_user(args.user) if not cur_user \
                else self.db_service.update_user(user_id, args.user)
        # the case of 409 is not possible because, lets suppose it is possible:
        # 409 on set_user => user already exists => status = 200 => update_user was called
        # 409 on update_user => user not exists => status = 201 => set_user was called
        # contradiction achieved!
        except TypeError as error:
            return str(error), 400  # invalid fields
        logger.debug(f"put returns {user.to_json()}")
        return user.to_mongo().to_dict(), status

    def delete(self, user_id):
        try:
            self.db_service.delete_user_by_id(user_id)
        except ResourceWarning as e:
            return str(e), 204
        return '', 200


@api_init
class SnapshotsByUserId(Resource):
    def get(self, user_id):
        logger.debug('inside get of snapshots by user id')
        user = self.db_service.get_user_by_id(user_id)
        if not user:
            return f"User {user_id} doesn't exist", 404
        snapshots = self.db_service.get_snapshots_by_user_id(user_id)
        logger.debug(f'got snapshots list {snapshots}')
        if not snapshots:
            return f"User {user_id} doesn't have snapshots yet", 200
        ret = []
        for snap in snapshots:
            ret.append(self.db_service.utils_get_serializable_snap_dict(snap))
        return ret, 200

    def post(self, user_id):
        logger.debug('inside post of snapshots by user id')
        self.parser.add_argument('snapshot', type=dict, location='json')
        args = self.parser.parse_args()
        user = self.db_service.get_user_by_id(user_id)
        if not user:
            return f"User {user_id} doesn't exist", 404
        if 'user_id' in args.snapshot.keys() and args.snapshot['user_id'] != user_id:
            return "cannot set snapshot of another user", 400
        args.snapshot['user_id'] = user_id
        print(args.snapshot)
        try:
            snap = self.db_service.set_snapshot(args.snapshot)
            logger.debug('successfully set snapshot')
        except ResourceWarning as error:
            # snap already exists, returns its snap_id
            return str(error).rsplit('_', 1)[1], 409
        except TypeError as error:
            return str(error), 400  # invalid fields
        dict_snap = self.db_service.utils_get_serializable_snap_dict(snap)
        logger.debug(f'going to send back {dict_snap}')
        return dict_snap, 201

    def delete(self, user_id):
        try:
            self.db_service.delete_all_snapshots_by_user_id(user_id)
        except ResourceWarning as e:
            return str(e), 204
        return '', 200


@api_init
class SnapshotByUserIdSnapshotId(Resource):
    def get(self, user_id, snap_id):
        snap = self.db_service.get_snapshot_by_user_id_snapshot_id(user_id, snap_id)
        if not snap:
            return f"Snapshot {snap_id} of user {user_id} doesn't exist", 404
        return self.db_service.utils_get_serializable_snap_dict(snap), 200

    def put(self, user_id, snap_id):
        logger.debug("inside put in snap by uid sip")
        self.parser.add_argument('snapshot', type=dict, location='json')
        args = self.parser.parse_args()
        cur_snap = self.db_service.get_snapshot_by_user_id_snapshot_id(user_id, snap_id)
        logger.debug('got cur_snap in put')
        status = 201 if not cur_snap else 200
        try:
            snap = self.db_service.set_snapshot(args.snapshot) if not cur_snap \
                else self.db_service.update_snapshot(cur_snap, args.snapshot)
        # 409 is not possible, see put method in UserById
        except TypeError as error:
            return str(error), 400  # invalid fields
        dict_snap = self.db_service.utils_get_serializable_snap_dict(snap)
        logger.debug(f'going to send back {dict_snap}')
        return dict_snap, status

    def delete(self, user_id, snap_id):
        try:
            self.db_service.delete_snapshot_by_user_id_snap_id(user_id, snap_id)
        except ResourceWarning as err:
            return str(err), 204
        return '', 200


@api_init
class ResultByUserIdSnapIdResultName(Resource):
    def get(self, user_id, snap_id, result_name):
        snapshot = self.db_service.get_snapshot_by_user_id_snapshot_id(user_id, snap_id)
        if not snapshot:
            return f"Snapshot {snap_id} doesn't exist", 404
        result = getattr(snapshot, result_name, None)
        if result is None:
            return f"result {result_name} doesn't exist in snapshot {snap_id} of user {user_id}", 404
        if result_name in ['color_image', 'depth_image']:
            return {'url': f'/users/{user_id}/snapshots/{snap_id}/{result_name}/data',
                    'content-type': result.content_type,
                    'width': result.width,
                    'height': result.height}
        return result.to_mongo().to_dict(), 200

    def delete(self, user_id, snap_id, result_name):
        try:
            self.db_service.delete_snapshot_by_user_id_snap_id_result_name(user_id, snap_id, result_name)
        except ResourceWarning as err:
            return str(err), 204
        return '', 200


@api_init
class DataByUserIdSnapIdResultName(Resource):
    def get(self, user_id, snap_id, result_name):
        snapshot = self.db_service.get_snapshot_by_user_id_snapshot_id(user_id, snap_id)
        if not snapshot:
            return f"Snapshot {snap_id} doesn't exist", 404
        if result_name not in ['color_image', 'depth_image']:
            return f'result {result_name} of {snap_id} does not contain any large data', 200
        result = getattr(snapshot, result_name, None)
        print(f'result is {result}')
        if not result:
            return f"result {result_name} doesn't exist in snapshot {snap_id} of user {user_id}", 404
        o = urlparse(result.path)
        if o.scheme == 'file' and o.netloc == 'localhost':
            return make_response(send_file(o.path, mimetype=result.content_type), 200)
        return 'Do not recognize data path', 404
