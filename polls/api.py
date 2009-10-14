from djangocore.api import site
from djangocore.api.models.dj import DjangoModelResource as ModelResource

from polls.models import Poll, Choice

site.register(ModelResource, model=Poll)
site.register(ModelResource, model=Choice)