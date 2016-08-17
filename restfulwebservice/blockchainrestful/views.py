from bigchaindb import Bigchain
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import rethinkdb as r

from blockchainrestful.serializers import BigBlockSerializer


class BigBlock(APIView):

    def __init__(self):
        self.b = Bigchain()
        self.conn = r.connect(db='bigchain')

    def get(self, request, height, format=None):
        cursor = r.table('bigchain').filter({'block_number': height}).run(self.conn)
        print(cursor.threshold)
        if cursor.threshold != 0:
            big_block = cursor.next()
            serializer = BigBlockSerializer(big_block)
            return Response(serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)