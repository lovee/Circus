# coding: utf-8
'''
Created on 2016年3月15日

@author: caohang
'''

import binascii
import struct
import base64
from crypt import crypt_api

ENCRYPT_KEY = 'boemgsllskenfgjw'

class BCPacket():
    """
    BC与BS间信令包定义，实现信令包的序列化与反序列化；
    """
    HEAD_FLAG = 0xAB65AB65

    def __init__(self):
        #信令消息头
        self.head_flag = BCPacket.HEAD_FLAG
        self.data_size = 0
        self.head_reserve = 0
        self.pkt_type = 0
        self.head_id = 0
        #信令消息体
        self.data = u''
        #完整数据流
        self.stream = b''
        #信令头数据流
        self.head_stream = b''

    def deserialize(self, stream):
        '''
        消息反序列化
        '''
        if len(stream) < 20:
            log_str = ("消息解析出错，原始数据流小于20, strem = %d") % len(stream)
            raise(Exception(log_str))
        flag, data_size, reserve, i_type, i_id = struct.unpack("<IIIII", stream[:20])
        if flag != BCPacket.HEAD_FLAG :
            log_str = ("消息解析出错，消息头标识错误，HeadFlag = %x") % flag
            raise(Exception(log_str))
        self.head_flag, self.data_size, self.head_reserve, self.pkt_type, self.head_id = flag, data_size, reserve, i_type, i_id
        self.stream = stream
        self.head_stream = stream[:20]
        self.data = stream[20:]

    def serialize(self, pkt_type, data):
        '''
        消息序列化
        '''
        self.pkt_type = pkt_type
        self.data = data
        self.data_size = len(data)
        #获取消息头
        self.head_stream = struct.pack("<IIIII", self.head_flag, self.data_size, self.head_reserve, self.pkt_type, self.head_id)
        #生成完整信令序列
        self.stream = self.head_stream + self.data

    def data_options(self):
        """
        返回信令消息体中的所有字段
        """
        return self.data.split('\r\n')

    def to_string(self):
        '''
        信令详细信息，用于log或print
        '''
        hdf = "*"
        detail_str = u""
        detail_str += (hdf+ "%s" % self.__class__)
        detail_str += "\n"
        detail_str += (hdf + "<Stream>" + "  ")
        detail_str += binascii.hexlify(self.stream)
        detail_str += "\n"
        detail_str += ("[Packet Detal]:")
        detail_str += "\n"
        detail_str += (hdf + "<Head>" + "  ")
        detail_str += ("%X"%self.head_flag + "    " + "%d"%self.data_size + "    " + "%d"%self.pkt_type + "    " + "%d"%self.head_reserve + "    " + "%d"%self.head_id)
        detail_str += "\n"
        detail_str += (hdf + '<Data Str>')
        detail_str += "\n"
        detail_str += self.data.decode("gbk").replace('\r\n', '\n')
        return detail_str

def get_pkt_by_stream(stream):
    """
    根据信令码流生成信令BCPacket对象
    """
    pkt = BCPacket()
    pkt.deserialize(stream)
    return pkt

def get_pkt_by_data(pkt_type, data):
    """
    根据信令号与信令数据生成BCPacket对象
    """
    pkt = BCPacket()
    pkt.serialize(pkt_type, data)
    return pkt

def pkt_heart(bc_name, bc_ip):
    """
    心跳信令
    """
    data = b''
    data += bc_name + '\r\n'
    data += bc_ip + '\r\n'
    data += ' ' + '\r\n'
    data += bc_name + '\r\n'
    data += '06' + '\r\n'
    data += '\r\n'
    data += '\r\n'
    data += '\r\n'
    data += '1' + '\r\n'
    data += '\r\n'
    return data

def pkt_connect(bc_name, bc_ip):
    """
    BC连接BS鉴权信令
    """
    data = b''
    data += bc_name + '\r\n'
    data += bc_ip + '\r\n'
    data += ' ' + '\r\n'
    data += bc_name + '\r\n'
    data += '06' + '\r\n'
    data += '\r\n'
    data += '\r\n'
    data += '\r\n'
    data += '1' + '\r\n'
    data += '4.6.3.0' + '\r\n'
    data += '0000' + '\r\n'
    data += 'NCCRYReq' + '\r\n'
    return data

def pkt_up(card, pwd, veri_code):
    """
    会员上机信令
    """
    if (0 == len(veri_code)):
        auth_str = '%s~%s' % (card, pwd)
    else:
        auth_str = '%s~%s~%s' % (card, pwd, veri_code)
    auth_str = crypt_api.encrypt_data(auth_str, ENCRYPT_KEY)
    data = b''
    data += '1' + '\r\n'
    data += '2' + '\r\n'
    data += '3' + '\r\n'
    #data += 'up2O/H9ySwLwN0HAAAA' + '\r\n'
    data += 'up2' + auth_str + '\r\n'
    data += '\r\n'
    return data

def pkt_down():
    """
    会员下机信令
    """
    data = b''
    data += 'down'
    return data