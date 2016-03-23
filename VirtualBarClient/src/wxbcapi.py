# coding: utf-8
'''
Created on 2016年3月15日

@author: caohang
'''

import ConfigParser
import time
import threading
import os
from wxbc import WXBC

class WXBCApi():
    """
    # WXBC模拟器RF调用接口；
    # 1、实现配置文件控制批量客户端模拟；
    # 2、实现RF远程调用；
    # 3、实现BC状态显示；
    """
    def __init__(self, env_ini):
        self.bc_box = {}
        self._loading(env_ini)
        self.print_thd = threading.Thread(target=self._print_bc_status, name='api_print_thd')
        self.print_thd.start()

    def _loading(self, env_ini):
        '''
        加载BC配置文件，实例化模拟端
        '''
        cp = ConfigParser.ConfigParser()
        cp.read(env_ini)
        for s in cp.sections():
            bshost = cp.get(s, 'bshost')
            bc = WXBC(name=s, bshost=(bshost, 11011))
            bc.startup()
            self.bc_box[s] = bc

    def _print_bc_status(self):
        """
        显示BC状态，仅用于状态显示线程调用；
        """
        while True:
            os.system('cls')
            #title = '|' + u"客户端".center(20) + '|' + u"状态".center(6) + '|' + u"卡号".center(20) + '|' + u"BS HOST".center(20) + '|'
            #print title
            for bc in self.bc_box.items():
                st = bc[1].get_status()
                #连接状态
                if st[3] is True:
                    conn = u'正常'
                else:
                    conn = u'断开'
                #业务状态
                if st[4]==0:
                    stat = u'0'
                elif st[4]==1:
                    stat = u'1'
                elif st[4]==2:
                    stat = u'锁屏'
                elif st[4]==3:
                    stat = u'解锁'
                elif st[4]==4:
                    stat = u'上机'
                s = ''
                s += st[0].ljust(20)
                s += '|'
                s += conn.center(6)
                s += '|'
                s += stat.center(6)
                s += '|'
                s += st[5].center(20)
                s += '|'
                s += st[6][0].center(17)
                s += '|'
                print(s)
            time.sleep(1)

    def is_virtual_client(self):
        """
        用于RF检测是否连接的是虚拟客户端
        """
        return True

    def bc_get_up(self, bc_name, card, pwd='', veri_code=''):
        """
        会员BC端上机
        """
        res = self.bc_box[bc_name].get_up(card, pwd, veri_code)
        return res

    def bc_get_down(self, bc_name):
        """
        会员BC端下机
        """
        res = self.bc_box[bc_name].get_down()
        return res

    def bc_reset(self, bc_name):
        """
        重置BC端为锁屏状态；
        """
        res = self.bc_box[bc_name].reset_status()
        return res
