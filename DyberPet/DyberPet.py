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

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QEvent
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontDatabase

from DyberPet.conf import *
from DyberPet.utils import *
from DyberPet.modules import *
from DyberPet.extra_windows import *

# version
dyberpet_version = '0.2.1'

if platform == 'win32':
    basedir = ''
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-1])

vf = open(os.path.join(basedir,'data/version'), 'w')
vf.write(dyberpet_version)
vf.close()

# initialize settings
import DyberPet.settings as settings
settings.init()

# some UI size parameters
status_margin = int(3 * settings.size_factor) #int(3 * resolution_factor)
statbar_h = int(15 * settings.size_factor) #int(15 * resolution_factor)


# system config
sys_hp_tiers = [0,50,80,100] #Line 52
sys_hp_interval = 2 #Line 485
sys_lvl_bar = [20, 120, 300, 600, 1200, 1800, 2400, 3200] #Line 134 sys_lvl_bar = [20, 200, 400, 800, 2000, 5000, 8000]
sys_pp_heart = 0.8 #Line 1001
sys_pp_item = 0.98 #Line 1010
sys_pp_audio = 0.8 #Line 1014


# Pet HP progress bar
class DP_HpBar(QProgressBar):
    hptier_changed = pyqtSignal(int, str, name='hptier_changed')

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

        elif hp_tier < settings.pet_data.hp_tier:
            self.hptier_changed.emit(hp_tier,'down')
            settings.pet_data.change_hp(self.hp_inner, hp_tier)
            
        else:
            settings.pet_data.change_hp(self.hp_inner) #.hp = current_value

        return int(after_value - before_value)



# Favorability Progress Bar
class DP_FvBar(QProgressBar):
    fvlvl_changed = pyqtSignal(int, name='fvlvl_changed')

    def __init__(self, *args, **kwargs):

        super(DP_FvBar, self).__init__(*args, **kwargs)

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

        else: #好感度升级
            if self.fvlvl == (len(self.lvl_bar)-1):
                current_value = self.maximum()
                if current_value == prev_value:
                    return 0
                self.setFormat('lv%s: %s/%s'%(int(self.fvlvl),int(current_value),self.points_to_lvlup))
                self.setValue(current_value)
                after_value = current_value

                settings.pet_data.change_fv(current_value, self.fvlvl)
                #告知动画模块、通知模块
                self.fvlvl_changed.emit(-1)

            else:
                after_value = current_value
                current_value += -self.maximum()
                self.fvlvl += 1
                self.points_to_lvlup = self.lvl_bar[self.fvlvl]
                self.setMinimum(0)
                self.setMaximum(self.points_to_lvlup)
                self.setFormat('lv%s: %s/%s'%(int(self.fvlvl),int(current_value),self.points_to_lvlup))
                self.setValue(current_value)

                settings.pet_data.change_fv(current_value, self.fvlvl)
                #告知动画模块、通知模块
                self.fvlvl_changed.emit(self.fvlvl)

        return int(after_value - before_value)




# Pet Object
class PetWidget(QWidget):
    setup_notification = pyqtSignal(str, str, name='setup_notification')
    addItem_toInven = pyqtSignal(int, list, name='addItem_toInven')
    fvlvl_changed_main_note = pyqtSignal(int, name='fvlvl_changed_main_note')
    fvlvl_changed_main_inve = pyqtSignal(int, name='fvlvl_changed_main_inve')
    hptier_changed_main_note = pyqtSignal(int, str, name='hptier_changed_main_note')

    setup_acc = pyqtSignal(dict, int, int, name='setup_acc')
    change_note = pyqtSignal(name='change_note')

    move_sig = pyqtSignal(int, int, name='move_sig')
    acc_withdrawed = pyqtSignal(str, name='acc_withdrawed')

    def __init__(self, parent=None, curr_pet_name='', pets=(), screens=[]):
        """
        宠物组件
        :param parent: 父窗口
        :param curr_pet_name: 当前宠物名称
        :param pets: 全部宠物列表
        """
        super(PetWidget, self).__init__(parent, flags=Qt.WindowFlags())
        self.pets = settings.pets
        self.curr_pet_name = settings.default_pet
        #self.pet_conf = PetConfig()

        self.image = None
        self.tray = None

        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_moving = False
        self.mouse_drag_pos = self.pos()

        # Screen info
        settings.screens = screens #[i.geometry() for i in screens]
        self.current_screen = settings.screens[0].geometry()
        settings.current_screen = settings.screens[0]
        self.screen_geo = QDesktopWidget().availableGeometry() #screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()

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
        self.timer = QTimer(singleShot=True, timeout=self.compensate_rewards)
        self.timer.start(10000)

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
            self.customContextMenuRequested.connect(self._show_right_menu)
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
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        # 是否跟随鼠标
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

    def ontop_update(self):
        if settings.on_top_hint:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()


    def _init_ui(self):
        #动画 --------------------------------------------------------
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.label.installEventFilter(self)
        #self.label.setStyleSheet("border : 2px solid blue")

        # 系统动画组件
        self.sys_src = _load_all_pic('sys')
        self.sys_conf = PetConfig.init_sys(self.sys_src, 1) #settings.size_factor)
        # ------------------------------------------------------------

        #数值 --------------------------------------------------------
        self.status_frame = QFrame()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)

        # 饱食度
        h_box1 = QHBoxLayout()
        h_box1.setContentsMargins(0,status_margin,0,0)
        h_box1.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.hpicon = QLabel(self)
        self.hpicon.setFixedSize(statbar_h,statbar_h)
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/HP_icon.png'))
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(QPixmap.fromImage(image))
        self.hpicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box1.addWidget(self.hpicon)
        self.pet_hp = DP_HpBar(self, minimum=0, maximum=100, objectName='PetHP')
        h_box1.addWidget(self.pet_hp)

        # 好感度
        h_box2 = QHBoxLayout()
        h_box2.setContentsMargins(0,status_margin,0,0)
        h_box2.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.emicon = QLabel(self)
        self.emicon.setFixedSize(statbar_h,statbar_h)
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/Fv_icon.png'))
        self.emicon.setScaledContents(True)
        self.emicon.setPixmap(QPixmap.fromImage(image))
        self.emicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box2.addWidget(self.emicon)
        self.pet_fv = DP_FvBar(self, minimum=0, maximum=100, objectName='PetEM')
        self.pet_hp.hptier_changed.connect(self.hpchange)
        self.pet_fv.fvlvl_changed.connect(self.fvchange)
        h_box2.addWidget(self.pet_fv)

        self.pet_hp.init_HP(settings.pet_data.hp, sys_hp_interval) #2)
        self.pet_fv.init_FV(settings.pet_data.fv, settings.pet_data.fv_lvl)
        self.hpicon.adjustSize()

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
        self.focus_time = QProgressBar(self, minimum=0, maximum=100, objectName='PetFC')
        self.focus_time.setFormat('')
        self.focus_time.setValue(100)
        self.focus_time.setAlignment(Qt.AlignCenter)
        self.focus_time.hide()
        self.focusicon.hide()
        h_box4.addWidget(self.focus_time)

        vbox.addLayout(h_box3)
        vbox.addLayout(h_box4)
        vbox.addLayout(h_box1)
        vbox.addLayout(h_box2)

        self.status_frame.setLayout(vbox)
        #self.status_frame.setStyleSheet("border : 2px solid blue")
        self.status_frame.setContentsMargins(0,0,0,0)
        #self.status_box.addWidget(self.status_frame)
        self.status_frame.hide()
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

        #self.setStyleSheet("border : 2px solid blue")

        # 初始化背包
        self.items_data = ItemData()
        self.inventory_window = Inventory(self.items_data)
        self.inventory_window.close_inventory.connect(self.show_inventory)
        self.inventory_window.use_item_inven.connect(self.use_item)
        self.inventory_window.item_note.connect(self.register_notification)
        self.inventory_window.item_anim.connect(self.item_drop_anim)
        self.addItem_toInven.connect(self.inventory_window.add_items)
        self.acc_withdrawed.connect(self.inventory_window.acc_withdrawed)
        self.fvlvl_changed_main_inve.connect(self.inventory_window.fvchange)

        # Settings
        self.setting_window = SettingUI()
        self.setting_window.close_setting.connect(self.show_settings)
        self.setting_window.scale_changed.connect(self.set_img)
        self.setting_window.scale_changed.connect(self.reset_size)
        self.setting_window.ontop_changed.connect(self.ontop_update)

        self.showing_comp = 0

        '''
        self.tomato_time.setFormat('无')
        self.tomato_time.setValue(0)
        self.tomato_time.hide()
        self.tomatoicon.hide()

        self.focus_time.setFormat('无')
        self.focus_time.setValue(0)
        self.focus_time.hide()
        self.focusicon.hide()
        '''



    def _set_menu(self, pets=()):
        """
        初始化菜单
        """
        menu = QMenu(self)

        # 背包
        self.open_invent = QAction('打开背包', menu)
        self.open_invent.triggered.connect(self.show_inventory)
        menu.addAction(self.open_invent)

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


        # 召唤同伴
        self.companion_menu = QMenu(menu)
        self.companion_menu.setTitle('召唤同伴')
        add_acts = [_build_act(name, self.companion_menu, self._add_pet) for name in pets]
        self.companion_menu.addActions(add_acts)
        if len(self.pet_conf.subpet.keys()) != 0:
            add_acts_sub = [_build_act(name, self.companion_menu, self._add_pet) for name in self.pet_conf.subpet if self.pet_conf.subpet[name]['fv_lock']<=settings.pet_data.fv_lvl]
            self.companion_menu.addActions(add_acts_sub)
        menu.addMenu(self.companion_menu)


        # 计划任务
        self.task_menu = QMenu(menu)
        self.task_menu.setTitle('计划任务')
        self.tomato_clock = QAction('番茄时钟', self.task_menu)
        self.tomato_clock.triggered.connect(self.show_tomato)
        self.task_menu.addAction(self.tomato_clock)
        self.focus_clock = QAction('专注时间', self.task_menu)
        self.focus_clock.triggered.connect(self.show_focus)
        self.task_menu.addAction(self.focus_clock)
        self.remind_clock = QAction('提醒我', self.task_menu)
        self.remind_clock.triggered.connect(self.show_remind)
        self.task_menu.addAction(self.remind_clock)
        menu.addMenu(self.task_menu)

        menu.addSeparator()

        # 切换角色子菜单
        self.change_menu = QMenu(menu)
        self.change_menu.setTitle('切换角色')
        change_acts = [_build_act(name, self.change_menu, self._change_pet) for name in pets]
        self.change_menu.addActions(change_acts)
        menu.addMenu(self.change_menu)



        # 开启/关闭掉落
        if settings.set_fall == 1:
            self.switch_fall = QAction('禁用掉落', menu)
        else:
            self.switch_fall = QAction('开启掉落', menu)
        self.switch_fall.triggered.connect(self.fall_onoff)
        menu.addAction(self.switch_fall)

        # 陪伴天数
        if self.showing_comp == 1:
            self.open_compday = QAction('关闭陪伴天数', menu)
        else:
            self.open_compday = QAction('显示陪伴天数', menu)
        #self.open_compday = QAction('显示陪伴天数', menu)
        self.open_compday.triggered.connect(self.show_compday)
        menu.addAction(self.open_compday)

        # Settings
        self.open_setting = QAction('设置', menu)
        self.open_setting.triggered.connect(self.show_settings)
        menu.addAction(self.open_setting)

        menu.addSeparator()

        # 快速访问
        web_file = os.path.join(basedir, 'res/role/sys/webs.json')
        if os.path.isfile(web_file):
            web_dict = json.load(open(web_file, 'r', encoding='UTF-8'))

            self.web_menu = QMenu(menu)
            self.web_menu.setTitle('快速访问')

            web_acts = [_build_act_param(name, web_dict[name], self.web_menu, self.open_web) for name in web_dict]
            self.web_menu.addActions(web_acts)
            menu.addMenu(self.web_menu)


        # 关于
        
        self.about_menu = QMenu(menu)
        self.about_menu.setTitle('关于')
        global dyberpet_version
        self.about_menu.addAction('DyberPet v%s'%dyberpet_version)
        self.about_menu.addSeparator()
        webpage = QAction('GitHub@ChaozhongLiu', self.about_menu)
        webpage.triggered.connect(lambda: webbrowser.open('https://github.com/ChaozhongLiu/DyberPet'))
        self.about_menu.addAction(webpage)
        menu.addMenu(self.about_menu)
        

        # 退出动作
        self.quit_act = QAction('退出', menu)
        self.quit_act.triggered.connect(self.quit)
        menu.addAction(self.quit_act)
        self.menu = menu

    def _update_fvlock(self):

        # 更新动作
        select_acts = []
        for i in range(len(self.pet_conf.act_name)):
            if self.pet_conf.act_name[i] is None:
                continue

            if self.pet_conf.act_type[i][1] == settings.pet_data.fv_lvl:
                select_acts.append(_build_act(self.pet_conf.act_name[i], self.act_menu, self._show_act))

        if len(select_acts) > 0:
            self.act_menu.addActions(select_acts)

        select_accs = []
        for name_i in self.pet_conf.acc_name:
            if self.pet_conf.accessory_act[name_i]['act_type'][1] == settings.pet_data.fv_lvl:
                select_accs.append(_build_act(name_i, self.act_menu, self._show_acc))

        if len(select_accs) > 0:
            self.act_menu.addActions(select_accs)
        #menu.addMenu(self.act_menu)

        # 更新同伴
        add_pets = []
        for name in self.pet_conf.subpet:
            if self.pet_conf.subpet[name]['fv_lock'] == settings.pet_data.fv_lvl:
                add_pets.append(_build_act(name, self.companion_menu, self._add_pet))

        if len(add_pets) > 0:
            self.companion_menu.addActions(add_pets)

    def _show_right_menu(self):
        """
        展示右键菜单
        :return:
        """
        # 光标位置弹出菜单
        self.menu.popup(QCursor.pos())

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

    def _change_pet(self, pet_name: str) -> None:
        """
        改变宠物
        :param pet_name: 宠物名称
        :return:
        """
        if self.curr_pet_name == pet_name:
            return
        # stop animation thread and start again
        self.stop_thread('Animation')
        self.stop_thread('Interaction')

        self.init_conf(pet_name)
        self.change_note.emit()
        self.repaint()
        self.runAnimation()
        self.runInteraction()

        self._setup_ui()
        self.workers['Scheduler'].send_greeting()

    def init_conf(self, pet_name: str) -> None:
        """
        初始化宠物窗口配置
        :param pet_name: 宠物名称
        :return:
        """
        self.curr_pet_name = pet_name
        pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, pic_dict, 1) #settings.size_factor)

        self.margin_value = 0.1 * max(self.pet_conf.width, self.pet_conf.height) # 用于将widgets调整到合适的大小

        settings.petname = pet_name

        self._set_menu(self.pets)
        self._set_tray()


    def _setup_ui(self):

        self.pet_hp.setFixedSize(int(max(100*settings.size_factor, 0.5*self.pet_conf.width)), statbar_h)
        self.pet_fv.setFixedSize(int(max(100*settings.size_factor, 0.5*self.pet_conf.width)), statbar_h)
        self.tomato_time.setFixedSize(int(max(100*settings.size_factor, 0.5*self.pet_conf.width)), statbar_h)
        self.focus_time.setFixedSize(int(max(100*settings.size_factor, 0.5*self.pet_conf.width)), statbar_h)

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


    def eventFilter(self, object, event):
        if event.type() == QEvent.Enter:
            self.status_frame.show()
            return True
        elif event.type() == QEvent.Leave:
            self.status_frame.hide()
        return False


    def _set_tray(self) -> None:
        """
        设置最小化托盘
        :return:
        """
        if self.tray is None:
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(QIcon(os.path.join(basedir, 'res/icons/icon.png')))
            self.tray.setContextMenu(self.menu)
            self.tray.show()
            #self.tray.showMessage("Input Something", "Enter your notification tittle and message", msecs=3000)
        else:
            self.tray.setContextMenu(self.menu)
            self.tray.show()

    def reset_size(self):
        self.setFixedSize((max(self.pet_hp.width()+statbar_h,self.pet_conf.width)+self.margin_value)*max(1.0,settings.tunable_scale),
                          (self.margin_value+4*statbar_h+self.pet_conf.height)*max(1.0, settings.tunable_scale))
        self.label.setFixedWidth(self.width())

        # 初始位置
        #screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = self.screen_width #screen_geo.width()
        work_height = self.screen_height #screen_geo.height()
        x = self.pos().x() + settings.current_anchor[0]
        y = self.current_screen.topLeft().y() + work_height-self.height()+settings.current_anchor[1]
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

        width_tmp = settings.current_img.width()*settings.tunable_scale
        height_tmp = settings.current_img.height()*settings.tunable_scale
        self.label.resize(width_tmp, height_tmp)
        self.label.setPixmap(QPixmap.fromImage(settings.current_img.scaled(width_tmp, height_tmp,
                                                                           aspectRatioMode=Qt.KeepAspectRatio,
                                                                           transformMode=Qt.SmoothTransformation)))
        #print(self.size())
        self.image = settings.current_img

    def compensate_rewards(self):
        self.inventory_window.compensate_rewards()

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
                message = '饱食度 %s'%diff
            else:
                message = '好感度 %s'%diff
            self.register_notification('status_%s'%status, message)


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
        self.close()
        sys.exit()

    def stop_thread(self, module_name):
        self.workers[module_name].kill()
        self.threads[module_name].terminate()
        self.threads[module_name].wait()
        #self.threads[module_name].wait()

    def fall_onoff(self):
        #global set_fall
        sender = self.sender()
        if sender.text()=="禁用掉落":
            sender.setText("开启掉落")
            settings.set_fall=0
        else:
            sender.setText("禁用掉落")
            settings.set_fall=1

    def show_compday(self):
        sender = self.sender()
        if sender.text()=="显示陪伴天数":
            acc = {'name':'compdays', 
                   'height':self.label.height(),
                   'message': "这是%s陪伴你的第 %i 天"%(settings.petname,settings.pet_data.days)}
            sender.setText("关闭陪伴天数")
            x = self.pos().x() + self.width()//2
            y = self.pos().y() + self.height() - self.label.height() - 20*settings.size_factor
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

    def show_settings(self):
        if self.setting_window.isVisible():
            self.setting_window.hide()
        else:
            self.setting_window.move(max(self.current_screen.topLeft().y(), self.pos().x()-self.setting_window.width()//2),
                                    max(self.current_screen.topLeft().y(), self.pos().y()-self.setting_window.height()))
            self.setting_window.show()
    

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

    def fvchange(self, fc_lvl):
        if fc_lvl == -1:
            self.fvlvl_changed_main_note.emit(fc_lvl)
        else:
            self.workers['Animation'].fvchange(fc_lvl)
            self.fvlvl_changed_main_note.emit(fc_lvl)
            self.fvlvl_changed_main_inve.emit(fc_lvl)
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

def _build_act_param(name: str, param: str, parent: QObject, act_func) -> QAction:
    """
    构建改变菜单动作
    :param pet_name: 菜单动作名称
    :param parent 父级菜单
    :param act_func: 菜单动作函数
    :return:
    """
    act = QAction(name, parent)
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


