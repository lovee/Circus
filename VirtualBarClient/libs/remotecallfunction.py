#coding=utf-8
#__author__ = 'wuxinxin'

from xml.etree import ElementTree

def getFileVersion(file_name):
    import os
    import win32api
    info = win32api.GetFileVersionInfo(file_name, os.sep)
    ms = info['ProductVersionMS']
    ls = info['ProductVersionLS']
    version = '%d.%d.%d.%d' % (win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls), win32api.LOWORD(ls))
    return version

class VersionInfo:
    def read_xml(self,text):
        '''读xml文件'''
        # 加载XML文件（2种方法,一是加载指定字符串，二是加载指定文件）
        # root = ElementTree.parse(r"D:/test.xml")
        root = ElementTree.fromstring(text)
        version = root.find('version').text

        lst_node_info = root.findall("infos/info")
        info_list = []
        for index in lst_node_info:
            print index.text
            info_list.append(index.text)

        return  (version, info_list)

    def read_versioninfo(self):
        #deploy_to = r'D:\work\slave_test\wxol\jifeiserver\versioninfo.xml'
        deploy_to = r'c:\satp_wxol'
        deploy_to = deploy_to + r'\jifeiserver\versioninfo.xml'
        (v, infos) = self.read_xml(open(deploy_to).read())
        return (v, infos)

def main():
    version = VersionInfo()
    deploy_to = r'D:\work\slave_test\wxol\jifeiserver\versioninfo.xml'
    (v1, info1) = version.read_xml(open(deploy_to).read())
    print 'main end'


if __name__ == '__main__':
    main()
