import json
import os
import time
from datetime import datetime
import textwrap as tr
import locale



def log(*args, **kwargs):
    """
    日志
    :param args:
    :param kwargs:
    :return:
    """
    print(*args, **kwargs)


def read_json(conf_file):
    """
    读取配置
    :param conf_file:
    :return: map
    """
    with open(conf_file, 'r', encoding='UTF-8') as file:
        return json.load(file)


def rename_pet_action(pet_name: str, start_idx: int) -> None:
    """
    根据宠物名, 重命名宠物文件夹下的图片, 从0到n
    :param start_idx: 开始坐标
    :param pet_name: 宠物名称
    :return:
    """
    path = '../res/role/{}/action/'.format(pet_name)
    files = os.listdir(path)
    for i, f in enumerate(files):
        os.rename(path + '/' + f, path + '/' + '{}.png'.format(start_idx + i))


def remove_pet_action(pet_name: str) -> None:
    """
    删除宠物动作
    :param pet_name: 宠物名称
    :return:
    """
    path = '../res/role/{}/action/'.format(pet_name)
    files = os.listdir(path)
    for file in files:
        os.remove(path + '/' + file)



def text_wrap(text, width):
    # Use textwrap to do the initial wrapping
    lines = tr.wrap(text, width)
    
    # Define punctuation that shouldn't appear at the end or start of a line
    prohibited_start = ",.!?;:，。！？；："

    new_lines = []
    for i, line in enumerate(lines):
        if i==0:
            pass
        elif line[0] in prohibited_start:
            lines[i-1] += line[0]
            line = line[1:]
        new_lines.append(line)

    texts_wrapped = '\n'.join(new_lines)
    
    return texts_wrapped


def get_child_folder(parentFolder, relative=False):
    all_files_and_dirs = os.listdir(parentFolder)
    if relative:
        all_dirs = [os.path.basename(d) for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]
    else:
        all_dirs = [os.path.join(parentFolder,d) for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]

    return all_dirs




def get_file_time(filePath):
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    ct = os.path.getctime(filePath)
    ct = time.strptime(time.ctime(ct))
    fileTime = datetime(year=int(ct[0]), month=int(ct[1]), day=int(ct[2]),
                        hour=int(ct[3]), minute=int(ct[4]), second=int(ct[5]))
    return fileTime
