from playhouse.migrate import *

import models

migrator = SqliteMigrator(models.db)

raw_title = IntegerField(default=0)
views = IntegerField(default=0)

migrate(
    migrator.add_column('post', 'raw_title', raw_title),
    migrator.add_column('post', 'views', views),
)