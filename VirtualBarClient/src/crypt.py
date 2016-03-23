# coding: utf-8
'''
Created on 2016年3月16日

@author: caohang
'''

import os
from ctypes import WinDLL, c_char, c_int, c_char_p, c_bool, c_uint

HERE = os.path.dirname(os.path.abspath(__file__))

class CryptDll:
    """
    调用crypt.dll,实现字符串的加解密；
    """
    def __init__(self):
        self.dllapi = WinDLL(HERE + os.path.sep + 'crypt.dll')

    def encrypt_data(self, encrypt_str, encrypt_key):
        """
        加密字符串;
        """
        self.dllapi.crypt_string.argtypes = [c_char_p, c_char_p]
        self.dllapi.crypt_string.restypes = c_char_p
        try:
            res = self.dllapi.crypt_string(encrypt_str, encrypt_key)
            if res:
                return c_char_p(res).value
            else:
                raise RuntimeError("encrypt_data failed, please check")
        except Exception as e:
            raise e

crypt_api = CryptDll()

if __name__ == '__main__':
    decrypted_key  = 'boemgsllskenfgjw'
    s = '111111~'
    s2 = crypt_api.encrypt_data(s, decrypted_key)
    print s2
