# coding: utf-8

import socket
import Queue
import threading
import binascii

# 监测管道基类，实现socket管道的创建和数据包截取；
# 组网如下：
# Client-->Pipe-->Server
class Pipe():
    def __init__(self, pipe_ip, pipe_port, server_ip, server_port):
        self.pipe_host = (pipe_ip, pipe_port)
        self.server_host = (server_ip, server_port)

        self.c2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.c2p_queue = Queue.Queue()
        self.p2s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p2s_queue = Queue.Queue()

        self._c2p_send_thd = None
        self._c2p_recv_thd = None
        self._p2s_send_thd = None
        self._p2s_recv_thd = None

        self._threads = []

    def start_up_c2p(self):
        self.c2p.bind(self.pipe_host)
        self.c2p.listen(1)
        self.c2p = self.c2p.accept()[0]
        self._c2p_recv_thd = threading.Thread(target=self._thd_recv, name='c2p_recv_thd', args=(self.c2p, self.c2p_queue))
        self._c2p_recv_thd.start()
        self._threads.append(self._c2p_recv_thd)
        self._c2p_send_thd = threading.Thread(target=self._thd_send, name='c2p_send_thd', args=(self.c2p, self.p2s_queue))
        self._c2p_send_thd.start()
        self._threads.append(self._c2p_send_thd)

    def start_up_p2s(self):
        self.p2s.connect(self.server_host)
        self._p2s_recv_thd = threading.Thread(target=self._thd_recv, name='p2s_recv_thd', args=(self.p2s, self.p2s_queue))
        self._p2s_recv_thd.start()
        self._threads.append(self._p2s_recv_thd)
        self._p2s_send_thd = threading.Thread(target=self._thd_send, name='p2s_send_thd', args=(self.p2s, self.c2p_queue))
        self._p2s_send_thd.start()
        self._threads.append(self._p2s_send_thd)

    def _thd_recv(self, i_socket, o_buff):
        while True:
            stream = i_socket.recv(1024)
            o_buff.put(stream)

    def _thd_send(self, i_socket, o_buff):
        while True:
            stream = o_buff.get()
            i_socket.send(stream)
            self.view(i_socket, stream)

    def run(self):
        # 启动Pipe监听端口，待Client连接；
        self.start_up_c2p()
        self.start_up_p2s()
        for t in self._threads:
            t.join()


    def view(self, i_socket, stream):
        hex_str = binascii.hexlify(stream)
        print(hex_str)


if __name__ == '__main__':
    pip = Pipe("10.34.43.71", 8889, "10.34.50.45", 21011)
    pip.run()
