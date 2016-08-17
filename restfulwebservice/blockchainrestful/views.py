from bigchaindb import Bigchain
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
import rethinkdb as r

b = Bigchain()
conn = r.connect(db='bigchain')


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_block(request, format=None):
    height = request.GET.get('height')
    transaction_id = request.GET.get('txid')
    if height is not None:
        return get_block_by_height(request, height, format)
    if transaction_id is not None:
        return get_block_by_transaction_id(request, transaction_id, format)
    return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_last_block(request, format=None):
    """
    查询最新的区块
    输入：无
    输出：区块信息
    """
    block = r.table('bigchain').max('block_number').run(conn)
    return Response(json.dumps(block))


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_block_by_id(request, block_id, format=None):
    """
    通过区块id查询区块
    输入：区块id
    输出：区块信息
    """
    pass


def get_block_by_height(request, height, format=None):
    """
    通过区块高度返回区块
    输入：区块高度
    输出：区块信息
    """
    cursor = r.table('bigchain').filter({'block_number': int(height)}).run(conn)
    if cursor.threshold != 0:
        block = cursor.next()
        return Response(json.dumps(block))
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)


def get_block_by_transaction_id(request, transaction_id, format=None):
    """
    通过交易id查询区块
    输入：交易id
    输出：包含该条交易的区块信息
    """
    cursor = r.table('bigchain').filter(lambda bigblock: bigblock['block']['transactions']['id']
                                        .contains(transaction_id)).run(conn)
    if cursor.threshold != 0:
        block = cursor.next()
        return Response(json.dumps(block))
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_last_transaction(request, format=None):
    """
    查询最新的交易
    输入：无
    输出：交易信息
    """
    pass


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_transaction_by_id(request, transaction_id, format=None):
    """
    通过交易id查询交易
    输入：交易id
    输出：交易信息
    """
    pass


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_key_pair(request, format=None):
    """
    获取秘钥
    输入：无
    输出：公钥和私钥
    """
    pass


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def trace_transactions(request, public_key, format=None):
    """
    溯源
    输入：物品公钥
    输出：交易序列
    """
    pass


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def create_transaction(request, public_key, who, where, when, thing, format=None):
    """
    区块创建Create交易
    输入：公钥，人员，地点，时间，物品
    输出：交易id
    """
    pass


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def transfer_transaction(request, tx_originator_public_key, tx_recipient_public_key, tx_originator_private_key, who,
                         where, when, thing, format=None):
    """
    创建Transfer交易
    输入：交易发起方公钥，交易接收方公钥，交易发起方私钥，人员，地点，时间，物品
    输出：交易id和剩余物品的秘钥
    """
    pass