from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from blockchainrestful import views

urlpatterns = [
    url(r'^block/$', views.get_block),
    url(r'^block/last/$', views.get_last_block),
    url(r'^block/(?P<id>[0-9a-z]+)/$', views.get_block_by_id),
    url(r'^transaction/last/$', views.get_last_transaction),
    url(r'^transaction/transfertype/$', views.get_transfer_transaction),
    url(r'^transaction/trace/$', views.trace_transaction),
    url(r'^transaction/create/$', views.create_transaction),
    url(r'^transaction/transfer/$', views.transfer_transaction),
    url(r'^transaction/common/trace/$', views.trace_common_transaction),
    url(r'^transaction/common/create/$', views.create_common_transaction),
    url(r'^transaction/common/(?P<id>[0-9a-z]+)/$', views.get_common_transaction),
    url(r'^transaction/(?P<id>[0-9a-z]+)/$', views.get_transaction_by_id),
    url(r'^key-pair/$', views.get_key_pair),
    # for bill
    url(r'^blocks/$', views.blocks),
    url(r'^blocks/(?P<key>[0-9a-z]+)/$', views.block),
    url(r'^transactions/$', views.transactions),
    url(r'^transactions/(?P<id>[0-9a-z]+)/$', views.transaction),
]

urlpatterns = format_suffix_patterns(urlpatterns)
