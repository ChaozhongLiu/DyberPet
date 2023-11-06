import sys
from sys import platform
import time
import math
import uuid
import types
import random
import inspect
from typing import List
import pynput.mouse as mouse
from datetime import datetime, timedelta


from apscheduler.schedulers.qt import QtScheduler
from apscheduler.triggers import interval, date, cron

from PySide6.QtCore import Qt, QTimer, QObject, QPoint, QUrl, QEvent, QRectF, QRect, QSize
from PySide6.QtGui import QImage, QPixmap, QIcon, QCursor,QPainter
from PySide6.QtGui import QFont, QTransform, QAction

from PySide6.QtWidgets import *
from PySide6.QtCore import QObject, QThread, Signal
#from PySide6.QtMultimedia import QSoundEffect, QMediaPlayer, QMediaContent

from qfluentwidgets import RoundMenu, Action
from qfluentwidgets import FluentIcon as FIF

from DyberPet.utils import *
from DyberPet.conf import *
from DyberPet.extra_windows import DPDialogue

import DyberPet.settings as settings
'''
try:
    size_factor = 1 #ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
except:
    size_factor = 1
'''

if platform == 'win32':
    basedir = ''
    flags = Qt.FramelessWindowHint | Qt.SubWindow | Qt.NoDropShadowWindowHint
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-1])
    flags = Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint

##############################
#          组件模块
##############################


class DPAccessory(QWidget):
    send_main_movement = Signal(int, int, name="send_main_movement")
    ontop_changed = Signal(name='ontop_changed')
    reset_size_sig = Signal(name='reset_size_sig')
    acc_withdrawed = Signal(str, name='acc_withdrawed')

    def __init__(self, parent=None):
        """
        宠物组件
        """
        super(DPAccessory, self).__init__(parent) #, flags=Qt.WindowFlags())

        self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        self.acc_dict = {}
        self.heart_list = []
        self.bubble_frame = _load_item_img(os.path.join(basedir, 'res/role/sys/action/bubble.png'))
        self.follow_main_list = []

    def setup_compdays(self, acc_act, pos_x, pos_y):
        if 'compdays' in self.acc_dict:
            self.acc_dict['compdays']._closeit()
        else:
            acc_index = 'compdays'
            self.acc_dict[acc_index] = QHangLabel(acc_index, acc_act,
                                                  pos_x, pos_y)

            self.acc_dict[acc_index].closed_acc.connect(self.remove_accessory)
            self.ontop_changed.connect(self.acc_dict[acc_index].ontop_update)


    def setup_accessory(self, acc_act, pos_x, pos_y):

        if acc_act.get('name','') == 'compdays':
            self.setup_compdays(acc_act, pos_x, pos_y)
            return

        acc_index = str(uuid.uuid4())

        if acc_act.get('name','') == 'item_drop':
            acc_act['frame'] = self.bubble_frame
            self.acc_dict[acc_index] = QItemDrop(acc_index, acc_act,
                                                 pos_x, pos_y)

            #self.acc_dict[acc_index].closed_acc.connect(self.remove_accessory)

        elif acc_act.get('name','') == 'pet':
            self.acc_dict[acc_index] = SubPet(acc_index, acc_act['pet_name'],
                                                 pos_x, pos_y)

            #self.acc_dict[acc_index].closed_acc.connect(self.remove_accessory)
            self.acc_dict[acc_index].setup_acc.connect(self.setup_accessory)
            self.reset_size_sig.connect(self.acc_dict[acc_index].reset_size)
            self.send_main_movement.connect(self.acc_dict[acc_index].update_main_pos)

        elif acc_act.get('name','') == 'dialogue':
            # 对话框不可重复打开
            for qacc in self.acc_dict:
                try:
                    msg_title = self.acc_dict[qacc].message['title']
                except:
                    continue
                if msg_title == acc_act['msg_dict']['title']:
                    return

            self.acc_dict[acc_index] = DPDialogue(acc_index, acc_act['msg_dict'],
                                                  pos_x, pos_y,
                                                  closable=True,
                                                  timeout=-1)

        elif acc_act.get('name','') == 'mouseDecor':
            for qacc in self.acc_dict:
                if not isinstance(self.acc_dict[qacc], DPMouseDecor):
                    continue

                if self.acc_dict[qacc].decor_name == acc_act['config']['name']:
                    # 收回挂件
                    self.acc_dict[qacc]._closeit()
                    return
                else:
                    # 替换挂件
                    self.acc_withdrawed.emit(self.acc_dict[qacc].decor_name)
                    self.acc_dict[qacc]._closeit()
                    break

            # 激活挂件
            self.acc_dict[acc_index] = DPMouseDecor(acc_index, acc_act['config'])
            self.acc_dict[acc_index].acc_withdrawed.connect(self.acc_withdrawed)


        else:

            if acc_act.get('name','') == 'heart':
                if len(self.heart_list) < 5:
                    self.heart_list.append(acc_index)
                else:
                    return
            # 跟随宠物具有唯一性，在场的情况下使用将收回
            if acc_act.get('unique', False):
                for qacc in self.acc_dict:
                    try:
                        cur_name = self.acc_dict[qacc].acc_act['name']
                    except:
                        continue
                    if cur_name == acc_act['name']:
                        self.acc_dict[qacc]._closeit()
                        return

            self.acc_dict[acc_index] = QAccessory(acc_index,
                                                  acc_act,
                                                  pos_x, pos_y
                                                  )

            if acc_act.get('follow_main', False):
                self.send_main_movement.connect(self.acc_dict[acc_index].update_main_pos)
            if acc_act.get('closable', False):
                self.acc_dict[acc_index].acc_withdrawed.connect(self.acc_withdrawed)

        self.acc_dict[acc_index].closed_acc.connect(self.remove_accessory)
        self.ontop_changed.connect(self.acc_dict[acc_index].ontop_update)


    def remove_accessory(self, acc_index):
        self.acc_dict.pop(acc_index)
        try:
            self.heart_list.remove(acc_index)
        except:
            pass

    #def send_main_movement(self, pos_x, pos_y):



def _load_item_img(img_path):
    return _get_q_img(img_path)

def _get_q_img(img_file) -> QImage:

    image = QImage()
    image.load(img_file)
    return image


HangLabelStyle = """
QLabel {
    background: rgba(255, 255, 255, 0);
    font-size: 16px;
    font-family: "黑体";
    border: 0px
}
"""
HangStyle = """
QFrame{
    background: rgba(255, 255, 255, 100);
    border: 3px solid #94b0c8;
    border-radius: 10px
}
"""

class QHangLabel(QWidget):
    closed_acc = Signal(str, name='closed_acc')

    def __init__(self, acc_index,
                 acc_act,
                 pos_x, pos_y,
                 parent=None):
        super(QHangLabel, self).__init__(parent)

        self.is_follow_mouse = False

        self.acc_index = acc_index
        self.message = acc_act['message']
        self.main_height = acc_act['height']

        self.setSizePolicy(QSizePolicy.Minimum, 
                           QSizePolicy.Minimum)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.BypassWindowManagerHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)

        # Text
        hbox_1 = QHBoxLayout()
        hbox_1.setContentsMargins(15,0,15,0)

        self.label = QLabel(self.message)
        self.label.setStyleSheet(HangLabelStyle)
        hbox_1.addWidget(self.label, Qt.AlignCenter)

        self.centralwidget = QFrame()
        self.centralwidget.setLayout(hbox_1)
        self.centralwidget.setStyleSheet(HangStyle)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.centralwidget, Qt.AlignCenter)
        self.setLayout(self.layout_window)

        self.adjustSize()

        self.move(pos_x-self.width()//2, pos_y-self.height())
        self.show()


    def _closeit(self):
        #self.closed_note.emit(self.note_index)
        self.close()

    def closeEvent(self, event):
        # we don't need the notification anymore, delete it!
        self.closed_acc.emit(self.acc_index)
        self.deleteLater()

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        if event.button() == Qt.LeftButton:
            # 左键绑定拖拽
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            event.accept()
            self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件, 左键且绑定跟随, 移动窗体
        :param event:
        :return:
        """
        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        松开鼠标操作
        :param event:
        :return:
        """
        self.is_follow_mouse = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    def ontop_update(self):
        if settings.on_top_hint:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()





class QAccessory(QWidget):
    closed_acc = Signal(str, name='closed_acc')
    acc_withdrawed = Signal(str, name='acc_withdrawed')

    def __init__(self, acc_index,
                 acc_act,
                 pos_x, pos_y,
                 parent=None):
        super(QAccessory, self).__init__(parent)

        self.acc_index = acc_index
        self.acc_act = acc_act
        #self.move(pos_x, pos_y)
        self.timeout = acc_act.get('timeout', True)
        self.closable = acc_act.get('closable', False)
        self.follow_main = acc_act.get('follow_main', False)
        self.delay_respond = 500 #ms
        self.delay_timer = 500 #ms
        self.speed_follow_main = acc_act.get('speed_follow_main', 5)
        self.at_destination = True
        self.move_right = False

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
        #self.waitn = 0
        if settings.on_top_hint:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()

        # 是否跟随鼠标
        self.is_follow_mouse = acc_act.get('follow_mouse', False)
        if self.is_follow_mouse:
            self.manager = MouseMoveManager()
            self.manager.moved.connect(self._move_to_mouse)
            #print('check')
            #self.setMouseTracking(True)
            #self.installEventFilter(self)
        #else:
        self.move(pos_x-self.anchor[0]*settings.tunable_scale, pos_y-self.anchor[1]*settings.tunable_scale)

        #print(self.is_follow_mouse)
        self.mouse_drag_pos = self.pos()

        self.destination = [pos_x-self.anchor[0]*settings.tunable_scale, pos_y-self.anchor[1]*settings.tunable_scale]

        # 是否可关闭
        if self.closable:
            menu = RoundMenu(parent=self)
            self.quit_act = Action(FIF.CLOSE,
                                   self.tr('Withdraw'), menu)
            self.quit_act.triggered.connect(self._withdraw)
            menu.addAction(self.quit_act)
            self.menu = menu

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
        #self.label.resize(self.current_img.width(), self.current_img.height())
        #self.label.setPixmap(QPixmap.fromImage(self.current_img))
        width_tmp = self.current_img.width()*settings.tunable_scale
        height_tmp = self.current_img.height()*settings.tunable_scale
        self.label.resize(width_tmp, height_tmp)
        self.label.setPixmap(QPixmap.fromImage(self.current_img.scaled(width_tmp, height_tmp, 
                                                                       aspectMode=Qt.KeepAspectRatio,
                                                                       mode=Qt.SmoothTransformation)))
        #print(self.size())

    def _move_to_mouse(self,x,y):
        #print(self.label.width()//2)
        if self.is_follow_mouse == 'x':
            self.move(x-self.anchor[0]*settings.tunable_scale, self.pos().y())
        elif self.is_follow_mouse == 'y':
            self.move(self.pos().x(), y-self.anchor[1]*settings.tunable_scale)
        else:
            self.move(x-self.anchor[0]*settings.tunable_scale,y-self.anchor[1]*settings.tunable_scale)

    def _withdraw(self):
        self.acc_withdrawed.emit(self.acc_act['name'])
        self._closeit()

    def _closeit(self):
        #self.closed_note.emit(self.note_index)
        self.close()

    def closeEvent(self, event):
        # we don't need the notification anymore, delete it!
        self.closed_acc.emit(self.acc_index)
        self.deleteLater()

    def ontop_update(self):
        if settings.on_top_hint:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        if event.button() == Qt.RightButton and self.closable:
            # 打开右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_right_menu)

    def _show_right_menu(self):
        self.menu.popup(QCursor.pos()-QPoint(0, 75))

    def update_main_pos(self, pos_x, pos_y):
        if self.follow_main:
            x_new = pos_x-self.anchor[0]*settings.tunable_scale - self.pos().x()
            y_pos = pos_y-self.anchor[1]*settings.tunable_scale - self.pos().y()
            if self.speed_follow_main*5 <= ((x_new**2 + y_pos**2)**0.5):
                self.at_destination = False
                self.destination = [pos_x-self.anchor[0]*settings.tunable_scale, pos_y-self.anchor[1]*settings.tunable_scale]
                #if self.delay_respond == self.delay_time:
                #self.move(pos_x-self.anchor[0]*settings.tunable_scale, pos_y-self.anchor[1]*settings.tunable_scale)
    '''
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
    '''

    def img_from_act(self, act):

        if self.current_act != act:
            self.previous_act = self.current_act
            self.current_act = act
            self.playid = 0

            n_repeat = math.ceil(act.frame_refresh / (20 / 1000))
            self.img_list_expand = [item for item in act.images for i in range(n_repeat)] * act.act_num

        img = self.img_list_expand[self.playid]

        self.playid += 1
        if self.playid >= len(self.img_list_expand):
            self.playid = 0
        #img = act.images[0]
        self.previous_img = self.current_img
        self.current_img = img

    def Action(self):

        if self.finished and self.timeout:
            #self.waitn += 1
            #if self.waitn >= self.timeout/20:
            self.timer.stop()
            self._closeit()
            return
        
        acts = self.acc_act['acc_list']
        #print(settings.act_id, len(acts))
        if self.act_id >= len(acts):
            if self.timeout:
                self.finished = True
                return
            else:
                self.act_id = 0

        #else:
        act = acts[self.act_id]
        n_repeat = math.ceil(act.frame_refresh / (20 / 1000))
        n_repeat *= len(act.images) * act.act_num
        self.img_from_act(act)
        if self.playid >= n_repeat-1:
            self.act_id += 1

        if self.move_right:
            self.previous_img = self.current_img
            self.current_img = self.current_img.mirrored(True, False)
        if self.previous_img != self.current_img:
            self.set_img()
            self._move(act)

        if self.follow_main and not self.at_destination:
            self.move_to_main()

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

    def move_to_main(self):

        # 延迟响应
        if self.delay_timer > 0:
            self.delay_timer += -20
            return

        movement_x = self.destination[0] - self.pos().x()
        movement_y = self.destination[1] - self.pos().y()
        if movement_y != 0:
            kb = abs(movement_x/movement_y)
            plus_x = int(self.speed_follow_main * kb / ((1+kb**2)**0.5) * (int(movement_x>0)*2-1))
            plus_y = int(self.speed_follow_main * 1  / ((1+kb**2)**0.5) * (int(movement_y>0)*2-1))
        else:
            plus_x = int(self.speed_follow_main * (int(movement_x>0)*2-1))
            plus_y = 0

        if plus_x > 0:
            self.move_right = True
        else:
            self.move_right = False

        if max(1,self.speed_follow_main*settings.tunable_scale) >= ((movement_x**2 + movement_y**2)**0.5):
            #plus_x = movement_x
            #plus_y = movement_y
            self.move_right = False
            self.at_destination = True
            self.delay_timer = self.delay_respond
            return

        self.move(self.pos().x()+plus_x, self.pos().y()+plus_y)




class MouseMoveManager(QObject):
    moved = Signal(int, int)
    clicked = Signal(bool)

    def __init__(self, movement=True, click=False, parent=None):
        super().__init__(parent)
        if movement and click:
            self._listener = mouse.Listener(on_move=self._handle_move,
                                            on_click=self._handle_click)
        elif movement:
            self._listener = mouse.Listener(on_move=self._handle_move)
        elif click:
            self._listener = mouse.Listener(on_click=self._handle_click)
        else:
            return

        self._listener.start()

    def _handle_move(self, x, y):
        #if not pressed:
        self.moved.emit(x, y)

    def _handle_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            self.clicked.emit(pressed)


class QItemLabel(QLabel):

    def __init__(self, frame):
        super(QItemLabel, self).__init__()
        self.frame = frame

    def paintEvent(self, event):
        super(QItemLabel, self).paintEvent(event)
        printer = QPainter(self)
        printer.drawPixmap(QPoint(0,0), QPixmap.fromImage(self.frame))


class QItemDrop(QWidget):
    closed_acc = Signal(str, name='closed_acc')

    def __init__(self, acc_index,
                 acc_act,
                 pos_x, pos_y,
                 parent=None):
        super(QItemDrop, self).__init__(parent)

        self.acc_index = acc_index
        self.acc_act = acc_act
        #self.move(pos_x, pos_y)
        self.size_wh = int(32) # * settings.size_factor)
        self.label = QItemLabel(self.acc_act['frame'].scaled(self.size_wh,self.size_wh))
        self.label.setFixedSize(self.size_wh,self.size_wh)
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.previous_img = None
        self.current_img = acc_act['item_image'][0]
        #self.anchor = acc_act['anchor']
        self.set_img()
        
        if settings.on_top_hint:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags)
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()

        self.move(pos_x, pos_y)

        self.petlayout = QVBoxLayout()
        self.petlayout.addWidget(self.label)
        self.petlayout.setAlignment(Qt.AlignCenter)
        self.petlayout.setContentsMargins(0,0,0,0)

        self.setLayout(self.petlayout)
        self.show()

        screen_geo = settings.current_screen.availableGeometry()
        self.current_screen = settings.current_screen.geometry()
        self.screen_width = screen_geo.width()
        work_height = screen_geo.height()
        self.floor_pos = work_height-self.height()

        # 运动轨迹相关
        self.finished = False
        self.v_x = random.uniform(2,4) * random.choice([-1,1])
        self.v_y = -random.uniform(5,10)
        self.gravity = 1.0
        self.waitn = 0
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.Action)
        #print(self.pet_conf.interact_speed)
        self.timer.start(20)

    def set_img(self):
        self.label.setPixmap(QPixmap.fromImage(self.current_img))

    def _closeit(self):
        #self.closed_note.emit(self.note_index)
        self.timer.stop()
        self.close()

    def closeEvent(self, event):
        # we don't need the notification anymore, delete it!
        self.closed_acc.emit(self.acc_index)
        self.deleteLater()

    def ontop_update(self):
        if settings.on_top_hint:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()

    def Action(self):

        if self.finished:
            self.waitn += 1
            if self.waitn >= 3000/20:
                self.timer.stop()
                self._closeit()
                return
            else:
                return
        
        plus_y = self.v_y
        plus_x = self.v_x
        self.v_y += self.gravity
        self._move(plus_x, plus_y)

    def _move(self, plus_x, plus_y):
        
        new_x = self.pos().x()+plus_x
        new_y = self.pos().y()+plus_y

        new_x, new_y = self.limit_in_screen(new_x, new_y)

        self.move(new_x, new_y)

    def limit_in_screen(self, new_x, new_y):
        # 超出当前屏幕左边界
        if new_x+self.width()//2 < self.current_screen.topLeft().x(): #self.border:
            #surpass_x = 'Left'
            new_x = self.current_screen.topLeft().x()-self.width()//2 #self.screen_width + self.border - self.width()

        # 超出当前屏幕右边界
        elif new_x+self.width()//2 > self.current_screen.topLeft().x() + self.screen_width: #self.current_screen.bottomRight().x(): # + self.border:
            #surpass_x = 'Right'
            new_x = self.current_screen.topLeft().x() + self.screen_width-self.width()//2 #self.border-self.width()

        # 超出当前屏幕上边界
        if new_y+self.height()-self.label.height()//2 < self.current_screen.topLeft().y(): #self.border:
            #surpass_y = 'Top'
            new_y = self.current_screen.topLeft().y() + self.label.height()//2 - self.height() #self.floor_pos

        # 超出当前屏幕下边界
        elif new_y > self.floor_pos:
            self.finished = True
            new_y = self.floor_pos

        return new_x, new_y



class SubPet(QWidget):
    closed_acc = Signal(str, name='closed_acc')
    setup_acc = Signal(dict, int, int, name='setup_acc')
    
    #sig_rmNote = Signal(str, name='sig_rmNote')
    #sig_addHeight = Signal(str, int, name='sig_addHeight')

    def __init__(self, acc_index,
                 pet_name,
                 pos_x, pos_y,
                 parent=None):
        """
        简化的宠物附件
        """
        super(SubPet, self).__init__(parent) #, flags=Qt.WindowFlags())
        self.pet_name = pet_name
        self.acc_index = acc_index

        self.previous_anchor = [0,0]
        self.current_anchor = [0,0]

        #self.pet_conf = PetConfig()
        self.move(pos_x, pos_y)


        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

        # Some geo info
        self.screen_geo = settings.current_screen.availableGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()
        self.current_screen = settings.current_screen.geometry()

        self.set_fall = 1
        self.main_x = pos_x
        self.main_y = pos_y

        self._init_ui()
        self._init_widget()
        self.init_conf(self.pet_name)
        self._setup_ui()

        self.show()

        # 动画模块
        self.onfloor = 1
        self.draging = 0
        self.set_fall = 1
        self.mouseposx1,self.mouseposx2,self.mouseposx3,self.mouseposx4,self.mouseposx5=0,0,0,0,0
        self.mouseposy1,self.mouseposy2,self.mouseposy3,self.mouseposy4,self.mouseposy5=0,0,0,0,0
        self.dragspeedx,dragspeedy=0,0
        self.fall_right = 0

        self.interact_speed = 20
        self.interact = None
        self.act_name = None
        self.interact_altered = False

        self.current_act = None
        self.previous_act = None
        self.playid = 0
        self.act_id = 0
        self.img_list_expand = []
        
        self.first_acc = False

        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.animation)
        self.timer.start(self.interact_speed)
        

    def _closeit(self):
        #self.closed_note.emit(self.note_index)
        self.timer.stop()
        self.close()

    def closeEvent(self, event):
        # we don't need the notification anymore, delete it!
        self.closed_acc.emit(self.acc_index)
        self.deleteLater()

    def ontop_update(self):
        if settings.on_top_hint:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        if event.button() == Qt.RightButton:
            # 打开右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_right_menu)
        if event.button() == Qt.LeftButton:
            #print('activated')
            # 左键绑定拖拽
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            
            if self.onfloor == 0:
            # Left press activates Drag interaction
            #global onfloor,draging
                
                self.onfloor=0
                self.draging=1
                self.start_interact('mousedrag')
                

            event.accept()
            self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件, 左键且绑定跟随, 移动窗体
        :param event:
        :return:
        """

        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            
            if self.mouseposx3 == 0:
                self.mouseposx1=QCursor.pos().x()
                self.mouseposx2=self.mouseposx1
                self.mouseposx3=self.mouseposx2
                self.mouseposx4=self.mouseposx3

                self.mouseposy1=QCursor.pos().y()
                self.mouseposy2=self.mouseposy1
                self.mouseposy3=self.mouseposy2
                self.mouseposy4=self.mouseposy3

            else:
                #mouseposx5=mouseposx4
                self.mouseposx4=self.mouseposx3
                self.mouseposx3=self.mouseposx2
                self.mouseposx2=self.mouseposx1
                self.mouseposx1=QCursor.pos().x()
                #mouseposy5=mouseposy4
                self.mouseposy4=self.mouseposy3
                self.mouseposy3=self.mouseposy2
                self.mouseposy2=self.mouseposy1
                self.mouseposy1=QCursor.pos().y()

            if self.onfloor == 1:
                self.onfloor=0
                self.draging=1

                self.start_interact('mousedrag')
            
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        松开鼠标操作
        :param event:
        :return:
        """
        if event.button()==Qt.LeftButton:

            self.is_follow_mouse = False
            self.setCursor(QCursor(Qt.ArrowCursor))

            if self.onfloor == 1:
                self.patpat()

            else:

                anim_area = QRect(self.pos() + QPoint(self.width()//2-self.label.width()//2, 
                                                      self.height()-self.label.height()), 
                                  QSize(self.label.width(), self.label.height()))
                intersected = self.current_screen.intersected(anim_area)
                area = intersected.width() * intersected.height() / self.label.width() / self.label.height()
                if area > 0.5:
                    pass
                else:
                    for screen in settings.screens:
                        if screen.geometry() == self.current_screen:
                            continue
                        intersected = screen.geometry().intersected(anim_area)
                        area_tmp = intersected.width() * intersected.height() / self.label.width() / self.label.height()
                        if area_tmp > 0.5:
                            self.switch_screen(screen)

                self.onfloor=0
                self.draging=0
                if self.set_fall == 1:

                    self.dragspeedx=(self.mouseposx1-self.mouseposx3)/2*settings.fixdragspeedx
                    self.dragspeedy=(self.mouseposy1-self.mouseposy3)/2*settings.fixdragspeedy
                    self.mouseposx1=self.mouseposx3=0
                    self.mouseposy1=self.mouseposy3=0

                    if self.dragspeedx > 0:
                        self.fall_right = 1
                    else:
                        self.fall_right = 0

                else:
                    self._move_customized(0,0)

                    self.current_img = self.pet_conf.default.images[0]
                    self.set_img()
                    self.start_interact(None)

    def update_main_pos(self, pos_x, pos_y):
        if self.dist_listen:
            self.main_x = pos_x
            self.main_y = pos_y

    def _show_right_menu(self):
        """
        展示右键菜单
        :return:
        """
        # 光标位置弹出菜单
        self.menu.popup(QCursor.pos()-QPoint(0, 50))

    def _init_ui(self):
        #动画 --------------------------------------------------------
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        #self.label.installEventFilter(self)
        #self.label.setStyleSheet("border : 2px solid blue")

        # 系统动画组件
        self.sys_src = _load_all_pic('sys')
        self.sys_conf = PetConfig.init_sys(self.sys_src)
        # ------------------------------------------------------------

        #Layout
        self.petlayout = QVBoxLayout()
        self.petlayout.addWidget(self.label)
        self.petlayout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.petlayout.setContentsMargins(0,0,0,0)

        self.setLayout(self.petlayout)

    def _init_widget(self) -> None:
        """
        初始化窗体, 无边框半透明窗口
        :return:
        """
        if settings.on_top_hint:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        # 是否跟随鼠标
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()
    
    def init_conf(self, pet_name: str) -> None:
        """
        初始化宠物窗口配置
        :param pet_name: 宠物名称
        :return:
        """
        self.curr_pet_name = pet_name
        '''
        if pet_name not in settings.pet_config_dict:
            pic_dict = _load_all_pic(pet_name)
            settings.pet_config_dict[pet_name] = PetConfig.init_config(self.curr_pet_name, pic_dict, settings.size_factor)
        self.pet_conf = settings.pet_config_dict[pet_name]
        '''

        pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, pic_dict) #settings.size_factor)

        self.margin_value = 0.5 * max(self.pet_conf.width, self.pet_conf.height) # 用于将widgets调整到合适的大小

        # 与主宠物的交互
        self.distance_acts = {}
        if 'distance' in self.pet_conf.main_interact:
            self.dist_listen = True
            for interact in self.pet_conf.main_interact['distance']:
                self.distance_acts[interact['value']] = interact['act']
        else:
            self.dist_listen = False

        self._set_menu()


    def _setup_ui(self):

        self.reset_size()

        #global current_img, previous_img
        self.previous_img = None #self.current_img
        self.current_img = self.pet_conf.default.images[0] #list(pic_dict.values())[0]
        self.previous_anchor = self.current_anchor
        self.current_anchor = self.pet_conf.default.anchor
        self.set_img()
        self.border = self.pet_conf.width/2


    def reset_size(self):
        self.setFixedSize((self.pet_conf.width+self.margin_value)*max(1.0,settings.tunable_scale),
                          (self.margin_value+self.pet_conf.height)*max(1.0, settings.tunable_scale))

        # 初始位置
        work_height = self.screen_height #screen_geo.height()
        x = self.pos().x() + self.current_anchor[0]
        if self.set_fall == 1:
            y = self.current_screen.topLeft().y() + work_height-self.height()+self.current_anchor[1]
        else:
            y = self.pos().y() + self.current_anchor[1]
        #y = self.current_screen.topLeft().y() + work_height-self.height()
        # make sure that for all stand png, png bottom is the ground
        self.floor_pos = self.current_screen.topLeft().y() + work_height-self.height()
        self.move(x,y)

    def set_img(self): #, img: QImage) -> None:

        if self.previous_anchor != self.current_anchor:

            self.move(self.pos().x()-self.previous_anchor[0]+self.current_anchor[0],
                      self.pos().y()-self.previous_anchor[1]+self.current_anchor[1])

        width_tmp = self.current_img.width()*settings.tunable_scale
        height_tmp = self.current_img.height()*settings.tunable_scale
        self.label.resize(width_tmp, height_tmp)
        self.label.setPixmap(QPixmap.fromImage(self.current_img.scaled(width_tmp, height_tmp,
                                                                       aspectMode=Qt.KeepAspectRatio,
                                                                       mode=Qt.SmoothTransformation)))
        #print(self.size())
        self.image = self.current_img

    def _set_menu(self):
        """
        初始化菜单
        """
        menu = RoundMenu(parent=self)

        # Select action
        self.act_menu = RoundMenu(self.tr("Select Action"), menu)
        self.act_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/jump.svg')))

        if self.pet_conf.act_name is not None:
            #select_acts = [_build_act(name, act_menu, self._show_act) for name in self.pet_conf.act_name]
            if self.curr_pet_name in settings.pets:
                select_acts = [_build_act(self.pet_conf.act_name[i], self.act_menu, self._show_act) for i in range(len(self.pet_conf.act_name)) if (self.pet_conf.act_type[i][1] <= settings.pet_data.allData_params[self.curr_pet_name]['FV_lvl']) and self.pet_conf.act_name[i] is not None]
            else:
                select_acts = [_build_act(self.pet_conf.act_name[i], self.act_menu, self._show_act) for i in range(len(self.pet_conf.act_name)) if (self.pet_conf.act_type[i][1] <= settings.pet_data.fv_lvl) and self.pet_conf.act_name[i] is not None]
            self.act_menu.addActions(select_acts)
        
        if self.pet_conf.acc_name is not None:
            if self.curr_pet_name in settings.pets:
                select_accs = [_build_act(self.pet_conf.acc_name[i], self.act_menu, self._show_acc) for i in range(len(self.pet_conf.acc_name)) if (self.pet_conf.accessory_act[self.pet_conf.acc_name[i]]['act_type'][1] <= settings.pet_data.allData_params[self.curr_pet_name]['FV_lvl']) ]
            else:
                select_accs = [_build_act(self.pet_conf.acc_name[i], self.act_menu, self._show_acc) for i in range(len(self.pet_conf.acc_name)) if (self.pet_conf.accessory_act[self.pet_conf.acc_name[i]]['act_type'][1] <= settings.pet_data.fv_lvl) ]
            self.act_menu.addActions(select_accs)

        menu.addMenu(self.act_menu)

        # Drop on/off
        if self.set_fall == 1:
            self.switch_fall = Action(QIcon(os.path.join(basedir,'res/icons/on.svg')),
                                      self.tr('Allow Drop'), menu)
        else:
            self.switch_fall = Action(QIcon(os.path.join(basedir,'res/icons/off.svg')),
                                      self.tr("Don't Drop"), menu)
        self.switch_fall.triggered.connect(self.fall_onoff)
        menu.addAction(self.switch_fall)
        
        # Exit pet
        menu.addAction(
            Action(FIF.CLOSE, self.tr('Exit'), triggered=self._closeit)
        )

        self.menu = menu

    def fall_onoff(self):
        sender = self.sender()
        if self.set_fall==1:
            sender.setText(self.tr("Don't Drop"))
            sender.setIcon(QIcon(os.path.join(basedir,'res/icons/off.svg')))
            self.set_fall=0
        else:
            sender.setText(self.tr("Allow Drop"))
            sender.setIcon(QIcon(os.path.join(basedir,'res/icons/on.svg')))
            self.set_fall=1

    def patpat(self):
        # 摸摸动画
        if self.interact != 'patpat_act':
            self.start_interact('patpat_act')

        # 概率触发浮动的心心
        prob_num_0 = random.uniform(0, 1)
        if prob_num_0 < 0.8:
            try:
                accs = self.sys_conf.accessory_act['heart']
            except:
                return
            x = self.pos().x()+self.width()//2 + random.uniform(-0.25, 0.25) * self.label.width()
            y = self.pos().y()+self.height()-0.8*self.label.height() + random.uniform(0, 1) * 10
            self.setup_acc.emit(accs, x, y)

    def _move_customized(self, plus_x, plus_y):

        pos = self.pos()
        new_x = pos.x() + plus_x
        new_y = pos.y() + plus_y

        # 正在下落的情况，可以切换屏幕
        if self.onfloor == 0:
            # 落地情况
            if new_y > self.floor_pos+self.current_anchor[1]:
                self.onfloor = 1
                new_x, new_y = self.limit_in_screen(new_x, new_y)
            # 在空中
            else:
                anim_area = QRect(self.pos() + QPoint(self.width()//2-self.label.width()//2, 
                                                      self.height()-self.label.height()), 
                                  QSize(self.label.width(), self.label.height()))
                intersected = self.current_screen.intersected(anim_area)
                area = intersected.width() * intersected.height() / self.label.width() / self.label.height()
                if area > 0.5:
                    pass
                    #new_x, new_y = self.limit_in_screen(new_x, new_y)
                else:
                    switched = False
                    for screen in settings.screens:
                        if screen.geometry() == self.current_screen:
                            continue
                        intersected = screen.geometry().intersected(anim_area)
                        area_tmp = intersected.width() * intersected.height() / self.label.width() / self.label.height()
                        if area_tmp > 0.5:
                            self.switch_screen(screen)
                            switched = True
                    if not switched:
                        new_x, new_y = self.limit_in_screen(new_x, new_y)

        # 正在做动作的情况，局限在当前屏幕内
        else:
            new_x, new_y = self.limit_in_screen(new_x, new_y)

        self.move(new_x, new_y)

    def switch_screen(self, screen):
        self.current_screen = screen.geometry()
        self.screen_geo = screen.availableGeometry() #screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()
        self.floor_pos = self.current_screen.topLeft().y() + self.screen_height -self.height()

    def limit_in_screen(self, new_x, new_y):
        # 超出当前屏幕左边界
        if new_x+self.width()//2 < self.current_screen.topLeft().x(): #self.border:
            new_x = self.current_screen.topLeft().x()-self.width()//2 #self.screen_width + self.border - self.width()

        # 超出当前屏幕右边界
        elif new_x+self.width()//2 > self.current_screen.topLeft().x() + self.screen_width: #self.current_screen.bottomRight().x(): # + self.border:
            new_x = self.current_screen.topLeft().x() + self.screen_width-self.width()//2 #self.border-self.width()

        # 超出当前屏幕上边界
        if new_y+self.height()-self.label.height()//2 < self.current_screen.topLeft().y(): #self.border:
            new_y = self.current_screen.topLeft().y() + self.label.height()//2 - self.height() #self.floor_pos

        # 超出当前屏幕下边界
        elif new_y > self.floor_pos+self.current_anchor[1]:
            new_y = self.floor_pos+self.current_anchor[1]

        return new_x, new_y

    def _show_act(self, act_name):
        #self.workers['Animation'].pause()
        self.start_interact('animat', act_name)

    def _show_acc(self, acc_name):
        #self.workers['Animation'].pause()
        self.start_interact('anim_acc', acc_name)

    def resume_animation(self):
        #self.workers['Animation'].resume()
        self.start_interact(None)

    def animation(self):

        if self.interact is None:
            if self.dist_listen:
                distance_to_main = ((self.main_x-self.pos().x()-self.width()/2)**2 + (self.main_y-self.pos().y()-self.height()/2)**2)**0.5
                for dist_value in self.distance_acts.keys():
                    if (distance_to_main+dist_value <0) or (distance_to_main>dist_value and dist_value>0):
                        if self.act_name != self.distance_acts[dist_value]:
                            self.empty_interact()
                        self.act_name = self.distance_acts[dist_value]
                        self.default_act(self.distance_acts[dist_value])
                        return
                if self.act_name != 'Default':
                    self.empty_interact()
                self.act_name = 'Default'
                self.default_act()
            elif settings.defaultAct.get(self.curr_pet_name, None) is not None:
                if self.act_name != settings.defaultAct[self.curr_pet_name]:
                    self.empty_interact()
                self.act_name = settings.defaultAct[self.curr_pet_name]
                self.default_act(settings.defaultAct[self.curr_pet_name])
            else:
                if self.act_name != 'Default':
                    self.empty_interact()
                self.act_name = 'Default'
                self.default_act()

        elif self.interact not in dir(self):
            self.interact = None

        else:
            if self.interact_altered:
                self.empty_interact()
                self.interact_altered = False
            getattr(self,self.interact)(self.act_name)

    def start_interact(self, interact, act_name=None):
        self.interact_altered = True
        if interact == 'anim_acc':
            self.first_acc = True
        self.interact = interact
        self.act_name = act_name

    def empty_interact(self):
        self.playid = 0
        self.act_id = 0

    def stop_interact(self):
        self.interact = None
        self.act_name = None
        self.first_acc = False
        self.playid = 0
        self.act_id = 0
        #self.sig_act_finished.emit()

    def img_from_act(self, act):

        if self.current_act != act:
            self.previous_act = self.current_act
            self.current_act = act
            self.playid = 0

            n_repeat = math.ceil(act.frame_refresh / (self.interact_speed / 1000))
            self.img_list_expand = [item for item in act.images for i in range(n_repeat)] * act.act_num

        img = self.img_list_expand[self.playid]

        self.playid += 1
        if self.playid >= len(self.img_list_expand):
            self.playid = 0
        #img = act.images[0]
        self.previous_img = self.current_img
        self.current_img = img
        self.previous_anchor = self.current_anchor
        self.current_anchor = [i * settings.tunable_scale for i in act.anchor]

    def default_act(self, act_name=None):
        if act_name is None:
            acts = [self.pet_conf.default]
        else:
            acts_index = self.pet_conf.act_name.index(act_name)
            acts = self.pet_conf.random_act[acts_index]

        if self.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            self.stop_interact()
            #self.sig_act_finished.emit()
        else:
            act = acts[self.act_id]
            n_repeat = math.ceil(act.frame_refresh / (self.interact_speed / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if self.playid >= n_repeat-1:
                self.act_id += 1

            if self.previous_img != self.current_img:
                self.set_img()
                self._move(act)

    def animat(self, act_name):

        acts_index = self.pet_conf.act_name.index(act_name)

        
        # 判断是否满足动作饱食度要求
        '''
        if settings.pet_data.hp_tier < self.pet_conf.act_type[acts_index][0]:
            self.sig_interact_note.emit('status_hp','[%s] 需要饱食度%i以上哦'%(act_name, self.hptier[self.pet_conf.act_type[acts_index][0]-1]))
            self.stop_interact()
            return
        '''
        
        acts = self.pet_conf.random_act[acts_index]
        #print(settings.act_id, len(acts))
        if self.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            self.stop_interact()
            #self.sig_act_finished.emit()
        else:
            act = acts[self.act_id]
            n_repeat = math.ceil(act.frame_refresh / (self.interact_speed / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if self.playid >= n_repeat-1:
                self.act_id += 1

            if act_name == 'onfloor' and self.fall_right ==1:
                self.previous_img = self.current_img
                self.current_img = self.current_img.mirrored(True, False)

            if self.previous_img != self.current_img or self.previous_anchor != self.current_anchor:
                self.set_img()
                self._move(act)

    def anim_acc(self, acc_name):
        '''
        # 判断是否满足动作饱食度要求
        if settings.pet_data.hp_tier < self.pet_conf.accessory_act[acc_name]['act_type'][0]:
            self.sig_interact_note.emit('status_hp','[%s] 需要饱食度%i以上哦'%(acc_name, self.hptier[self.pet_conf.accessory_act[acc_name]['act_type'][0]-1]))
            self.stop_interact()
            return
        '''
        if self.first_acc:
            accs = self.pet_conf.accessory_act[acc_name]
            self.register_accessory(accs)
            self.first_acc = False

        acts = self.pet_conf.accessory_act[acc_name]['act_list']

        if self.act_id >= len(acts):
            self.stop_interact()

        else:
            act = acts[self.act_id]
            n_repeat = math.ceil(act.frame_refresh / (self.interact_speed / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if self.playid >= n_repeat-1:
                self.act_id += 1

            if self.previous_img != self.current_img or self.previous_anchor != self.current_anchor:
                self.set_img()
                self._move(act)

    def register_accessory(self, accs):
        self.setup_acc.emit(accs, self.pos().x()+self.width()//2, self.pos().y()+self.height())

    def patpat_act(self, act_name):
        acts = [self.pet_conf.patpat]
        #print(settings.act_id, len(acts))
        if self.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            self.stop_interact()
            #self.sig_act_finished.emit()
        else:
            act = acts[self.act_id]
            n_repeat = math.ceil(act.frame_refresh / (self.interact_speed / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if self.playid >= n_repeat-1:
                self.act_id += 1

            if self.previous_img != self.current_img or self.previous_anchor != self.current_anchor:
                self.set_img()
                self._move(act)

    def mousedrag(self, act_name):

        # Falling is OFF
        if not self.set_fall:
            if self.draging==1:
                acts = self.pet_conf.drag

                self.img_from_act(acts)
                if self.previous_img != self.current_img or self.previous_anchor != self.current_anchor:
                    self.set_img()
                
            else:
                self.stop_interact()


        # Falling is ON
        elif self.set_fall==1 and self.onfloor==0:
            if self.draging==1:
                acts = self.pet_conf.drag
                self.img_from_act(acts)
                if self.previous_img != self.current_img or self.previous_anchor != self.current_anchor:
                    self.set_img()

            elif self.draging==0:
                acts = self.pet_conf.fall
                self.img_from_act(acts)

                #global fall_right
                if self.fall_right:
                    previous_img = self.current_img
                    self.current_img = self.current_img.mirrored(True, False)
                if self.previous_img != self.current_img or self.previous_anchor != self.current_anchor:
                    self.set_img()

                self.drop()

        else:
            self.interact = 'animat' #None
            self.act_name = 'onfloor' #None
            self.playid = 0
            self.act_id = 0
                
    def drop(self):
        #掉落
        plus_y = self.dragspeedy #+ self.pet_conf.dropspeed
        plus_x = self.dragspeedx
        self.dragspeedy = self.dragspeedy + settings.gravity

        self._move_customized(plus_x, plus_y)

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

        self._move_customized(plus_x, plus_y)



def _load_all_pic(pet_name: str) -> dict:
    """
    加载宠物所有动作图片
    :param pet_name: 宠物名称
    :return: {动作编码: 动作图片}
    """
    img_dir = os.path.join(basedir, 'res/role/{}/action/'.format(pet_name))
    images = os.listdir(img_dir)
    return {image.split('.')[0]: _get_q_img(img_dir + image) for image in images}


def _get_q_img(img_path: str) -> QImage:
    """
    将图片路径加载为 QImage
    :param img_path: 图片路径
    :return: QImage
    """
    image = QImage()
    image.load(img_path)
    return image


def _build_act(name: str, parent: QObject, act_func, icon=None) -> Action:
    """
    构建改变菜单动作
    :param pet_name: 菜单动作名称
    :param parent 父级菜单
    :param act_func: 菜单动作函数
    :return:
    """
    if icon:
        act = Action(icon, name, parent)
    else:
        act = Action(name, parent)
    act.triggered.connect(lambda: act_func(name))
    return act



class DPMouseDecor(QWidget):
    closed_acc = Signal(str, name='closed_acc')
    acc_withdrawed = Signal(str, name='acc_withdrawed')

    def __init__(self, acc_index,
                 config,
                 parent=None):
        super(DPMouseDecor, self).__init__(parent)

        self.acc_index = acc_index
        self.config = config
        self.decor_name = config['name']
        self.cursor_size = 48

        self.label = QLabel(self)
        self.label.setScaledContents(False)
        self.previous_img = None
        self.current_img = config['default'][0].images[0]
        self.anchor = [-24, -24] #config['anchor']
        self.set_img()

        self.petlayout = QVBoxLayout()
        self.petlayout.addWidget(self.label)
        self.petlayout.setAlignment(Qt.AlignCenter)
        self.petlayout.setContentsMargins(0,0,0,0)

        self.setLayout(self.petlayout)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint | Qt.BypassWindowManagerHint)
        self.show()
        
        self.manager = MouseMoveManager(click=True)
        self.manager.moved.connect(self._move_to_mouse)
        self.manager.clicked.connect(self._handle_click)

        self.act_name = 'default'
        self.current_act = None
        self.previous_act = None
        self.playid = 0
        self.act_id = 0
        #self.finished = False
        #self.waitn = 0
        
        # 摆动相关
        self.mousepos9=[self.pos().x(), self.pos().y()]
        self.mousepos8=[self.pos().x(), self.pos().y()]
        self.mousepos7=[self.pos().x(), self.pos().y()]
        self.mousepos6=[self.pos().x(), self.pos().y()]
        self.mousepos5=[self.pos().x(), self.pos().y()]
        self.mousepos4=[self.pos().x(), self.pos().y()]
        self.mousepos3=[self.pos().x(), self.pos().y()]
        self.mousepos2=[self.pos().x(), self.pos().y()]
        self.mousepos1=[self.pos().x(), self.pos().y()]
        self.mousepos0=[self.pos().x(), self.pos().y()]

        self.angle_destination = 0
        self.angle_current = 0
        self.angle_delta = 0

        
        # 是否可关闭
        #if self.closable:
        menu = RoundMenu(parent=self)
        self.quit_act = Action(FIF.CLOSE,
                               self.tr('Withdraw'), menu)
        self.quit_act.triggered.connect(self._withdraw)
        menu.addAction(self.quit_act)
        self.menu = menu
        
        
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.Action)
        self.fresh_ms = 40
        self.timer.start(self.fresh_ms)
        

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        if event.button() == Qt.RightButton:
            # 打开右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_right_menu)

    def _show_right_menu(self):
        self.menu.popup(QCursor.pos()-QPoint(0, 50))

    def set_img(self):
        width_tmp = self.cursor_size #*settings.size_factor
        height_tmp = self.cursor_size #*settings.size_factor
        self.label.resize(width_tmp, height_tmp)
        self.label.setPixmap(QPixmap.fromImage(self.current_img.scaled(width_tmp, height_tmp, 
                                                                       aspectMode=Qt.KeepAspectRatio,
                                                                       mode=Qt.SmoothTransformation)))
        #print(self.size())

    def _move_to_mouse(self,x,y):
        #print(self.label.width()//2)
        self.move(x+self.anchor[0], y+self.anchor[1])

    def _handle_click(self, pressed):
        if pressed:
            self.act_name = 'click'
        else:
            self.act_name = 'default'

        self.playid = 0
        self.act_id = 0

    def _withdraw(self):
        self.acc_withdrawed.emit(self.decor_name)
        self._closeit()

    def _closeit(self):
        self.close()

    def closeEvent(self, event):
        self.closed_acc.emit(self.acc_index)
        self.deleteLater()

    def ontop_update(self):
        return

    def img_from_act(self, act, rotation=0):

        if self.current_act != act:
            self.previous_act = self.current_act
            self.current_act = act
            self.playid = 0

            n_repeat = math.ceil(act.frame_refresh / (self.fresh_ms / 1000))
            self.img_list_expand = [item for item in act.images for i in range(n_repeat)] * act.act_num

        img = self.img_list_expand[self.playid]

        self.playid += 1
        if self.playid >= len(self.img_list_expand):
            self.playid = 0
        #img = act.images[0]
        self.previous_img = self.current_img
        self.current_img = img.transformed(QTransform().rotate(rotation), Qt.SmoothTransformation)

    def Action(self):

        self.mousepos8=self.mousepos7
        self.mousepos7=self.mousepos6
        self.mousepos6=self.mousepos5
        self.mousepos5=self.mousepos4
        self.mousepos4=self.mousepos3
        self.mousepos3=self.mousepos2
        self.mousepos2=self.mousepos1
        self.mousepos1=self.mousepos0
        self.mousepos0=[self.pos().x(), self.pos().y()]

        rotation = self.cal_rotate()
        rotation = self.continuous_change(rotation)
        
        acts = self.config[self.act_name]
        #print(settings.act_id, len(acts))
        if self.act_id >= len(acts):
            self.act_id = 0

        #else:
        act = acts[self.act_id]
        n_repeat = math.ceil(act.frame_refresh / (self.fresh_ms / 1000))
        n_repeat *= len(act.images) * act.act_num
        self.img_from_act(act, rotation)
        if self.playid >= n_repeat-1:
            self.act_id += 1

        if self.previous_img != self.current_img:
            self.set_img()
            self._move(act)

    def cal_rotate(self):
        ax = (self.mousepos0[0]+self.mousepos8[0]-2*self.mousepos4[0])/40 * settings.fixdragspeedx
        ay = (self.mousepos0[1]+self.mousepos8[1]-2*self.mousepos4[1])/40 * settings.fixdragspeedy

        if ax==0 and ay==0:
            return 0
        elif ay == 0:
            return 360-90 if ax>0 else 90
        elif ax == 0:
            return 0 if ay<0 else 180

        theta = math.degrees(math.atan(ay/ax))
        g = settings.gravity * 2000
        a = math.sqrt(ax**2 + ay**2)

        if ay < 0:
            c = math.sqrt(a**2 + g**2 - 2*a*g*math.cos(math.radians(90+theta)))
        else:
            c = math.sqrt(a**2 + g**2 - 2*a*g*math.cos(math.radians(90-theta)))
        
        cos_gama = (c**2 + g**2 - a**2) / (2*c*g)
        gama = math.degrees(math.acos(cos_gama))

        return 360-gama if ax>0 else gama

    def continuous_change(self, rotation):

        if self.angle_destination != rotation:
            self.angle_destination = rotation
            angle_diff = rotation - self.angle_current
            self.angle_delta = max(1, abs(angle_diff) / 20) * (2*int(angle_diff>0)-1)

        if self.angle_destination - rotation < self.angle_delta:
            self.angle_current = self.angle_destination
        else:
            self.angle_current += self.angle_delta
        return self.angle_current



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



