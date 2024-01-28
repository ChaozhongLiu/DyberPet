import sys
from sys import platform
import time
import math
import uuid
import types
import random
import inspect
from typing import List
from datetime import datetime, timedelta

from apscheduler.schedulers.qt import QtScheduler
from apscheduler.triggers import interval, date, cron

from PySide6.QtWidgets import *
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtCore import Qt, QTimer, QObject, QPoint, QUrl
from PySide6.QtGui import QImage, QPixmap, QIcon, QCursor
from PySide6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput #, QMediaContent

from DyberPet.utils import *
from DyberPet.conf import *
from DyberPet.extra_windows import QToaster

import DyberPet.settings as settings
'''
if platform == 'win32':
    basedir = ''
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-1])
'''
basedir = settings.BASEDIR

##############################
#          通知模块
##############################
'''
通知类型：
1. 系统通知
    字段：system
    图标：DyberPet icon

2. 数值相关通知
    字段：status_{hp, fv, coin}
    图标：hp icon, fv icon, coin icon

3. 计时相关通知
    字段：clock_{tomato, focus, remind}
    图标：tomato icon, clock icon

4. 物品数量变化通知
    字段：item
    图标：item icon

5. 喂食通知
    字段：feed_{1,2,3}
    图标: item icon

6. 问好
    字段: greeting_{1,2,3,4}
    图标: system
'''


class DPNote(QWidget):

    noteToLog = Signal(QPixmap, str, name="noteToLog")

    def __init__(self, parent=None):
        """
        通知组件
        """
        super(DPNote, self).__init__(parent)

        self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        sys_note_conf = dict(json.load(open(os.path.join(basedir, 'res/icons/note_icon.json'), 'r', encoding='UTF-8')))
        try:
            pet_note_conf = dict(json.load(open(os.path.join(basedir, 'res/role/{}/note/note.json'.format(settings.petname)), 'r', encoding='UTF-8')))
        except:
            pet_note_conf = {}
        self.icon_dict, self.sound_dict = self.init_note(sys_note_conf, pet_note_conf)
        pet_cof = dict(json.load(open(os.path.join(basedir, 'res/role/{}/pet_conf.json'.format(settings.petname)), 'r', encoding='UTF-8')))
        self.item_favorite = pet_cof.get('item_favorite', [])
        self.item_dislike = pet_cof.get('item_dislike', [])

        self.note_in_prepare = False
        self.note_dict = {}
        self.height_dict = {}
        self.sound_playing = []

        if platform == 'win32':
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        else:
            # SubWindow not work in MacOS
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        

    def init_note(self, sys_note_conf, pet_note_conf):
        note_config = {}
        sound_config = {}
        for k, v in sys_note_conf.items():
            if k in pet_note_conf.keys():
                if 'image' in pet_note_conf[k].keys():
                    img_file = os.path.join(basedir, 'res/role/{}/note/{}'.format(settings.petname, pet_note_conf[k]['image']))
                else:
                    img_file = os.path.join(basedir, 'res/icons/{}'.format(sys_note_conf[k].get('image', 'icon.png')))

                if 'sound' in pet_note_conf[k].keys():
                    url = os.path.join(basedir, 'res/role/{}/note/{}'.format(settings.petname, pet_note_conf[k]['sound'])) #QUrl.fromLocalFile('res/role/{}/note/{}'.format(settings.pet_data.petname, pet_note_conf[k]['sound']))
                else:
                    url = os.path.join(basedir, 'res/sounds/{}'.format(sys_note_conf[k].get('sound', 'Notification.wav'))) #QUrl.fromLocalFile('res/sounds/{}'.format(sys_note_conf[k].get('sound', '13945.wav')))

                if 'sound_priority' in pet_note_conf[k].keys():
                    pty = pet_note_conf[k]['sound_priority']
                else:
                    pty = sys_note_conf[k].get('sound_priority', 0)

                if 'fv_lock' in pet_note_conf[k].keys():
                    flk = pet_note_conf[k]['fv_lock']
                else:
                    flk = sys_note_conf[k].get('fv_lock', 0)
            else:
                img_file = os.path.join(basedir, 'res/icons/{}'.format(sys_note_conf[k].get('image', 'icon.png')))

                url = os.path.join(basedir, 'res/sounds/{}'.format(sys_note_conf[k].get('sound', 'Notification.wav')))  #QUrl.fromLocalFile('res/sounds/{}'.format(sys_note_conf[k].get('sound', '13945.wav')))

                pty = sys_note_conf[k].get('sound_priority', 0)
                flk = sys_note_conf[k].get('fv_lock', 0)

            note_config[k] = {'image':_load_item_img(img_file), 'sound':url, 'fv_lock':flk}

            if url in sound_config.keys():
                pass
            else:
                sound_config[url] = {'sound':_load_item_sound(url), 'priority': pty}

        for k, v in pet_note_conf.items():
            if k in note_config.keys():
                continue

            if 'image' in pet_note_conf[k].keys():
                img_file = os.path.join(basedir, 'res/role/{}/note/{}'.format(settings.petname, pet_note_conf[k]['image']))
            else:
                img_file = os.path.join(basedir, 'res/icons/icon.png')

            if 'sound' in pet_note_conf[k].keys():
                url = os.path.join(basedir, 'res/role/{}/note/{}'.format(settings.petname, pet_note_conf[k]['sound']))
            else:
                url = os.path.join(basedir, 'res/sounds/Notification.wav')

            if 'sound_priority' in pet_note_conf[k].keys():
                pty = pet_note_conf[k]['sound_priority']
            else:
                pty = 0

            flk = pet_note_conf[k].get('fv_lock', 0)

            note_config[k] = {'image':_load_item_img(img_file), 'sound':url, 'fv_lock':flk}

            if url in sound_config.keys():
                pass
            else:
                sound_config[url] = {'sound':_load_item_sound(url), 'priority': pty}

        return note_config, sound_config #{'image':image, 'sound':player}

    def change_pet(self):
        sys_note_conf = dict(json.load(open(os.path.join(basedir, 'res/icons/note_icon.json'), 'r', encoding='UTF-8')))
        try:
            pet_note_conf = dict(json.load(open(os.path.join(basedir, 'res/role/{}/note/note.json'.format(settings.petname)), 'r', encoding='UTF-8')))
        except:
            pet_note_conf = {}
        self.icon_dict, self.sound_dict = self.init_note(sys_note_conf, pet_note_conf)

        pet_cof = dict(json.load(open(os.path.join(basedir, 'res/role/{}/pet_conf.json'.format(settings.petname)), 'r', encoding='UTF-8')))
        self.item_favorite = pet_cof.get('item_favorite', [])
        self.item_dislike = pet_cof.get('item_dislike', [])


    def setup_notification(self, note_type, message=''):
        # 排队 避免显示冲突
        while self.note_in_prepare:
            time.sleep(1)

        self.note_in_prepare = True

        if note_type in self.icon_dict.keys():
            icon = self.icon_dict[note_type]['image']
            note_type_use = note_type

        elif note_type in self.items_data.item_dict.keys():
            icon = self.items_data.item_dict[note_type]['image']
            note_type_use = 'system'

        elif note_type == 'random':
            random_list = [i for i in self.icon_dict.keys() if i.startswith('random') and\
                           self.icon_dict[i]['fv_lock']<= settings.pet_data.fv_lvl]
            #print(random_list)
            if len(random_list) == 0:
                self.note_in_prepare = False
                return
            else:
                note_type_use = random.sample(random_list,1)[0]
                icon = self.icon_dict[note_type_use]['image']

        else:
            icon = self.icon_dict['system']['image']
            note_type_use = 'system'

        note_index = str(uuid.uuid4())
        if message != '':
            height_margin = sum(self.height_dict.values()) + 10*(len(self.height_dict.keys()))
            self.note_dict[note_index] = QToaster(note_index,
                                                  message=message,
                                                  icon=icon,
                                                  corner=Qt.BottomRightCorner,
                                                  height_margin=height_margin,
                                                  closable=True,
                                                  timeout=5000)
            self.note_dict[note_index].closed_note.connect(self.remove_note)
            Toaster_height = self.note_dict[note_index].height()
            self.height_dict[note_index] = int(Toaster_height)

        # 播放声音
        sound_key = self.icon_dict[note_type_use]['sound']
        sound_pty = self.sound_dict[sound_key]['priority']

        play_now = False
        
        for i in self.sound_dict.keys():
            if not self.sound_dict[i]['sound'].isPlaying():
                continue
            else:
                played_pty = self.sound_dict[i]['priority']
                if played_pty >= sound_pty:
                    play_now = True
                    break
                else:
                    self.sound_dict[i]['sound'].stop()
                    break
        
        if not play_now:
            self.sound_playing = [note_index, sound_key]
            self.sound_dict[sound_key]['sound'].setVolume(settings.volume)
            self.sound_dict[sound_key]['sound'].play()

        
        self.note_in_prepare = False

        if message != '':
            self.noteToLog.emit(icon, message)


    def remove_note(self, note_index, close_type):
        self.note_dict.pop(note_index)
        self.height_dict.pop(note_index)
        if close_type == 'button':
            if note_index == self.sound_playing[0]:
                self.sound_dict[self.sound_playing[1]]['sound'].stop()
            #for i in self.sound_dict.keys():
            #    self.sound_dict[i]['sound'].stop()

    def hpchange_note(self, hp_tier, direction):
        # 宠物到达饥饿状态和饿死时，发出通知
        if direction == 'up':
            return
        if hp_tier == 0:
            self.setup_notification('status_hp', message=self.tr('宠物要饿死啦！(好感度开始下降)'))
        elif hp_tier == 1:
            self.setup_notification('status_hp', message=self.tr('宠物现在很饿哦~ （好感度停止增加）'))

    def fvchange_note(self, fv_lvl):
        #print(fv_lvl,'note')
        if fv_lvl == -1:
            self.setup_notification('status_fv', message=self.tr('恭喜你！好感度已达上限！感谢这么久以来的陪伴！'))
        else:
            self.setup_notification('status_fv', message=f"{self.tr('好感度升级至')} lv{int(fv_lvl)}! {self.tr('更多的内容可能已经解锁啦！')}")






def _load_item_img(img_path):
    return _get_q_img(img_path)

def _get_q_img(img_file) -> QPixmap:
    image = QPixmap()
    image.load(img_file)
    return image

def _load_item_sound(file_path):
    
    player = QSoundEffect()
    url = QUrl.fromLocalFile(file_path)
    player.setSource(url)
    player.setVolume(settings.volume)
    return player


