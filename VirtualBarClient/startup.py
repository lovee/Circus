# coding: utf-8


import sys
import os

reload(sys)
sys.setdefaultencoding('utf8')

__version__ = '1.0.0'
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    import sys
    sys.path.append(os.path.join(HERE, 'libs'))
    sys.path.append(os.path.join(HERE, 'src'))
    import main
    main.main()

if __name__ == '__main__':
    main()
