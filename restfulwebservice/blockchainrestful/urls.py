from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from blockchainrestful import views

urlpatterns = [
    url(r'^block/last/$', views.get_last_block),
    url(r'^block/(?P<id>[0-9a-z]+)/$', views.get_block_by_id),
    url(r'^block/$', views.get_block),
    url(r'^transaction/last/$', views.get_last_transaction),
    url(r'^transaction/(?P<id>[0-9a-z]+)/$', views.get_transaction_by_id),
]

urlpatterns = format_suffix_patterns(urlpatterns)