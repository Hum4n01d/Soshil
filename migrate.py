from playhouse.migrate import *

import models

migrator = PostgresqlMigrator(models.db_proxy)

content = TextField(default='')

def do_migration():
    migrate(
        migrator.add_column('post', 'new_content', content)
    )
    
    posts = models.Post.select()
        
    for post in posts:
        models.Post.update(new_content=post.content).execute()
        
    migrate(
        migrator.drop_column('post', 'content')
    )
        
    migrate(
        migrator.add_column('post', 'content', content)
    )
    
    for post in posts:
        models.Post.update(content=post.new_content).execute()