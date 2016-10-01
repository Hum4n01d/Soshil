# from playhouse.migrate import *
#
# import models
# import psycopg2
#
# import urllib.parse
#
# database_url = "postgres://wlkrojwtknjotj:ivdQ6mfwqTsAVM2FQMRwUopLEW@ec2-54-243-245-58.compute-1.amazonaws.com:5432/ddt7q377sum4gj"
#
# urllib.parse.uses_netloc.append('postgres')
# url = urllib.parse.urlparse(database_url)
# db = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
#
# migrator = PostgresqlMigrator(db)
#
# raw_content = TextField(default='')
# new_raw_content = TextField(default='')
#
# migrate(
#     migrator.add_column('post', 'content'),
#     migrator.drop_column('post', 'raw_content')
# )
#
# posts = models.Post.select()
#
# for post in posts:
#     models.Post.update(new_content=post.content, new_raw_content=post.raw_content).where(models.Post == post).execute()
#
# migrate(
#     migrator.drop_column('post', 'content'),
#     migrator.drop_column('post', 'raw_content')
# )