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
        self.icon_conf = dict(json.load(open('res/icons/note_icon.json', 'r', encoding='UTF-8')))
        self.icon_dict = {k: self.init_icon(v) for k, v in self.icon_conf.items()}

        self.note_in_prepare = False
        self.note_dict = {}
        self.height_dict = {}

        # ------------------------------------------------------------
        # 通知栏声音
        self.player = QSoundEffect()
        url = QUrl.fromLocalFile('res/13945.wav')
        #content = QMediaContent(url)
        #self.player.setMedia(content)
        self.player.setSource(url)
        self.player.setVolume(0.4)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)

    def init_icon(self, icon_params):
        img_file = 'res/icons/{}'.format(icon_params.get('image', 'icon.png'))
        image = QImage()
        image.load(img_file)
        return image


    def setup_notification(self, note_type, message=''):
        #print(note_type)
        # 排队 避免显示冲突
        while self.note_in_prepare:
            time.sleep(1)

        self.note_in_prepare = True

        if note_type in self.icon_dict.keys():
            icon = self.icon_dict[note_type]
        elif note_type in self.items_data.item_dict.keys():
            icon = self.items_data.item_dict[note_type]['image']
        else:
            icon = self.icon_dict['system']
        
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
        if not self.player.isPlaying():
            self.player.play()

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

    def remove_note(self, note_index):
        self.note_dict.pop(note_index)
        self.height_dict.pop(note_index)

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







