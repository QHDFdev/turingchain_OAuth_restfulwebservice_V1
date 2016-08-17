from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from blockchainrestful import views

urlpatterns = [
    url(r'^block/last/$', views.get_last_block),
]

urlpatterns = format_suffix_patterns(urlpatterns)