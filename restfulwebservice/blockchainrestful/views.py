from bigchaindb import Bigchain
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
import rethinkdb as r

b = Bigchain()
conn = r.connect(db='bigchain')


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_last_block(request, format=None):
    block = r.table('bigchain').max('block_number').run(conn)
    return Response(json.dumps(block))