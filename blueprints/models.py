import datetime

import peewee
from playhouse.migrate import PostgresqlMigrator
from playhouse.shortcuts import model_to_dict
from werkzeug.security import check_password_hash, generate_password_hash

from blueprints import app

database = peewee.PostgresqlDatabase(None)
database.init(database=app.config['DATABASE'],
              user=app.config['DB_USER'],
              password=app.config['DB_PASSWORD'],
              host='localhost')

migrator = PostgresqlMigrator(database)


class BaseModel(peewee.Model):
    @classmethod
    def create_model(cls, data):
        model_obj = cls(**data)
        try:
            model_obj.save()
        except (peewee.IntegrityError, peewee.InternalError):
            cls._meta.database.rollback()
            raise ValueError
        return model_obj

    class Meta:
        database = database


class User(BaseModel):
    username = peewee.CharField(unique=True)
    email = peewee.CharField(unique=True)
    password_hash = peewee.CharField()
    is_admin = peewee.BooleanField(default=False)

    def to_dict(self) -> dict:
        return model_to_dict(self, exclude=[type(self).password_hash])

    @classmethod
    def from_dict(cls, data: dict):
        is_admin = data.get('is_admin', False)
        data = {field: str(data[field]) for field in cls._meta.allowed_fields}
        data['password_hash'] = generate_password_hash(data['password'])
        del data['password']
        data['is_admin'] = is_admin
        return super().create_model(data)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return self.username

    class Meta:
        table_name = 'users'
        allowed_fields = 'username email password'.split()


class Post(BaseModel):
    title = peewee.CharField()
    author = peewee.ForeignKeyField(User, backref='posts')
    text = peewee.TextField()
    pub_date = peewee.DateTimeField(default=datetime.datetime.now())

    def to_dict(self):
        post = model_to_dict(self, exclude=[User.password_hash])
        post['pub_date'] = str(post['pub_date'])
        return post

    @classmethod
    def from_dict(cls, data):
        data['title'] = str(data['title'])
        data['text'] = str(data['text'])
        return super().create_model(data)

    def __repr__(self):
        return f'{self.author}: {self.title}'

    class Meta:
        table_name = 'posts'
        allowed_fields = 'title text pub_date'.split()


def create_tables():
    with database:
        database.drop_tables([Post, User])
        database.create_tables([Post, User])


if __name__ == '__main__':
    create_tables()
