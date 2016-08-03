import os

from datetime import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *
import psycopg2
import urllib.parse

db_proxy = Proxy()

try:
    heroku = os.environ['HEROKU']

    if heroku:
        urllib.parse.uses_netloc.append('postgres')
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
        db = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
except KeyError:
    db = SqliteDatabase('soshil.db')
    
db_proxy.initialize(db)

class User(UserMixin, Model):
    username = CharField()
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_date = DateTimeField(default=datetime.now)
    avatar_url = CharField(default='')
    is_admin = BooleanField(default=False)
    github_user = BooleanField(default=False)
  
    class Meta:
        database = db_proxy
    
    def get_posts(self):
        return Post.select().where(Post.user == self)
    
    def get_stream(self):
        return Post.select().where(
            (Post.user << self.following()) |
            (Post.user == self)
        )

    def following(self):
        '''The users that we are following'''
        return (
            User.select().join(
                Relationship, on=Relationship.to_user
            ).where(Relationship.from_user == self)
        )

    def followers(self):
        '''Get users following the current user'''
        return (
            User.select().join(
                Relationship, on=Relationship.from_user
            ).where(Relationship.to_user == self)
        )
    
    @classmethod
    def create_user(cls, username, email, password, avatar_url='', admin=False, github_user=False):
        if github_user:
            cls.create(
                username=username,
                email=email,
                password='',
                is_admin=admin,
                avatar_url=avatar_url,
                github_user=github_user
            )
        else:
            try:
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    avatar_url=avatar_url,
                    is_admin=admin
                )
            except IntegrityError:
                raise ValueError('User already exists')

class Post(Model):
    title = CharField(max_length=100)
    timestamp = DateTimeField(default=datetime.now)
    user = ForeignKeyField(
        rel_model=User,
        related_name='posts'
    )
    content = CharField(max_length=250)
    likes = IntegerField(default=0)

    class Meta:
        database = db_proxy
        order_by = ('-timestamp',)

class Comment(Model):
    timestamp = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, related_name='commenter')
    post = ForeignKeyField(Post, related_name='post_comments')
    content = CharField(max_length=250)

    class Meta:
        database = db_proxy
        order_by = ('-timestamp',)

class Relationship(Model):
    from_user = ForeignKeyField(User, related_name='relationships')
    to_user = ForeignKeyField(User, related_name='relate_to')

    class Meta:
        database = db_proxy
        indexes = (
            (('from_user', 'to_user'), True),
	)

def Notifcation(Model):
    title = CharField(default='Notification')
    content = TextField()
    date = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, related_name='notifications')

    class Meta:
        database = db_proxy

def initialize():
    db_proxy.connect()
    db_proxy.create_tables([User, Relationship, Post, Comment], safe=True)
    db_proxy.close()