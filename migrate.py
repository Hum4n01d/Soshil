from playhouse.migrate import *

import models

migrator = PostgresqlMigrator(models.db_proxy)

def do_migration():
    migrate(
        migrator.drop_column('post', 'likes')
    )