import os

from datetime import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *
import psycopg2
import urllib.parse

from app import parse_for_mentions

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
        if not password == '':
            password = generate_password_hash(password)

        try:
            cls.create(
                username=username,
                email=email,
                password=password,
                avatar_url=avatar_url,
                is_admin=admin,
                github_user=github_user
            )
        except IntegrityError:
            raise ValueError('User already exists')

class Post(Model):
    title = CharField(max_length=100)
    content = CharField(max_length=250)
    raw_content = CharField(default='')

    timestamp = DateTimeField(default=datetime.now)
    user = ForeignKeyField(
        rel_model=User,
        related_name='posts'
    )

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

class Notification(Model):
    title = CharField(default='Notification')
    link = CharField()
    date = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, related_name='notifications')

    class Meta:
        database = db_proxy

    @classmethod
    def create_notification(cls, title, link, user):
        cls.create(
            user=user,
            link=link,
            title=parse_for_mentions(title)
        )

def initialize():
    db_proxy.connect()
    db_proxy.create_tables([User, Relationship, Post, Comment, Notification], safe=True)
    db_proxy.close()