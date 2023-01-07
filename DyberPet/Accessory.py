import sys
import time
import math
import random
import inspect
import types
import uuid
from datetime import datetime, timedelta
import pynput.mouse as mouse

from apscheduler.schedulers.qt import QtScheduler
from apscheduler.triggers import interval, date, cron

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QUrl, QEvent
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtMultimedia import QSoundEffect, QMediaPlayer, QMediaContent

from typing import List

from DyberPet.utils import *
from DyberPet.conf import *

import DyberPet.settings as settings


##############################
#          组件模块
##############################


class DPAccessory(QWidget):
    def __init__(self, parent=None):
        """
        宠物组件
        """
        super(DPAccessory, self).__init__(parent, flags=Qt.WindowFlags())

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.acc_dict = {}


    def setup_accessory(self, acc_act, pos_x, pos_y):
        acc_index = str(uuid.uuid4())
        ### 位置的判定要改进 ###
        ### 判定重叠关系 ###
        self.acc_dict[acc_index] = QAccessory(acc_index,
                                               acc_act,
                                               pos_x, pos_y,
                                               timeout=0
                                              )
        self.acc_dict[acc_index].closed_acc.connect(self.remove_accessory)

    def remove_accessory(self, acc_index):
        self.acc_dict.pop(acc_index)






class QAccessory(QWidget):
    closed_acc = pyqtSignal(str, name='closed_acc')

    def __init__(self, acc_index,
                 acc_act,
                 pos_x, pos_y,
                 timeout=5000,
                 parent=None):
        super(QAccessory, self).__init__(parent)

        self.acc_index = acc_index
        self.acc_act = acc_act
        #self.move(pos_x, pos_y)
        self.timeout = timeout

        self.label = QLabel(self)
        self.previous_img = None
        self.current_img = acc_act['acc_list'][0].images[0]
        self.anchor = acc_act['anchor']
        self.set_img()

        self.current_act = None
        self.previous_act = None
        self.playid = 0
        self.act_id = 0
        self.finished = False
        self.waitn = 0
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()

        # 是否跟随鼠标
        self.is_follow_mouse = acc_act['follow_mouse']
        if self.is_follow_mouse:
            self.manager = MouseMoveManager()
            self.manager.moved.connect(self._move_to_mouse)
            print('check')
            #self.setMouseTracking(True)
            #self.installEventFilter(self)
        else:
            self.move(pos_x-self.anchor[0], pos_y-self.anchor[1])


        #print(self.is_follow_mouse)
        self.mouse_drag_pos = self.pos()

        self.petlayout = QVBoxLayout()
        self.petlayout.addWidget(self.label)
        self.petlayout.setAlignment(Qt.AlignCenter)
        self.petlayout.setContentsMargins(0,0,0,0)

        self.setLayout(self.petlayout)
        self.show()

        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.Action)
        #print(self.pet_conf.interact_speed)
        self.timer.start(20)

    def set_img(self):
        self.label.resize(self.current_img.width(), self.current_img.height())
        self.label.setPixmap(QPixmap.fromImage(self.current_img))
    
    '''
    def eventFilter(self, object, event):
        #print(event.type() == QEvent.MouseMove)
        if event.type() == QEvent.MouseMove and self.is_follow_mouse:
            print('!check')
            self.move(event.globalPos())
        return super().eventFilter(self, object, event)

    
    def mouseMoveEvent(self, event):
        """
        鼠标移动事件 移动窗体
        :param event:
        :return: 
        """
        print('move mouse')

        if self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            event.accept()
    '''

    def _move_to_mouse(self,x,y):
        #print(self.label.width()//2)
        self.move(x-self.anchor[0],y-self.anchor[1])

    def _closeit(self):
        #self.closed_note.emit(self.note_index)
        self.close()

    def closeEvent(self, event):
        # we don't need the notification anymore, delete it!
        self.closed_acc.emit(self.acc_index)
        self.deleteLater()

    def img_from_act(self, act):

        if self.current_act != act:
            self.previous_act = self.current_act
            self.current_act = act
            self.playid = 0

        n_repeat = math.ceil(act.frame_refresh / (20 / 1000))
        img_list_expand = [item for item in act.images for i in range(n_repeat)] * act.act_num
        img = img_list_expand[self.playid]

        self.playid += 1
        if self.playid >= len(img_list_expand):
            self.playid = 0
        #img = act.images[0]
        self.previous_img = self.current_img
        self.current_img = img

    def Action(self):

        if self.finished:
            self.waitn += 1
            if self.waitn >= self.timeout/20:
                self.timer.stop()
                self._closeit()
                return
            else:
                return
        
        acts = self.acc_act['acc_list']
        #print(settings.act_id, len(acts))
        if self.act_id >= len(acts):
            #print('finish?')
            #settings.act_id = 0
            #self.interact = None
            self.finished = True
            #self.sig_act_finished.emit()
        else:
            act = acts[self.act_id]
            n_repeat = math.ceil(act.frame_refresh / (20 / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if self.playid >= n_repeat-1:
                self.act_id += 1

            if self.previous_img != self.current_img:
                self.set_img()
                #self._move(act)

    def _move(self, act: QAction) -> None: #pos: QPoint, act: QAction) -> None:
        """
        在 Thread 中发出移动Signal
        :param act: 动作
        :return
        """
        #print(act.direction, act.frame_move)
        plus_x = 0.
        plus_y = 0.
        direction = act.direction

        if direction is None:
            pass
        else:
            if direction == 'right':
                plus_x = act.frame_move

            if direction == 'left':
                plus_x = -act.frame_move

            if direction == 'up':
                plus_y = -act.frame_move

            if direction == 'down':
                plus_y = act.frame_move

        self.move(self.pos().x()+plus_x, self.pos().y()+plus_y)




class MouseMoveManager(QObject):
    moved = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = mouse.Listener(on_move=self._handle_move)
        self._listener.start()

    def _handle_move(self, x, y):
        #if not pressed:
        self.moved.emit(x, y)


















