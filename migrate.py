from playhouse.migrate import *

import models

migrator = PostgresqlMigrator(models.db_proxy)

new_raw_content = TextField(default='')

def do_migration():
    for post in Post.select():
        models.Post.update(raw_content=post.new_raw_content).execute()