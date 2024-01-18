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
    locale.setlocale(locale.LC_ALL, 'C')
    ct = os.path.getctime(filePath)
    ct = time.strptime(time.ctime(ct))
    fileTime = datetime(year=int(ct[0]), month=int(ct[1]), day=int(ct[2]),
                        hour=int(ct[3]), minute=int(ct[4]), second=int(ct[5]))
    return fileTime



def get_MODs(filePath):
    modNames = []

    itemMods = get_child_folder(filePath, relative=False)
    itemMods = [i for i in itemMods if not os.path.basename(i).startswith('_')] # omit folder name starts with '_'
    modTimes = [get_file_time(mod) for mod in itemMods]
    paired_list = zip(modTimes, itemMods)
    # Sort the pairs
    sorted_pairs = sorted(paired_list)
    # Extract the sorted elements
    sorted_itemMods = [element for _, element in sorted_pairs]

    for i, itemFolder in enumerate(sorted_itemMods):

        if not os.path.exists(os.path.join(itemFolder, 'items_config.json')):
            continue

        info_file = os.path.join(itemFolder, 'info.json')
        if os.path.exists(info_file):
            info = dict(json.load(open(info_file, 'r', encoding='UTF-8')))
            modName = info.get('modName', None)
        else:
            modName = None
        if not modName:
            modName = os.path.basename(itemFolder)

        modNames.append(modName)

    return modNames



def MaskPhrase(phrase):
    def mask_word(word):
        if len(word) <= 3:
            return "?" * len(word)
        else:
            return word[0] + "?" * (len(word) - 2) + word[-1]

    # Splitting the phrase into words and spaces
    words = []
    current_word = ""
    for char in phrase:
        if char.isspace():
            if current_word:  # Add the current word to the list before the space
                words.append(current_word)
                current_word = ""
            words.append(char)  # Add the space as a separate element
        else:
            current_word += char
    if current_word:  # Add the last word if there is one
        words.append(current_word)

    # Mask each word and join back into a phrase
    masked_words = [mask_word(word) if not word.isspace() else word for word in words]
    return ''.join(masked_words)