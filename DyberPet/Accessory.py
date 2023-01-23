import sys
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

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QUrl, QEvent, QRectF
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor,QPainter
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtMultimedia import QSoundEffect, QMediaPlayer, QMediaContent

from DyberPet.utils import *
from DyberPet.conf import *

import DyberPet.settings as settings


##############################
#          组件模块
##############################


class DPAccessory(QWidget):
    send_main_movement = pyqtSignal(int, int, name="send_main_movement")

    def __init__(self, parent=None):
        """
        宠物组件
        """
        super(DPAccessory, self).__init__(parent, flags=Qt.WindowFlags())

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.acc_dict = {}
        self.heart_list = []
        self.bubble_frame = _load_item_img('res/role/sys/action/bubble.png')
        self.follow_main_list = []


    def setup_accessory(self, acc_act, pos_x, pos_y):
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
        else:

            if acc_act.get('name','') == 'heart':
                if len(self.heart_list) < 5:
                    self.heart_list.append(acc_index)
                else:
                    return
            # 如果附件具有唯一性
            if acc_act.get('unique', False):
                for qacc in self.acc_dict:
                    try:
                        cur_name = self.acc_dict[qacc].acc_act['name']
                    except:
                        continue
                    if cur_name == acc_act['name']:
                        return

            self.acc_dict[acc_index] = QAccessory(acc_index,
                                                  acc_act,
                                                  pos_x, pos_y
                                                  )

            if acc_act.get('follow_main', False):
                self.send_main_movement.connect(self.acc_dict[acc_index].update_main_pos)

        self.acc_dict[acc_index].closed_acc.connect(self.remove_accessory)


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



class QAccessory(QWidget):
    closed_acc = pyqtSignal(str, name='closed_acc')

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
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
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
        else:
            self.move(pos_x-self.anchor[0]*settings.tunable_scale, pos_y-self.anchor[1]*settings.tunable_scale)

        #print(self.is_follow_mouse)
        self.mouse_drag_pos = self.pos()

        self.destination = [pos_x-self.anchor[0]*settings.tunable_scale, pos_y-self.anchor[1]*settings.tunable_scale]

        # 是否可关闭
        if self.closable:
            menu = QMenu(self)
            self.quit_act = QAction('收回', menu)
            self.quit_act.triggered.connect(self._closeit)
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
        self.label.resize(self.current_img.width(), self.current_img.height())
        self.label.setPixmap(QPixmap.fromImage(self.current_img))

    def _move_to_mouse(self,x,y):
        #print(self.label.width()//2)
        self.move(x-self.anchor[0]*settings.tunable_scale,y-self.anchor[1]*settings.tunable_scale)

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
        if event.button() == Qt.RightButton and self.closable:
            # 打开右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_right_menu)

    def _show_right_menu(self):
        self.menu.popup(QCursor.pos())

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

        if self.speed_follow_main >= ((movement_x**2 + movement_y**2)**0.5):
            #plus_x = movement_x
            #plus_y = movement_y
            self.move_right = False
            self.at_destination = True
            self.delay_timer = self.delay_respond
            return

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


class QItemLabel(QLabel):

    def __init__(self, frame):
        super(QItemLabel, self).__init__()
        self.frame = frame

    def paintEvent(self, event):
        super(QItemLabel, self).paintEvent(event)
        printer = QPainter(self)
        printer.drawPixmap(QPoint(0,0), QPixmap.fromImage(self.frame))


class QItemDrop(QWidget):
    closed_acc = pyqtSignal(str, name='closed_acc')

    def __init__(self, acc_index,
                 acc_act,
                 pos_x, pos_y,
                 parent=None):
        super(QItemDrop, self).__init__(parent)

        self.acc_index = acc_index
        self.acc_act = acc_act
        #self.move(pos_x, pos_y)
        self.size_wh = int(32 * settings.size_factor)
        self.label = QItemLabel(self.acc_act['frame'].scaled(self.size_wh,self.size_wh))
        self.label.setFixedSize(self.size_wh,self.size_wh)
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.previous_img = None
        self.current_img = acc_act['item_image'][0]
        #self.anchor = acc_act['anchor']
        self.set_img()
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
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

        screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
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

        if new_x+self.width()//2 < 0: #self.border:
            new_x = -self.width()//2 #self.screen_width + self.border - self.width()

        elif new_x+self.width()//2 > self.screen_width: # + self.border:
            new_x = self.screen_width-self.width()//2 #self.border-self.width()

        if new_y+self.height()-self.label.height() < 0: #self.border:
            new_y = self.label.height() - self.height() #self.floor_pos

        elif new_y >= self.floor_pos:
            self.finished = True
            new_y = self.floor_pos

        self.move(new_x, new_y)



class SubPet(QWidget):
    closed_acc = pyqtSignal(str, name='closed_acc')
    setup_acc = pyqtSignal(dict, int, int, name='setup_acc')
    
    #sig_rmNote = pyqtSignal(str, name='sig_rmNote')
    #sig_addHeight = pyqtSignal(str, int, name='sig_addHeight')

    def __init__(self, acc_index,
                 pet_name,
                 pos_x, pos_y,
                 parent=None):
        """
        简化的宠物附件
        """
        super(SubPet, self).__init__(parent, flags=Qt.WindowFlags())
        self.pet_name = pet_name
        self.acc_index = acc_index

        self.previous_anchor = [0,0]
        self.current_anchor = [0,0]

        self.pet_conf = PetConfig()
        self.move(pos_x, pos_y)


        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

        # Some geo info
        self.screen_geo = QDesktopWidget().availableGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()

        self.set_fall = 1

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

    def _show_right_menu(self):
        """
        展示右键菜单
        :return:
        """
        # 光标位置弹出菜单
        self.menu.popup(QCursor.pos())

    def _init_ui(self):
        #动画 --------------------------------------------------------
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        #self.label.installEventFilter(self)
        #self.label.setStyleSheet("border : 2px solid blue")

        # 系统动画组件
        self.sys_src = _load_all_pic('sys')
        self.sys_conf = PetConfig.init_sys(self.sys_src, settings.size_factor)
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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
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
        pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, pic_dict, settings.size_factor)

        self.margin_value = 0.5 * max(self.pet_conf.width, self.pet_conf.height) # 用于将widgets调整到合适的大小

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
        #screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        #screen_width = screen_geo.width()
        work_height = self.screen_height #screen_geo.height()
        x=self.pos().x()
        y=work_height-self.height()
        # make sure that for all stand png, png bottom is the ground
        self.floor_pos = work_height-self.height()
        self.move(x,y)

    def set_img(self): #, img: QImage) -> None:

        if self.previous_anchor != self.current_anchor:
            #print('check')
            self.move(self.pos().x()-self.previous_anchor[0]+self.current_anchor[0],
                      self.pos().y()-self.previous_anchor[1]+self.current_anchor[1])

        width_tmp = self.current_img.width()*settings.tunable_scale
        height_tmp = self.current_img.height()*settings.tunable_scale
        self.label.resize(width_tmp, height_tmp)
        self.label.setPixmap(QPixmap.fromImage(self.current_img.scaled(width_tmp, height_tmp,
                                                                       aspectRatioMode=Qt.KeepAspectRatio)))
        #print(self.size())
        self.image = self.current_img

    def _set_menu(self):
        """
        初始化菜单
        """
        menu = QMenu(self)

        # 选择动作
        self.act_menu = QMenu(menu)
        self.act_menu.setTitle('选择动作')

        if self.pet_conf.act_name is not None:
            #select_acts = [_build_act(name, act_menu, self._show_act) for name in self.pet_conf.act_name]
            select_acts = [_build_act(self.pet_conf.act_name[i], self.act_menu, self._show_act) for i in range(len(self.pet_conf.act_name)) if (self.pet_conf.act_type[i][1] <= settings.pet_data.fv_lvl) and self.pet_conf.act_name[i] is not None]
            self.act_menu.addActions(select_acts)
        
        if self.pet_conf.acc_name is not None:
            select_accs = [_build_act(self.pet_conf.acc_name[i], self.act_menu, self._show_acc) for i in range(len(self.pet_conf.acc_name)) if (self.pet_conf.accessory_act[self.pet_conf.acc_name[i]]['act_type'][1] <= settings.pet_data.fv_lvl) ]
            self.act_menu.addActions(select_accs)

        menu.addMenu(self.act_menu)

        # 开启/关闭掉落
        if self.set_fall == 1:
            switch_fall = QAction('禁用掉落', menu)
        else:
            switch_fall = QAction('开启掉落', menu)
        switch_fall.triggered.connect(self.fall_onoff)
        menu.addAction(switch_fall)
        
        # 退出动作
        quit_act = QAction('退出', menu)
        quit_act.triggered.connect(self._closeit)
        menu.addAction(quit_act)
        self.menu = menu

    def fall_onoff(self):
        #global set_fall
        sender = self.sender()
        if sender.text()=="禁用掉落":
            sender.setText("开启掉落")
            self.set_fall=0
        else:
            sender.setText("禁用掉落")
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

        #print(act_list)
        #direction, frame_move = str(act_list[0]), float(act_list[1])
        pos = self.pos()
        new_x = pos.x() + plus_x
        new_y = pos.y() + plus_y

        if new_x+self.width()//2 < 0: #self.border:
            new_x = -self.width()//2 #self.screen_width + self.border - self.width()

        elif new_x+self.width()//2 > self.screen_width: # + self.border:
            new_x = self.screen_width-self.width()//2 #self.border-self.width()

        if new_y+self.height()-self.label.height() < 0: #self.border:
            new_y = self.label.height() - self.height() #self.floor_pos

        elif new_y >= self.floor_pos:
            #falling situation
            if self.onfloor == 0:
                self.onfloor = 1
                new_y = self.floor_pos

        self.move(new_x, new_y)

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
        self.current_anchor = act.anchor

    def default_act(self):
        acts = [self.pet_conf.default]

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

            if self.previous_img != self.current_img:
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

            if self.previous_img != self.current_img:
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

            if self.previous_img != self.current_img:
                self.set_img()
                self._move(act)

    def mousedrag(self, act_name):

        # Falling is OFF
        if not self.set_fall:
            if self.draging==1:
                acts = self.pet_conf.drag

                self.img_from_act(acts)
                if self.previous_img != self.current_img:
                    self.set_img()
                
            else:
                self.stop_interact()


        # Falling is ON
        elif self.set_fall==1 and self.onfloor==0:
            if self.draging==1:
                acts = self.pet_conf.drag
                self.img_from_act(acts)
                if self.previous_img != self.current_img:
                    self.set_img()

            elif self.draging==0:
                acts = self.pet_conf.fall
                self.img_from_act(acts)

                #global fall_right
                if self.fall_right:
                    previous_img = self.current_img
                    self.current_img = self.current_img.mirrored(True, False)
                if self.previous_img != self.current_img:
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





class Acc(QWidget):
    closed_acc = pyqtSignal(str, name='closed_acc')
    setup_acc = pyqtSignal(dict, int, int, name='setup_acc')
    
    #sig_rmNote = pyqtSignal(str, name='sig_rmNote')
    #sig_addHeight = pyqtSignal(str, int, name='sig_addHeight')

    def __init__(self, acc_index,
                 pet_name,
                 pos_x, pos_y,
                 parent=None):
        """
        简化的宠物附件
        """
        super(SubPet, self).__init__(parent, flags=Qt.WindowFlags())
        self.pet_name = pet_name
        self.acc_index = acc_index

        self.previous_anchor = [0,0]
        self.current_anchor = [0,0]

        self.pet_conf = PetConfig()
        self.move(pos_x, pos_y)


        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

        # Some geo info
        self.screen_geo = QDesktopWidget().availableGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()

        self.set_fall = 1

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







def _load_all_pic(pet_name: str) -> dict:
    """
    加载宠物所有动作图片
    :param pet_name: 宠物名称
    :return: {动作编码: 动作图片}
    """
    img_dir = 'res/role/{}/action/'.format(pet_name)
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

def _build_act(name: str, parent: QObject, act_func) -> QAction:
    """
    构建改变菜单动作
    :param pet_name: 菜单动作名称
    :param parent 父级菜单
    :param act_func: 菜单动作函数
    :return:
    """
    act = QAction(name, parent)
    act.triggered.connect(lambda: act_func(name))
    return act
