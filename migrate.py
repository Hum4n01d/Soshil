from playhouse.migrate import *

import models

migrator = PostgresqlMigrator(models.db_proxy)

def do_migration():
    migrate(
        migrator.add_not_null('post', 'content')
    )