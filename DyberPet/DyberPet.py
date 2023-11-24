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

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer, QObject, QPoint, QEvent
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontDatabase, QAction

from qfluentwidgets import CaptionLabel, setFont, Action #,RoundMenu
from qfluentwidgets import FluentIcon as FIF
from DyberPet.custom_widgets import SystemTray
from .custom_roundmenu import RoundMenu

from DyberPet.conf import *
from DyberPet.utils import *
from DyberPet.modules import *
from DyberPet.Accessory import MouseMoveManager
from DyberPet.extra_windows import *
#from DyberPet.DyberPetBackup.StartBackupManager import *

# initialize settings
import DyberPet.settings as settings
settings.init()

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

# version
dyberpet_version = settings.VERSION
vf = open(os.path.join(basedir,'data/version'), 'w')
vf.write(dyberpet_version)
vf.close()

# some UI size parameters
status_margin = int(3) # * settings.size_factor) #int(3 * resolution_factor)
statbar_h = int(15) # * settings.size_factor) #int(15 * resolution_factor)
icons_wh = 20

# system config
sys_hp_tiers = settings.HP_TIERS #[0,50,80,100] #Line 52
sys_hp_interval = settings.HP_INTERVAL #2 #Line 485
sys_lvl_bar = settings.LVL_BAR #[20, 120, 300, 600, 1200, 1800, 2400, 3200] #Line 134 sys_lvl_bar = [20, 200, 400, 800, 2000, 5000, 8000, 5000, 5000, 5000, 5000]
sys_pp_heart = settings.PP_HEART #0.8 #Line 1001
sys_pp_item = settings.PP_ITEM #0.98 #Line 1010
sys_pp_audio = settings.PP_AUDIO #0.8 #Line 1014


# Pet HP progress bar
class DP_HpBar(QProgressBar):
    hptier_changed = Signal(int, str, name='hptier_changed')
    hp_updated = Signal(int, name='hp_updated')

    def __init__(self, *args, **kwargs):

        super(DP_HpBar, self).__init__(*args, **kwargs)

        stylesheet = '''QProgressBar {
                                        font-family: "Segoe UI";
                                        border: 1px solid #08060f;
                                        border-radius: 7px;
                                      }
                        QProgressBar::chunk {
                                        background-color: #FAC486;
                                        border-radius: 5px;}'''
        self.setStyleSheet(stylesheet)

        self.setFormat('0/100')
        self.setValue(0)
        self.setAlignment(Qt.AlignCenter)
        self.hp_tiers = sys_hp_tiers #[0,50,80,100]

        self.hp_max = 100
        self.interval = 1
        self.hp_inner = 0
        self.hp_perct = 0

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
        stylesheet = f'''QProgressBar {{
                                        font-family: "Segoe UI";
                                        border: 1px solid #08060f;
                                        border-radius: 7px;
                                      }}
                        QProgressBar::chunk {{
                                        background-color: {colors[settings.pet_data.hp_tier]};
                                        border-radius: 5px;}}'''
        self.setStyleSheet(stylesheet)



# Favorability Progress Bar
class DP_FvBar(QProgressBar):
    fvlvl_changed = Signal(int, name='fvlvl_changed')
    fv_updated = Signal(int, int, name='fv_updated')

    def __init__(self, *args, **kwargs):

        super(DP_FvBar, self).__init__(*args, **kwargs)

        stylesheet = '''QProgressBar {
                                        font-family: "Segoe UI";
                                        border: 1px solid #08060f;
                                        border-radius: 7px;
                                      }
                        QProgressBar::chunk {
                                        background-color: #F4665C;
                                        border-radius: 5px;}'''
        self.setStyleSheet(stylesheet)

        self.fvlvl = 0
        self.lvl_bar = sys_lvl_bar #[20, 120, 300, 600, 1200]
        self.points_to_lvlup = self.lvl_bar[self.fvlvl]
        self.setMinimum(0)
        self.setMaximum(self.points_to_lvlup)
        self.setFormat('lv%s: 0/%s'%(int(self.fvlvl), self.points_to_lvlup))
        self.setValue(0)
        self.setAlignment(Qt.AlignCenter)

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
            elif settings.pet_data.hp_tier == 0:
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
    addItem_toInven = Signal(int, list, name='addItem_toInven')
    fvlvl_changed_main_note = Signal(int, name='fvlvl_changed_main_note')
    fvlvl_changed_main_inve = Signal(int, name='fvlvl_changed_main_inve')
    hptier_changed_main_note = Signal(int, str, name='hptier_changed_main_note')

    setup_acc = Signal(dict, int, int, name='setup_acc')
    change_note = Signal(name='change_note')

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

        self.image = None
        self.tray = None

        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_moving = False
        self.mouse_drag_pos = self.pos()
        self.mouse_pos = [0, 0]

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

        # 开始动画模块和交互模块
        self.threads = {}
        self.workers = {}
        self.runAnimation()
        self.runInteraction()
        self.runScheduler()
        self._setup_ui()

        # 初始化重复提醒任务
        self.remind_window.initial_task()

        # 启动完毕10s后检查好感度等级奖励补偿
        self.compensate_timer = None
        self._setup_compensate()

    def _setup_compensate(self):
        self._stop_compensate()
        self.compensate_timer = QTimer(singleShot=True, timeout=self._compensate_rewards)
        self.compensate_timer.start(10000)

    def _stop_compensate(self):
        if self.compensate_timer:
            self.compensate_timer.stop()

    def moveEvent(self, event):
        self.move_sig.emit(self.pos().x()+self.width()//2, self.pos().y()+self.height())

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """

        if event.button() == Qt.RightButton:
            # 打开右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_Staus_menu)
        if event.button() == Qt.LeftButton:
            # 左键绑定拖拽
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            
            if settings.onfloor == 0:
            # Left press activates Drag interaction
                if settings.set_fall == 1:              
                    settings.onfloor=0
                settings.draging=1
                self.workers['Animation'].pause()
                self.workers['Interaction'].start_interact('mousedrag')
                

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

            self.mouse_moving = True

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
                if settings.set_fall == 1:
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
            self.setCursor(QCursor(Qt.ArrowCursor))

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
                    

                if settings.set_fall == 1:
                    settings.onfloor=0
                    settings.draging=0
                    settings.prefall=1

                    settings.dragspeedx=(settings.mouseposx1-settings.mouseposx3)/2*settings.fixdragspeedx
                    settings.dragspeedy=(settings.mouseposy1-settings.mouseposy3)/2*settings.fixdragspeedy
                    settings.mouseposx1=settings.mouseposx3=0
                    settings.mouseposy1=settings.mouseposy3=0

                    if settings.dragspeedx > 0:
                        settings.fall_right = 1
                    else:
                        settings.fall_right = 0

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
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/Tomato_icon.png'))
        self.tomatoicon.setScaledContents(True)
        self.tomatoicon.setPixmap(QPixmap.fromImage(image))
        self.tomatoicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box3.addWidget(self.tomatoicon)
        self.tomato_time = QProgressBar(self, minimum=0, maximum=25, objectName='PetTM')
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
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/Timer_icon.png'))
        self.focusicon.setScaledContents(True)
        self.focusicon.setPixmap(QPixmap.fromImage(image))
        self.focusicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box4.addWidget(self.focusicon)
        self.focus_time = QProgressBar(self, minimum=0, maximum=0, objectName='PetFC')
        self.focus_time.setFormat('')
        self.focus_time.setValue(0)
        self.focus_time.setAlignment(Qt.AlignCenter)
        self.focus_time.hide()
        self.focusicon.hide()
        h_box4.addWidget(self.focus_time)

        vbox.addLayout(h_box3)
        vbox.addLayout(h_box4)
        #vbox.addLayout(h_box1)
        #vbox.addLayout(h_box2)

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
        self.petlayout.addWidget(self.label)
        self.petlayout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        #self.petlayout.setAlignment(Qt.AlignBottom)
        self.petlayout.setContentsMargins(0,0,0,0)
        #self.layout.addLayout(self.dialogue_box, Qt.AlignBottom | Qt.AlignHCenter)
        self.layout.addLayout(self.petlayout, Qt.AlignBottom | Qt.AlignHCenter)
        # ------------------------------------------------------------

        self.setLayout(self.layout)
        # ------------------------------------------------------------

        # 番茄钟设置
        self.tomato_window = Tomato()
        self.tomato_window.close_tomato.connect(self.show_tomato)
        self.tomato_window.confirm_tomato.connect(self.run_tomato)
        self.tomato_window.cancelTm.connect(self.cancel_tomato)

        # 专注时间
        self.focus_window = Focus()
        self.focus_window.close_focus.connect(self.show_focus)
        self.focus_window.confirm_focus.connect(self.run_focus)
        self.focus_window.cancelFocus.connect(self.cancel_focus)
        self.focus_window.pauseTimer_focus.connect(self.pause_focus)

        # 提醒我
        self.remind_window = Remindme()
        self.remind_window.close_remind.connect(self.show_remind)
        self.remind_window.confirm_remind.connect(self.run_remind)

        # 初始化背包
        self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        #self._init_Inventory()

        self.showing_comp = 0


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


    def _set_menu(self, pets=()):
        """
        Option Menu
        """
        menu = RoundMenu(self.tr("More Options"), self)
        menu.setIcon(FIF.MENU)

        # Backpack
        '''
        self.open_invent = Action(QIcon(os.path.join(basedir,'res/icons/backpack.svg')),
                                  self.tr('Backpack'),
                                  triggered = self.show_inventory)
        menu.addAction(self.open_invent)
        '''

        # Select action
        self.act_menu = RoundMenu(self.tr("Select Action"), menu)
        self.act_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/jump.svg')))

        self.start_follow_mouse = Action(QIcon(os.path.join(basedir,'res/icons/cursor.svg')),
                                         self.tr('Follow Cursor'),
                                         triggered = self.follow_mouse_act)
        self.act_menu.addAction(self.start_follow_mouse)
        self.act_menu.addSeparator()

        if self.pet_conf.act_name is not None:
            #select_acts = [_build_act(name, act_menu, self._show_act) for name in self.pet_conf.act_name]
            self.select_acts = [_build_act(self.pet_conf.act_name[i], self.act_menu, self._show_act) for i in range(len(self.pet_conf.act_name)) if (self.pet_conf.act_type[i][1] <= settings.pet_data.fv_lvl) and self.pet_conf.act_name[i] is not None]
            self.act_menu.addActions(self.select_acts)
        
        if self.pet_conf.acc_name is not None:
            self.select_accs = [_build_act(self.pet_conf.acc_name[i], self.act_menu, self._show_acc) for i in range(len(self.pet_conf.acc_name)) if (self.pet_conf.accessory_act[self.pet_conf.acc_name[i]]['act_type'][1] <= settings.pet_data.fv_lvl) ]
            self.act_menu.addActions(self.select_accs)

        menu.addMenu(self.act_menu)


        # Launch pet/partner
        self.companion_menu = RoundMenu(self.tr("Call Partner"), menu)
        self.companion_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/partner.svg')))

        add_acts = [_build_act(name, self.companion_menu, self._add_pet) for name in pets]
        self.companion_menu.addActions(add_acts)
        if len(self.pet_conf.subpet.keys()) != 0:
            add_acts_sub = [_build_act(name, self.companion_menu, self._add_pet) for name in self.pet_conf.subpet if self.pet_conf.subpet[name]['fv_lock']<=settings.pet_data.fv_lvl]
            self.companion_menu.addActions(add_acts_sub)
        menu.addMenu(self.companion_menu)


        # Task
        self.task_menu = RoundMenu(self.tr("Tasks"), menu)
        self.task_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/task.svg')))

        pomodoro_conf = os.path.join(basedir, 'res/icons/Pomodoro.json')
        if os.path.isfile(pomodoro_conf):
            pomodoro = json.load(open(pomodoro_conf, 'r', encoding='UTF-8'))
            self.tomato_clock = Action(QIcon(os.path.join(basedir,'res/icons/tomato.svg')),
                                       pomodoro['title'], self.task_menu)
        else:
            self.tomato_clock = Action(QIcon(os.path.join(basedir,'res/icons/tomato.svg')),
                                       self.tr('Pomodoro'), self.task_menu)

        self.tomato_clock.triggered.connect(self.show_tomato)
        self.task_menu.addAction(self.tomato_clock)

        self.focus_clock = Action(QIcon(os.path.join(basedir,'res/icons/focus.svg')),
                                         self.tr('Focus'),
                                         triggered = self.show_focus)
        self.task_menu.addAction(self.focus_clock)

        self.remind_clock = Action(QIcon(os.path.join(basedir,'res/icons/bell.svg')),
                                         self.tr('Reminder'),
                                         triggered = self.show_remind)
        self.task_menu.addAction(self.remind_clock)
        menu.addMenu(self.task_menu)

        menu.addSeparator()

        # Default Action
        self.defaultAct_menu = RoundMenu(self.tr("Default Action"), menu)
        self.defaultAct_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/repeatone.svg')))


        if self.pet_conf.act_name is not None:
            self.default_acts = [_build_act(icon=QIcon(os.path.join(basedir, 'res/icons/dot.png')),
                                            name=self.pet_conf.act_name[i], parent=self.defaultAct_menu, act_func=self._set_defaultAct) for i in range(len(self.pet_conf.act_name)) if (self.pet_conf.act_type[i][1] <= settings.pet_data.fv_lvl) and self.pet_conf.act_name[i] is not None]
            if settings.defaultAct[self.curr_pet_name] is not None:
                for action in self.default_acts:
                    if settings.defaultAct[self.curr_pet_name] == action.text():
                        action.setIcon(QIcon(os.path.join(basedir, 'res/icons/dotfill.png')))
            self.defaultAct_menu.addActions(self.default_acts)

        menu.addMenu(self.defaultAct_menu)

        # Change Character
        self.change_menu = RoundMenu(self.tr("Change Character"), menu)
        self.change_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/character.svg')))
        change_acts = [_build_act(name, self.change_menu, self._change_pet) for name in pets]
        self.change_menu.addActions(change_acts)
        menu.addMenu(self.change_menu)

        # Drop on/off
        if settings.set_fall == 1:
            self.switch_fall = Action(QIcon(os.path.join(basedir,'res/icons/on.svg')),
                                      self.tr('Allow Drop'), menu)
        else:
            self.switch_fall = Action(QIcon(os.path.join(basedir,'res/icons/off.svg')),
                                      self.tr("Don't Drop"), menu)
        self.switch_fall.triggered.connect(self.fall_onoff)
        menu.addAction(self.switch_fall)

        '''
        # Settings
        self.open_setting = Action(QIcon(os.path.join(basedir,'res/icons/SystemPanel.png')), self.tr('System'), triggered=self.show_controlPanel)
        menu.addAction(self.open_setting)
        '''
        
        # Visit website
        web_file = os.path.join(basedir, 'res/role/sys/webs.json')
        if os.path.isfile(web_file):
            web_dict = json.load(open(web_file, 'r', encoding='UTF-8'))

            self.web_menu = RoundMenu(self.tr("Website"), menu)
            self.web_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/website.svg')))

            web_acts = [_build_act_param(name, web_dict[name], self.web_menu, self.open_web) for name in web_dict]
            self.web_menu.addActions(web_acts)
            menu.addMenu(self.web_menu)
            
        menu.addSeparator()

        self.menu = menu
        self.menu.addAction(Action(FIF.POWER_BUTTON, self.tr('Exit'), triggered=self.quit))


    def _update_fvlock(self):

        # Update selectable animations
        #select_acts = []
        for i in range(len(self.pet_conf.act_name)):
            act_name = self.pet_conf.act_name[i]
            act_type = self.pet_conf.act_type[i]

            if act_name is None:
                continue

            if act_type[1] > settings.pet_data.fv_lvl:
                if act_name in [acti.text() for acti in self.select_acts]:
                    act_index = [acti.text() for acti in self.select_acts].index(act_name)
                    self.act_menu.removeAction(self.select_acts[act_index])
                    self.select_acts.remove(self.select_acts[act_index])
            else:
                if act_name not in [acti.text() for acti in self.select_acts]:
                    new_act = _build_act(act_name, self.act_menu, self._show_act)
                    self.act_menu.addAction(new_act)
                    self.select_acts.append(new_act)

            #select_acts.append(_build_act(self.pet_conf.act_name[i], self.act_menu, self._show_act))

        #if len(select_acts) > 0:
        #    self.act_menu.addActions(select_acts)

        # Update selectable animations that has accessory
        #select_accs = []
        for acc_name in self.pet_conf.acc_name:
            acc_type = self.pet_conf.accessory_act[acc_name]['act_type']

            if acc_type[1] > settings.pet_data.fv_lvl:
                if acc_name in [acci.text() for acci in self.select_accs]:
                    acc_index = [acci.text() for acci in self.select_accs].index(acc_name)
                    self.act_menu.removeAction(self.select_accs[acc_index])
                    self.select_accs.remove(self.select_accs[acc_index])
            else:
                if acc_name not in [acci.text() for acci in self.select_accs]:
                    new_acc = _build_act(acc_name, self.act_menu, self._show_acc)
                    self.act_menu.addAction(new_acc)
                    self.select_accs.append(new_acc)

            #if self.pet_conf.accessory_act[name_i]['act_type'][1] == settings.pet_data.fv_lvl:
            #    select_accs.append(_build_act(name_i, self.act_menu, self._show_acc))

        #if len(select_accs) > 0:
        #    self.act_menu.addActions(select_accs)
        #menu.addMenu(self.act_menu)

        # Update default animation options
        #default_acts = []
        for i in range(len(self.pet_conf.act_name)):
            act_name = self.pet_conf.act_name[i]
            act_type = self.pet_conf.act_type[i]

            if act_name is None:
                continue

            if act_type[1] > settings.pet_data.fv_lvl:
                if act_name in [acti.text() for acti in self.default_acts]:
                    act_index = [acti.text() for acti in self.default_acts].index(act_name)
                    self.defaultAct_menu.removeAction(self.default_acts[act_index])
                    self.default_acts.remove(self.default_acts[act_index])
            else:
                if act_name not in [acti.text() for acti in self.default_acts]:
                    new_act = _build_act(icon=QIcon(os.path.join(basedir, 'res/icons/dot.png')),
                                         name=act_name, parent=self.defaultAct_menu, act_func=self._set_defaultAct)
                    self.defaultAct_menu.addAction(new_act)
                    self.default_acts.append(new_act)

            #default_acts.append(_build_act(self.pet_conf.act_name[i], self.defaultAct_menu, self._set_defaultAct))

        #if len(default_acts) > 0:
        #    self.defaultAct_menu.addActions(default_acts)

        # update partner list
        old_petlist = self.companion_menu.actions()
        for name in self.pet_conf.subpet:

            if self.pet_conf.subpet[name]['fv_lock'] > settings.pet_data.fv_lvl:
                if name in [peti.text() for peti in old_petlist]:
                    pet_index = [peti.text() for peti in old_petlist].index(name)
                    self.companion_menu.removeAction(old_petlist[pet_index])
                    old_petlist.remove(old_petlist[pet_index])

            else:
                if name not in [peti.text() for peti in old_petlist]:
                    new_pet = _build_act(name, self.companion_menu, self._add_pet)
                    self.companion_menu.addAction(new_pet)
                    old_petlist.append(new_pet)


            #add_pets.append(_build_act(name, self.companion_menu, self._add_pet))

        #if len(add_pets) > 0:
        #    self.companion_menu.addActions(add_pets)


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

        # Status Title
        hp_tier = settings.pet_data.hp_tier
        statusText = self.tr("Status: ") + f"{settings.TIER_NAMES[hp_tier]}"
        self.statLabel = CaptionLabel(statusText, self)
        setFont(self.statLabel, 14, QFont.Normal)
        #self.daysLabel.setFixedWidth(75)

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
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/HP_icon.png'))
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(QPixmap.fromImage(image))
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
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/Fv_icon.png'))
        self.emicon.setScaledContents(True)
        self.emicon.setPixmap(QPixmap.fromImage(image))
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
        self.StatMenu.addWidget(self.statLabel, selectable=False)
        self.StatMenu.addWidget(self.statusWidget, selectable=False)
        #self.StatMenu.addWidget(fvbar, selectable=False)
        self.StatMenu.addSeparator()        

        self.StatMenu.addMenu(self.menu)
        self.StatMenu.addActions([
            #Action(FIF.MENU, self.tr('More Options'), triggered=self._show_right_menu),
            Action(QIcon(os.path.join(basedir,'res/icons/dashboard.svg')), self.tr('Dashboard'), triggered=self._show_dashboard),
            Action(QIcon(os.path.join(basedir,'res/icons/SystemPanel.png')), self.tr('System'), triggered=self._show_controlPanel),
            Action(FIF.POWER_BUTTON, self.tr('Exit'), triggered=self.quit),
        ])

    def _update_statusTitle(self, hp_tier):
        statusText = self.tr("Status: ") + f"{settings.TIER_NAMES[hp_tier]}"
        self.statLabel.setText(statusText)


    def _show_right_menu(self):
        """
        展示右键菜单
        :return:
        """
        # 光标位置弹出菜单
        self.menu.popup(QCursor.pos())

    def _show_Staus_menu(self):
        """
        展示右键菜单
        :return:
        """
        # 光标位置弹出菜单
        self.StatMenu.popup(QCursor.pos()-QPoint(0, 275))

    def _add_pet(self, pet_name: str):
        pet_acc = {'name':'pet', 'pet_name':pet_name}
        self.setup_acc.emit(pet_acc, int(self.current_screen.topLeft().x() + random.uniform(0.4,0.7)*self.screen_width), self.pos().y())
        #for test
        #self.setup_acc.emit(pet_acc, int(random.uniform(0.69,0.7)*self.screen_width), self.pos().y())

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
        self.workers['Animation'].hpchange(settings.pet_data.hp_tier, None)
        self.workers['Animation'].fvchange(settings.pet_data.fv_lvl)
        # cancel default animation if any
        defaul_act = settings.defaultAct[self.curr_pet_name]
        if defaul_act is not None:
            self._set_defaultAct(self, defaul_act)
        self._update_fvlock()
        # add default animation back
        if defaul_act in [acti.text() for acti in self.defaultAct_menu.actions()]:
            self._set_defaultAct(self, defaul_act)

        # Update BackPack
        ################### Task in need
        ##### self._init_Inventory()
        ###################
        self.refresh_bag.emit()

        self._set_Statusmenu()

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
        #self.show_controlPanel.emit()
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
        self.workers['Animation'].hpchange(settings.pet_data.hp_tier, None)
        self.workers['Animation'].fvchange(settings.pet_data.fv_lvl)

        # Update Backpack
        ################### Task in need
        ##### self._init_Inventory()
        ###################
        self.refresh_bag.emit()

        self.change_note.emit()
        self.repaint()
        self.runAnimation()
        self.runInteraction()

        self._setup_ui()
        self.workers['Scheduler'].send_greeting()
        # Compensate items if any
        self._setup_compensate()

    def init_conf(self, pet_name: str) -> None:
        """
        初始化宠物窗口配置
        :param pet_name: 宠物名称
        :return:
        """
        self.curr_pet_name = pet_name
        settings.petname = pet_name
        pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, pic_dict) #settings.size_factor)
        self.margin_value = 0 #0.1 * max(self.pet_conf.width, self.pet_conf.height) # 用于将widgets调整到合适的大小

        self._set_menu(self.pets)
        self._set_Statusmenu()
        self._set_tray()


    def _setup_ui(self):

        #bar_width = int(max(100*settings.size_factor, 0.5*self.pet_conf.width))
        bar_width = int(max(100, 0.5*self.pet_conf.width))
        bar_width = int(min(200, bar_width))
        self.tomato_time.setFixedSize(bar_width, statbar_h)
        self.focus_time.setFixedSize(bar_width, statbar_h)

        self.reset_size()

        settings.previous_img = settings.current_img
        settings.current_img = self.pet_conf.default.images[0] #list(pic_dict.values())[0]
        settings.previous_anchor = settings.current_anchor
        settings.current_anchor = self.pet_conf.default.anchor
        self.set_img()
        self.border = self.pet_conf.width/2

        
        # 初始位置
        #screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = self.screen_width #screen_geo.width()
        work_height = self.screen_height #screen_geo.height()
        x = self.current_screen.topLeft().x() + int(screen_width*0.8)
        y = self.current_screen.topLeft().y() + work_height - self.height()
        self.move(x,y)

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
            self.tray = SystemTray(self.menu, self) #QSystemTrayIcon(self)
            self.tray.setIcon(QIcon(os.path.join(basedir, 'res/icons/icon.png')))
            #self.tray.setContextMenu(self.menu)
            self.tray.show()
            #self.tray.showMessage("Input Something", "Enter your notification tittle and message", msecs=3000)
        else:
            self.tray.setMenu(self.menu)
            self.tray.show()

    def reset_size(self):
        #self.setFixedSize((max(self.pet_hp.width()+statbar_h,self.pet_conf.width)+self.margin_value)*max(1.0,settings.tunable_scale),
        #                  (self.margin_value+4*statbar_h+self.pet_conf.height)*max(1.0, settings.tunable_scale))
        self.setFixedSize( int(max(self.tomato_time.width()+statbar_h,self.pet_conf.width*settings.tunable_scale)),
                           int(statbar_h+self.pet_conf.height*settings.tunable_scale)
                         )

        self.label.setFixedWidth(self.width())

        # 初始位置
        #screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = self.screen_width #screen_geo.width()
        work_height = self.screen_height #screen_geo.height()
        x = self.pos().x() + settings.current_anchor[0]
        if settings.set_fall == 1:
            y = self.current_screen.topLeft().y() + work_height-self.height()+settings.current_anchor[1]
        else:
            y = self.pos().y() + settings.current_anchor[1]
        # make sure that for all stand png, png bottom is the ground
        #self.floor_pos = work_height-self.height()
        self.floor_pos = self.current_screen.topLeft().y() + work_height - self.height()
        self.move(x,y)
        self.move_sig.emit(self.pos().x()+self.width()//2, self.pos().y()+self.height())

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
        self.label.resize(width_tmp, height_tmp)
        self.label.setPixmap(QPixmap.fromImage(settings.current_img.scaled(width_tmp, height_tmp,
                                                                           aspectMode=Qt.KeepAspectRatio,
                                                                           mode=Qt.SmoothTransformation)))
        #print(self.size())
        self.image = settings.current_img

    def _compensate_rewards(self):
        self.compensate_rewards.emit()

    def register_notification(self, note_type, message):

        self.setup_notification.emit(note_type, message)


    def register_accessory(self, accs):
        self.setup_acc.emit(accs, self.pos().x()+self.width()//2, self.pos().y()+self.height())


    def _change_status(self, status, change_value, from_mod='Scheduler', send_note=False):
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

    def _hp_updated(self, hp):
        self.hp_updated.emit(hp)

    def _fv_updated(self, fv, fv_lvl):
        self.fv_updated.emit(fv, fv_lvl)


    def _change_time(self, status, timeleft):
        if status not in ['tomato','tomato_start','tomato_rest','tomato_end',
                          'focus_start','focus','focus_end']:
            return
        elif status == 'tomato_start':
            self.tomato_time.setMaximum(25)
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
            self.tomato_window.newTomato()
        elif status == 'tomato_rest':
            self.tomato_time.setMaximum(5)
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
        elif status == 'tomato':
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
        elif status == 'tomato_end':
            self.tomato_time.setValue(0)
            self.tomato_time.setFormat('')
            self.tomato_window.endTomato()
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
            self.focus_window.endFocus()

    def use_item(self, item_name):
        # 食物
        if self.items_data.item_dict[item_name]['item_type']=='consumable':
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('use_item', item_name)

        # 附件物品
        elif item_name in self.pet_conf.act_name or item_name in self.pet_conf.acc_name:
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('use_clct', item_name)

        # 对话物品
        elif self.items_data.item_dict[item_name]['item_type']=='dialogue':
            if item_name in self.pet_conf.msg_dict:
                accs = {'name':'dialogue', 'msg_dict':self.pet_conf.msg_dict[item_name]}
                x = self.pos().x()+self.width()//2
                y = self.pos().y()+self.height()
                self.setup_acc.emit(accs, x, y)
                return

        # 系统附件物品
        elif item_name in self.sys_conf.acc_name:
            accs = self.sys_conf.accessory_act[item_name]
            x = self.pos().x()+self.width()//2
            y = self.pos().y()+self.height()
            self.setup_acc.emit(accs, x, y)

        # 鼠标挂件
        elif item_name in self.sys_conf.mouseDecor:
            accs = {'name':'mouseDecor', 'config':self.sys_conf.mouseDecor[item_name]}
            x = self.pos().x()+self.width()//2
            y = self.pos().y()+self.height()
            self.setup_acc.emit(accs, x, y)
        else:
            pass


        # 使用物品 改变数值
        self._change_status('hp', self.items_data.item_dict[item_name]['effect_HP'], from_mod='inventory', send_note=True)
        if item_name in self.pet_conf.item_favorite:
            self._change_status('fv',
                                int(self.items_data.item_dict[item_name]['effect_FV']*self.pet_conf.item_favorite[item_name]),
                                from_mod='inventory', send_note=True)

        elif item_name in self.pet_conf.item_dislike:
            self._change_status('fv', 
                                int(self.items_data.item_dict[item_name]['effect_FV']*self.pet_conf.item_dislike[item_name]),
                                from_mod='inventory', send_note=True)

        else:
            self._change_status('fv', self.items_data.item_dict[item_name]['effect_FV'], from_mod='inventory', send_note=True)

    def add_item(self, n_items, item_names=[]):
        self.addItem_toInven.emit(n_items, item_names)

    def patpat(self):
        # 摸摸动画
        if self.workers['Interaction'].interact != 'patpat':
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('patpat')

        # 概率触发浮动的心心
        prob_num_0 = random.uniform(0, 1)
        if prob_num_0 < sys_pp_heart:
            try:
                accs = self.sys_conf.accessory_act['heart']
            except:
                return
            x = self.pos().x()+self.width()//2 + random.uniform(-0.25, 0.25) * self.label.width()
            y = self.pos().y()+self.height()-0.8*self.label.height() + random.uniform(0, 1) * 10
            self.setup_acc.emit(accs, x, y)

        elif prob_num_0 > sys_pp_item:
            self.addItem_toInven.emit(1, [])
            #print('物品掉落！')

        if prob_num_0 > sys_pp_audio:
            #随机语音
            self.register_notification('random', '')

    def item_drop_anim(self, item_name):
        item = self.items_data.item_dict[item_name]
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

    def _show_controlPanel(self):
        self.show_controlPanel.emit()

    def _show_dashboard(self):
        self.show_dashboard.emit()

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
        #if self.tomato_clock.text()=="番茄时钟":
            #self.tomato_clock.setText("取消番茄时钟")
            #self.tomato_window.hide()
        self.workers['Scheduler'].add_tomato(n_tomato=int(nt))
        self.tomatoicon.show()
        self.tomato_time.show()

    def cancel_tomato(self):
        self.workers['Scheduler'].cancel_tomato()
        #self.tomatoicon.hide()
        #self.tomato_time.hide()

    def change_tomato_menu(self):
        #if self.tomato_clock.text()=="取消番茄时钟":
        #    self.tomato_clock.setText("番茄时钟")
        self.tomatoicon.hide()
        self.tomato_time.hide()

    def show_focus(self):
        if self.focus_window.isVisible():
            self.focus_window.hide()
        
        else:
            self.focus_window.move(max(self.current_screen.topLeft().y(),self.pos().x()-self.focus_window.width()//2),
                                   max(self.current_screen.topLeft().y(),self.pos().y()-self.focus_window.height()))
            self.focus_window.show()
        '''
        elif self.focus_clock.text()=="取消专注任务":
            self.focus_clock.setText("专注时间")
            self.workers['Scheduler'].cancel_focus()
            self.focusicon.hide()
            self.focus_time.hide()
        '''

    def run_focus(self, task, hs, ms):
        #sender = self.sender()
        #print(self.focus_clock.text())
        #if self.focus_clock.text()=="专注时间":
            #self.focus_clock.setText("取消专注任务")
            #self.focus_window.hide()
        if task == 'range':
            if hs==0 and ms==0:
                return
            self.workers['Scheduler'].add_focus(time_range=[hs,ms])
        elif task == 'point':
            self.workers['Scheduler'].add_focus(time_point=[hs,ms])
        self.focusicon.show()
        self.focus_time.show()
        #else:
        #    self.focus_clock.setText("专注时间")
        #    self.workers['Scheduler'].cancel_focus()

    def pause_focus(self, state):
        if state: # 暂停
            self.workers['Scheduler'].pause_focus()
        else: # 继续
            self.workers['Scheduler'].resume_focus(int(self.focus_time.value()), int(self.focus_time.maximum()))


    def cancel_focus(self):
        self.workers['Scheduler'].cancel_focus(int(self.focus_time.maximum()-self.focus_time.value()))

    def change_focus_menu(self):
        #if self.focus_clock.text()=="取消专注任务":
            #self.focus_clock.setText("专注时间")
        self.focusicon.hide()
        self.focus_time.hide()


    def show_remind(self):
        if self.remind_window.isVisible():
            self.remind_window.hide()
        else:
            self.remind_window.move(max(self.current_screen.topLeft().y(),self.pos().x()-self.remind_window.width()//2),
                                    max(self.current_screen.topLeft().y(),self.pos().y()-self.remind_window.height()))
            self.remind_window.show()

    def run_remind(self, task_type, hs=0, ms=0, texts=''):
        if task_type == 'range':
            self.workers['Scheduler'].add_remind(texts=texts, time_range=[hs,ms])
        elif task_type == 'point':
            self.workers['Scheduler'].add_remind(texts=texts, time_point=[hs,ms])
        elif task_type == 'repeat_interval':
            self.workers['Scheduler'].add_remind(texts=texts, time_range=[hs,ms], repeat=True)
        elif task_type == 'repeat_point':
            self.workers['Scheduler'].add_remind(texts=texts, time_point=[hs,ms], repeat=True)

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
        

    '''
    def show_backup_manager(self):
        self.backupManager = BackupManager()
        # BackupManager.setAttribute(BackupManager, QtCore.Qt.AA_EnableHighDpiScaling)
        if sys.platform == 'win32':
            self.backupManager.setWindowFlags(
                Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            self.backupManager.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        self.backupManager.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        cardShadowSE = QtWidgets.QGraphicsDropShadowEffect(self.backupManager)
        cardShadowSE.setColor(QColor(189, 167, 165))
        cardShadowSE.setOffset(0, 0)
        cardShadowSE.setBlurRadius(20)
        self.backupManager.setGraphicsEffect(cardShadowSE)

        # 支持HDPI
        self.backupManager.setGeometry(0, 0, int(800 * size_factor), int(600 * size_factor))
        self.backupManager.dialogContainer.setGeometry(int(12 * size_factor), int(12 * size_factor), int(800 * size_factor - 24 * size_factor), int(600 * size_factor - 24 * size_factor))
        self.backupManager.menuBarSE.setMaximumHeight(int(24 * size_factor))
        self.backupManager.menuBarSE.setStyleSheet('#menuBarSE{ background: rgb(241,234,235); border: 1px solid rgb(241,234,235); border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; height: ' + str(800 * size_factor) + 'px;}')
        self.backupManager.closeApp.setMaximumHeight(int(16 * size_factor))
        self.backupManager.closeApp.setMaximumWidth(int(16 * size_factor))
        self.backupManager.closeApp.setStyleSheet('QPushButton{ height: ' + str(16 * size_factor) + 'px; width: ' + str(16 * size_factor) + 'px; background: rgb(241,234,235); border: 0px solid rgb(241,234,235); border-radius: ' + str(5 * size_factor) +'px; color: #534343; font-size: ' + str(14 * size_factor) + 'px; border-image: url(:/icons/res/close.svg); } QPushButton:Hover{ font-weight: bold; background: rgb(231,226,226); color: #211a1a; } QPushButton:Pressed{ font-weight: bold; background: #ffdad9; color: #2d1516; } ')
        self.backupManager.titleBar.setStyleSheet('#titleBar{ background: rgb(241,234,235); border: 1px solid rgb(241,234,235); height: ' + str(64 * size_factor) + 'px;}')
        self.backupManager.appTitle.setStyleSheet('#appTitle{ font-size: ' + str(12 * 1) + 'pt; color: #1f1f1f; font-weight: bold; background: transparent; font: ' + str(12 * 1) + 'pt "黑体"; }')
        self.backupManager.verticalLayout_4.setContentsMargins(int(24 * size_factor), int(24 * size_factor), int(24 * size_factor), int(24 * size_factor))
        self.backupManager.savesDesc.setStyleSheet('QLabel{ font-size: ' + str(10.5 * 1) + 'pt; color: #211a1a; font: ' + str(10.5 * 1) + 'pt "黑体"; }')
        self.backupManager.setSaveModeRead.setStyleSheet('QPushButton{ height: ' + str(24 * size_factor) + 'px; background: rgb(241,234,235); border: 0px solid rgb(241,234,235); border-radius: 5px; color: #534343; font-size: ' + str(10.5 * 1) + 'pt; font: ' + str(10.5 * 1) + 'pt "黑体"; } QPushButton:Hover{ font-weight: bold; background: rgb(231,226,226); color: #211a1a; } QPushButton:Pressed{ font-weight: bold; background: #ffdad9; color: #2d1516; } QPushButton:Checked{ font-weight: bold; background: #ffdad9; color: #2d1516; }')
        self.backupManager.setSaveModeWrite.setStyleSheet('QPushButton{ height: ' + str(24 * size_factor) + 'px; background: rgb(241,234,235); border: 0px solid rgb(241,234,235); border-radius: 5px; color: #534343; font-size: ' + str(10.5 * 1) + 'pt; font: ' + str(10.5 * 1) + 'pt "黑体"; } QPushButton:Hover{ font-weight: bold; background: rgb(231,226,226); color: #211a1a; } QPushButton:Pressed{ font-weight: bold; background: #ffdad9; color: #2d1516; } QPushButton:Checked{ font-weight: bold; background: #ffdad9; color: #2d1516; }')
        self.backupManager.saveSlot1.setStyleSheet('QPushButton{ min-height: ' + str(32 * size_factor) + 'px; background: rgb(241,234,235); border: 0px solid rgb(241,234,235); border-radius: 5px; color: #534343; font-size: ' + str(10.5 * 1) + 'pt; font: ' + str(10.5 * 1) + 'pt "黑体"; } QPushButton:Hover{ font-weight: bold; background: rgb(231,226,226); color: #211a1a; } QPushButton:Pressed{ font-weight: bold; background: #ffdad9; color: #2d1516; } QPushButton:Checked{ font-weight: bold; background: #ffdad9; color: #2d1516; }')
        self.backupManager.saveSlot2.setStyleSheet('QPushButton{ min-height: ' + str(32 * size_factor) + 'px; background: rgb(241,234,235); border: 0px solid rgb(241,234,235); border-radius: 5px; color: #534343; font-size: ' + str(10.5 * 1) + 'pt; font: ' + str(10.5 * 1) + 'pt "黑体"; } QPushButton:Hover{ font-weight: bold; background: rgb(231,226,226); color: #211a1a; } QPushButton:Pressed{ font-weight: bold; background: #ffdad9; color: #2d1516; } QPushButton:Checked{ font-weight: bold; background: #ffdad9; color: #2d1516; }')
        self.backupManager.saveSlot3.setStyleSheet('QPushButton{ min-height: ' + str(32 * size_factor) + 'px; margin-top: -3px; background: rgb(241,234,235); border: 0px solid rgb(241,234,235); border-radius: 5px; color: #534343; font-size: ' + str(10.5 * 1) + 'pt; font: ' + str(10.5 * 1) + 'pt "黑体"; } QPushButton:Hover{ font-weight: bold; background: rgb(231,226,226); color: #211a1a; } QPushButton:Pressed{ font-weight: bold; background: #ffdad9; color: #2d1516; } QPushButton:Checked{ font-weight: bold; background: #ffdad9; color: #2d1516; }')
        self.backupManager.navBar.setVisible(0)
        # 底部导航栏启用时请注释掉下面这个
        self.backupManager.appFrame.setStyleSheet('#appFrame{background: #fff; border: 0px solid #fff; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; border-top-left-radius: 0px; border-top-right-radius: 0px;}')
        self.backupManager.appContainer.setStyleSheet('#appContainer{background: #fff; border: 0px solid #fff; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; border-top-left-radius: 0px; border-top-right-radius: 0px;}')

        # 好了 注释到这里就可以了 别把下面也注释了
        self.backupManager.show()
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

        # Start the thread
        self.threads['Animation'].start()
        self.threads['Animation'].setTerminationEnabled()


    def hpchange(self, hp_tier, direction):
        self.workers['Animation'].hpchange(hp_tier, direction)
        self.hptier_changed_main_note.emit(hp_tier, direction)
        self._update_statusTitle(hp_tier)

    def fvchange(self, fv_lvl):
        if fv_lvl == -1:
            self.fvlvl_changed_main_note.emit(fv_lvl)
        else:
            self.workers['Animation'].fvchange(fv_lvl)
            self.fvlvl_changed_main_note.emit(fv_lvl)
            self.fvlvl_changed_main_inve.emit(fv_lvl)
            self._update_fvlock()

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
            new_x, new_y = self.limit_in_screen(new_x, new_y)

        self.move(new_x, new_y)


    def switch_screen(self, screen):
        self.current_screen = screen.geometry()
        settings.current_screen = screen
        self.screen_geo = screen.availableGeometry() #screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()
        self.floor_pos = self.current_screen.topLeft().y() + self.screen_height -self.height()


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
        elif new_y > self.floor_pos+settings.current_anchor[1]:
            #surpass_y = 'Bottom'
            new_y = self.floor_pos+settings.current_anchor[1]

        return new_x, new_y


    def _show_act(self, act_name):
        self.workers['Animation'].pause()
        self.workers['Interaction'].start_interact('animat', act_name)

    def _show_acc(self, acc_name):
        self.workers['Animation'].pause()
        self.workers['Interaction'].start_interact('anim_acc', acc_name)

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


'''
def text_wrap(texts):
    n_char = len(texts)
    n_line = int(n_char//7 + 1)
    texts_wrapped = ''
    for i in range(n_line):
        texts_wrapped += texts[(7*i):min((7*i + 7),n_char)] + '\n'
    texts_wrapped = texts_wrapped.rstrip('\n')

    return texts_wrapped


if __name__ == '__main__':
    # 加载所有角色, 启动应用并展示第一个角色
    pets = read_json(os.path.join(basedir, 'res/role/pets.json'))
    app = QApplication(sys.argv)
    p = PetWidget(pets=pets)
    sys.exit(app.exec_())
'''



