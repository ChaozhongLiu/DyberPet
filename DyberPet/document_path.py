import platform
import os

# 程序根目录
if platform == 'win32':
    document_basedir = ''
else:
    document_basedir = os.path.dirname(__file__)
    document_basedir = document_basedir.replace('\\','/')
    document_basedir = '/'.join(document_basedir.split('/')[:-1])

# 数据路径
document_datadir = os.path.join(document_basedir, 'data')

# 设置路径
document_configpath = os.path.join(document_basedir, 'data/settings.json')