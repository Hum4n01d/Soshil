from playhouse.migrate import *
from peewee import PostgresqlDatabase

import models

migrator = PostgresqlMigrator(models.db_proxy)
