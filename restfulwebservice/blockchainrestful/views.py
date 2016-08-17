from bigchaindb import Bigchain
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
import json
import rethinkdb as r

b = Bigchain()
conn = r.connect(db='bigchain')


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


@api_view(['GET'])
def get_last_block(request, format=None):
    big_block = r.table('bigchain').max('block_number').run(conn)
    return JSONResponse(json.dumps(big_block['votes']))