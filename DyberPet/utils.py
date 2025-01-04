import json
import os
import time
import platform
import subprocess
import ctypes

from datetime import datetime
import textwrap as tr
import locale
import bisect

from itertools import accumulate
from PySide6.QtCore import QTime
from glob import glob


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


def _qtime_to_min(input_time):
    return input_time.hour()*60 + input_time.minute()

def _min_to_qtime(input_time):
    new_hour = input_time // 60
    new_minute = input_time % 60

    return QTime(new_hour, new_minute)

convert_dict = {('min', 'qtime'):_min_to_qtime,
                ('qtime', 'min'):_qtime_to_min}

def TimeConverter(input_time, from_format, to_format):
    return convert_dict[(from_format, to_format)](input_time)


def find_dir_with_subdir(parent_dir, sub_dir):
    """Given the parent_dir, find all 'parent_dir/child_dir/sub_dir' and return as a list"""
    
    pcs_dirs = glob(os.path.join(parent_dir, f'**/{sub_dir}/'), recursive=True)
    pcs_dirs = [os.path.normpath(i) for i in pcs_dirs]

    filtered_dirs = []
    for dir_path in pcs_dirs:
        relative_path = os.path.relpath(dir_path, parent_dir)
        depth = relative_path.count(os.sep)
        if depth == 1:
            filtered_dirs.append(dir_path)
    
    return filtered_dirs



class SubPet_Manager:
    """
    Class to manage subpets positions
    Subpet can be on either left or right of the main pet.
    """
    def __init__(self):
        # Dictionary to store subpet name and their anchor_x, subpet width
        # {subpet_name: {'anchor_x': int, 'width': int}}
        self.subpets = {}
        self.default_distance = 30

    def add_subpet(self, subpet_name, width):
        """
        Add a subpet to the manager and automatically calculate its anchor_x.
        :param subpet_name: Name of the subpet
        """
        if not self.subpets:
            new_anchor_x = self.default_distance
        else:
            # Determine the side (left or right) of the subpet by numbers on each side
            left_num = sum(1 for subpet in self.subpets.values() if subpet['anchor_x'] < 0)
            right_num = len(self.subpets) - left_num
            if left_num < right_num:
                # set subpet on the left side
                new_anchor_x = min(0, min(self.subpets.values(), key=lambda x: x['anchor_x'])['anchor_x']) - self.default_distance - width
            else:
                # set subpet on the right side
                rightmost_subpet_name = max(self.subpets, key=lambda x: self.subpets[x]['anchor_x'])
                if self.subpets[rightmost_subpet_name]['anchor_x'] < 0:
                    new_anchor_x = self.default_distance
                else:
                    new_anchor_x = self.subpets[rightmost_subpet_name]['anchor_x'] + self.subpets[rightmost_subpet_name]['width'] + self.default_distance

        self.subpets[subpet_name] = {'anchor_x': new_anchor_x, 'width': width}
        

    def remove_subpet(self, subpet_name):
        """
        Remove a subpet from the manager.
        :param subpet_name: Name of the subpet to be removed
        """
        if subpet_name in self.subpets:
            
            removed_subpet = self.subpets.pop(subpet_name)
            # determine which side the removed subpet is on
            if removed_subpet['anchor_x'] < 0:
                # it is on the left side
                # update the anchor_x of all subpets on its left
                for subpet_name in self.subpets.keys():
                    if self.subpets[subpet_name]['anchor_x'] < removed_subpet['anchor_x']:
                        self.subpets[subpet_name]['anchor_x'] -= removed_subpet['anchor_x']
            else:
                # it is on the right side
                for subpet_name in self.subpets.keys():
                    if self.subpets[subpet_name]['anchor_x'] > removed_subpet['anchor_x']:
                        self.subpets[subpet_name]['anchor_x'] += -removed_subpet['anchor_x'] - removed_subpet['width']

    def update_anchor(self, subpet_name, new_anchor_x):
        """
        Update the anchor position of a subpet.
        :param subpet_name: Name of the subpet
        :param new_anchor_x: The new x-coordinate anchor position of the subpet
        """
        raise NotImplementedError("This method is not implemented yet.")

    def get_anchor(self, subpet_name):
        """
        Get the anchor position of a subpet.
        :param subpet_name: Name of the subpet
        :return: The x-coordinate anchor position of the subpet
        """
        return self.subpets.get(subpet_name, {'anchor_x': None, 'width': None})['anchor_x']


def convert_fv_versions(fv:int, fv_lvl:int, from_fv_bar:list, to_fv_bar:list):
    """
    In case favor system levels are updated. Convert from old fv levels to new levels
    """
    fv_points = sum(from_fv_bar[:fv_lvl]) + fv
    cumulative_sum = list(accumulate(to_fv_bar))
    pos = bisect.bisect_left(cumulative_sum, fv_points)
    if pos == 0:
        return pos, fv_points
    elif pos >= len(cumulative_sum):
        return len(cumulative_sum)-1, to_fv_bar[-1]
    elif cumulative_sum[pos] == fv_points:
        pos += 1
        return pos, fv_points - cumulative_sum[pos-1]
    else:
        return pos, fv_points - cumulative_sum[pos-1]



def is_system_active():
    system = platform.system()

    if system == "Windows":
        try:
            GetTickCount64 = ctypes.windll.kernel32.GetTickCount64
            GetTickCount64.restype = ctypes.c_ulonglong  # Use ctypes.c_ulonglong for ULONGLONG
            uptime_ms = GetTickCount64()
            return uptime_ms > 0
        except Exception as e:
            print("System mode checking failed. Return True")
            return True

    elif system == "Darwin":  # macOS
        try:
            output = subprocess.check_output(["pmset", "-g", "ps"], text=True)
            if "Sleep" not in output:
                return True
            return False
        except Exception as e:
            print("System mode checking failed. Return True")
            return True

    else:
        print("Unsupported platform.")
        return True

def is_system_locked():
    system = platform.system()

    if system == "Windows":
        import ctypes
        user32 = ctypes.windll.User32
        is_locked = (user32.GetForegroundWindow() % 10 == 0)
        return is_locked

    elif system == "Darwin":
        # macOS not implemented yet
        return False

    else:
        # Unsupported platform
        return False