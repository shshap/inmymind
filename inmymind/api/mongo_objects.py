import mongoengine


class User(mongoengine.Document):
    user_id = mongoengine.IntField(primary_key=True, required=True)
    username = mongoengine.StringField()
    birthday = mongoengine.IntField()
    GENDER_ENUM = (0, 1, 2)
    gender = mongoengine.IntField(max_length=1, choises=GENDER_ENUM)  # or a string field

    meta = {
        'db_alias': 'core',
        'collection': 'users',
        'indexes': [
            'username',
        ],
        'ordering': 'user_id'
    }


class Pose(mongoengine.EmbeddedDocument):
    def _exact_len(n):
        def func(lst):
            if len(lst) != n:
                raise mongoengine.ValidationError(f'List must be {n} elements, got {len(lst)}')

        return func

    translation = mongoengine.ListField(mongoengine.FloatField(), validation=_exact_len(3))
    rotation = mongoengine.ListField(mongoengine.FloatField(), validation=_exact_len(4))


class Feelings(mongoengine.EmbeddedDocument):
    hunger = mongoengine.FloatField()
    thirst = mongoengine.FloatField()
    exhaustion = mongoengine.FloatField()
    happiness = mongoengine.FloatField()


class Image(mongoengine.EmbeddedDocument):
    path = mongoengine.StringField(required=True)
    width = mongoengine.IntField(required=True)
    height = mongoengine.IntField(required=True)
    content_type = mongoengine.StringField(required=True)


class Snapshot(mongoengine.Document):
    user_id = mongoengine.IntField(required=True)
    datetime = mongoengine.IntField(required=True)
    pose = mongoengine.EmbeddedDocumentField(Pose)
    color_image = mongoengine.EmbeddedDocumentField(Image)
    depth_image = mongoengine.EmbeddedDocumentField(Image)
    feelings = mongoengine.EmbeddedDocumentField(Feelings)

    meta = {
        'db_alias': 'core',
        'collection': 'snapshots',
        'indexes': [
            {
                'fields': ['user_id', 'datetime'],
                'unique': True
            }
        ],
        'ordering': 'user_id'
    }
