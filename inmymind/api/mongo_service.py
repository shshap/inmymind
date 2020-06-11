from urllib.parse import urlparse

from bson import ObjectId
from mongoengine import connect
from mongoengine.errors import NotUniqueError, ValidationError, FieldDoesNotExist
from typing import List, Optional

from . import logger, config
from .mongo_objects import User, Snapshot, Pose, Feelings, Image


class MongoService:
    def __init__(self, raw_url):
        db_name = config['db']['db_name']
        url = urlparse(raw_url)
        connect(db_name, alias=config['db']['alias'], host=url.hostname, port=url.port)

    ############################ UTILS ############################

    def utils_get_user_dict(self, user: User):
        dict_user = user.to_mongo().to_dict()
        dict_user['user_id'] = dict_user.pop('_id')
        return dict_user

    def utils_get_serializable_snap_dict(self, obj):
        dict_snap = obj.to_mongo().to_dict()
        print(f'dict_snap is {dict_snap}')
        for key, value in list(dict_snap.items()):
            if isinstance(value, ObjectId):
                new_key = key[1:] if key[0] == '_' else key
                dict_snap[new_key] = str(dict_snap.pop(key))
        return dict_snap

    ############################ GET ############################
    def get_users_list(self) -> Optional[List[User]]:
        users = User.objects.only("user_id", "username")
        return list(users)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        user = User.objects(user_id=user_id).first()
        return user

    def get_snapshots_by_user_id(self, user_id) -> List[Snapshot]:
        logger.debug('in get_snapshots_by_user_id')
        snapshots = Snapshot.objects(user_id=user_id).only("pk", "datetime")
        return list(snapshots)

    def get_snapshot_by_user_id_snapshot_id(self, user_id, snap_id):
        snapshot = Snapshot.objects(pk=snap_id, user_id=user_id).first()
        return snapshot

    ############################ SET ############################

    def set_user(self, dict_fields: dict):  # _handle_user_data
        logger.debug(f"set user: {dict_fields}")
        try:
            if User.objects(user_id=dict_fields['user_id']).first():
                raise ResourceWarning("user already exists")
            user = User(**dict_fields)
            user.save()
            logger.debug('created user successfuly')
        except NotUniqueError:
            raise ResourceWarning("user already exists")
        except (KeyError, FieldDoesNotExist, ValidationError):
            raise TypeError("invalid fields or user_id not presented")
        return user

    def set_snapshot(self, dict_fields):
        logger.debug('in set_snapshot')
        logger.debug(f'dict_fields is {dict_fields}')
        try:
            datetime = dict_fields['datetime']
            user_id = dict_fields['user_id']
        except KeyError:
            raise TypeError("datetime or user_id are not presented")
        try:
            snap = Snapshot(user_id=user_id, datetime=datetime)
            self._add_to_snapshot(snap, dict_fields)
            snap.save()
        except NotUniqueError:
            cur_snap = Snapshot.objects(user_id=user_id, datetime=datetime).first()
            raise ResourceWarning(f"snapshot with these user_id and datetime already exists, with id_{cur_snap.pk}")
        except (FieldDoesNotExist, ValidationError) as e:
            raise TypeError(f"invalid fields: {str(e)}")
        return snap

    def _add_to_snapshot(self, snap: Snapshot, dict_fields: dict):
        for field_name in dict_fields.keys():
            logger.debug(f'field name is {field_name}')
            if field_name in ['user_id', 'datetime']:
                continue
            elif field_name == 'pose':
                dict_pose = dict_fields['pose']
                dict_pose = {subfield: list(dict_pose[subfield].values()) for subfield in dict_pose.keys()}
                snap.pose = Pose(**dict_pose)
            elif field_name == 'feelings':
                snap.feelings = Feelings(**dict_fields['feelings'])
            elif field_name == 'color_image':
                snap.color_image = Image(**dict_fields['color_image'])
            elif field_name == 'depth_image':
                snap.depth_image = Image(**dict_fields['depth_image'])
            else:
                raise TypeError(f'unknown field name: {field_name}')

    ########################## UPDATE ###########################

    def update_user(self, user_id: int, dict_fields: dict):
        if 'user_id' in dict_fields.keys() and user_id != dict_fields['user_id']:
            logger.debug(f'raising exception: user_id cannot br changed for {dict_fields} and user_id is {user_id}')
            raise TypeError("user_id field cannot be changed")
        user = User.objects(user_id=user_id).first()
        if not user:
            raise ResourceWarning("user doesn't exists")
        try:
            user.update(**dict_fields)
        except (FieldDoesNotExist, ValidationError):
            raise TypeError("invalid fields")
        return user

    def update_snapshot(self, cur_snap, dict_fields: dict):
        try:
            self._add_to_snapshot(cur_snap, dict_fields)
            cur_snap.save()
        except (FieldDoesNotExist, ValidationError) as e:
            raise TypeError(f"invalid fields: {str(e)}")
        return cur_snap

    ########################## DELETE ###########################

    def delete_all(self):
        some_user = User.objects.first()
        some_snap = Snapshot.objects.first()
        if not some_user and not some_snap:
            raise ResourceWarning("user is not in db")
        User.drop_collection()
        Snapshot.drop_collection()

    def delete_user_by_id(self, user_id):
        user = User.objects(user_id=user_id).first()
        if not user:
            raise ResourceWarning("user is not in db")
        user.delete()
        self.delete_all_snapshots_by_user_id(user_id)

    def delete_all_snapshots_by_user_id(self, user_id):
        some_snap = Snapshot.objects(user_id=user_id).first()
        if not some_snap:
            raise ResourceWarning('user does not have any snapshot')
        Snapshot.objects(user_id=user_id).delete()

    def delete_snapshot_by_user_id_snap_id(self, user_id, snap_id):
        snap = Snapshot.objects(user_id=user_id, pk=snap_id).first()
        if not snap:
            raise ResourceWarning("snap is not in db")
        snap.delete()

    def delete_snapshot_by_user_id_snap_id_result_name(self, user_id, snap_id, result_name):
        snap = Snapshot.objects(user_id=user_id, pk=snap_id).first()
        if not snap:
            raise ResourceWarning("snap is not in db")
        dict_snap = snap.to_mongo().to_dict()
        if result_name not in dict_snap.keys():
            raise ResourceWarning("snap doesn't contains this result")
        snap.delete()
        for field in [result_name, '_id', 'user_id']:
            dict_snap.pop(field)
        snap = Snapshot(pk=snap_id, user_id=user_id, datetime=dict_snap.pop('datetime'))
        self._add_to_snapshot(snap, dict_snap)
        snap.save()
