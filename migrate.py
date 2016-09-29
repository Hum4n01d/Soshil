from playhouse.migrate import *

import models

migrator = PostgresqlMigrator(models.db_proxy)

old_raw_content = CharField(default='')
new_raw_content = TextField(default='')

def do_migration():
    posts = models.Post.select()
        
    for post in posts:
        models.Post.update(new_raw_content=post.raw_content).execute()
        
    migrate(
        migrator.drop_column('post', 'raw_content', old_raw_content)
    )
        
    migrate(
        migrator.add_column('post', 'raw_content', new_raw_content)
    )
    
    for post in posts:
        models.Post.update(raw_contnet=post.new_raw_content).execute()