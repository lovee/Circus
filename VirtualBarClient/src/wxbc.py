# coding: utf-8
'''
Created on 2016年3月15日

@author: caohang
'''

import threading
import time
import Queue
import logging
from bcsocket import BCSocket
from bcpacket import *

class WXBC():
    """
    # WXBC模拟器；
    # 1、实现启动、关闭、信令收发和状态监听等功能；
    """
    def __init__(self, name, ip='127.0.0.1', mac='0.0.0.0', bshost=("127.0.0.1", 11011)):
        self.socket = BCSocket(name)
        self.que_ack_pkt = Queue.Queue()
        self.name = name
        self.ip = ip
        self.mac = mac
        self.card = ""
        #BC模拟器状态0:保留, 1:保留, 2:锁屏, 3:解锁, 4:上机
        self.status = 2
        self.bshost = bshost
        self.bs_ip, self.bs_port = bshost
        self.conn_flag = threading.Event()
        self.conn_flag.set()
        self.thd_comm = None
        self.thd_listener = None

    def _connect(self):
        """
        登录BS，仅用于通信线程调用
        """
        if not self.socket.is_connected():
            try:
                self.socket.connect(self.bshost)
                self.conn_flag.set()
            except Exception as e:
                self.conn_flag.set()
                # self.status = 0
                return 1
        else:
            data = pkt_connect(self.name, self.bs_ip)
            login_pkt = get_pkt_by_data(2, data)
            self.socket.send_pkt(login_pkt)
            self.conn_flag.clear()
            # if self.card != "":
            #     self.status = 4
            # else:
            #     self.status = 2

    def _communicate(self):
        """
        维护BS连接，仅用于通信线程调用
        """
        data = pkt_heart(self.name, self.bs_ip)
        hrt_pkt = get_pkt_by_data(3, data)
        while True:
            if (self.socket.is_connected() and self.is_connected()):
                time.sleep(1)
            else:
                self._connect()

    def _heart_beat(self):
        """
        心跳，仅用于心跳线程调用；
        """
        data = pkt_heart(self.name, self.bs_ip)
        hrt_pkt = get_pkt_by_data(3, data)
        while True:
            if (self.socket.is_connected() and self.is_connected()):
                self.socket.send_pkt(hrt_pkt)
                time.sleep(10)
            else:
                time.sleep(1)

    def _listener(self):
        """
        监听并处理BS通知信令，仅用于监听线程调用；
        待完善!
        """
        while True:
            pkt = self.socket.recv_pkt(1)
            if pkt is None:
                continue
            opts = pkt.data_options()
            #上机通知信令
            if pkt.pkt_type == 0x4:
                if opts[4]=='':
                    self.status = 3
                else:
                    self.status = 4
                self.card = opts[4]
            #锁屏
            elif pkt.pkt_type == 0x5:
                self.status = 2
                self.card = ""
            #保存ACK信令
            # if (pkt.pkt_type & 0x80000000) > 0:
            #     self.que_ack_pkt.put(pkt)
            self.que_ack_pkt.put(pkt)

    def is_connected(self):
        """
        BC是否已经连接到BS
        """
        return not self.conn_flag.is_set()

    def startup(self):
        """
        启动BC
        """
        #通信维护线程
        self.thd_comm = threading.Thread(target=self._communicate, name='bc_communicate_thd')
        self.thd_comm.start()
        #信令监听线程
        self.thd_listener = threading.Thread(target=self._listener, name='bc_listener_thd')
        self.thd_listener.start()
        #心跳线程
        self.thd_heart_beat = threading.Thread(target=self._heart_beat, name='bc_heart_beat_thd')
        self.thd_heart_beat.start()

    def shutdown(self):
        """
        关闭BC
        待完善！
        """
        pass

    def get_status(self):
        """
        获取BC状态信息
        """
        s = (self.name, self.ip, self.mac, self.is_connected(), self.status, self.card, self.bshost)
        return s

    def chk_status_is(self, stat, timeout=5):
        """
        检查BC状态是
        0:保留, 1:保留, 2:锁屏, 3:解锁, 4:上机
        """
        res = False
        while timeout > 0 :
            if self.status == stat:
                res = True
                break
            else:
                time.sleep(1)
                timeout -= 1
        return res

    def chk_status_is_not(self, stat, timeout=2):
        """
        检查BC状态不是
        0:保留, 1:保留, 2:锁屏, 3:解锁, 4:上机
        """
        res = False
        while timeout > 0 :
            if self.status != stat:
                res = True
                break
            else:
                time.sleep(1)
                timeout -= 1
        return res

    def reset_status(self):
        """
        重置BC状态为锁屏状态
        """
        self.status = 2
        self.card = ""
        self.que_ack_pkt = Queue.Queue()

    def get_ack_pkt(self, ack_pkt_type, timeout=10):
        """
        获取请求信令的响应包
        """
        while timeout > 0:
            times = self.que_ack_pkt.qsize()
            for i in range(times):
                ack_pkt = self.que_ack_pkt.get_nowait()
                if ack_pkt.pkt_type == ack_pkt_type:
                    return ack_pkt
                else:
                    self.que_ack_pkt.put(ack_pkt)
            time.sleep(1)
            timeout -= 1
        return None

    def get_up(self, card, pwd='', veri_code=''):
        """
        会员上机
        """
        logging.info("[%s][%s][%d] Call method : get_up(card=%s, pwd=%s, veri_code=%s)" % (self.name, self.card, self.status, card, pwd, veri_code))
        res = False
        pkt_type = 7
        ack_pkt = None
        data = pkt_up(card, pwd, veri_code)
        #带验证码的上机信令
        if len(veri_code) != 0:
            pkt_type = 65
        pkt = get_pkt_by_data(pkt_type, data)
        self.socket.send_pkt(pkt)
        if self.chk_status_is(4) is True:
            res = True
        else:
            if pkt_type == 65:
                ack_pkt = self.get_ack_pkt(65)
            else:
                ack_pkt = self.get_ack_pkt(0x80000000 + pkt_type)
            if ack_pkt is not None:
                ack_pkt_opts = ack_pkt.data_options()
                print(ack_pkt_opts[3], ack_pkt_opts[4])
                res = False
            else:
                print(99, 'Failure up the machine, BS no response.')
                res = False
        return res

    def get_down(self):
        """
        会员下机
        """
        logging.info("[%s][%s][%d] Call method : get_down()" % (self.name, self.card, self.status))
        data = pkt_down()
        pkt = get_pkt_by_data(6, data)
        self.socket.send_pkt(pkt)
        return True