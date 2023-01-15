import sys
import time
import math
import random
import inspect
import types
import uuid
from datetime import datetime, timedelta

from apscheduler.schedulers.qt import QtScheduler
from apscheduler.triggers import interval, date, cron

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QUrl
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtMultimedia import QSoundEffect, QMediaPlayer, QMediaContent

from typing import List

from DyberPet.utils import *
from DyberPet.conf import *
from DyberPet.extra_windows import QToaster

#from win32api import GetMonitorInfo, MonitorFromPoint


import DyberPet.settings as settings


##############################
#          通知模块
##############################
'''
通知类型：
1. 系统通知
    字段：system
    图标：DyberPet icon

2. 数值相关通知
    字段：status_{hp, fv}
    图标：hp icon, fv icon

3. 计时相关通知
    字段：clock_{tomato, focus}
    图标：tomato icon, clock icon

4. 物品数量变化通知
    字段：item
    图标：item icon
'''


class DPNote(QWidget):
    def __init__(self, parent=None):
        """
        宠物组件
        :param parent: 父窗口
        :param curr_pet_name: 当前宠物名称
        :param pets: 全部宠物列表
        """
        super(DPNote, self).__init__(parent, flags=Qt.WindowFlags())

        self.items_data = ItemData()
        sys_note_conf = dict(json.load(open('res/icons/note_icon.json', 'r', encoding='UTF-8')))
        try:
            pet_note_conf = dict(json.load(open('res/role/{}/note/note.json'.format(settings.petname), 'r', encoding='UTF-8')))
        except:
            pet_note_conf = {}
        self.icon_dict, self.sound_dict = self.init_note(sys_note_conf, pet_note_conf) #{k: self.init_icon(v) for k, v in sys_note_conf.items()}
        pet_cof = dict(json.load(open('res/role/{}/pet_conf.json'.format(settings.petname), 'r', encoding='UTF-8')))
        self.item_favorite = pet_cof.get('item_favorite', [])
        self.item_dislike = pet_cof.get('item_dislike', [])

        self.note_in_prepare = False
        self.note_dict = {}
        self.height_dict = {}

        # ------------------------------------------------------------
        # 通知栏声音
        '''
        self.player = QSoundEffect()
        url = QUrl.fromLocalFile('res/13945.wav')
        #content = QMediaContent(url)
        #self.player.setMedia(content)
        self.player.setSource(url)
        self.player.setVolume(0.4)
        '''

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)

    def init_note(self, sys_note_conf, pet_note_conf):
        note_config = {}
        sound_config = {}
        for k, v in sys_note_conf.items():
            if k in pet_note_conf.keys():
                if 'image' in pet_note_conf[k].keys():
                    img_file = 'res/role/{}/note/{}'.format(settings.petname, pet_note_conf[k]['image'])
                    #image = QImage()
                    #image.load(img_file)
                else:
                    img_file = 'res/icons/{}'.format(sys_note_conf[k].get('image', 'icon.png'))
                    #image = QImage()
                    #image.load(img_file)

                if 'sound' in pet_note_conf[k].keys():
                    #player = QSoundEffect()
                    url = 'res/role/{}/note/{}'.format(settings.petname, pet_note_conf[k]['sound']) #QUrl.fromLocalFile('res/role/{}/note/{}'.format(settings.pet_data.petname, pet_note_conf[k]['sound']))
                    #player.setSource(url)
                    #player.setVolume(0.4)
                else:
                    #player = QSoundEffect()
                    url = 'res/sounds/{}'.format(sys_note_conf[k].get('sound', '13945.wav')) #QUrl.fromLocalFile('res/sounds/{}'.format(sys_note_conf[k].get('sound', '13945.wav')))
                    #player.setSource(url)
                    #player.setVolume(0.4)
            else:
                img_file = 'res/icons/{}'.format(sys_note_conf[k].get('image', 'icon.png'))
                #image = QImage()
                #image.load(img_file)

                #player = QSoundEffect()
                url = 'res/sounds/{}'.format(sys_note_conf[k].get('sound', '13945.wav')) #QUrl.fromLocalFile('res/sounds/{}'.format(sys_note_conf[k].get('sound', '13945.wav')))
                #player.setSource(url)
                #player.setVolume(0.4)

            note_config[k] = {'image':_load_item_img(img_file), 'sound':url}
            if url in sound_config.keys():
                pass
            else:
                sound_config[url] = _load_item_sound(url)

        #sound_file = 'res/sounds/{}'.format(icon_params.get('sound', '13945.wav'))
        #sound = QSound(sound_file)

        return note_config, sound_config #{'image':image, 'sound':player}

    def change_pet(self):
        sys_note_conf = dict(json.load(open('res/icons/note_icon.json', 'r', encoding='UTF-8')))
        try:
            pet_note_conf = dict(json.load(open('res/role/{}/note/note.json'.format(settings.petname), 'r', encoding='UTF-8')))
        except:
            pet_note_conf = {}
        self.icon_dict, self.sound_dict = self.init_note(sys_note_conf, pet_note_conf)

        pet_cof = dict(json.load(open('res/role/{}/pet_conf.json'.format(settings.petname), 'r', encoding='UTF-8')))
        self.item_favorite = pet_cof.get('item_favorite', [])
        self.item_dislike = pet_cof.get('item_dislike', [])


    def setup_notification(self, note_type, message=''):
        #print(note_type)
        # 排队 避免显示冲突
        while self.note_in_prepare:
            time.sleep(1)

        self.note_in_prepare = True

        if note_type in self.icon_dict.keys():
            icon = self.icon_dict[note_type]['image']
            note_type_use = note_type
        elif note_type in self.items_data.item_dict.keys():
            icon = self.items_data.item_dict[note_type]['image']
            if '-' in message:
                if note_type in self.item_favorite:
                    note_type_use = 'feed_1'
                elif note_type in self.item_dislike:
                    note_type_use = 'feed_3'
                else:
                    note_type_use = 'feed_2'
            else:
                note_type_use = 'system'
        else:
            icon = self.icon_dict['system']['image']
            note_type_use = 'system'
        
        '''
        n_note = len(self.height_dict.keys()) + 1
        note_index = min(set(range(n_note)) - set(self.height_dict.keys()))
        print(note_index)

        height_margin = 0
        for ind in self.height_dict.keys():
            if ind < note_index:
                height_margin += self.height_dict[ind] + 10
        '''

        note_index = str(uuid.uuid4())
        height_margin = sum(self.height_dict.values()) + 10*(len(self.height_dict.keys()))
        #print(height_margin)
        #note_index = len(self.note_list)
        self.note_dict[note_index] = QToaster(note_index,
                                              message=message,
                                              icon=icon,
                                              corner=Qt.BottomRightCorner,
                                              height_margin=height_margin,
                                              closable=True,
                                              timeout=5000)
        #if not self.player.isPlaying():
        #    self.player.play()
        if note_type_use in ['feed_1','feed_2','feed_3']:
            if sum([self.sound_dict[i].isPlaying() for i in self.sound_dict.keys()]) == 0:
                pass
            else:
                for i in self.sound_dict.keys():
                    self.sound_dict[i].stop()
            self.sound_dict[self.icon_dict[note_type_use]['sound']].setVolume(settings.volume)
            self.sound_dict[self.icon_dict[note_type_use]['sound']].play()
        else:
            if sum([self.sound_dict[i].isPlaying() for i in self.sound_dict.keys()]) == 0:
                self.sound_dict[self.icon_dict[note_type_use]['sound']].setVolume(settings.volume)
                self.sound_dict[self.icon_dict[note_type_use]['sound']].play()

        self.note_dict[note_index].closed_note.connect(self.remove_note)
        Toaster_height = self.note_dict[note_index].height()
        self.height_dict[note_index] = int(Toaster_height)
        self.note_in_prepare = False
        #print('check')
        #self.send_notification.emit(note_index, message, icon)
    '''
    def add_height(self, note_index, height):
        self.height_dict[note_index] = int(height)
    '''

    def remove_note(self, note_index, close_type):
        self.note_dict.pop(note_index)
        self.height_dict.pop(note_index)
        if close_type == 'button':
            for i in self.sound_dict.keys():
                self.sound_dict[i].stop()

    def hpchange_note(self, hp_tier, direction):
        # 宠物到达饥饿状态和饿死时，发出通知
        if direction == 'up':
            return
        if hp_tier == 0:
            self.setup_notification('status_hp', message='宠物要饿死啦！(好感度开始下降)')
        elif hp_tier == 1:
            self.setup_notification('status_hp', message='宠物现在很饿哦~ （好感度停止增加）')

    def fvchange_note(self, fv_lvl):
        #print(fv_lvl,'note')
        if fv_lvl == -1:
            self.setup_notification('status_fv', message='恭喜你！好感度已达上限！感谢这么久以来的陪伴！')
        else:
            self.setup_notification('status_fv', message='好感度升级至 lv%s 啦！更多的动作和物品已经解锁！'%(int(fv_lvl)))

    '''
    def showToaster(self):
        if self.sender() == self.windowBtn:
            parent = self
            desktop = False
        else:
            parent = None
            desktop = True
        corner = QtCore.Qt.Corner(self.cornerCombo.currentData())
        QToaster.showMessage(
            parent, self.textEdit.text(), corner=corner, desktop=desktop)
    '''




def _load_item_img(img_path):
    return _get_q_img(img_path)

def _get_q_img(img_file) -> QImage:
    image = QImage()
    image.load(img_file)
    return image

def _load_item_sound(file_path):
    player = QSoundEffect()
    url = QUrl.fromLocalFile(file_path)
    player.setSource(url)
    player.setVolume(settings.volume)
    return player


