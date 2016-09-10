import hashlib
import models

users = models.User.select()

for user in users:
    email = user.email.encode('utf-8')
    gravatar_url = 'https://www.gravatar.com/avatar/' + hashlib.md5(email).hexdigest() + '?d=retro&s=75'

    models.User.update(
        avatar_url=gravatar_url
    ).where(
        models.User.id == user.id
    ).execute()

