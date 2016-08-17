from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from blockchainrestful import views

urlpatterns = [
    url(r'^block/last/$', views.get_last_block),
    url(r'^block/(?P<id>[0-9a-z]+)/$', views.get_block_by_id),
    url(r'^block?height=(?P<height>[0-9]+)/$', views.get_block_by_height),
    url(r'^transaction/last/$', views.get_last_transaction),
]

urlpatterns = format_suffix_patterns(urlpatterns)