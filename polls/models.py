from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

class Poll(models.Model):
    """A poll."""
    question = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(User)
    pub_date = models.DateTimeField(default=datetime.now)
    
    def __unicode__(self):
        return self.question

class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    answer = models.CharField(max_length=255)
    votes = models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.answer


from djangocore.api.base import site
from djangocore.api.dj import DjangoModelResource as ModelResource
try:
    site.register(Poll, ModelResource)
    site.register(Choice, ModelResource)
except:
    pass