from bigchaindb import Bigchain
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
import rethinkdb as r

b = Bigchain()
conn = r.connect(db='bigchain')

@login_required
@api_view(['GET'])
def get_last_block(request, format=None):
    block = r.table('bigchain').max('block_number').run(conn)
    return Response(json.dumps(block))