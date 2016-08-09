import os

from playhouse.migrate import *
import urllib.parse

try:
    heroku = os.environ['HEROKU']

    if heroku:
        urllib.parse.uses_netloc.append('postgres')
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
        db = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
except KeyError:
    db = SqliteDatabase('soshil.db')

migrator = PostgresqlMigrator(db)

raw_title = CharField()
raw_content = CharField()

with db.transaction():
    migrate(
        migrator.drop_column('post', 'raw_title'),
    )