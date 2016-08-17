from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from blockchainrestful.views import BigBlock

urlpatterns = [
    url(r'^block/(?P<height>[0-9]+)/$', BigBlock.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)