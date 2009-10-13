# Django dependencies.
from django.conf.urls.defaults import patterns, url, include

# Intra-app dependencies.
from djangocore.utils import underscore
from djangocore.transform.forms import transformer
from djangocore.api.resources import BaseResource

class FormResource(BaseResource):
    form = None # a model form class to use when creating and updating objects

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urlpatterns = patterns('',
            url('^form/$',      self.mapper,    self.ops(get='form')),
            url('^$',           self.mapper,    self.ops(post='submit')),
        )
        return urlpatterns
    
    def get_url_prefix(self):
        return 'forms/%s/' % underscore(self.__class__.__name__)
    
    def meta(self, request):
        return transformer.render(self.form)

    def submit(self, request):
        raise NotImplementedError
