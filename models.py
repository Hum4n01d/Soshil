import re
import bleach
import requests

from flask import url_for
from os import environ
from datetime import datetime
from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *
import psycopg2
from flask import g

db_proxy = Proxy()

try:
    heroku = environ['HEROKU']

    if heroku:
        import urllib.parse

        database_url = environ["DATABASE_URL"]

        urllib.parse.uses_netloc.append('postgres')
        url = urllib.parse.urlparse(database_url)
        db = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
except KeyError:
    db = SqliteDatabase('soshil.db')
    
db_proxy.initialize(db)

def parse_post(text, notification=False, page='', edit=False):
    # Parse for @mentions using regular expressions

    matches = re.findall(r'.?@[\w]+', text)

    for match in matches:
        if match[0] == '\\':
            break

        username = match.replace('@', '').strip()

        link = url_for('profile', username=username)

        template = '[@]({link})[{username}]({link})'

        if match[0] == ' ':
            template = ' {}'.format(template)

        text = text.replace(match, template.format(
            link=link,
            username=username
        ))

        if not notification and not edit:
            try:
                Notification.create_notification(
                    title='@{} mentioned you!'.format(g.user._get_current_object().username),
                    link=page,
                    user=User.get(User.username ** username)
                )
            except DoesNotExist:
                pass

    # Escape backslashed @mentions like "\@mention"
    backslash_matches = re.findall(r'\\@[\w]+', text)

    for backslash_match in backslash_matches:
        text = text.replace(backslash_match, backslash_match.strip('\\'))

    # Use the bleach library to remove malicious HTML
    text = bleach.clean(text)

    return text

class BaseModel(Model):
    class Meta:
        database = db_proxy

class User(UserMixin, BaseModel):
    username = CharField(max_length=15)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_date = DateTimeField(default=datetime.now)
    avatar_url = CharField(default='')
    is_admin = BooleanField(default=False)
    github_user = BooleanField(default=False)

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

class Post(BaseModel):
    title = CharField(max_length=100)
    content = TextField()
    raw_content = CharField(default='')
    #new_raw_content = TextField()

    timestamp = DateTimeField(default=datetime.now)
    user = ForeignKeyField(
        rel_model=User,
        related_name='posts'
    )

    def get_likes(self):
        '''The users that have liked the post'''
        return (
            User.select().join(
                Like, on=Like.user
            ).where(Like.post == self)
        )

    def get_number_of_comments(self):
        '''The users that have viewed the post'''
        return Comment.select().where(Comment.post == self).count()

    class Meta:
        database = db_proxy
        order_by = ('-timestamp',)

class Comment(BaseModel):
    timestamp = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, related_name='commenter')
    post = ForeignKeyField(Post, related_name='post_comments')
    content = CharField(max_length=250)

    class Meta:
        database = db_proxy
        order_by = ('-timestamp',)

class Relationship(BaseModel):
    from_user = ForeignKeyField(User, related_name='relationships')
    to_user = ForeignKeyField(User, related_name='relate_to')

    class Meta:
        database = db_proxy
        indexes = (
            (('from_user', 'to_user'), True),
	    )

class Like(BaseModel):
    user = ForeignKeyField(User, related_name='liker')
    post = ForeignKeyField(Post, related_name='liked_post')

    class Meta:
        database = db_proxy
        indexes = (
            (('user', 'post'), True),
	    )

class Notification(BaseModel):
    title = CharField(default='Notification')
    link = CharField()
    date = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, related_name='notifications')

    class Meta:
        database = db_proxy

    @classmethod
    def create_notification(cls, title, user, link=''):
        cls.create(
            user=user,
            link=link,
            title=parse_post(title, notification=True)
        )

def initialize():
    db_proxy.connect()
    db_proxy.create_tables([User, Relationship, Post, Comment, Notification, Like], safe=True)

    db_proxy.close()

if __name__ == '__main__':
    initialize()