import copy
import time
import json

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_condition import ConditionalPermission, C, And, Or, Not
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from bigchaindb import Bigchain, crypto
import rethinkdb as r

from blockchainrestful.custom import IsTest
from blockchainrestful.custom import IsAdmin
from blockchainrestful.custom import IsUser
from blockchainrestful.custom import IsManager

b = Bigchain()
conn = r.connect(db='bigchain')


@api_view(['GET'])
def get_block(request, format=None):
    """
    通过属性得到区块
    输入：区块高度(height)或交易id(txid)
    """
    height = request.GET.get('height')
    transaction_id = request.GET.get('txid')
    if height is not None:
        return get_block_by_height(request, height, format)
    if transaction_id is not None:
        return get_block_by_transaction_id(request, transaction_id, format)
    return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_last_block(request, format=None):
    """
    查询最新的区块
    输入：无
    输出：区块信息
    """
    block = r.table('bigchain').max('block_number').run(conn)
    return Response(block)


@api_view(['GET'])
def get_block_by_id(request, id, format=None):
    """
    通过区块id查询区块
    输入：区块id
    输出：区块信息
    """
    cursor = r.table('bigchain').filter({'id': id}).run(conn)
    if cursor.threshold != 0:
        block = cursor.next()
        cursor.close()
        return Response(block)
    else:
        cursor.close()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_block_by_height(request, height, format=None):
    """
    通过区块高度返回区块
    输入：区块高度
    输出：区块信息
    """
    cursor = r.table('bigchain').filter({'block_number': int(height)}).run(conn)
    if cursor.threshold != 0:
        block = cursor.next()
        cursor.close()
        return Response(block)
    else:
        cursor.close()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
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
        cursor.close()
        return Response(block)
    else:
        cursor.close()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes((Or(IsAdmin, IsManager),))
def get_last_transaction(request, format=None):
    """
    查询最新的交易
    输入：无
    输出：交易信息
    """
    tx = r.table('bigchain').max('block_number')['block']['transactions'] \
        .max(lambda tx: tx['transaction']['timestamp']).run(conn)
    return Response(tx)


@api_view(['GET'])
@permission_classes((Or(IsAdmin, IsManager),))
def get_transaction_by_id(request, id, format=None):
    """
    通过交易id查询交易
    输入：交易id
    输出：交易信息
    """
    tx = b.get_transaction(id)
    if tx is not None:
        return Response(tx)
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes((Or(IsAdmin, IsManager),))
def get_transfer_transaction(request, format=None):
    """
    查询transfer transaction
    输入：num
    输出：特定数量的交易
    """
    num = request.GET.get('num')
    blocks = r.table('bigchain').filter(lambda bigblock: bigblock['block']['transactions'] \
                                        .contains(lambda tx: tx['transaction']['operation']=='TRANSFER')) \
                                        .order_by(r.desc('block_number')).limit(int(num)).run(conn)
    return Response(blocks)


@api_view(['GET'])
@permission_classes((Or(IsAdmin, IsManager, IsUser),))
def get_key_pair(request, format=None):
    """
    获取秘钥
    输入：无
    输出：公钥和私钥
    """
    private_key, public_key = crypto.generate_key_pair()
    return Response({'private_key': private_key, 'public_key': public_key})


@api_view(['GET'])
@permission_classes((Or(IsAdmin, IsManager),))
def trace_transaction(request, format=None):
    """
    溯源
    输入：物品公钥(pubkey)
    输出：交易序列
    """
    public_key = request.GET.get('pubkey')
    input_list = b.get_owned_ids(public_key)
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
        return Response({'txs': tx_ids})
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((Or(IsAdmin, IsManager),))
def create_transaction(request, format=None):
    """
    区块创建Create交易
    输入：前一个交易id(previous_process_tx_id)
         公钥(public_key)
         人员(who: {original: whoItem, goto: whoItem})，
         whoItem: user_id, user_type, user_name, company_name, company_id, u_company_id
         地点(where: {original: whereItem, goto: whereItem})
         whereItem: nation, region, place, region_id
         时间(when: make_date, send_date, receive_date, expire_date)
         物品(thing: thing_type_id, thing_type_name, thing_id, thing_name, origin_place, thing_order_quantity, thing_order_batch, price)
    输出：交易id
    """
    data = request.data
    public_key = data.pop('public_key', None)
    tx = b.create_transaction(b.me, public_key, None, 'CREATE', payload=data)
    tx_signed = b.sign_transaction(tx, b.me_private)
    b.write_transaction(tx_signed)
    return Response({'id': tx_signed['id']})


@api_view(['POST'])
@permission_classes((Or(IsAdmin, IsManager),))
def transfer_transaction(request, format=None):
    """
    创建Transfer交易
    输入：前一个交易id(previous_process_tx_id)
         交易发起方公钥(tx_originator_public_key)，
         交易接收方公钥(tx_recipient_public_key)，
         交易发起方私钥(tx_originator_private_key)，
         人员(who: {original: whoItem, goto: whoItem})，
         whoItem: user_id, user_type, user_name, company_name, company_id, u_company_id
         地点(where: {original: whereItem, goto: whereItem})
         whereItem: nation, region, place, region_id
         时间(when: make_date, send_date, receive_date, expire_date)
         物品(thing: thing_type_id, thing_type_name, thing_id, thing_name, origin_place, thing_order_quantity, thing_order_batch, price)
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
        data['who']['goto'] = copy.deepcopy(data['who']['original'])
        data['where']['goto'] = copy.deepcopy(data['where']['original'])
        for key, value in data['who']['original'].items():
            data['who']['original'][key] = None
        for key, value in data['where']['original'].items():
            data['where']['original'][key] = None
        data['when']['receive_date'] = data['when']['send_date']
        data['previous_process_tx_id'] = tx_signed['id']
        private_key, public_key = crypto.generate_key_pair()
        tx = b.create_transaction(b.me, public_key, None, 'CREATE', payload=data)
        tx_signed_2 = b.sign_transaction(tx, b.me_private)
        b.write_transaction(tx_signed_2)
        return Response({'txs': {'transfer_id': tx_signed['id'], 'create_id': tx_signed_2['id']},
                         'key_pair': {'public_key': public_key, 'private_key': private_key}})
    return Response({'transfer tx id': tx_signed['id']})


@api_view(['GET'])
@permission_classes((Or(IsAdmin, IsManager, IsUser),))
def get_common_transaction(request, id, format=None):
    """
    通用交易查询函数
    输入：交易id
    输出：交易信息
    """
    tx = b.get_transaction(id)
    if tx is not None:
        # 将content转为含中文的dict
        content = eval(tx['transaction']['data']['payload']['content'].encode('ascii').decode('unicode-escape'))
        return Response({'previous_process_tx_id': tx['transaction']['data']['payload']['previous_process_tx_id'],
                         'content': content})
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes((Or(IsAdmin, IsUser, IsManager),))
def trace_common_transaction(request, format=None):
    """
    通用交易回溯函数
    输入：交易id(txid)
    输出：交易序列
    """
    last_tx_id = request.GET.get('txid')
    tx_ids = []
    tx = b.get_transaction(last_tx_id)
    if tx is not None:
        tx_id = tx['id']
        while tx['transaction']['data']['payload']['previous_process_tx_id'] is not None:
            tx_ids.append(tx_id)
            tx = b.get_transaction(tx['transaction']['data']['payload']['previous_process_tx_id'])
            tx_id = tx['id']
        tx_ids.append(tx_id)
        return Response({'txs': tx_ids})
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((Or(IsTest, IsUser, IsManager, IsAdmin),))
def create_common_transaction(request, format=None):
    """
    通用交易插入函数
    输入：数据，前一个交易id(previous_process_tx_id)
    输出：交易id
    """
    data = request.data
    previous_process_tx_id = data.pop('previous_process_tx_id', None)
    # 将content转为unicode string存储
    content = str(data['content']).encode('unicode-escape')
    private_key, public_key = crypto.generate_key_pair()
    tx = b.create_transaction(b.me, public_key, None, 'CREATE',
                              payload={'previous_process_tx_id': previous_process_tx_id, 'content': content})
    tx_signed = b.sign_transaction(tx, b.me_private)
    b.write_transaction(tx_signed)
    return Response({'id': tx_signed['id']})

# bill
def error(sts, msg):
    '''
    make error message to client
    Para:
      sts - int, status of HTTP response
      mag - string of message
    Return:
      Response
    '''
    return Response({'error': msg}, status=sts)


def rdb_select(filtes=[], fields=[], sortby=None, order='asc',
            limit=None, keys=None, db_name='bigchain'):
    '''
    rethinkdb wrapper
    Para:
      filtes - list of dict or a function for filter
      fields - list of string, pluck by this, only one layer
        eg: ['block_number'] means pluck data['block_number']
        can`t pluck multi layer like data['block']['transaction']
      keys - list of string, key to select data of table, layer by layer
        eg: ['block', 'transaction'] means deal data['block']['transaction']
        this parameter can only set by local other than HTTP.
      sortby - string or function, for sort
      order - 'des' or 'asc', default 'asc'
      limit - string or int, limit the counter of return, less than 100
    Return:
     list of data
    '''
    rdbc = r.connect(db=db_name)
    if limit != None:  # get limit int type
        try:
            limit = int(limit)
        except TypeError:
            limit = 100
    else:
        limit = 100
    # make rql
    rql = r.table(db_name)
    if keys != None:  # like r.table('bigchain')['block']['transaction']...
        for key in keys:
            rql = rql.__getitem__(key)
    if len(filtes) > 0 :  # add filter
        for filte in filtes:
            rql = rql.filter(filte)
    if sortby != None:  # add sort
        if order != 'des':  # add sort order
            if limit != 1:
                rql = rql.order_by(sortby)
            else:
                rql = rql.min(sortby)
        else:
            if limit != 1:
                rql = rql.order_by(r.desc(sortby))
            else:
                rql = rql.max(sortby)
    if limit != 1: # add limit
        rql = rql.limit(limit)
    if len(fields) != 0:  # pluck data
        rql = rql.pluck(fields)
    # get data
    rtn = None
    try:
        rtn = rql.run(rdbc)
    except:
        # handle error?
        rtn = None
    # for filter, rql.run() will return a DefaultCursor other than a list
    ans = []
    if rtn is None:
        pass
    elif 'close' in dir(rtn):
        # conv DefaultCursor to a dict
        for data in rtn:
            ans.append(data)
        rtn.close()
    else:
        ans = rtn
    # close connection
    rdbc.close()

    return ans


def field_filter(source, fields):
    '''
    filter fields
    Para:
      source - dict
      fields - list of string
    Retrun:
      list
    '''
    if len(fields) == 0:
        ans = source
    else:
        ans = {}
        for field in fields:
            try:
                ans[field] = source[field]
            except KeyError:
                pass
    return ans


@api_view(['GET'])
def block(request, key, format=None):
    '''
    URL:
      blocks/[id]/
    Use for:
      get one block data by id or block number
    Para:
      field - field to filter json dict
    Return:
      a json dict
    '''
    # get block dakta
    fields = request.GET.getlist('field')
    if len(key) > 60:  # select by block id
        key_name = 'id'
    else:  # select by block number
        key_name = 'block_number'
        try:
            key = int(key)
        except ValueError:
            return error(400, 'wrong parameter')
    data = rdb_select(filtes=[{key_name: key}], fields=fields)
    if len(data) == 0:
        return error(404, 'can not find this block')
    else:
        return Response(data[0])


@api_view(['GET'])
def blocks(request, format=None):
    '''
    URL:
      blocks/
    Use for:
      get block data
    Para:
      field - filter every json dict
      limit - limit list length
      sortby - sort by specified field
      order - the order for sort, 'asc' or 'des', default 'asc'
    Return:
      a json list of the dicts
    '''
    # get paras
    fields = request.GET.getlist('field')
    limit = request.GET.get('limit', None)
    sortby = request.GET.get('sortby', None)
    order = request.GET.get('order', None)
    # get data from database
    datas = rdb_select(fields=fields, sortby=sortby, order=order, limit=limit)
    if len(datas) == 0:
        return error(404, 'can not find blocks')
    else:
        return Response(datas)


@api_view(['GET'])
@permission_classes((Or(IsAdmin, IsManager),))
def transaction(request, id, format=None):
    '''
    URL:
      transaction/[id]
    Use for:
      get one transaction data by id
    Para:
      field - field to filter json dict
    Return:
      a json dict
    '''
    # get paras
    fields = request.GET.getlist('field')
    # get transaction
    data = b.get_transaction(id)
    if data == None:
        return error(404, 'can not find this transaction')
    else:
        return Response(field_filter(data, fields))


@api_view(['GET', 'POST'])
@permission_classes((Or(IsAdmin, IsManager),))
def transactions(request, format=None):
    '''
    URL:
      transactions/
    Use for:
      get or create bill transaction
    Para:
      GET:
        field - filter every json dict
        operation - CREATE or TRANSFER
        limit - limit list length, less than 100
        sortby - sort by specified field, for timestamp
        order - the order for sort, asc or des, default asc
        receive_pubk - public key to get all transactions`id by receive,
          do not support some paras like limit
        origin_pubk - public key to get all transactions`id by origin
      POST:
        origin_pubk - transaction origin public key, if no this value, will
          create one CREATE transaction
        origin_prik - transaction origin private key, if no this value, will
          create one CREATE transaction
        pre_txid - previous transaction id
        receive_pubk - transaction receive public key
        data - data json string
    '''
    if request.method == 'GET':
        # get paras
        fields = request.GET.getlist('field')
        limit = request.GET.get('limit', None)
        sortby = request.GET.get('sortby', None)
        order = request.GET.get('order', None)
        receive_pubk = request.GET.get('receive_pubk', None)
        origin_pubk = request.GET.get('origin_pubk', None)
        operation = request.GET.get('operation', None)
        # make sort function for rethinkdb driver
        sort_func = None
        if sortby != None:
            sort_func = lambda ts: ts['transaction'][sortby]
        # make filter
        filtes_funcs = []
        if receive_pubk != None:
            # filtes_funcs = lambda x: x['transaction'].contains(lambda x: \
            #            x['conditions'].contains(lambda x: x['new_owners'].\
            #            contains(receive_pubk)))
            # return by method get_owned_ids
            return Response(
                [{'id': x['txid']} for x in Bigchain().get_owned_ids(
                    receive_pubk)])
        elif origin_pubk != None:
            filtes_funcs.append(lambda x: x['transaction'].contains(lambda x: \
                       x['fulfillments'].contains(lambda x: x['current_owners'].\
                       contains(origin_pubk))))
            fields.append('id')
        if operation != None:
            filtes_funcs.append(lambda t: t.contains(\
                lambda x: x['transaction']['operation'] == operation))
        # get datas
        datas = rdb_select(sortby=sort_func, order=order, filtes=filtes_funcs,
                        keys=['block', 'transactions'], limit=limit)
        # can`t pluck, limit this data by rethinkdb driver, handle with hand
        # limit
        try:
            limit = int(limit)
        except TypeError:
            limit = 100
        limit = min(100, limit)  # limit less than 100
        # return datas by max operation
        if limit == 1 and sortby != None:
            return Response(field_filter(datas[0], fields))
        # return normal datas, it`s format willbe [[d1, ...], [d2, ..], ...]
        #  change format to [d1, d2, d3...]
        ans = []
        for alist in datas:
            for data in alist:
                if len(ans) >= limit:
                    return Response(ans)
                ans.append(field_filter(data, fields))  # filter data

        return Response(ans)
    elif request.method == 'POST':
        # get paras
        origin_pubk = request.POST.get('origin_pubk', None)
        origin_prik = request.POST.get('origin_prik', None)
        pre_txid = request.POST.get('pre_txid', None)
        receive_pubk = request.POST.get('receive_pubk', None)
        data = request.POST.get('data', '{}')
        # make sure paras
        receive_prik = ''
        bdb_input = None
        bdb_type = 'CREATE'
        bdb = Bigchain()
        try:
            data = json.loads(data)  # json string to json data
        except JSONDecodeError:
            return error(400, 'Wrong json string format')
        # bill data format checker
        left_money = 0
        pre_data = None
        billm = 'Bill_amount_money'
        bill = 'bill'
        if billm not in data.keys():
            return error(400, 'Wrong data format')
        # make sure paras
        if receive_pubk == None:  # create a pair
            receive_prik, receive_pubk = crypto.generate_key_pair()
        if origin_pubk == None:  # create transaction
            origin_pubk = bdb.me
            origin_prik = bdb.me_private
        else:  # transfer transaction
            bdb_type = 'TRANSFER'
            if origin_prik == None:
                return error(400, 'need private key')
            if pre_txid == None:
                return error(400, 'need pre_txid when transfer')
            # get previous bill, and check it
            pre_tx = bdb.get_transaction(pre_txid)
            if pre_tx == None:
                return error(400, 'This pre_txid does not exist')
            # make input, in our case, the key 'cid' will always be 0
            bdb_input = {'cid': 0, 'txid': pre_txid}
            # check bdb_input belong origin
            if bdb_input not in bdb.get_owned_ids(origin_pubk):
                return error(400, 'This pre_txid does not belong the origin')
            # money check
            pre_data = pre_tx['transaction']['data']['payload']
            pre_money = pre_data[bill][billm]
            now_money = data[billm]
            if now_money > pre_money:
                return error(400, 'money to less')
            left_money = pre_money - now_money
        # start transaction
        tx = bdb.create_transaction(origin_pubk, receive_pubk, bdb_input,
                                    bdb_type, payload={'pre_txid': pre_txid,
                                                        'bill': data})
        bdb.write_transaction(bdb.sign_transaction(tx, origin_prik))
        # create new bill with left money
        if pre_data != None:
            # change data
            pre_data[bill][billm] = left_money
            pre_data['pre_txid'] = pre_txid
            ltx = bdb.create_transaction(bdb.me, origin_pubk, None,
                                        'CREATE', payload=pre_data)
            bdb.write_transaction(bdb.sign_transaction(ltx, bdb.me_private))
        return Response({'txid': tx['id'], 'receive_pubk': receive_pubk,
                        'receive_prik': receive_prik})
