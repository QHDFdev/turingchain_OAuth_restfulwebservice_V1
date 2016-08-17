from bigchaindb import Bigchain
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
import rethinkdb as r

b = Bigchain()
conn = r.connect(db='bigchain')


@api_view(['GET'])
def get_last_block(request, format=None):
    big_block = r.table('bigchain').max('block_number').run(conn)
    return Response(json.dumps(big_block))