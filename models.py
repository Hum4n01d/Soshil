from datetime import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *

DATABASE = SqliteDatabase('soshil.db')

class User(UserMixin, Model):
    username = CharField()
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_date = DateTimeField(default=datetime.now)
    avatar_url = CharField(default='')
    is_admin = BooleanField(default=False)
    github_user = BooleanField(default=False)
  
    class Meta:
        database = DATABASE
    
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
    
    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)

class Comment(Model):
    timestamp = DateTimeField(default=datetime.now)
    user = ForeignKeyField(
        rel_model=User,
        related_name='comments'
    )
    post = ForeignKeyField(
        rel_model=Post,
        related_name='comments'
    )
    content = CharField(max_length=250)

    class Meta:
        database= DATABASE
        order_by = ('-timestamp',)

class Relationship(Model):
    from_user = ForeignKeyField(User, related_name='relationships')
    to_user = ForeignKeyField(User, related_name='relate_to')

    class Meta:
        database = DATABASE
        indexes = (
            (('from_user', 'to_user'), True),
        )
    
def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Post, Relationship], safe=True)
    DATABASE.close()