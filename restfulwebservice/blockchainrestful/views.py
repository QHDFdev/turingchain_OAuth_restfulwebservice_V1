from bigchaindb import Bigchain
from rest_framework.decorators import api_view
from rest_framework.response import Response
import rethinkdb as r

from blockchainrestful.serializers import BigBlockSerializer

b = Bigchain()
conn = r.connect(db='bigchain')


@api_view(['GET'])
def get_last_block(request, format=None):
    big_block = r.table('bigchain').max('block_number').run(conn)
    serializer = BigBlockSerializer(big_block)
    return Response(serializer.data)