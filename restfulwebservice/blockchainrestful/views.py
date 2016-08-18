from bigchaindb import Bigchain, crypto
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json, time
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
def get_block_by_id(request, id, format=None):
    """
    通过区块id查询区块
    输入：区块id
    输出：区块信息
    """
    cursor = r.table('bigchain').filter({'id': int(id)}).run(conn)
    if cursor.threshold != 0:
        block = cursor.next()
        return Response(json.dumps(block))
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    tx = r.table('bigchain').max('block_number')['block']['transactions'] \
        .max(lambda tx: tx['transaction']['timestamp']).run(conn)
    return Response(json.dumps(tx))


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_transaction_by_id(request, id, format=None):
    """
    通过交易id查询交易
    输入：交易id
    输出：交易信息
    """
    tx = b.get_transaction(id)
    if tx is not None:
        return Response(json.dumps(tx))
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_key_pair(request, format=None):
    """
    获取秘钥
    输入：无
    输出：公钥和私钥
    """
    private_key, public_key = crypto.generate_key_pair()
    return Response(json.dumps({'private_key': private_key, 'public_key': public_key}))


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def trace_transaction(request, format=None):
    """
    溯源
    输入：物品公钥
    输出：交易序列
    """
    public_key = request.GET.get('pubkey')
    print(public_key)
    input_list = b.get_owned_ids(public_key)
    print(input_list)
    if input_list != []:
        tx_ids = []
        input = input_list.pop()
        tx = b.get_transaction(input['txid'])
        tx_id = tx['id']
        while tx['transaction']['data']['payload']['previous_process_tx_id'] is not None:
            tx_ids.append(tx_id)
            tx = b.get_transaction(tx['transaction']['data']['payload']['previous_process_tx_id'])
            tx_id = tx['id']
        tx_ids.append(tx_id)
        return Response(json.dumps({'txs': tx_ids}))
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def create_transaction(request, format=None):
    """
    区块创建Create交易
    输入：公钥，人员，地点，时间，物品
    输出：交易id
    """
    data = request.data
    public_key = data.pop('public_key', None)
    tx = b.create_transaction(b.me, public_key, None, 'CREATE', payload=data)
    tx_signed = b.sign_transaction(tx, b.me_private)
    b.write_transaction(tx_signed)
    return Response(json.dumps({'id': tx_signed['id']}))


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def transfer_transaction(request, format=None):
    """
    创建Transfer交易
    输入：交易发起方公钥，交易接收方公钥，交易发起方私钥，人员，地点，时间，物品
    输出：交易id和剩余物品的秘钥
    """
    # get total numbers
    data = request.data
    tx_originator_public_key = data.pop('tx_originator_public_key', None)
    tx_originator_private_key = data.pop('tx_originator_private_key', None)
    tx_recipient_public_key = data.pop('tx_recipient_public_key', None)
    input_list = b.get_owned_ids(tx_originator_public_key)
    if input_list == []:
        return Response(status=status.HTTP_204_NO_CONTENT)
    input = input_list.pop()
    tx = b.get_transaction(input['txid'])
    total = tx['transaction']['data']['payload']['thing']['thing_order_quantity']
    # transfer
    tx = b.create_transaction(tx_originator_public_key, tx_recipient_public_key, input, 'TRANSFER', payload=data)
    tx_signed = b.sign_transaction(tx, tx_originator_private_key)
    b.write_transaction(tx_signed)
    # deal with remains
    remain = int(total) - int(data['thing']['thing_order_quantity'])
    if remain > 0:
        time.sleep(5)
        data['thing']['thing_order_quantity'] = str(remain)
        data['who']['goto'] = data['who']['original']
        data['where']['goto'] = data['where']['original']
        for item in data['who']['original']:
            item = None
        for item in data['where']['original']:
            item = None
        data['when']['receive_date'] = data['when']['send_date']
        data['previous_process_tx_id'] = tx_signed['id']
        private_key, public_key = crypto.generate_key_pair()
        tx = b.create_transaction(b.me, public_key, None, 'CREATE', payload=data)
        tx_signed_2 = b.sign_transaction(tx, b.me_private)
        b.write_transaction(tx_signed_2)
        return Response(json.dumps({'txs': [tx_signed['id'], tx_signed_2['id']], 'key_pair': {'public_key': public_key,
                                                                                              'private_key': private_key}}))
    return Response(json.dumps({'transfer tx id': tx_signed['id']}))