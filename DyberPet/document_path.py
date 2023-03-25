import platform
import os
import json
import sys

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

# 依赖项，搬自settings.py
def get_petlist(dirname):
    folders = os.listdir(dirname)
    pets = []
    subpets = []
    for folder in folders:
        folder_path = os.path.join(dirname, folder)
        if folder != 'sys' and os.path.isdir(folder_path):
            pets.append(folder)
            conf_path = os.path.join(folder_path, 'pet_conf.json')
            conf = dict(json.load(open(conf_path, 'r', encoding='UTF-8')))
            subpets += [i for i in conf.get('subpet',{}).keys()]
    pets = list(set(pets))
    subpets = list(set(subpets))
    for subpet in subpets:
        pets.remove(subpet)

    return pets

# 宠物路径
document_pets = get_petlist(os.path.join(document_basedir, 'res/role'))

# 程序路径
document_application_path = os.path.abspath(sys.argv[0])