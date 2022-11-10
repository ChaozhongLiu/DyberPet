import json
import os


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


if __name__ == '__main__':
    # remove_pet_action('test')
    rename_pet_action('test', 29)