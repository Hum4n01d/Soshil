from playhouse.migrate import *

import models

migrator = SqliteMigrator(models.db_proxy)

raw_title = IntegerField(default=0)
views = IntegerField(default=0)

def do_migration():
    migrate(
        migrator.add_column('post', 'views', views),
    )