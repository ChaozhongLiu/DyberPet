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
from PySide6.QtCore import Qt, QTimer, QObject, QPoint, QUrl, QRect, QSize, QPropertyAnimation, QAbstractAnimation
from PySide6.QtGui import QImage, QPixmap, QIcon, QCursor
from PySide6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput

from qfluentwidgets import TextWrap, TransparentToolButton, BodyLabel
from qfluentwidgets import FluentIcon as FIF

from DyberPet.utils import *
from DyberPet.conf import *

import DyberPet.settings as settings

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
            self.note_dict[note_index] = DyberToaster(note_index,
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
            self.setup_notification('status_hp', message=self.tr('Your pet is starving! (Favor point starts decreasing)'))
        elif hp_tier == 1:
            self.setup_notification('status_hp', message=self.tr('Your pet is hungry now~ (Favor point stops increasing)'))

    def fvchange_note(self, fv_lvl):
        #print(fv_lvl,'note')
        if fv_lvl == -1:
            self.setup_notification('status_fv',
                                    message=self.tr('Congrats! You have reached the max FV level! Thank you for your companionship all this time!'))
        else:
            self.setup_notification('status_fv',
                                    message=f"{self.tr('Favor leveled up:')} lv{int(fv_lvl)}! {self.tr('More features have been unlocked!')}")




class DyberToaster(QFrame):
    closed_note = Signal(str, str, name='closed_note')

    def __init__(self, note_index,
                 message='', #parent
                 icon=FIF.INFO,
                 corner=Qt.BottomRightCorner,
                 height_margin=10,
                 closable=True,
                 timeout=5000,
                 parent=None):
        super().__init__(parent=parent)

        self.note_index = note_index
        self.message = message
        self.icon = icon
        self.corner = corner
        self.height_margin = height_margin
        self.isClosable = closable
        self.timeout = timeout
        self.margin = int(10)
        self.close_type = 'faded'
        
        # Duration and Animation
        self.timer = QTimer(singleShot=True, timeout=self.hide)
        self.opacityAni = QPropertyAnimation(self, b'windowOpacity')
        self.opacityAni.setStartValue(0.)
        self.opacityAni.setEndValue(1.)
        self.opacityAni.setDuration(100)
        self.opacityAni.finished.connect(self.checkClosed)
        
        self.__initWidget()
        self.__setForShow()

    def __initWidget(self):
        self.contentLabel = BodyLabel(self)
        self.contentLabel.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.contentLabel.setWordWrap(True)
        self.contentLabel.setFixedWidth(150)
        self.contentLabel.setText(self.message)
        
        self.iconWidget =  QLabel()
        self.iconWidget.setFixedSize(int(26), int(26))
        self.iconWidget.setScaledContents(True)
        self.iconWidget.setPixmap(self.icon)

        self.closeButton = TransparentToolButton(FIF.CLOSE, self)
        self.closeButton.setFixedSize(26, 26)
        self.closeButton.setIconSize(QSize(14, 14))
        self.closeButton.setCursor(Qt.PointingHandCursor)
        self.closeButton.setVisible(self.isClosable)
        self.closeButton.clicked.connect(self._closeit)

        self.__initLayout()
        self.adjustSize()

    def __initLayout(self):
        frame = QFrame()
        frame.setStyleSheet('''
            QFrame {
                border: 1px solid black;
                border-radius: 6px; 
                background: rgb(255, 255, 255);
            }
            QLabel{
                border: 0px;
                font: 14px 'Segoe UI', 'Microsoft YaHei', 'PingFang SC';
                color: black;
                background-color: transparent;
            }
        ''')
        # Layout
        self.hBoxLayout = QHBoxLayout()
        self.hBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.hBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        # add icon to layout
        self.hBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignVCenter | Qt.AlignLeft)
        spacerItem1 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.hBoxLayout.addItem(spacerItem1)

        # add message to layout
        self.hBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignVCenter | Qt.AlignLeft)

        # add close button to layout
        spacerItem2 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hBoxLayout.addItem(spacerItem2)
        self.hBoxLayout.addWidget(self.closeButton, 0, Qt.AlignVCenter | Qt.AlignRight)

        frame.setLayout(self.hBoxLayout)
        wholebox = QHBoxLayout()
        wholebox.setContentsMargins(0,0,0,0)
        wholebox.addWidget(frame)
        self.setLayout(wholebox)


    def _closeit(self, close_type='button'):
        if not close_type:
            close_type = 'button'
        self.close_type = close_type
        self.close()

    def checkClosed(self):
        # if we have been fading out, we're closing the notification
        if self.opacityAni.direction() == QAbstractAnimation.Backward: #self.opacityAni.Backward:
            self._closeit('faded')

    def restore(self):
        # this is a "helper function", that can be called from mouseEnterEvent
        # and when the parent widget is resized. We will not close the
        # notification if the mouse is in or the parent is resized
        self.timer.stop()
        # also, stop the animation if it's fading out...
        self.opacityAni.stop()
        # ...and restore the opacity
        self.setWindowOpacity(1)

    def hide(self):
        # start hiding
        self.opacityAni.setDirection(QAbstractAnimation.Backward)
        self.opacityAni.setDuration(500)
        self.opacityAni.start()

    def enterEvent(self, event):
        self.restore()

    def leaveEvent(self, event):
        self.timer.start()

    def closeEvent(self, event):
        # we don't need the notification anymore, delete it!
        self.closed_note.emit(self.note_index, self.close_type)
        self.deleteLater()

    def showEvent(self, e):
        super().showEvent(e)
        self.adjustSize()

    def __setForShow(self):
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        if platform == 'win32':
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.BypassWindowManagerHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
        else:
            # SubWindow not work in MacOS
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.BypassWindowManagerHint | Qt.NoDropShadowWindowHint)

        # get current screen
        parentRect = self._getCurrentRect()

        # raise the widget and adjust its size to the minimum
        self.raise_()
        self.adjustSize()

        # Note position
        self.height_margin = int(self.height_margin) #*size_factor)
        geo = self.geometry()
        if self.corner == Qt.TopLeftCorner:
            geo.moveTopLeft(
                parentRect.topLeft() + QPoint(self.margin, self.margin+self.height_margin))
        elif self.corner == Qt.TopRightCorner:
            geo.moveTopRight(
                parentRect.topRight() + QPoint(-self.margin, self.margin+self.height_margin))
        elif self.corner == Qt.BottomRightCorner:
            geo.moveBottomRight(
                parentRect.bottomRight() + QPoint(-self.margin, -(self.margin+self.height_margin)))
        else:
            geo.moveBottomLeft(
                parentRect.bottomLeft() + QPoint(self.margin, -(self.margin+self.height_margin)))

        self.timer.setInterval(self.timeout)
        self.timer.start()
        self.setGeometry(geo)
        self.show()
        self.opacityAni.start()


    def _getCurrentRect(self):
        currentScreen = QApplication.primaryScreen()
        # reference for the screen
        reference = QRect(QCursor.pos() - QPoint(1, 1), 
                          QSize(3, 3))
        maxArea = 0
        for screen in QApplication.screens():
            intersected = screen.geometry().intersected(reference)
            area = intersected.width() * intersected.height()
            if area > maxArea:
                maxArea = area
                currentScreen = screen
        return currentScreen.availableGeometry()




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


