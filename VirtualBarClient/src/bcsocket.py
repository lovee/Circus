# coding: utf-8
'''
Created on 2016年3月15日

@author: caohang
'''

import socket
import Queue
import threading
import struct
import logging
import time
from errno import EWOULDBLOCK

from bcpacket import get_pkt_by_stream

class BCSocket():
    """
    客户端模拟器Socket，实现BC<-->BS间信令包的发送与接收；
    """
    def __init__(self, name=""):
        self.name = name
        self.bc_socket = None
        self.bs_host = ("127.0.0.1",11011)
        self._threads = []
        self._thd_send = None
        self._thd_recv = None
        self._que_send = Queue.Queue()
        self._que_recv = Queue.Queue()
        self.connected_flag = threading.Event()
        self.connected_flag.set()

    def _recv(self):
        """
        仅用于socket数据接收线程调用
        """
        buf = b''
        while not self.connected_flag.is_set():
            try:
                buf = self._recv_data(20)
                flag, data_size, reserve, i_type, i_id = struct.unpack("<IIIII", buf)
                if(flag != 0xAB65AB65):
                    logging.error("异常消息，接收线程异常退出")
                    self.disconnect()
                buf += self._recv_data(data_size)
                pkt = get_pkt_by_stream(buf)
                self._que_recv.put(pkt)
                log   = "\n"
                log += "<<<<<<<<<<<<<<<<<<<<<[%s][%s:%d] Recv Packet<<<<<<<<<<<<<<<<<<<<<" % (self.name, self.bs_host[0], self.bs_host[1])
                log += "\n"
                log += pkt.to_string()
                logging.debug(log)
                buf = b''
            except Exception as e:
                logging.error("[%s][%s:%d] recv data exception %s, end recv thread." % (self.name, self.bs_host[0], self.bs_host[1], e))
                self.disconnect()
                break

    def _recv_data(self, n):
        """
        socket非阻塞式数据接收，仅用于内部调用
        """
        data = ''
        while len(data) < n:
            if self.connected_flag.is_set():
                break
            try:
                recv_chunk_size = n - len(data)
                if recv_chunk_size < 1024:
                    chunk = self.bc_socket.recv(recv_chunk_size)
                else:
                    chunk = self.bc_socket.recv(1024)
                data += chunk
            except socket.error, why:
                if why.args[0] == EWOULDBLOCK:
                    time.sleep(1)
                else:
                    raise why
        return data

    def _send(self):
        """
        仅用于socket数据发送线程调用
        """
        while not self.connected_flag.is_set():
            try:
                pkt = self._que_send_get(timeout=1)
                if pkt is None:
                    continue
            except Queue.Empty:
                continue
            #打印非心跳信令
            if pkt.pkt_type!=3:
                log   = "\n"
                log += ">>>>>>>>>>>>>>>>>>>>>[%s][%s:%d] Send Packet>>>>>>>>>>>>>>>>>>>>>" % (self.name, self.bs_host[0], self.bs_host[1])
                log += "\n"
                log += pkt.to_string()
                logging.debug(log)
            try:
                self._send_data(pkt.stream)
            except Exception as e:
                logging.error("[%s][%s:%d] send data exception %s, end send thread." % (self.name, self.bs_host[0], self.bs_host[1], e))
                #self.disconnect()
                break

    def _send_data(self, stream):
        """
        socket非阻塞式数据发送，仅用于内部调用
        """
        try:
            send_bytes = self.bc_socket.send(stream)
            if send_bytes > 0:
                over_data = stream[send_bytes:]
                if len(over_data) > 0:
                    self._send_data(over_data)
        except socket.error, why:
            if why.args[0] == EWOULDBLOCK:
                return
            else:
                raise why

    def _que_send_get(self, timeout=1):
        """
        从发送信令队列中获取信令，优先获取登录信令，解决改BS时间引起的断链优先重连；
        """
        while timeout >= 0:
            qsize = self._que_send.qsize()
            if qsize > 0:
                for i in range(qsize):
                    pkt = self._que_send.get_nowait()
                    #如果有登录信令，优先返回
                    if pkt.pkt_type == 2:
                        return pkt
                    else:
                        self._que_send.put(pkt)
                pkt = self._que_send.get_nowait()
                return pkt
            time.sleep(1)
            timeout -= 1
        return None

    def connect(self, bs_host=()):
        """
        建立socket连接
        """
        self.bc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.bc_socket.connect(bs_host)
            self.connected_flag.clear()
            self.bs_host = bs_host
            self.bc_socket.setblocking(0)
            logging.info("[%s][%s:%d] connect success." % (self.name, self.bs_host[0], self.bs_host[1]))
        except Exception as e:
            self.connected_flag.set()
            raise e
        #self._que_recv.empty()
        #self._que_send.empty()
        self._thd_send = threading.Thread(target=self._send, name='bc_send_thd')
        self._thd_recv = threading.Thread(target=self._recv, name='bc_recv_thd')
        self._thd_send.start()
        self._thd_recv.start()
        self._threads.append(self._thd_send)
        self._threads.append(self._thd_recv)

    def disconnect(self):
        """
        断开socket连接
        """
        if self.is_connected():
            logging.info("[%s][%s:%d] disconnect." % (self.name, self.bs_host[0], self.bs_host[1]))
            self.connected_flag.set()
            try:
                self.bc_socket.close()
            except Exception:
                pass
            for t in self._threads:
                if t is not threading.current_thread():
                    t.join(timeout=3)

    def is_connected(self):
        """
        socket是否连接正常
        """
        return not self.connected_flag.is_set()

    def send_pkt(self, bc_pkt):
        """
        发送信令包
        """
        self._que_send.put(bc_pkt)

    def recv_pkt(self, time_out=10):
        """
        接收信令包
        """
        try:
            pkt = self._que_recv.get(timeout=time_out)
        except Queue.Empty:
            pkt = None
        return pkt