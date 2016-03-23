# coding: utf-8

import os
import logging
from robotremoteserver import RobotRemoteServer
from wxbcapi import WXBCApi

HERE = os.path.dirname(os.path.abspath(__file__))
#日志级别INFO/DEBUG
LOG_LEVEL = logging.DEBUG
logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=HERE+'/logs/bc.log',
                    filemode='w')

def main():
    RobotRemoteServer(WXBCApi(HERE+'/etc/bc.ini'), host='0.0.0.0', port=8886)

