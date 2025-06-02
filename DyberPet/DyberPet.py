import sys
from sys import platform
import time
import math
import types
import random
import inspect
import webbrowser
from typing import List
from pathlib import Path
import pynput.mouse as mouse
import threading
import json

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer, QObject, QPoint, QEvent, QElapsedTimer
from PySide6.QtCore import QObject, QThread, Signal, QRectF, QRect, QSize, QPropertyAnimation, QAbstractAnimation
from PySide6.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontMetrics, QAction, QBrush, QPen, QColor, QFontDatabase, QPainterPath, QRegion, QIntValidator, QDoubleValidator, QLinearGradient

from qfluentwidgets import CaptionLabel, setFont, Action, BodyLabel, StrongBodyLabel, TransparentToolButton, PrimaryPushButton #,RoundMenu
from qfluentwidgets import FluentIcon as FIF
from DyberPet.custom_widgets import SystemTray
from .custom_roundmenu import RoundMenu

from DyberPet.conf import *
from DyberPet.utils import *
from DyberPet.modules import *
from DyberPet.Accessory import MouseMoveManager
from DyberPet.custom_widgets import RoundBarBase, LevelBadge
from DyberPet.bubbleManager import BubbleManager
from DyberPet.ai_connector import AIConnector

# initialize settings
import DyberPet.settings as settings
settings.init()

basedir = settings.BASEDIR
configdir = settings.CONFIGDIR


# version
dyberpet_version = settings.VERSION
vf = open(os.path.join(configdir,'data/version'), 'w')
vf.write(dyberpet_version)
vf.close()

# some UI size parameters
status_margin = int(3)
statbar_h = int(20)
icons_wh = 20

# system config
sys_hp_tiers = settings.HP_TIERS 
sys_hp_interval = settings.HP_INTERVAL
sys_lvl_bar = settings.LVL_BAR
sys_pp_heart = settings.PP_HEART
sys_pp_item = settings.PP_ITEM
sys_pp_audio = settings.PP_AUDIO


# Pet HP progress bar
class DP_HpBar(QProgressBar):
    hptier_changed = Signal(int, str, name='hptier_changed')
    hp_updated = Signal(int, name='hp_updated')

    def __init__(self, *args, **kwargs):

        super(DP_HpBar, self).__init__(*args, **kwargs)

        self.setFormat('0/100')
        self.setValue(0)
        self.setAlignment(Qt.AlignCenter)
        self.hp_tiers = sys_hp_tiers #[0,50,80,100]

        self.hp_max = 100
        self.interval = 1
        self.hp_inner = 0
        self.hp_perct = 0

        # Custom colors and sizes
        self.bar_color = QColor("#FAC486")  # Fill color
        self.border_color = QColor(0, 0, 0) # Border color
        self.border_width = 1               # Border width in pixels
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Full widget rect minus border width to avoid overlap
        full_rect = QRectF(self.border_width / 2.0, self.border_width / 2.0,
                           self.width() - self.border_width, self.height() - self.border_width)
        radius = (self.height() - self.border_width) / 2.0

        # Draw the background rounded rectangle
        painter.setBrush(QBrush(QColor(240, 240, 240)))  # Light gray background
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.drawRoundedRect(full_rect, radius, radius)

        # Create a clipping path for the filled progress that is inset by the border width
        clip_path = QPainterPath()
        inner_rect = full_rect.adjusted(self.border_width, self.border_width, -self.border_width, -self.border_width)
        clip_path.addRoundedRect(inner_rect, radius - self.border_width, radius - self.border_width)
        painter.setClipPath(clip_path)

        # Calculate progress rect and draw it within the clipping region
        progress_width = (self.width() - 2 * self.border_width) * self.value() / self.maximum()
        progress_rect = QRectF(self.border_width, self.border_width,
                               progress_width, self.height() - 2 * self.border_width)

        painter.setBrush(QBrush(self.bar_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(progress_rect)
        
        # Text drawing
        painter.setClipping(False)  # Disable clipping to draw text over entire bar
        text = self.format()  # Use the format string directly
        painter.setPen(QColor(0, 0, 0))  # Set text color
        font = QFont("Segoe UI", 9, QFont.Normal)
        painter.setFont(font)
        #painter.drawText(full_rect, Qt.AlignCenter, text)
        font_metrics = QFontMetrics(font)
        text_height = font_metrics.height()
        # Draw text in the calculated position
        painter.drawText(full_rect.adjusted(0, -font_metrics.descent()//2, 0, 0), Qt.AlignCenter, text)

    def init_HP(self, change_value, interval_time):
        self.hp_max = int(100*interval_time)
        self.interval = interval_time
        if change_value == -1:
            self.hp_inner = self.hp_max
            settings.pet_data.change_hp(self.hp_inner)
        else:
            self.hp_inner = change_value
        self.hp_perct = math.ceil(round(self.hp_inner/self.interval, 1))
        self.setFormat('%i/100'%self.hp_perct)
        self.setValue(self.hp_perct)
        self._onTierChanged()
        self.hp_updated.emit(self.hp_perct)

    def updateValue(self, change_value, from_mod):

        before_value = self.value()

        if from_mod == 'Scheduler':
            if settings.HP_stop:
                return
            new_hp_inner = max(self.hp_inner + change_value, 0)

        else:

            if change_value > 0:
                new_hp_inner = min(self.hp_inner + change_value*self.interval, self.hp_max)

            elif change_value < 0:
                new_hp_inner = max(self.hp_inner + change_value*self.interval, 0)

            else:
                return 0


        if new_hp_inner == self.hp_inner:
            return 0
        else:
            self.hp_inner = new_hp_inner

        new_hp_perct = math.ceil(round(self.hp_inner/self.interval, 1))
            
        if new_hp_perct == self.hp_perct:
            settings.pet_data.change_hp(self.hp_inner)
            return 0
        else:
            self.hp_perct = new_hp_perct
            self.setFormat('%i/100'%self.hp_perct)
            self.setValue(self.hp_perct)
        
        after_value = self.value()

        hp_tier = sum([int(after_value>i) for i in self.hp_tiers])

        #告知动画模块、通知模块
        if hp_tier > settings.pet_data.hp_tier:
            self.hptier_changed.emit(hp_tier,'up')
            settings.pet_data.change_hp(self.hp_inner, hp_tier)
            self._onTierChanged()

        elif hp_tier < settings.pet_data.hp_tier:
            self.hptier_changed.emit(hp_tier,'down')
            settings.pet_data.change_hp(self.hp_inner, hp_tier)
            self._onTierChanged()
            
        else:
            settings.pet_data.change_hp(self.hp_inner) #.hp = current_value

        self.hp_updated.emit(self.hp_perct)
        return int(after_value - before_value)

    def _onTierChanged(self):
        colors = ["#f8595f", "#f8595f", "#FAC486", "#abf1b7"]
        self.bar_color = QColor(colors[settings.pet_data.hp_tier])  # Fill color
        self.update()
        



# Favorability Progress Bar
class DP_FvBar(QProgressBar):
    fvlvl_changed = Signal(int, name='fvlvl_changed')
    fv_updated = Signal(int, int, name='fv_updated')

    def __init__(self, *args, **kwargs):

        super(DP_FvBar, self).__init__(*args, **kwargs)

        # Custom colors and sizes
        self.bar_color = QColor("#F4665C")  # Fill color
        self.border_color = QColor(0, 0, 0) # Border color
        self.border_width = 1               # Border width in pixels

        self.fvlvl = 0
        self.lvl_bar = sys_lvl_bar #[20, 120, 300, 600, 1200]
        self.points_to_lvlup = self.lvl_bar[self.fvlvl]
        self.setMinimum(0)
        self.setMaximum(self.points_to_lvlup)
        self.setFormat('lv%s: 0/%s'%(int(self.fvlvl), self.points_to_lvlup))
        self.setValue(0)
        self.setAlignment(Qt.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Full widget rect minus border width to avoid overlap
        full_rect = QRectF(self.border_width / 2.0, self.border_width / 2.0,
                           self.width() - self.border_width, self.height() - self.border_width)
        radius = (self.height() - self.border_width) / 2.0

        # Draw the background rounded rectangle
        painter.setBrush(QBrush(QColor(240, 240, 240)))  # Light gray background
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.drawRoundedRect(full_rect, radius, radius)

        # Create a clipping path for the filled progress that is inset by the border width
        clip_path = QPainterPath()
        inner_rect = full_rect.adjusted(self.border_width, self.border_width, -self.border_width, -self.border_width)
        clip_path.addRoundedRect(inner_rect, radius - self.border_width, radius - self.border_width)
        painter.setClipPath(clip_path)

        # Calculate progress rect and draw it within the clipping region
        progress_width = (self.width() - 2 * self.border_width) * self.value() / self.maximum()
        progress_rect = QRectF(self.border_width, self.border_width,
                               progress_width, self.height() - 2 * self.border_width)

        painter.setBrush(QBrush(self.bar_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(progress_rect)
        
        # Text drawing
        painter.setClipping(False)  # Disable clipping to draw text over entire bar
        text = self.format()  # Use the format string directly
        painter.setPen(QColor(0, 0, 0))  # Set text color
        font = QFont("Segoe UI", 9, QFont.Normal)
        painter.setFont(font)
        #painter.drawText(full_rect, Qt.AlignCenter, text)
        font_metrics = QFontMetrics(font)
        text_height = font_metrics.height()
        # Draw text in the calculated position
        painter.drawText(full_rect.adjusted(0, -font_metrics.descent()//2, 0, 0), Qt.AlignCenter, text)

    def init_FV(self, fv_value, fv_lvl):
        self.fvlvl = fv_lvl
        self.points_to_lvlup = self.lvl_bar[self.fvlvl]
        self.setMinimum(0)
        self.setMaximum(self.points_to_lvlup)
        self.setFormat('lv%s: %i/%s'%(int(self.fvlvl), fv_value, self.points_to_lvlup))
        self.setValue(fv_value)
        self.fv_updated.emit(self.value(), self.fvlvl)

    def updateValue(self, change_value, from_mod):

        before_value = self.value()

        if from_mod == 'Scheduler':
            if settings.pet_data.hp_tier > 1:
                prev_value = self.value()
                current_value = self.value() + change_value #, self.maximum())
            elif settings.pet_data.hp_tier == 0 and not settings.FV_stop:
                prev_value = self.value()
                current_value = self.value() - 1
            else:
                return 0

        elif change_value != 0:
            prev_value = self.value()
            current_value = self.value() + change_value

        else:
            return 0


        if current_value < self.maximum():
            self.setValue(current_value)

            current_value = self.value()
            if current_value == prev_value:
                return 0
            else:
                self.setFormat('lv%s: %s/%s'%(int(self.fvlvl), int(current_value), int(self.maximum())))
                settings.pet_data.change_fv(current_value)
            after_value = self.value()

            self.fv_updated.emit(self.value(), self.fvlvl)
            return int(after_value - before_value)

        else: #好感度升级
            addedValue = self._level_up(current_value, prev_value)
            self.fv_updated.emit(self.value(), self.fvlvl)
            return addedValue

    def _level_up(self, newValue, oldValue, added=0):
        if self.fvlvl == (len(self.lvl_bar)-1):
            current_value = self.maximum()
            if current_value == oldValue:
                return 0
            self.setFormat('lv%s: %s/%s'%(int(self.fvlvl),int(current_value),self.points_to_lvlup))
            self.setValue(current_value)
            settings.pet_data.change_fv(current_value, self.fvlvl)
            #告知动画模块、通知模块
            self.fvlvl_changed.emit(-1)
            return current_value - oldValue + added

        else:
            #after_value = newValue
            added_tmp = self.maximum() - oldValue
            newValue -= self.maximum()
            self.fvlvl += 1
            self.points_to_lvlup = self.lvl_bar[self.fvlvl]
            self.setMinimum(0)
            self.setMaximum(self.points_to_lvlup)
            self.setFormat('lv%s: %s/%s'%(int(self.fvlvl),int(newValue),self.points_to_lvlup))
            self.setValue(newValue)
            settings.pet_data.change_fv(newValue, self.fvlvl)
            #告知动画模块、通知模块
            self.fvlvl_changed.emit(self.fvlvl)

            if newValue < self.maximum():
                return newValue + added_tmp + added
            else:
                return self._level_up(newValue, 0, added_tmp)




# Pet Object
class PetWidget(QWidget):
    setup_notification = Signal(str, str, name='setup_notification')
    setup_bubbleText = Signal(dict, int, int, name="setup_bubbleText")
    close_bubble = Signal(str, name="close_bubble")
    addItem_toInven = Signal(int, list, name='addItem_toInven')
    fvlvl_changed_main_note = Signal(int, name='fvlvl_changed_main_note')
    fvlvl_changed_main_inve = Signal(int, name='fvlvl_changed_main_inve')
    hptier_changed_main_note = Signal(int, str, name='hptier_changed_main_note')

    setup_acc = Signal(dict, int, int, name='setup_acc')
    change_note = Signal(name='change_note')
    close_all_accs = Signal(name='close_all_accs')

    move_sig = Signal(int, int, name='move_sig')
    #acc_withdrawed = Signal(str, name='acc_withdrawed')
    send_positions = Signal(list, list, name='send_positions')

    lang_changed = Signal(name='lang_changed')
    show_controlPanel = Signal(name='show_controlPanel')

    show_dashboard = Signal(name='show_dashboard')
    hp_updated = Signal(int, name='hp_updated')
    fv_updated = Signal(int, int, name='fv_updated')

    compensate_rewards = Signal(name="compensate_rewards")
    refresh_bag = Signal(name="refresh_bag")
    addCoins = Signal(int, name='addCoins')
    autofeed = Signal(name='autofeed')

    stopAllThread = Signal(name='stopAllThread')

    taskUI_Timer_update = Signal(name="taskUI_Timer_update")
    taskUI_task_end = Signal(name="taskUI_task_end")
    single_pomo_done = Signal(name="single_pomo_done")

    refresh_acts = Signal(name='refresh_acts')

    def __init__(self, parent=None, curr_pet_name=None, pets=(), screens=[]):
        """
        宠物组件
        :param parent: 父窗口
        :param curr_pet_name: 当前宠物名称
        :param pets: 全部宠物列表
        """
        super(PetWidget, self).__init__(parent) #, flags=Qt.WindowFlags())
        self.pets = settings.pets
        if curr_pet_name is None:
            self.curr_pet_name = settings.default_pet
        else:
            self.curr_pet_name = curr_pet_name
        #self.pet_conf = PetConfig()

        # 定义动作名称映射表
        self.action_name_map = {
            "睡觉": "sleep",
            "生气": "angry",
            "走路": "right_walk",
            "行走": "right_walk",
            "左走": "left_walk",
            "右走": "right_walk",
            "左右行走": "right_walk",
            "站立": "default",
            "默认": "default",
            "拖拽": "drag",
            "掉落": "fall",
            "摔倒": "fall",
            "地面": "on_floor",
            "在地上": "on_floor",
            "地板": "on_floor",
            "专注": "focus",
            "入睡": "fall_asleep"
        }
        
        self.image = None
        self.tray = None

        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_moving = False
        self.mouse_drag_pos = self.pos()
        self.mouse_pos = [0, 0]

        # Record too frequent mouse clicking
        self.click_timer = QElapsedTimer()
        self.click_interval = 1000  # Max interval in ms to consider consecutive clicks
        self.click_count = 0

        # Screen info
        settings.screens = screens #[i.geometry() for i in screens]
        self.current_screen = settings.screens[0].availableGeometry() #geometry()
        settings.current_screen = settings.screens[0]
        #self.screen_geo = QDesktopWidget().availableGeometry() #screenGeometry()
        self.screen_width = self.current_screen.width() #self.screen_geo.width()
        self.screen_height = self.current_screen.height() #self.screen_geo.height()

        self._init_ui()
        self._init_widget()
        self.init_conf(self.curr_pet_name) # if curr_pet_name else self.pets[0])

        #self._set_menu(pets)
        #self._set_tray()
        self.show()

        self._setup_ui()

        # 开始动画模块和交互模块
        self.threads = {}
        self.workers = {}
        self.runAnimation()
        self.runInteraction()
        self.runScheduler()
        

        # 初始化重复提醒任务 - feature deleted
        #self.remind_window.initial_task()

        # 启动完毕10s后检查好感度等级奖励补偿
        self.compensate_timer = None
        self._setup_compensate()

        # 初始化 AI 对话连接器
        self.aiConnector = AIConnector(self)
        self.aiConnector.response_received.connect(self._handle_ai_response)
        self.aiConnector.error_occurred.connect(self._handle_ai_error)

    def _setup_compensate(self):
        self._stop_compensate()
        self.compensate_timer = QTimer(singleShot=True, timeout=self._compensate_rewards)
        self.compensate_timer.start(10000)

    def _stop_compensate(self):
        if self.compensate_timer:
            self.compensate_timer.stop()

    def moveEvent(self, event):
        self.move_sig.emit(self.pos().x()+self.width()//2, self.pos().y()+self.height())

    def enterEvent(self, event):
        # Change the cursor when it enters the window
        self.setCursor(self.cursor_default)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Restore the original cursor when it leaves the window
        self.setCursor(self.cursor_user)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        
        if event.button() == Qt.RightButton:
            # 打开右键菜单
            if settings.draging:
                return
            #self.setContextMenuPolicy(Qt.CustomContextMenu)
            #self.customContextMenuRequested.connect(self._show_Staus_menu)
            self._show_Staus_menu()
            
        if event.button() == Qt.LeftButton:
            # 左键绑定拖拽
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            
            if settings.onfloor == 0:
            # Left press activates Drag interaction
                if settings.set_fall:              
                    settings.onfloor=0
                settings.draging=1
                self.workers['Animation'].pause()
                self.workers['Interaction'].start_interact('mousedrag')
            
            # Record click
            if self.click_timer.isValid() and self.click_timer.elapsed() <= self.click_interval:
                self.click_count += 1
            else:
                self.click_count = 1
                self.click_timer.restart()
                
            event.accept()
            #self.setCursor(QCursor(Qt.ArrowCursor))
            self.setCursor(self.cursor_clicked)

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件, 左键且绑定跟随, 移动窗体
        :param event:
        :return:
        """
        
        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)

            self.mouse_moving = True
            self.setCursor(self.cursor_dragged)

            if settings.mouseposx3 == 0:
                
                settings.mouseposx1=QCursor.pos().x()
                settings.mouseposx2=settings.mouseposx1
                settings.mouseposx3=settings.mouseposx2
                settings.mouseposx4=settings.mouseposx3

                settings.mouseposy1=QCursor.pos().y()
                settings.mouseposy2=settings.mouseposy1
                settings.mouseposy3=settings.mouseposy2
                settings.mouseposy4=settings.mouseposy3
            else:
                #mouseposx5=mouseposx4
                settings.mouseposx4=settings.mouseposx3
                settings.mouseposx3=settings.mouseposx2
                settings.mouseposx2=settings.mouseposx1
                settings.mouseposx1=QCursor.pos().x()
                #mouseposy5=mouseposy4
                settings.mouseposy4=settings.mouseposy3
                settings.mouseposy3=settings.mouseposy2
                settings.mouseposy2=settings.mouseposy1
                settings.mouseposy1=QCursor.pos().y()

            if settings.onfloor == 1:
                if settings.set_fall:
                    settings.onfloor=0
                settings.draging=1
                self.workers['Animation'].pause()
                self.workers['Interaction'].start_interact('mousedrag')
            

            event.accept()
            #print(self.pos().x(), self.pos().y())

    def mouseReleaseEvent(self, event):
        """
        松开鼠标操作
        :param event:
        :return:
        """
        if event.button()==Qt.LeftButton:

            self.is_follow_mouse = False
            #self.setCursor(QCursor(Qt.ArrowCursor))
            self.setCursor(self.cursor_default)

            #print(self.mouse_moving, settings.onfloor)
            if settings.onfloor == 1 and not self.mouse_moving:
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
                    

                if settings.set_fall:
                    settings.onfloor=0
                    settings.draging=0
                    settings.prefall=1

                    settings.dragspeedx=(settings.mouseposx1-settings.mouseposx3)/2*settings.fixdragspeedx
                    settings.dragspeedy=(settings.mouseposy1-settings.mouseposy3)/2*settings.fixdragspeedy
                    settings.mouseposx1=settings.mouseposx3=0
                    settings.mouseposy1=settings.mouseposy3=0

                    if settings.dragspeedx > 0:
                        settings.fall_right = True
                    else:
                        settings.fall_right = False

                else:
                    settings.draging=0
                    self._move_customized(0,0)
                    settings.current_img = self.pet_conf.default.images[0]
                    self.set_img()
                    self.workers['Animation'].resume()
            self.mouse_moving = False


    def _init_widget(self) -> None:
        """
        初始化窗体, 无边框半透明窗口
        :return:
        """
        if settings.on_top_hint:
            if platform == 'win32':
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
            else:
                # SubWindow not work in MacOS
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            if platform == 'win32':
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
            else:
                # SubWindow not work in MacOS
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        # 是否跟随鼠标
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

    def ontop_update(self):
        if settings.on_top_hint:
            if platform == 'win32':
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
            else:
                # SubWindow not work in MacOS
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            if platform == 'win32':
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
            else:
                # SubWindow not work in MacOS
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()


    def _init_ui(self):
        # The Character ----------------------------------------------------------------------------
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.label.installEventFilter(self)
        #self.label.setStyleSheet("border : 2px solid blue")

        # system animations
        self.sys_src = _load_all_pic('sys')
        self.sys_conf = PetConfig.init_sys(self.sys_src) 
        # ------------------------------------------------------------------------------------------

        # Hover Timer --------------------------------------------------------
        self.status_frame = QFrame()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)

        # 番茄时钟
        h_box3 = QHBoxLayout()
        h_box3.setContentsMargins(0,0,0,0)
        h_box3.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.tomatoicon = QLabel(self)
        self.tomatoicon.setFixedSize(statbar_h,statbar_h)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/Tomato_icon.png'))
        self.tomatoicon.setScaledContents(True)
        self.tomatoicon.setPixmap(image)
        self.tomatoicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box3.addWidget(self.tomatoicon)
        self.tomato_time = RoundBarBase(fill_color="#ef4e50", parent=self) #QProgressBar(self, minimum=0, maximum=25, objectName='PetTM')
        self.tomato_time.setFormat('')
        self.tomato_time.setValue(25)
        self.tomato_time.setAlignment(Qt.AlignCenter)
        self.tomato_time.hide()
        self.tomatoicon.hide()
        h_box3.addWidget(self.tomato_time)

        # 专注时间
        h_box4 = QHBoxLayout()
        h_box4.setContentsMargins(0,status_margin,0,0)
        h_box4.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.focusicon = QLabel(self)
        self.focusicon.setFixedSize(statbar_h,statbar_h)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/Timer_icon.png'))
        self.focusicon.setScaledContents(True)
        self.focusicon.setPixmap(image)
        self.focusicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box4.addWidget(self.focusicon)
        self.focus_time = RoundBarBase(fill_color="#47c0d2", parent=self) #QProgressBar(self, minimum=0, maximum=0, objectName='PetFC')
        self.focus_time.setFormat('')
        self.focus_time.setValue(0)
        self.focus_time.setAlignment(Qt.AlignCenter)
        self.focus_time.hide()
        self.focusicon.hide()
        h_box4.addWidget(self.focus_time)

        vbox.addStretch()
        vbox.addLayout(h_box3)
        vbox.addLayout(h_box4)

        self.status_frame.setLayout(vbox)
        #self.status_frame.setStyleSheet("border : 2px solid blue")
        self.status_frame.setContentsMargins(0,0,0,0)
        #self.status_box.addWidget(self.status_frame)
        #self.status_frame.hide()
        # ------------------------------------------------------------

        #Layout_1 ----------------------------------------------------
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)

        self.petlayout = QVBoxLayout()
        self.petlayout.addWidget(self.status_frame)

        image_hbox = QHBoxLayout()
        image_hbox.setContentsMargins(0,0,0,0)
        image_hbox.addStretch()
        image_hbox.addWidget(self.label, Qt.AlignBottom | Qt.AlignHCenter)
        image_hbox.addStretch()

        self.petlayout.addLayout(image_hbox, Qt.AlignBottom | Qt.AlignHCenter)
        self.petlayout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.petlayout.setContentsMargins(0,0,0,0)
        self.layout.addLayout(self.petlayout, Qt.AlignBottom | Qt.AlignHCenter)
        # ------------------------------------------------------------

        self.setLayout(self.layout)
        # ------------------------------------------------------------


        # 初始化背包
        #self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        settings.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        #self._init_Inventory()
        #self.showing_comp = 0

        # 客制化光标
        self.cursor_user = self.cursor()
        system_cursor_size = 32
        if os.path.exists(os.path.join(basedir, 'res/icons/cursor_default.png')):
            self.cursor_default = QCursor(QPixmap("res/icons/cursor_default.png").scaled(system_cursor_size, system_cursor_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cursor_default = self.cursor_user
        if os.path.exists(os.path.join(basedir, 'res/icons/cursor_clicked.png')):
            self.cursor_clicked = QCursor(QPixmap("res/icons/cursor_clicked.png").scaled(system_cursor_size, system_cursor_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cursor_clicked = self.cursor_user
        if os.path.exists(os.path.join(basedir, 'res/icons/cursor_dragged.png')):
            self.cursor_dragged = QCursor(QPixmap("res/icons/cursor_dragged.png").scaled(system_cursor_size, system_cursor_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cursor_dragged = self.cursor_user

    '''
    def _init_Inventory(self):
        self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        self.inventory_window = Inventory(self.items_data)
        self.inventory_window.close_inventory.connect(self.show_inventory)
        self.inventory_window.use_item_inven.connect(self.use_item)
        self.inventory_window.item_note.connect(self.register_notification)
        self.inventory_window.item_anim.connect(self.item_drop_anim)
        self.addItem_toInven.connect(self.inventory_window.add_items)
        self.acc_withdrawed.connect(self.inventory_window.acc_withdrawed)
        self.fvlvl_changed_main_inve.connect(self.inventory_window.fvchange)
    '''


    def _set_menu(self, pets=()):
        """
        Option Menu
        """
        #menu = RoundMenu(self.tr("More Options"), self)
        #menu.setIcon(FIF.MENU)

        # Select action
        self.act_menu = RoundMenu(self.tr("Select Action"))
        self.act_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/jump.svg')))

        if platform == 'win32':
            self.start_follow_mouse = Action(QIcon(os.path.join(basedir,'res/icons/cursor.svg')),
                                            self.tr('Follow Cursor'),
                                            triggered = self.follow_mouse_act)
            self.act_menu.addAction(self.start_follow_mouse)
            self.act_menu.addSeparator()

        acts_config = settings.act_data.allAct_params[settings.petname]
        self.select_acts = [ _build_act(k, self.act_menu, self._show_act) for k,v in acts_config.items() if v['unlocked']]
        if self.select_acts:
            self.act_menu.addActions(self.select_acts)

        #menu.addMenu(self.act_menu)


        # Launch pet/partner
        self.companion_menu = RoundMenu(self.tr("Call Partner"))
        self.companion_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/partner.svg')))

        add_acts = [_build_act(name, self.companion_menu, self._add_pet) for name in pets]
        self.companion_menu.addActions(add_acts)

        #menu.addMenu(self.companion_menu)
        #menu.addSeparator()

        # Change Character
        self.change_menu = RoundMenu(self.tr("Change Character"))
        self.change_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/system/character.svg')))
        change_acts = [_build_act(name, self.change_menu, self._change_pet) for name in pets]
        self.change_menu.addActions(change_acts)
        #menu.addMenu(self.change_menu)

        # Drop on/off
        '''
        if settings.set_fall == 1:
            self.switch_fall = Action(QIcon(os.path.join(basedir,'res/icons/on.svg')),
                                      self.tr('Allow Drop'), menu)
        else:
            self.switch_fall = Action(QIcon(os.path.join(basedir,'res/icons/off.svg')),
                                      self.tr("Don't Drop"), menu)
        self.switch_fall.triggered.connect(self.fall_onoff)
        '''
        #menu.addAction(self.switch_fall)

        
        # Visit website - feature deprecated
        '''
        web_file = os.path.join(basedir, 'res/role/sys/webs.json')
        if os.path.isfile(web_file):
            web_dict = json.load(open(web_file, 'r', encoding='UTF-8'))

            self.web_menu = RoundMenu(self.tr("Website"), menu)
            self.web_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/website.svg')))

            web_acts = [_build_act_param(name, web_dict[name], self.web_menu, self.open_web) for name in web_dict]
            self.web_menu.addActions(web_acts)
            menu.addMenu(self.web_menu)
        '''
            
        #menu.addSeparator()
        #self.menu = menu
        #self.menu.addAction(Action(FIF.POWER_BUTTON, self.tr('Exit'), triggered=self.quit))


    def _update_fvlock(self):

        # Update selectable animations
        acts_config = settings.act_data.allAct_params[settings.petname]
        for act_name, act_conf in acts_config.items():
            if act_conf['unlocked']:
                if act_name not in [acti.text() for acti in self.select_acts]:
                    new_act = _build_act(act_name, self.act_menu, self._show_act)
                    self.act_menu.addAction(new_act)
                    self.select_acts.append(new_act)
            else:
                if act_name in [acti.text() for acti in self.select_acts]:
                    act_index = [acti.text() for acti in self.select_acts].index(act_name)
                    self.act_menu.removeAction(self.select_acts[act_index])
                    self.select_acts.remove(self.select_acts[act_index])


    def _set_Statusmenu(self):

        # Character Name
        self.statusTitle = QWidget()
        hboxTitle = QHBoxLayout(self.statusTitle)
        hboxTitle.setContentsMargins(0,0,0,0)
        self.nameLabel = CaptionLabel(self.curr_pet_name, self)
        setFont(self.nameLabel, 14, QFont.DemiBold)
        #self.nameLabel.setFixedWidth(75)

        daysText = self.tr(" (Fed for ") + str(settings.pet_data.days) +\
                   self.tr(" days)")
        self.daysLabel = CaptionLabel(daysText, self)
        setFont(self.daysLabel, 14, QFont.Normal)

        hboxTitle.addStretch(1)
        hboxTitle.addWidget(self.nameLabel, Qt.AlignLeft | Qt.AlignVCenter)
        hboxTitle.addStretch(1)
        hboxTitle.addWidget(self.daysLabel, Qt.AlignRight | Qt.AlignVCenter)
        #hboxTitle.addStretch(1)
        self.statusTitle.setFixedSize(225, 25)

        # # Status Title
        # hp_tier = settings.pet_data.hp_tier
        # statusText = self.tr("Status: ") + f"{settings.TIER_NAMES[hp_tier]}"
        # self.statLabel = CaptionLabel(statusText, self)
        # setFont(self.statLabel, 14, QFont.Normal)

        # Level Badge
        lvlWidget = QWidget()
        h_box0 = QHBoxLayout(lvlWidget)
        h_box0.setContentsMargins(0,0,0,0)
        h_box0.setSpacing(5)
        h_box0.setAlignment(Qt.AlignCenter)
        lvlLable = CaptionLabel(self.tr("Level"))
        setFont(lvlLable, 13, QFont.Normal)
        lvlLable.adjustSize()
        lvlLable.setFixedSize(43, lvlLable.height())
        self.lvl_badge = LevelBadge(settings.pet_data.fv_lvl)
        h_box0.addWidget(lvlLable)
        #h_box0.addStretch(1)
        h_box0.addWidget(self.lvl_badge)
        h_box0.addStretch(1)
        lvlWidget.setFixedSize(250, 25)

        # Hunger status
        hpWidget = QWidget()
        h_box1 = QHBoxLayout(hpWidget)
        h_box1.setContentsMargins(0,0,0,0) #status_margin,0,0)
        h_box1.setSpacing(5)
        h_box1.setAlignment(Qt.AlignCenter) #AlignBottom | Qt.AlignHCenter)
        hpLable = CaptionLabel(self.tr("Satiety"))
        setFont(hpLable, 13, QFont.Normal)
        hpLable.adjustSize()
        hpLable.setFixedSize(43, hpLable.height())
        self.hpicon = QLabel(self)
        self.hpicon.setFixedSize(icons_wh,icons_wh)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/HP_icon.png'))
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(image)
        self.hpicon.setAlignment(Qt.AlignCenter) #AlignBottom | Qt.AlignRight)
        h_box1.addWidget(hpLable)
        h_box1.addStretch(1)
        h_box1.addWidget(self.hpicon)
        #h_box1.addStretch(1)
        self.pet_hp = DP_HpBar(self, minimum=0, maximum=100, objectName='PetHP')
        self.pet_hp.hp_updated.connect(self._hp_updated)
        h_box1.addWidget(self.pet_hp)
        h_box1.addStretch(1)

        # favor status
        fvWidget = QWidget()
        h_box2 = QHBoxLayout(fvWidget)
        h_box2.setContentsMargins(0,0,0,0) #status_margin,0,0)
        h_box2.setSpacing(5)
        h_box2.setAlignment(Qt.AlignCenter) #Qt.AlignBottom | Qt.AlignHCenter)
        fvLable = CaptionLabel(self.tr("Favor"))
        setFont(fvLable, 13, QFont.Normal)
        fvLable.adjustSize()
        fvLable.setFixedSize(43, fvLable.height())
        self.emicon = QLabel(self)
        self.emicon.setFixedSize(icons_wh,icons_wh)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/Fv_icon.png'))
        self.emicon.setScaledContents(True)
        self.emicon.setPixmap(image)
        #self.emicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box2.addWidget(fvLable, Qt.AlignHCenter | Qt.AlignTop)
        h_box2.addStretch(1)
        h_box2.addWidget(self.emicon)
        self.pet_fv = DP_FvBar(self, minimum=0, maximum=100, objectName='PetEM')
        self.pet_fv.fv_updated.connect(self._fv_updated)

        self.pet_hp.hptier_changed.connect(self.hpchange)
        self.pet_fv.fvlvl_changed.connect(self.fvchange)
        h_box2.addWidget(self.pet_fv)
        h_box2.addStretch(1)

        self.pet_hp.init_HP(settings.pet_data.hp, sys_hp_interval) #2)
        self.pet_fv.init_FV(settings.pet_data.fv, settings.pet_data.fv_lvl)
        self.pet_hp.setFixedSize(145, 15)
        self.pet_fv.setFixedSize(145, 15)

        # Status Widget
        self.statusWidget = QWidget()
        StatVbox = QVBoxLayout(self.statusWidget)
        StatVbox.setContentsMargins(0,5,30,10)
        StatVbox.setSpacing(5)
        
        #StatVbox.addWidget(self.statusTitle, Qt.AlignVCenter)
        StatVbox.addStretch(1)
        #StatVbox.addWidget(self.daysLabel)
        StatVbox.addWidget(hpWidget, Qt.AlignLeft | Qt.AlignVCenter)
        StatVbox.addWidget(fvWidget, Qt.AlignLeft | Qt.AlignVCenter)
        StatVbox.addStretch(1)
        #statusWidget.setLayout(StatVbox)
        #statusWidget.setContentsMargins(0,0,0,0)
        self.statusWidget.setFixedSize(250, 70)
        
        self.StatMenu = RoundMenu(parent=self)
        self.StatMenu.addWidget(self.statusTitle, selectable=False)
        self.StatMenu.addSeparator()
        #self.StatMenu.addWidget(self.statLabel, selectable=False)
        self.StatMenu.addWidget(lvlWidget, selectable=False)
        self.StatMenu.addWidget(self.statusWidget, selectable=False)
        #self.StatMenu.addWidget(fvbar, selectable=False)
        self.StatMenu.addSeparator()

        #self.StatMenu.addMenu(self.menu)
        self.StatMenu.addActions([
            #Action(FIF.MENU, self.tr('More Options'), triggered=self._show_right_menu),
            Action(QIcon(os.path.join(basedir,'res/icons/dashboard.svg')), self.tr('Dashboard'), triggered=self._show_dashboard),
            Action(QIcon(os.path.join(basedir,'res/icons/SystemPanel.png')), self.tr('System'), triggered=self._show_controlPanel),
        ])
        
        # 添加 AI 对话选项
        if settings.ai_enabled and settings.ai_api_key:
            self.StatMenu.addActions([
                Action(FIF.ROBOT, self.tr('Chat with Pet'), triggered=self.show_ai_chat_dialog),
            ])
            
        self.StatMenu.addSeparator()

        self.StatMenu.addMenu(self.act_menu)
        self.StatMenu.addMenu(self.companion_menu)
        self.StatMenu.addMenu(self.change_menu)
        self.StatMenu.addSeparator()
        
        self.StatMenu.addActions([
            Action(FIF.POWER_BUTTON, self.tr('Exit'), triggered=self.quit),
        ])


    # def _update_statusTitle(self, hp_tier):
    #     statusText = self.tr("Status: ") + f"{settings.TIER_NAMES[hp_tier]}"
    #     self.statLabel.setText(statusText)


    def _show_Staus_menu(self):
        """
        展示右键菜单
        :return:
        """
        # 光标位置弹出菜单
        self.StatMenu.popup(QCursor.pos()-QPoint(0, self.StatMenu.height()-20))

    def _add_pet(self, pet_name: str):
        pet_acc = {'name':'pet', 'pet_name':pet_name}
        #self.setup_acc.emit(pet_acc, int(self.current_screen.topLeft().x() + random.uniform(0.4,0.7)*self.screen_width), self.pos().y())
        # To accomodate any subpet that always follows main, change the position to top middle pos of pet
        self.setup_acc.emit(pet_acc, int( self.pos().x() + self.width()/2 ), self.pos().y())

    def open_web(self, web_address):
        try:
            webbrowser.open(web_address)
        except:
            return
    '''
    def freeze_pet(self):
        """stop all thread, function for save import"""
        self.stop_thread('Animation')
        self.stop_thread('Interaction')
        self.stop_thread('Scheduler')
        #del self.threads, self.workers
    '''
    
    def refresh_pet(self):
        # stop animation thread and start again
        self.stop_thread('Animation')
        self.stop_thread('Interaction')

        # Change status
        self.pet_hp.init_HP(settings.pet_data.hp, sys_hp_interval) #2)
        self.pet_fv.init_FV(settings.pet_data.fv, settings.pet_data.fv_lvl)

        # Change status related behavior
        #self.workers['Animation'].hpchange(settings.pet_data.hp_tier, None)
        #self.workers['Animation'].fvchange(settings.pet_data.fv_lvl)

        # Animation config data update
        settings.act_data._pet_refreshed(settings.pet_data.fv_lvl)
        self.refresh_acts.emit()

        # cancel default animation if any
        '''
        defaul_act = settings.defaultAct[self.curr_pet_name]
        if defaul_act is not None:
            self._set_defaultAct(self, defaul_act)
        self._update_fvlock()
        # add default animation back
        if defaul_act in [acti.text() for acti in self.defaultAct_menu.actions()]:
            self._set_defaultAct(self, defaul_act)
        '''

        # Update BackPack
        #self._init_Inventory()
        self.refresh_bag.emit()
        self._set_menu(self.pets)
        self._set_Statusmenu()
        self._set_tray()

        # restart animation and interaction
        self.runAnimation()
        self.runInteraction()
        
        # restore data system
        settings.pet_data.frozen_data = False

        # Compensate items if any
        self._setup_compensate()
    

    def _change_pet(self, pet_name: str) -> None:
        """
        改变宠物
        :param pet_name: 宠物名称
        :return:
        """
        if self.curr_pet_name == pet_name:
            return
        
        # close all accessory widgets (subpet, accessory animation, etc.)
        self.close_all_accs.emit()

        # stop animation thread and start again
        self.stop_thread('Animation')
        self.stop_thread('Interaction')

        # reload pet data
        settings.pet_data._change_pet(pet_name)

        # reload new pet
        self.init_conf(pet_name)

        # Change status
        self.pet_hp.init_HP(settings.pet_data.hp, sys_hp_interval) #2)
        self.pet_fv.init_FV(settings.pet_data.fv, settings.pet_data.fv_lvl)

        # Change status related behavior
        #self.workers['Animation'].hpchange(settings.pet_data.hp_tier, None)
        #self.workers['Animation'].fvchange(settings.pet_data.fv_lvl)

        # Update Backpack
        #self._init_Inventory()
        self.refresh_bag.emit()
        self.refresh_acts.emit()

        self.change_note.emit()
        self.repaint()
        self._setup_ui()

        self.runAnimation()
        self.runInteraction()

        self.workers['Scheduler'].send_greeting()
        # Compensate items if any
        self._setup_compensate()
        # Due to Qt internal behavior, sometimes has to manually correct the position back
        pos_x, pos_y = self.pos().x(), self.pos().y()
        QTimer.singleShot(10, lambda: self.move(pos_x, pos_y))

    def init_conf(self, pet_name: str) -> None:
        """
        初始化宠物窗口配置
        :param pet_name: 宠物名称
        :return:
        """
        self.curr_pet_name = pet_name
        settings.petname = pet_name
        settings.tunable_scale = settings.scale_dict.get(pet_name, 1.0)
        pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, pic_dict) #settings.size_factor)
        
        self.margin_value = 0 #0.1 * max(self.pet_conf.width, self.pet_conf.height) # 用于将widgets调整到合适的大小
        # Add customized animation
        settings.act_data.init_actData(pet_name, settings.pet_data.hp_tier, settings.pet_data.fv_lvl)
        self._load_custom_anim()
        settings.pet_conf = self.pet_conf

        # Update coin name and image according to the pet config
        if self.pet_conf.coin_config:
            coin_config = self.pet_conf.coin_config.copy()
            if not coin_config['image']:
                coin_config['image'] = settings.items_data.default_coin['image']
            settings.items_data.coin = coin_config
        else:
            settings.items_data.coin = settings.items_data.default_coin.copy()

        # Init bubble behavior manager
        self.bubble_manager = BubbleManager()
        self.bubble_manager.register_bubble.connect(self.register_bubbleText)

        self._set_menu(self.pets)
        self._set_Statusmenu()
        self._set_tray()


    def _load_custom_anim(self):
        acts_conf = settings.act_data.allAct_params[settings.petname]
        for act_name, act_conf in acts_conf.items():
            if act_conf['act_type'] == 'customized' and act_name not in self.pet_conf.custom_act:
                # generate new Act objects for cutomized animation
                acts = []
                for act in act_conf.get('act_list', []):
                    acts.append(self._prepare_act_obj(act))
                accs = []
                for act in act_conf.get('acc_list', []):
                    accs.append(self._prepare_act_obj(act))
                # save the new animation config with same format as self.pet_conf.accessory_act
                self.pet_conf.custom_act[act_name] = {"act_list": acts,
                                                      "acc_list": accs,
                                                      "anchor": act_conf.get('anchor_list',[]),
                                                      "act_type": act_conf['status_type']}

    def _prepare_act_obj(self, actobj):
        
        # if this act is a skipping act e.g. [60, 20]
        if len(actobj) == 2:
            return actobj
        else:
            act_conf_name = actobj[0]
            act_idx_start = actobj[1]
            act_idx_end = actobj[2]+1
            act_repeat_num = actobj[3]
            new_actobj = self.pet_conf.act_dict[act_conf_name].customized_copy(act_idx_start, act_idx_end, act_repeat_num)
            return new_actobj

    def updateList(self):
        self.workers['Animation'].update_prob()

    def _addNewAct(self, act_name):
        acts_config = settings.act_data.allAct_params[settings.petname]
        act_conf = acts_config[act_name]

        # Add to pet_conf
        acts = []
        for act in act_conf.get('act_list', []):
            acts.append(self._prepare_act_obj(act))
        accs = []
        for act in act_conf.get('acc_list', []):
            accs.append(self._prepare_act_obj(act))
        self.pet_conf.custom_act[act_name] = {"act_list": acts,
                                                "acc_list": accs,
                                                "anchor": act_conf.get('anchor_list',[]),
                                                "act_type": act_conf['status_type']}
        # update random action prob
        self.updateList()
        # Add to menu
        if act_conf['unlocked']:
            select_act = _build_act(act_name, self.act_menu, self._show_act)
            self.select_acts.append(select_act)
            self.act_menu.addAction(select_act)
    
    def _deleteAct(self, act_name):
        # delete from self.pet_config
        self.pet_conf.custom_act.pop(act_name)
        # update random action prob
        self.updateList()

        # delete from menu
        act_index = [acti.text() for acti in self.select_acts].index(act_name)
        self.act_menu.removeAction(self.select_acts[act_index])
        self.select_acts.remove(self.select_acts[act_index])


    def _setup_ui(self):

        #bar_width = int(max(100*settings.size_factor, 0.5*self.pet_conf.width))
        bar_width = int(max(100, 0.5*self.pet_conf.width))
        bar_width = int(min(200, bar_width))
        self.tomato_time.setFixedSize(bar_width, statbar_h-5)
        self.focus_time.setFixedSize(bar_width, statbar_h-5)

        self.reset_size(setImg=False)

        settings.previous_img = settings.current_img
        settings.current_img = self.pet_conf.default.images[0] #list(pic_dict.values())[0]
        settings.previous_anchor = [0, 0] #settings.current_anchor
        settings.current_anchor = [int(i*settings.tunable_scale) for i in self.pet_conf.default.anchor]
        self.set_img()
        self.border = self.pet_conf.width/2

        
        # 初始位置
        #screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = self.screen_width #screen_geo.width()
        work_height = self.screen_height #screen_geo.height()
        x = self.current_screen.topLeft().x() + int(screen_width*0.8) - self.width()//2
        y = self.current_screen.topLeft().y() + work_height - self.height()
        self.move(x,y)
        if settings.previous_anchor != settings.current_anchor:
            self.move(self.pos().x() - settings.previous_anchor[0] + settings.current_anchor[0],
                      self.pos().y() - settings.previous_anchor[1] + settings.current_anchor[1])
            #self.move(self.pos().x()-settings.previous_anchor[0]*settings.tunable_scale+settings.current_anchor[0]*settings.tunable_scale,
            #          self.pos().y()-settings.previous_anchor[1]*settings.tunable_scale+settings.current_anchor[1]*settings.tunable_scale)

    '''
    def eventFilter(self, object, event):
        return
    
        if event.type() == QEvent.Enter:
            self.status_frame.show()
            return True
        elif event.type() == QEvent.Leave:
            self.status_frame.hide()
        return False
    '''

    def _set_tray(self) -> None:
        """
        设置最小化托盘
        :return:
        """
        if self.tray is None:
            self.tray = SystemTray(self.StatMenu, self) #QSystemTrayIcon(self)
            self.tray.setIcon(QIcon(os.path.join(basedir, 'res/icons/icon.png')))
            self.tray.show()
        else:
            self.tray.setMenu(self.StatMenu)
            self.tray.show()

    def reset_size(self, setImg=True):
        #self.setFixedSize((max(self.pet_hp.width()+statbar_h,self.pet_conf.width)+self.margin_value)*max(1.0,settings.tunable_scale),
        #                  (self.margin_value+4*statbar_h+self.pet_conf.height)*max(1.0, settings.tunable_scale))
        self.setFixedSize( int(max(self.tomato_time.width()+statbar_h,self.pet_conf.width*settings.tunable_scale)),
                           int(2*statbar_h+self.pet_conf.height*settings.tunable_scale)
                         )

        #self.label.setFixedWidth(self.width())

        # 初始位置
        #screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = self.screen_width #screen_geo.width()
        work_height = self.screen_height #screen_geo.height()
        x = self.pos().x() + settings.current_anchor[0]
        if settings.set_fall:
            y = self.current_screen.topLeft().y() + work_height-self.height()+settings.current_anchor[1]
        else:
            y = self.pos().y() + settings.current_anchor[1]
        # make sure that for all stand png, png bottom is the ground
        #self.floor_pos = work_height-self.height()
        self.floor_pos = self.current_screen.topLeft().y() + work_height - self.height()
        self.move(x,y)
        self.move_sig.emit(self.pos().x()+self.width()//2, self.pos().y()+self.height())

        if setImg:
            self.set_img()

    def set_img(self): #, img: QImage) -> None:
        """
        为窗体设置图片
        :param img: 图片
        :return:
        """
        #print(settings.previous_anchor, settings.current_anchor)
        if settings.previous_anchor != settings.current_anchor:
            self.move(self.pos().x()-settings.previous_anchor[0]+settings.current_anchor[0],
                      self.pos().y()-settings.previous_anchor[1]+settings.current_anchor[1])

        width_tmp = int(settings.current_img.width()*settings.tunable_scale)
        height_tmp = int(settings.current_img.height()*settings.tunable_scale)

        # HighDPI-compatible scaling solution
        # self.label.setScaledContents(True)
        self.label.setFixedSize(width_tmp, height_tmp)
        self.label.setPixmap(settings.current_img) #QPixmap.fromImage(settings.current_img))
        # previous scaling soluton
        #self.label.resize(width_tmp, height_tmp)
        #self.label.setPixmap(QPixmap.fromImage(settings.current_img.scaled(width_tmp, height_tmp,
        #                                                                 aspectMode=Qt.KeepAspectRatio,
        #                                                                 mode=Qt.SmoothTransformation)))
        self.image = settings.current_img

    def _compensate_rewards(self):
        self.compensate_rewards.emit()
        # Note user if App updates available
        if settings.UPDATE_NEEDED:
            self.register_notification("system",
                                       self.tr("App update available! Please check System - Settings - Check Updates for detail."))

    def register_notification(self, note_type, message):
        self.setup_notification.emit(note_type, message)


    def register_bubbleText(self, bubble_dict:dict):
        self.setup_bubbleText.emit(bubble_dict, self.pos().x()+self.width()//2, self.pos().y()+self.height())

    def _process_greeting_mssg(self, bubble_dict:dict):
        self.bubble_manager.add_usertag(bubble_dict, 'end', send=True)

    def register_accessory(self, accs):
        self.setup_acc.emit(accs, self.pos().x()+self.width()//2, self.pos().y()+self.height())


    def _change_status(self, status, change_value, from_mod='Scheduler', send_note=False):
        # Check system status
        if from_mod == 'Scheduler' and is_system_locked() and settings.auto_lock:
            print("System locked, skip HP and FV changes")
            return
        if status not in ['hp','fv']:
            return
        elif status == 'hp':
            
            diff = self.pet_hp.updateValue(change_value, from_mod)

        elif status == 'fv':
            
            diff = self.pet_fv.updateValue(change_value, from_mod)

        if send_note:

            if diff > 0:
                diff = '+%s'%diff
            elif diff < 0:
                diff = str(diff)
            else:
                return
            if status == 'hp':
                message = self.tr('Satiety') + " " f'{diff}'
            else:
                message = self.tr('Favorability') + " " f'{diff}' #'好感度 %s'%diff
            self.register_notification('status_%s'%status, message)
        
        # Periodically triggered events
        if status == 'hp' and from_mod == 'Scheduler': # avoid being called in both hp and fv
            # Random Bubble
            if random.uniform(0, 1) < settings.PP_BUBBLE:
                self.bubble_manager.trigger_scheduled()

            # Auto-Feed
            if settings.pet_data.hp <= settings.AUTOFEED_THRESHOLD*settings.HP_INTERVAL:
                self.autofeed.emit()

    def _hp_updated(self, hp):
        self.hp_updated.emit(hp)

    def _fv_updated(self, fv, fv_lvl):
        self.fv_updated.emit(fv, fv_lvl)


    def _change_time(self, status, timeleft):
        if status not in ['tomato','tomato_start','tomato_rest','tomato_end',
                          'focus_start','focus','focus_end','tomato_cencel','focus_cancel']:
            return

        if status in ['tomato','tomato_rest','tomato_end','focus','focus_end']:
            self.taskUI_Timer_update.emit()

        if status == 'tomato_start':
            self.tomato_time.setMaximum(25)
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
            #self.tomato_window.newTomato()
        elif status == 'tomato_rest':
            self.tomato_time.setMaximum(5)
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
            self.single_pomo_done.emit()
        elif status == 'tomato':
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
        elif status == 'tomato_end':
            self.tomato_time.setValue(0)
            self.tomato_time.setFormat('')
            #self.tomato_window.endTomato()
            self.taskUI_task_end.emit()
        elif status == 'tomato_cencel':
            self.tomato_time.setValue(0)
            self.tomato_time.setFormat('')

        elif status == 'focus_start':
            if timeleft == 0:
                self.focus_time.setMaximum(1)
                self.focus_time.setValue(0)
                self.focus_time.setFormat('%s min'%(int(timeleft)))
            else:
                self.focus_time.setMaximum(timeleft)
                self.focus_time.setValue(timeleft)
                self.focus_time.setFormat('%s min'%(int(timeleft)))
        elif status == 'focus':
            self.focus_time.setValue(timeleft)
            self.focus_time.setFormat('%s min'%(int(timeleft)))
        elif status == 'focus_end':
            self.focus_time.setValue(0)
            self.focus_time.setMaximum(0)
            self.focus_time.setFormat('')
            #self.focus_window.endFocus()
            self.taskUI_task_end.emit()
        elif status == 'focus_cancel':
            self.focus_time.setValue(0)
            self.focus_time.setMaximum(0)
            self.focus_time.setFormat('')

    def use_item(self, item_name):
        # Check if it's pet-required item
        if item_name == settings.required_item:
            reward_factor = settings.FACTOR_FEED_REQ
            self.close_bubble.emit('feed_required')
        else:
            reward_factor = 1

        # 食物
        if settings.items_data.item_dict[item_name]['item_type']=='consumable':
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('use_item', item_name)
            self.bubble_manager.trigger_bubble('feed_done')

        # 附件物品
        elif item_name in self.pet_conf.act_name or item_name in self.pet_conf.acc_name:
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('use_clct', item_name)

        # 对话物品
        elif settings.items_data.item_dict[item_name]['item_type']=='dialogue':
            if item_name in self.pet_conf.msg_dict:
                accs = {'name':'dialogue', 'msg_dict':self.pet_conf.msg_dict[item_name]}
                x = self.pos().x() #+self.width()//2
                y = self.pos().y() #+self.height()
                self.setup_acc.emit(accs, x, y)
                return

        # 系统附件物品
        elif item_name in self.sys_conf.acc_name:
            accs = self.sys_conf.accessory_act[item_name]
            x = self.pos().x()+self.width()//2
            y = self.pos().y()+self.height()
            self.setup_acc.emit(accs, x, y)
        
        # Subpet
        elif settings.items_data.item_dict[item_name]['item_type']=='subpet':
            pet_acc = {'name':'subpet', 'pet_name':item_name}
            x = self.pos().x()+self.width()//2
            y = self.pos().y()+self.height()
            self.setup_acc.emit(pet_acc, x, y)
            return

        else:
            pass

        # 鼠标挂件 - currently gave up :(
        '''
        elif item_name in self.sys_conf.mouseDecor:
            accs = {'name':'mouseDecor', 'config':self.sys_conf.mouseDecor[item_name]}
            x = self.pos().x()+self.width()//2
            y = self.pos().y()+self.height()
            self.setup_acc.emit(accs, x, y)
        '''
        
        # 使用物品 改变数值
        self._change_status('hp', 
                            int(settings.items_data.item_dict[item_name]['effect_HP']*reward_factor),
                            from_mod='inventory', send_note=True)
        
        if item_name in self.pet_conf.item_favorite:
            self._change_status('fv',
                                int(settings.items_data.item_dict[item_name]['effect_FV']*self.pet_conf.item_favorite[item_name]*reward_factor),
                                from_mod='inventory', send_note=True)

        elif item_name in self.pet_conf.item_dislike:
            self._change_status('fv', 
                                int(settings.items_data.item_dict[item_name]['effect_FV']*self.pet_conf.item_dislike[item_name]*reward_factor),
                                from_mod='inventory', send_note=True)

        else:
            self._change_status('fv', 
                                int(settings.items_data.item_dict[item_name]['effect_FV']*reward_factor),
                                from_mod='inventory', send_note=True)

    def add_item(self, n_items, item_names=[]):
        self.addItem_toInven.emit(n_items, item_names)

    def patpat(self):
        # 摸摸动画
        if self.click_count >= 7:
            self.bubble_manager.trigger_bubble("pat_frequent")
        elif self.workers['Interaction'].interact != 'patpat':
            if settings.focus_timer_on:
                self.bubble_manager.trigger_bubble("pat_focus")
            else:
                self.workers['Animation'].pause()
                self.workers['Interaction'].start_interact('patpat')

        # 概率触发浮动的心心
        prob_num_0 = random.uniform(0, 1)
        if prob_num_0 < sys_pp_heart:
            try:
                accs = self.sys_conf.accessory_act['heart']
            except:
                return
            x = QCursor.pos().x() #self.pos().x()+self.width()//2 + random.uniform(-0.25, 0.25) * self.label.width()
            y = QCursor.pos().y() #self.pos().y()+self.height()-0.8*self.label.height() + random.uniform(0, 1) * 10
            self.setup_acc.emit(accs, x, y)

        elif prob_num_0 < settings.PP_COIN:
            # Drop random amount of coins
            self.addCoins.emit(0)

        elif prob_num_0 > sys_pp_item:
            self.addItem_toInven.emit(1, [])
            #print('物品掉落！')

        if prob_num_0 > sys_pp_audio:
            #随机语音
            if random.uniform(0, 1) > 0.5:
                # This will be deprecated soon
                self.register_notification('random', '')
            else:
                self.bubble_manager.trigger_patpat_random()

    def item_drop_anim(self, item_name):
        if item_name == 'coin':
            accs = {"name":"item_drop", "item_image":[settings.items_data.coin['image']]}
        else:
            item = settings.items_data.item_dict[item_name]
            accs = {"name":"item_drop", "item_image":[item['image']]}
        x = self.pos().x()+self.width()//2 + random.uniform(-0.25, 0.25) * self.label.width()
        y = self.pos().y()+self.height()-self.label.height()
        self.setup_acc.emit(accs, x, y)



    def quit(self) -> None:
        """
        关闭窗口, 系统退出
        :return:
        """
        settings.pet_data.save_data()
        settings.pet_data.frozen()
        self.stop_thread('Animation')
        self.stop_thread('Interaction')
        self.stop_thread("Scheduler")
        self.stopAllThread.emit()
        self.close()
        sys.exit()

    def stop_thread(self, module_name):
        self.workers[module_name].kill()
        self.threads[module_name].terminate()
        self.threads[module_name].wait()
        #self.threads[module_name].wait()

    def follow_mouse_act(self):
        sender = self.sender()
        if settings.onfloor == 0:
            return
        if sender.text()==self.tr("Follow Cursor"):
            sender.setText(self.tr("Stop Follow"))
            self.MouseTracker = MouseMoveManager()
            self.MouseTracker.moved.connect(self.update_mouse_position)
            self.get_positions('mouse')
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('followTarget', 'mouse')
        else:
            sender.setText(self.tr("Follow Cursor"))
            self.MouseTracker._listener.stop()
            self.workers['Interaction'].stop_interact()

    def get_positions(self, object_name):

        main_pos = [int(self.pos().x() + self.width()//2), int(self.pos().y() + self.height() - self.label.height())]

        if object_name == 'mouse':
            self.send_positions.emit(main_pos, self.mouse_pos)

    def update_mouse_position(self, x, y):
        self.mouse_pos = [x, y]

    def stop_trackMouse(self):
        self.start_follow_mouse.setText(self.tr("Follow Cursor"))
        self.MouseTracker._listener.stop()

    '''
    def fall_onoff(self):
        #global set_fall
        sender = self.sender()
        if settings.set_fall==1:
            sender.setText(self.tr("Don't Drop"))
            sender.setIcon(QIcon(os.path.join(basedir,'res/icons/off.svg')))
            settings.set_fall=0
        else:
            sender.setText(self.tr("Allow Drop"))
            sender.setIcon(QIcon(os.path.join(basedir,'res/icons/on.svg')))
            settings.set_fall=1
    '''

    def _show_controlPanel(self):
        self.show_controlPanel.emit()
        # 连接控制面板的菜单更新信号
        try:
            # 获取控制面板窗口实例
            from DyberPet.run_DyberPet import app_instance
            if hasattr(app_instance, 'controlPanel'):
                app_instance.controlPanel.update_menu_signal.connect(self.update_menu)
        except:
            pass

    def _show_dashboard(self):
        self.show_dashboard.emit()

    '''
    def show_compday(self):
        sender = self.sender()
        if sender.text()=="显示陪伴天数":
            acc = {'name':'compdays', 
                   'height':self.label.height(),
                   'message': "这是%s陪伴你的第 %i 天"%(settings.petname,settings.pet_data.days)}
            sender.setText("关闭陪伴天数")
            x = self.pos().x() + self.width()//2
            y = self.pos().y() + self.height() - self.label.height() - 20 #*settings.size_factor
            self.setup_acc.emit(acc, x, y)
            self.showing_comp = 1
        else:
            sender.setText("显示陪伴天数")
            self.setup_acc.emit({'name':'compdays'}, 0, 0)
            self.showing_comp = 0
    '''

    def show_tomato(self):
        if self.tomato_window.isVisible():
            self.tomato_window.hide()

        else:
            self.tomato_window.move(max(self.current_screen.topLeft().y(),self.pos().x()-self.tomato_window.width()//2),
                                    max(self.current_screen.topLeft().y(),self.pos().y()-self.tomato_window.height()))
            self.tomato_window.show()

        '''
        elif self.tomato_clock.text()=="取消番茄时钟":
            self.tomato_clock.setText("番茄时钟")
            self.workers['Scheduler'].cancel_tomato()
            self.tomatoicon.hide()
            self.tomato_time.hide()
        '''

    def run_tomato(self, nt):
        self.workers['Scheduler'].add_tomato(n_tomato=int(nt))
        self.tomatoicon.show()
        self.tomato_time.show()
        settings.focus_timer_on = True

    def cancel_tomato(self):
        self.workers['Scheduler'].cancel_tomato()

    def change_tomato_menu(self):
        self.tomatoicon.hide()
        self.tomato_time.hide()
        settings.focus_timer_on = False

    
    def show_focus(self):
        if self.focus_window.isVisible():
            self.focus_window.hide()
        
        else:
            self.focus_window.move(max(self.current_screen.topLeft().y(),self.pos().x()-self.focus_window.width()//2),
                                   max(self.current_screen.topLeft().y(),self.pos().y()-self.focus_window.height()))
            self.focus_window.show()


    def run_focus(self, task, hs, ms):
        if task == 'range':
            if hs<=0 and ms<=0:
                return
            self.workers['Scheduler'].add_focus(time_range=[hs,ms])
        elif task == 'point':
            self.workers['Scheduler'].add_focus(time_point=[hs,ms])
        self.focusicon.show()
        self.focus_time.show()
        settings.focus_timer_on = True

    def pause_focus(self, state):
        if state: # 暂停
            self.workers['Scheduler'].pause_focus()
        else: # 继续
            self.workers['Scheduler'].resume_focus(int(self.focus_time.value()), int(self.focus_time.maximum()))


    def cancel_focus(self):
        self.workers['Scheduler'].cancel_focus(int(self.focus_time.maximum()-self.focus_time.value()))

    def change_focus_menu(self):
        self.focusicon.hide()
        self.focus_time.hide()
        settings.focus_timer_on = False


    def show_remind(self):
        if self.remind_window.isVisible():
            self.remind_window.hide()
        else:
            self.remind_window.move(max(self.current_screen.topLeft().y(),self.pos().x()-self.remind_window.width()//2),
                                    max(self.current_screen.topLeft().y(),self.pos().y()-self.remind_window.height()))
            self.remind_window.show()

    ''' Reminder function deleted from v0.3.7
    def run_remind(self, task_type, hs=0, ms=0, texts=''):
        if task_type == 'range':
            self.workers['Scheduler'].add_remind(texts=texts, time_range=[hs,ms])
        elif task_type == 'point':
            self.workers['Scheduler'].add_remind(texts=texts, time_point=[hs,ms])
        elif task_type == 'repeat_interval':
            self.workers['Scheduler'].add_remind(texts=texts, time_range=[hs,ms], repeat=True)
        elif task_type == 'repeat_point':
            self.workers['Scheduler'].add_remind(texts=texts, time_point=[hs,ms], repeat=True)
    '''

    def show_inventory(self):
        if self.inventory_window.isVisible():
            self.inventory_window.hide()
        else:
            self.inventory_window.move(max(self.current_screen.topLeft().y(), self.pos().x()-self.inventory_window.width()//2),
                                    max(self.current_screen.topLeft().y(), self.pos().y()-self.inventory_window.height()))
            self.inventory_window.show()
            #print(self.inventory_window.size())

    '''
    def show_settings(self):
        if self.setting_window.isVisible():
            self.setting_window.hide()
        else:
            #self.setting_window.move(max(self.current_screen.topLeft().y(), self.pos().x()-self.setting_window.width()//2),
            #                        max(self.current_screen.topLeft().y(), self.pos().y()-self.setting_window.height()))
            #self.setting_window.resize(800,800)
            self.setting_window.show()
    '''

    '''
    def show_settingstest(self):
        self.settingUI = SettingMainWindow()
        
        if sys.platform == 'win32':
            self.settingUI.setWindowFlags(
                Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            self.settingUI.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        self.settingUI.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        cardShadowSE = QtWidgets.QGraphicsDropShadowEffect(self.settingUI)
        cardShadowSE.setColor(QColor(189, 167, 165))
        cardShadowSE.setOffset(0, 0)
        cardShadowSE.setBlurRadius(20)
        self.settingUI.setGraphicsEffect(cardShadowSE)
        
        self.settingUI.show()
    '''

    def runAnimation(self):
        # Create thread for Animation Module
        self.threads['Animation'] = QThread()
        self.workers['Animation'] = Animation_worker(self.pet_conf)
        self.workers['Animation'].moveToThread(self.threads['Animation'])

        # Connect signals and slots
        self.threads['Animation'].started.connect(self.workers['Animation'].run)
        self.workers['Animation'].sig_setimg_anim.connect(self.set_img)
        self.workers['Animation'].sig_move_anim.connect(self._move_customized)
        self.workers['Animation'].sig_repaint_anim.connect(self.repaint)
        self.workers['Animation'].acc_regist.connect(self.register_accessory)

        # Start the thread
        self.threads['Animation'].start()
        self.threads['Animation'].setTerminationEnabled()


    def hpchange(self, hp_tier, direction):
        self.workers['Animation'].hpchange(hp_tier, direction)
        self.hptier_changed_main_note.emit(hp_tier, direction)
        #self._update_statusTitle(hp_tier)

    def fvchange(self, fv_lvl):
        if fv_lvl == -1:
            self.fvlvl_changed_main_note.emit(fv_lvl)
        else:
            self.workers['Animation'].fvchange(fv_lvl)
            self.fvlvl_changed_main_note.emit(fv_lvl)
            self.fvlvl_changed_main_inve.emit(fv_lvl)
            self._update_fvlock()
            self.lvl_badge.set_level(fv_lvl)
        self.refresh_acts.emit()
        self.bubble_manager.trigger_bubble(bb_type="fv_lvlup")

    def runInteraction(self):
        # Create thread for Interaction Module
        self.threads['Interaction'] = QThread()
        self.workers['Interaction'] = Interaction_worker(self.pet_conf)
        self.workers['Interaction'].moveToThread(self.threads['Interaction'])

        # Connect signals and slots
        self.workers['Interaction'].sig_setimg_inter.connect(self.set_img)
        self.workers['Interaction'].sig_move_inter.connect(self._move_customized)
        self.workers['Interaction'].sig_act_finished.connect(self.resume_animation)
        self.workers['Interaction'].sig_interact_note.connect(self.register_notification)
        self.workers['Interaction'].acc_regist.connect(self.register_accessory)
        self.workers['Interaction'].query_position.connect(self.get_positions)
        self.workers['Interaction'].stop_trackMouse.connect(self.stop_trackMouse)
        self.send_positions.connect(self.workers['Interaction'].receive_pos)

        # Start the thread
        self.threads['Interaction'].start()
        self.threads['Interaction'].setTerminationEnabled()

    def runScheduler(self):
        # Create thread for Scheduler Module
        self.threads['Scheduler'] = QThread()
        self.workers['Scheduler'] = Scheduler_worker()
        self.workers['Scheduler'].moveToThread(self.threads['Interaction'])

        # Connect signals and slots
        self.threads['Scheduler'].started.connect(self.workers['Scheduler'].run)
        self.workers['Scheduler'].sig_settext_sche.connect(self.register_notification) #_set_dialogue_dp)
        self.workers['Scheduler'].sig_setact_sche.connect(self._show_act)
        self.workers['Scheduler'].sig_setstat_sche.connect(self._change_status)
        self.workers['Scheduler'].sig_focus_end.connect(self.change_focus_menu)
        self.workers['Scheduler'].sig_tomato_end.connect(self.change_tomato_menu)
        self.workers['Scheduler'].sig_settime_sche.connect(self._change_time)
        self.workers['Scheduler'].sig_addItem_sche.connect(self.add_item)
        self.workers['Scheduler'].sig_setup_bubble.connect(self._process_greeting_mssg)

        # Start the thread
        self.threads['Scheduler'].start()
        self.threads['Scheduler'].setTerminationEnabled()



    def _move_customized(self, plus_x, plus_y):

        #print(act_list)
        #direction, frame_move = str(act_list[0]), float(act_list[1])
        pos = self.pos()
        new_x = pos.x() + plus_x
        new_y = pos.y() + plus_y

        # 正在下落的情况，可以切换屏幕
        if settings.onfloor == 0:
            # 落地情况
            if new_y > self.floor_pos+settings.current_anchor[1]:
                settings.onfloor = 1
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
            new_x, new_y = self.limit_in_screen(new_x, new_y, on_action=True)

        self.move(new_x, new_y)


    def switch_screen(self, screen):
        self.current_screen = screen.geometry()
        settings.current_screen = screen
        self.screen_geo = screen.availableGeometry() #screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()
        self.floor_pos = self.current_screen.topLeft().y() + self.screen_height -self.height()


    def limit_in_screen(self, new_x, new_y, on_action=False):
        # 超出当前屏幕左边界
        if new_x+self.width()//2 < self.current_screen.topLeft().x():
            #surpass_x = 'Left'
            new_x = self.current_screen.topLeft().x()-self.width()//2
            if not on_action:
                settings.dragspeedx = -settings.dragspeedx * settings.SPEED_DECAY
                settings.fall_right = not settings.fall_right

        # 超出当前屏幕右边界
        elif new_x+self.width()//2 > self.current_screen.topLeft().x() + self.screen_width:
            #surpass_x = 'Right'
            new_x = self.current_screen.topLeft().x() + self.screen_width-self.width()//2
            if not on_action:
                settings.dragspeedx = -settings.dragspeedx * settings.SPEED_DECAY
                settings.fall_right = not settings.fall_right

        # 超出当前屏幕上边界
        if new_y+self.height()-self.label.height()//2 < self.current_screen.topLeft().y():
            #surpass_y = 'Top'
            new_y = self.current_screen.topLeft().y() + self.label.height()//2 - self.height()
            if not on_action:
                settings.dragspeedy = abs(settings.dragspeedy) * settings.SPEED_DECAY

        # 超出当前屏幕下边界
        elif new_y > self.floor_pos+settings.current_anchor[1]:
            #surpass_y = 'Bottom'
            new_y = self.floor_pos+settings.current_anchor[1]

        return new_x, new_y


    def _show_act(self, act_name):
        print(f"执行动作: {act_name}")

        # 检查动作是否存在于配置中
        acts_config = settings.act_data.allAct_params[settings.petname]

        # 如果动作不在配置中，尝试使用默认动作
        if act_name not in acts_config:
            # 检查是否是默认动作
            default_actions = ["default", "drag", "fall", "on_floor", "focus", "sleep", "angry", "fall_asleep"]
            if act_name in default_actions:
                # 对于默认动作，直接使用pet_conf中的动作
                if hasattr(self.pet_conf, 'act_dict') and act_name in self.pet_conf.act_dict:
                    print(f"使用pet_conf中的默认动作: {act_name}")
                    self.workers['Animation'].pause()
                    # 直接调用动画模块执行动作
                    self._execute_default_action(act_name)
                    return
                else:
                    print(f"默认动作 {act_name} 不存在于pet_conf中")
                    self.register_notification("warning", f"动作 {act_name} 不可用")
                    return
            else:
                print(f"动作 {act_name} 不存在于动作配置中")
                self.register_notification("warning", f"动作 {act_name} 不可用")
                return

        # 动作存在于配置中，正常执行
        self.workers['Animation'].pause()
        self.workers['Interaction'].start_interact('actlist', act_name)

    def _execute_default_action(self, act_name):
        """执行默认动作（直接使用pet_conf中的动作）"""
        try:
            # 检查动作是否在act_dict中
            if hasattr(self.pet_conf, 'act_dict') and act_name in self.pet_conf.act_dict:
                print(f"使用act_dict_action执行默认动作: {act_name}")
                self.workers['Interaction'].start_interact('act_dict_action', act_name)
            else:
                # 尝试使用animat方法
                print(f"使用animat执行默认动作: {act_name}")
                self.workers['Interaction'].start_interact('animat', act_name)
            print(f"成功启动默认动作: {act_name}")
        except Exception as e:
            print(f"执行默认动作失败: {act_name}, 错误: {str(e)}")
            self.register_notification("error", f"执行动作 {act_name} 失败")
            # 恢复动画
            self.workers['Animation'].resume()

    '''
    def _show_acc(self, acc_name):
        self.workers['Animation'].pause()
        self.workers['Interaction'].start_interact('anim_acc', acc_name)
    '''
    def _set_defaultAct(self, act_name):

        if act_name == settings.defaultAct[self.curr_pet_name]:
            settings.defaultAct[self.curr_pet_name] = None
            settings.save_settings()
            for action in self.defaultAct_menu.menuActions():
                if action.text() == act_name:
                    action.setIcon(QIcon(os.path.join(basedir, 'res/icons/dot.png')))
        else:
            for action in self.defaultAct_menu.menuActions():
                if action.text() == settings.defaultAct[self.curr_pet_name]:
                    action.setIcon(QIcon(os.path.join(basedir, 'res/icons/dot.png')))
                elif action.text() == act_name:
                    action.setIcon(QIcon(os.path.join(basedir, 'res/icons/dotfill.png'))) #os.path.join(basedir, 'res/icons/check_icon.png')))

            settings.defaultAct[self.curr_pet_name] = act_name
            settings.save_settings()


    def resume_animation(self):
        self.workers['Animation'].resume()
    
    def _mightEventTrigger(self):
        # Update date
        settings.pet_data.update_date()
        # Update companion days
        daysText = self.tr(" (Fed for ") + str(settings.pet_data.days) +\
                   self.tr(" days)")
        self.daysLabel.setText(daysText)

    def _handle_ai_response(self, response):
        """智能处理 AI 回复，包含动作验证和错误处理"""
        # 解析回复，提取动作指令和文本
        parsed_response = self.aiConnector.parse_response(response)
        action = parsed_response["action"]
        text = parsed_response["text"]
        action_valid = parsed_response.get("action_valid", False)
        action_source = parsed_response.get("action_source", "none")
        raw_action = parsed_response.get("raw_action")

        print(f"[AI回复处理] 动作指令: {action} (有效: {action_valid}, 来源: {action_source})")
        print(f"[AI回复处理] 文本内容: {text}")

        # 如果不是"思考中..."的消息才显示为气泡
        if text != "思考中...":
            # 显示回复文本
            bubble_dict = {
                "icon": "system",
                "message": text,
                "bubble_type": "ai_chat"
            }
            self.register_bubbleText(bubble_dict)

        # 如果有对话框打开，添加消息到对话框
        if hasattr(self, 'aiChatDialog') and self.aiChatDialog.isVisible():
            # 使用QTimer.singleShot确保UI更新在主线程中异步执行
            QTimer.singleShot(0, lambda: self.aiChatDialog.addMessage(text, "bot"))
        
        # 智能动作执行逻辑
        if action:
            print(f"[动作执行] 开始处理动作: {action}")

            # 如果动作已经通过AI连接器验证，直接执行
            if action_valid:
                print(f"[动作执行] 动作已验证，直接执行: {action} (来源: {action_source})")
                # 使用QTimer.singleShot确保在主线程中执行
                QTimer.singleShot(0, lambda: self._show_act(action))

                # 记录成功执行的动作
                success_msg = f"AI智能选择动作: {action}"
                if action_source == "direct_match":
                    success_msg += " (精确匹配)"
                elif action_source == "case_insensitive_match":
                    success_msg += " (忽略大小写匹配)"
                elif action_source == "partial_match":
                    success_msg += " (部分匹配)"

                print(f"[动作执行] ✅ {success_msg}")

            else:
                # 动作验证失败，使用降级策略
                print(f"[动作执行] 动作验证失败，尝试降级策略: {action}")

                # 获取当前可用的动作配置进行二次匹配
                acts_config = settings.act_data.allAct_params[settings.petname]

                # 尝试在acts_config中查找
                fallback_action = None

                # 1. 检查是否在acts_config中
                if action in acts_config:
                    fallback_action = action
                    print(f"[动作执行] 在acts_config中找到: {action}")

                # 2. 使用action_name_map映射
                elif action in self.action_name_map:
                    mapped_action = self.action_name_map[action]
                    fallback_action = mapped_action
                    print(f"[动作执行] 通过action_name_map映射: {action} -> {mapped_action}")

                # 3. 检查默认动作
                else:
                    default_actions = ["default", "drag", "fall", "on_floor", "focus", "sleep", "angry", "fall_asleep"]
                    for act_name in default_actions:
                        if action.lower() == act_name.lower() or act_name.lower() in action.lower():
                            fallback_action = act_name
                            print(f"[动作执行] 匹配到默认动作: {act_name}")
                            break

                # 执行降级动作或使用默认动作
                if fallback_action:
                    print(f"[动作执行] ✅ 使用降级动作: {fallback_action}")
                    QTimer.singleShot(0, lambda: self._show_act(fallback_action))
                else:
                    # 最后的降级策略：使用"站立"作为默认动作
                    default_fallback = "站立"
                    if default_fallback in acts_config:
                        print(f"[动作执行] ⚠️ 使用最终降级动作: {default_fallback}")
                        QTimer.singleShot(0, lambda: self._show_act(default_fallback))
                        self.register_notification("info", f"AI选择的动作'{raw_action}'不可用，已切换为默认动作")
                    else:
                        print(f"[动作执行] ❌ 无法执行任何动作: {action}")
                        self.register_notification("warning", f"AI选择的动作'{raw_action}'不可用且无可用的降级动作")
        else:
            print(f"[动作执行] 无动作指令，仅显示文本回复")
    
    def get_available_actions(self):
        """获取当前宠物可用的所有动作列表"""
        available_actions = []
        
        # 添加默认动作
        default_actions = ["default", "drag", "fall", "on_floor", "focus", "sleep", "angry", "fall_asleep"]
        available_actions.extend(default_actions)
        
        # 添加宠物特有的动作
        acts_config = settings.act_data.allAct_params[settings.petname]
        for act_name, act_conf in acts_config.items():
            if act_conf['unlocked']:
                available_actions.append(act_name)
        
        # 添加宠物配置中的动作
        for act_name in settings.pet_conf.act_dict.keys():
            if act_name not in available_actions:
                available_actions.append(act_name)
        
        # 添加自定义动作
        for act_name in settings.pet_conf.custom_act.keys():
            if act_name not in available_actions:
                available_actions.append(act_name)
        
        return available_actions

    def show_ai_chat_dialog(self):
        """显示 AI 对话输入框"""
        if not settings.ai_enabled:
            self.register_notification("warning", self.tr("AI 对话功能未启用，请在设置中启用"))
            return
        
        if not settings.ai_api_key:
            self.register_notification("warning", self.tr("未设置 API Key，请在设置中配置"))
            return
        
        # 创建自定义对话框
        if not hasattr(self, 'aiChatDialog'):
            self.aiChatDialog = AIChatDialog()
            self.aiChatDialog.setPetName(settings.petname)
            self.aiChatDialog.chat_submitted.connect(self._handle_chat_input)
            
            # 连接动作信号
            self.aiChatDialog.action_triggered.connect(self._show_act)
            
            # 加载可用动作按钮
            self._load_action_buttons()
        
        # 显示对话框
        if not self.aiChatDialog.isVisible():
            # 将对话框放在宠物附近
            dialogPos = self.pos() + QPoint(self.width() + 10, 0)
            self.aiChatDialog.move(dialogPos)
            self.aiChatDialog.show()
        else:
            self.aiChatDialog.activateWindow()
            
    def _load_action_buttons(self):
        """加载动作按钮 - 只从pet_conf.json的random_act配置中加载"""
        common_actions = []

        # 只从pet_conf.json的random_act配置中获取动作
        pet_conf_path = os.path.join(basedir, f'res/role/{settings.petname}/pet_conf.json')
        if os.path.exists(pet_conf_path):
            try:
                with open(pet_conf_path, 'r', encoding='utf-8') as f:
                    pet_conf_data = json.load(f)
                    if 'random_act' in pet_conf_data:
                        for act in pet_conf_data['random_act']:
                            act_name = act.get('name', '')
                            act_list = act.get('act_list', [])
                            act_prob = act.get('act_prob', 0)
                            act_type = act.get('act_type', [2,1])

                            # 过滤条件：
                            # 1. 必须有名称和动作列表
                            # 2. act_prob > 0 (排除概率为0的动作)
                            # 3. 不是特殊动作 (排除 act_type [0,10000] 的动作)
                            if (act_name and act_list and act_prob > 0 and
                                not (len(act_type) == 2 and act_type[1] >= 10000)):

                                # 使用动作名称作为action_id，保持与右键菜单一致
                                common_actions.append({
                                    "name": act_name,
                                    "action_id": act_name  # 使用动作名称而不是act_list[0]
                                })
                                print(f"添加pet_conf动作按钮: {act_name} -> {act_name} (概率: {act_prob})")
                            else:
                                print(f"跳过动作: {act_name} (概率: {act_prob}, 类型: {act_type})")

            except Exception as e:
                print(f"读取pet_conf.json出错: {str(e)}")

        # 设置动作按钮
        if common_actions:
            self.aiChatDialog.setActionButtons(common_actions)
            print(f"最终设置的动作按钮数量: {len(common_actions)}")
        else:
            print("没有找到可用的动作按钮")

    def _handle_chat_input(self, user_input):
        """处理用户输入的聊天内容"""
        # 不再显示用户输入的消息为气泡
        # bubble_dict = {
        #     "icon": "system",
        #     "message": user_input,
        #     "bubble_type": "user_chat"
        # }
        # self.register_bubbleText(bubble_dict)
        
        # 使用异步方式发送AI请求
        def send_request():
            self.aiConnector.send_to_openai(user_input)
        
        # 创建独立线程发送请求
        request_thread = threading.Thread(target=send_request)
        request_thread.daemon = True
        request_thread.start()

    # 在 PetWidget 类中添加一个更新菜单的方法
    def update_menu(self):
        """更新菜单，特别是 AI 对话选项"""
        self._set_Statusmenu()
        self.register_notification("system", self.tr("菜单已更新"))

    def _handle_ai_error(self, error_message):
        """处理 AI 错误"""
        self.register_notification("error", error_message)
        if hasattr(self, 'aiChatDialog') and self.aiChatDialog.isVisible():
            # 使用QTimer.singleShot确保UI更新在主线程中异步执行
            QTimer.singleShot(0, lambda: self.aiChatDialog.addMessage(error_message, "bot"))


def _load_all_pic(pet_name: str) -> dict:
    """
    加载宠物所有动作图片
    :param pet_name: 宠物名称
    :return: {动作编码: 动作图片}
    """
    img_dir = os.path.join(basedir, 'res/role/{}/action/'.format(pet_name))
    images = os.listdir(img_dir)
    return {image.split('.')[0]: _get_q_img(img_dir + image) for image in images}

def _get_q_img(img_path: str) -> QPixmap:
    """
    将图片路径加载为 QPixmap
    :param img_path: 图片路径
    :return: QPixmap
    """
    #image = QImage()
    image = QPixmap()
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

def _build_act_param(name: str, param: str, parent: QObject, act_func) -> Action:
    """
    构建改变菜单动作
    :param pet_name: 菜单动作名称
    :param parent 父级菜单
    :param act_func: 菜单动作函数
    :return:
    """
    act = Action(name, parent)
    act.triggered.connect(lambda: act_func(param))
    return act

# 添加一个新的AI聊天对话框类
class AIChatDialog(QWidget):
    """自定义AI聊天对话框"""
    
    chat_submitted = Signal(str, name='chat_submitted')
    action_triggered = Signal(str, name='action_triggered')
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 修改窗口标志，移除Qt.Window标志，确保对话框不会抢占焦点
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化thinking_widget为None
        self.thinking_widget = None
        
        # 初始化动作按钮列表
        self.action_buttons = []
        
        self.__initUI()
        
    def __initUI(self):
        # 主布局
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        
        # 创建一个带圆角的框架
        self.frame = QFrame(self)
        self.frame.setObjectName("chatFrame")
        self.frame.setStyleSheet("""
            #chatFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #d0d0d0;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.frame.setGraphicsEffect(shadow)
        
        # 框架布局
        self.frameLayout = QVBoxLayout(self.frame)
        self.frameLayout.setContentsMargins(15, 15, 15, 15)
        self.frameLayout.setSpacing(10)
        
        # 标题栏
        self.titleBar = QWidget()
        self.titleBarLayout = QHBoxLayout(self.titleBar)
        self.titleBarLayout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        self.titleLabel = StrongBodyLabel()
        self.titleLabel.setObjectName("titleLabel")
        self.titleLabel.setStyleSheet("font-size: 16px; color: #009faa;")
        
        # 关闭按钮
        self.closeButton = TransparentToolButton(FIF.CLOSE, self)
        self.closeButton.setIconSize(QSize(16, 16))
        self.closeButton.clicked.connect(self.close)
        
        self.titleBarLayout.addWidget(self.titleLabel)
        self.titleBarLayout.addStretch()
        self.titleBarLayout.addWidget(self.closeButton)
        
        # 提示文本
        self.tipLabel = BodyLabel("与宠物聊天，它会以可爱的方式回应你~")
        self.tipLabel.setStyleSheet("color: #666666;")
        
        # 动作按钮区域
        self.actionArea = QWidget()
        self.actionAreaLayout = QVBoxLayout(self.actionArea)
        self.actionAreaLayout.setContentsMargins(0, 0, 0, 0)
        
        self.actionButtonsLabel = BodyLabel("动作快捷选择：")
        self.actionButtonsLabel.setStyleSheet("color: #009faa; font-weight: bold;")
        self.actionAreaLayout.addWidget(self.actionButtonsLabel)
        
        # 动作按钮流式布局（使用FlowLayout更好，但这里先用QGridLayout简化）
        self.actionButtonsArea = QWidget()
        self.actionButtonsLayout = QGridLayout(self.actionButtonsArea)
        self.actionButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.actionButtonsLayout.setSpacing(5)
        self.actionAreaLayout.addWidget(self.actionButtonsArea)
        
        self.actionToggleButton = TransparentToolButton(FIF.DOWN, self)
        self.actionToggleButton.setToolTip("显示/隐藏动作按钮")
        self.actionToggleButton.clicked.connect(self.toggleActionArea)
        self.actionAreaLayout.addWidget(self.actionToggleButton, 0, Qt.AlignCenter)
        
        # 聊天历史区域
        self.chatHistory = QScrollArea()
        self.chatHistory.setWidgetResizable(True)
        self.chatHistory.setFrameShape(QFrame.NoFrame)
        self.chatHistory.setMinimumHeight(150)
        
        self.chatHistoryContent = QWidget()
        self.chatHistoryLayout = QVBoxLayout(self.chatHistoryContent)
        self.chatHistoryLayout.setAlignment(Qt.AlignTop)
        self.chatHistoryLayout.setSpacing(10)
        self.chatHistoryLayout.setContentsMargins(5, 5, 5, 5)
        
        self.chatHistory.setWidget(self.chatHistoryContent)
        self.chatHistory.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f5;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #f5f5f5;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 输入区域
        self.inputLayout = QHBoxLayout()
        self.chatInput = QLineEdit()
        self.chatInput.setPlaceholderText("输入你想说的话...")
        self.chatInput.setMinimumWidth(300)
        self.chatInput.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px;
                background-color: #f5f5f5;
                selection-background-color: #009faa;
            }
        """)
        self.chatInput.returnPressed.connect(self.submitChat)
        
        self.sendButton = PrimaryPushButton("发送")
        self.sendButton.clicked.connect(self.submitChat)
        
        self.inputLayout.addWidget(self.chatInput)
        self.inputLayout.addWidget(self.sendButton)
        
        # 添加到框架布局
        self.frameLayout.addWidget(self.titleBar)
        self.frameLayout.addWidget(self.tipLabel)
        self.frameLayout.addWidget(self.actionArea)
        self.frameLayout.addWidget(self.chatHistory)
        self.frameLayout.addLayout(self.inputLayout)
        
        # 添加框架到主布局
        self.mainLayout.addWidget(self.frame)
        
        # 设置拖动
        self.oldPos = None
        self.titleBar.mousePressEvent = self.titleBarMousePressEvent
        self.titleBar.mouseMoveEvent = self.titleBarMouseMoveEvent
        self.titleBar.mouseReleaseEvent = self.titleBarMouseReleaseEvent
        
        # 设置大小
        self.setMinimumWidth(350)
        self.adjustSize()
        
        # 初始隐藏动作区域
        self.actionToggleButton.setIcon(FIF.DOWN)
        self.actionButtonsArea.hide()
    
    def closeEvent(self, event):
        """关闭事件，确保资源正确释放"""
        super().closeEvent(event)
        
    def titleBarMousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
    
    def titleBarMouseMoveEvent(self, event):
        if self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()
    
    def titleBarMouseReleaseEvent(self, event):
        self.oldPos = None
    
    def submitChat(self):
        text = self.chatInput.text().strip()
        if text:
            self.addMessage(text, "user")
            self.chat_submitted.emit(text)
            self.chatInput.clear()
            
            # 显示"思考中..."消息
            self.showThinkingMessage()
    
    def setPetName(self, name):
        self.titleLabel.setText(f"与{name}聊天")
    
    def toggleActionArea(self):
        """切换动作按钮区域的显示状态"""
        if self.actionButtonsArea.isVisible():
            self.actionButtonsArea.hide()
            self.actionToggleButton.setIcon(FIF.DOWN)
        else:
            self.actionButtonsArea.show()
            self.actionToggleButton.setIcon(FIF.UP)
        
        # 调整窗口大小
        self.adjustSize()
    
    def setActionButtons(self, actions):
        """设置动作按钮
        
        Args:
            actions: 动作名称列表，格式可以是[{name: "动作名称", action_id: "动作ID"}]或["动作名称"]
        """
        # 清除现有按钮
        for button in self.action_buttons:
            self.actionButtonsLayout.removeWidget(button)
            button.deleteLater()
        self.action_buttons.clear()
        
        # 添加新按钮
        row, col = 0, 0
        max_cols = 3  # 每行最多3个按钮
        
        def create_action_button(action_name, action_id=None):
            button = QPushButton(action_name)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #d0d0d0;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            button.setCursor(Qt.PointingHandCursor)
            
            # 创建一个固定的action_id捕获变量，避免闭包问题
            action_id_to_emit = action_id if action_id else action_name
            print(f"创建动作按钮: {action_name} -> {action_id_to_emit}")
            
            # 使用lambda时创建独立的作用域以避免闭包问题
            button.clicked.connect(lambda checked=False, aid=action_id_to_emit: self.action_triggered.emit(aid))
            return button
        
        for action in actions:
            if isinstance(action, dict):
                action_name = action.get('name', '')
                action_id = action.get('action_id', action_name)
                button = create_action_button(action_name, action_id)
            else:
                button = create_action_button(action, action)
            
            self.actionButtonsLayout.addWidget(button, row, col)
            self.action_buttons.append(button)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 确保动作区域可见
        self.actionButtonsArea.show()
        self.actionToggleButton.setIcon(FIF.UP)
        self.adjustSize()
    
    def showThinkingMessage(self):
        """显示"思考中..."消息"""
        # 如果已经有思考中消息，先移除
        if self.thinking_widget:
            self.chatHistoryLayout.removeWidget(self.thinking_widget)
            self.thinking_widget.deleteLater()
        
        # 创建新的思考中消息
        self.thinking_widget = QWidget()
        msgLayout = QHBoxLayout(self.thinking_widget)
        msgLayout.setContentsMargins(0, 0, 0, 0)
        
        bubbleWidget = QWidget()
        bubbleLayout = QVBoxLayout(bubbleWidget)
        bubbleLayout.setContentsMargins(10, 8, 10, 8)
        
        msgLabel = BodyLabel("思考中...")
        msgLabel.setWordWrap(True)
        msgLabel.setStyleSheet("color: #666666; font-style: italic;")
        bubbleLayout.addWidget(msgLabel)
        
        msgLayout.addWidget(bubbleWidget)
        msgLayout.addStretch()
        bubbleWidget.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
        """)
        
        self.chatHistoryLayout.addWidget(self.thinking_widget)
        
        # 滚动到底部
        QTimer.singleShot(50, lambda: self.chatHistory.verticalScrollBar().setValue(
            self.chatHistory.verticalScrollBar().maximum()))
    
    def addMessage(self, text, sender):
        """添加消息到聊天历史"""
        # 创建消息控件
        msgWidget = QWidget()
        msgLayout = QHBoxLayout(msgWidget)
        msgLayout.setContentsMargins(0, 0, 0, 0)
        
        # 创建消息气泡
        bubbleWidget = QWidget()
        bubbleLayout = QVBoxLayout(bubbleWidget)
        bubbleLayout.setContentsMargins(10, 8, 10, 8)
        
        msgLabel = BodyLabel(text)
        msgLabel.setWordWrap(True)
        msgLabel.setStyleSheet("color: #333333;")
        bubbleLayout.addWidget(msgLabel)
        
        # 设置气泡样式
        if sender == "user":
            msgLayout.addStretch()
            msgLayout.addWidget(bubbleWidget)
            bubbleWidget.setStyleSheet("""
                background-color: #dcf8c6;
                border-radius: 10px;
            """)
        else:
            # 如果有思考中消息，先移除
            if self.thinking_widget:
                self.chatHistoryLayout.removeWidget(self.thinking_widget)
                self.thinking_widget.deleteLater()
                self.thinking_widget = None
                
            msgLayout.addWidget(bubbleWidget)
            msgLayout.addStretch()
            bubbleWidget.setStyleSheet("""
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            """)
        
        self.chatHistoryLayout.addWidget(msgWidget)
        
        # 滚动到底部
        QTimer.singleShot(50, lambda: self.chatHistory.verticalScrollBar().setValue(
            self.chatHistory.verticalScrollBar().maximum()))


