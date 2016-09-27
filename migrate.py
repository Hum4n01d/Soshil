from playhouse.migrate import *

import models

migrator = SqliteMigrator(models.db_proxy)

likes = IntegerField(default=0)
views = IntegerField(default=0)

def do_migration():
    migrate(
        migrator.drop_column('post', 'likes', likes),
    )