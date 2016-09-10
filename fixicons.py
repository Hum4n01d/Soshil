import hashlib
import models

models.User.update(models.User.avatar_url == 'https://avatars2.githubusercontent.com/u/8015809?v=3&s=75').where(models.User.username ** "brld").execute()

models.User.update(models.User.avatar_url == 'https://avatars3.githubusercontent.com/u/17019573?v=3&s=75').where(models.User.username ** "ianardo").execute()

models.User.update(models.User.avatar_url == 'https://avatars3.githubusercontent.com/u/17228477?v=3&s=75').where(models.User.username ** "hum4n01d").execute()