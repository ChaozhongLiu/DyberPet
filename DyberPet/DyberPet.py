import sys
import time
import math
import random
import inspect
import types
import webbrowser

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QEvent #, QUrl
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontDatabase
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal
#from PyQt5.QtMultimedia import QSoundEffect, QMediaPlayer, QMediaContent

from typing import List

from DyberPet.modules import *
from DyberPet.utils import *
from DyberPet.conf import *
from DyberPet.extra_windows import *
#repaint() to update()?

# version
dyberpet_version = '0.1.11'

import DyberPet.settings as settings
settings.init()


'''
size_factor = 1 #resolution_factor = min(width/2560, height/1440)
screen_scale = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
font_factor = 1 / screen_scale
'''
status_margin = 3 * settings.size_factor #int(3 * resolution_factor)
statbar_h = 15 * settings.size_factor #int(15 * resolution_factor)


class DP_HpBar(QProgressBar):
    hptier_changed = pyqtSignal(int, str, name='hptier_changed')

    def __init__(self, *args, **kwargs):

        super(DP_HpBar, self).__init__(*args, **kwargs)

        self.setFormat('0/100')
        self.setValue(0)
        self.setAlignment(Qt.AlignCenter)
        self.hp_tiers = [0,50,80,100]

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
                #prev_value = self.value()
                #current_value = min(self.value() + change_value, 100)
                new_hp_inner = min(self.hp_inner + change_value*self.interval, self.hp_max)

            elif change_value < 0:
                #prev_value = self.value()
                #current_value = self.value() + change_value
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

        #?????????????????????????????????
        if hp_tier > settings.pet_data.hp_tier:
            self.hptier_changed.emit(hp_tier,'up')
            settings.pet_data.change_hp(self.hp_inner, hp_tier)

        elif hp_tier < settings.pet_data.hp_tier:
            self.hptier_changed.emit(hp_tier,'down')
            settings.pet_data.change_hp(self.hp_inner, hp_tier)
            
        else:
            settings.pet_data.change_hp(self.hp_inner) #.hp = current_value

        return int(after_value - before_value)




class DP_FvBar(QProgressBar):
    fvlvl_changed = pyqtSignal(int, name='fvlvl_changed')

    def __init__(self, *args, **kwargs):

        super(DP_FvBar, self).__init__(*args, **kwargs)

        self.fvlvl = 0
        self.lvl_bar = [20, 120, 300, 600, 1200]
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
        '''
        if from_mod == 'init':
            self.setValue(change_value)
            self.setFormat('lv%s: %s/%s'%(int(self.fvlvl), int(self.value()), int(self.maximum())))
            return 0
        '''

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

        else: #???????????????
            if self.fvlvl == (len(self.lvl_bar)-1):
                current_value = self.maximum()
                if current_value == prev_value:
                    return 0
                self.setFormat('lv%s: %s/%s'%(int(self.fvlvl),int(current_value),self.points_to_lvlup))
                self.setValue(current_value)
                after_value = current_value

                settings.pet_data.change_fv(current_value, self.fvlvl)
                #?????????????????????????????????
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
                #?????????????????????????????????
                self.fvlvl_changed.emit(self.fvlvl)

        return int(after_value - before_value)





class PetWidget(QWidget):
    setup_notification = pyqtSignal(str, str, name='setup_notification')
    addItem_toInven = pyqtSignal(int, list, name='addItem_toInven')
    fvlvl_changed_main_note = pyqtSignal(int, name='fvlvl_changed_main_note')
    fvlvl_changed_main_inve = pyqtSignal(int, name='fvlvl_changed_main_inve')
    hptier_changed_main_note = pyqtSignal(int, str, name='hptier_changed_main_note')

    setup_acc = pyqtSignal(dict, int, int, name='setup_acc')
    change_note = pyqtSignal(name='change_note')
    #sig_rmNote = pyqtSignal(str, name='sig_rmNote')
    #sig_addHeight = pyqtSignal(str, int, name='sig_addHeight')

    def __init__(self, parent=None, curr_pet_name='', pets=()):
        """
        ????????????
        :param parent: ?????????
        :param curr_pet_name: ??????????????????
        :param pets: ??????????????????
        """
        super(PetWidget, self).__init__(parent, flags=Qt.WindowFlags())
        self.pets = pets
        self.curr_pet_name = ''
        self.pet_conf = PetConfig()

        self.image = None
        self.tray = None
        
        '''
        #global size_factor, font_factor, status_margin, statbar_h
        screen_resolution = QDesktopWidget().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        settings.size_factor = math.sqrt(width/2560 * height/1440)
        settings.font_factor *= settings.size_factor
        settings.size_factor *= settings.screen_scale
        settings.status_margin *= settings.size_factor
        settings.statbar_h *= settings.size_factor
        '''

        # ????????????????????????
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

        # Some geo info
        self.screen_geo = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()

        self._init_ui()
        self._init_widget()
        self.init_conf(curr_pet_name if curr_pet_name else pets[0])

        #self._set_menu(pets)
        #self._set_tray()
        self.show()

        # ?????????????????????????????????
        self.threads = {}
        self.workers = {}
        #self.runNotification()
        self.runAnimation()
        self.runInteraction()
        self.runScheduler()
        self._setup_ui(self.pic_dict)
        '''
        self.timer = QTimer()
        self.timer.timeout.connect(self.random_act)
        self.timer.start(self.pet_conf.refresh)
        '''

    def mousePressEvent(self, event):
        """
        ??????????????????
        :param event: ??????
        :return:
        """
        if event.button() == Qt.RightButton:
            # ??????????????????
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_right_menu)
        if event.button() == Qt.LeftButton:
            #print('activated')
            # ??????????????????
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            
            # Left press activates Drag interaction
            #global onfloor,draging
            settings.onfloor=0
            settings.draging=1
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('mousedrag')

            event.accept()
            self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        """
        ??????????????????, ?????????????????????, ????????????
        :param event:
        :return:
        """
        #global mouseposx1,mouseposx2,mouseposx3,mouseposx4,mouseposx5
        #global mouseposy1,mouseposy2,mouseposy3,mouseposy4,mouseposy5

        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            
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
            

            event.accept()

    def mouseReleaseEvent(self, event):
        """
        ??????????????????
        :param event:
        :return:
        """
        if event.button()==Qt.LeftButton:
            #print('released')
            self.is_follow_mouse = False
            self.setCursor(QCursor(Qt.ArrowCursor))

            #global onfloor,draging,playid,set_fall
            #playid=0
            settings.onfloor=0
            settings.draging=0
            if settings.set_fall == 1:
                #global dragspeedx,dragspeedy,mouseposx1,mouseposx3,mouseposy1,mouseposy3,fixdragspeedx,fixdragspeedy
                settings.dragspeedx=(settings.mouseposx1-settings.mouseposx3)/2*settings.fixdragspeedx
                settings.dragspeedy=(settings.mouseposy1-settings.mouseposy3)/2*settings.fixdragspeedy
                settings.mouseposx1=settings.mouseposx3=0
                settings.mouseposy1=settings.mouseposy3=0
                #global fall_right
                if settings.dragspeedx > 0:
                    settings.fall_right = 1
                else:
                    settings.fall_right = 0

            else:
                self._move_customized(0,0)
                #global current_img
                settings.current_img = self.pet_conf.default.images[0]
                self.set_img()
                self.workers['Animation'].resume()


    def _init_widget(self) -> None:
        """
        ???????????????, ????????????????????????
        :return:
        """
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        # ??????????????????
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

    '''
    def _init_img(self, img: QImage) -> None:
        """
        ?????????????????????
        :param img:
        :return:
        """
        #global current_img
        settings.current_img = img
        self.set_img()
        self.resize(self.pet_conf.width, self.pet_conf.height)
        self.show()
    '''

    def _init_ui(self):
        #?????? --------------------------------------------------------
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.label.installEventFilter(self)
        #self.label.setStyleSheet("border : 2px solid blue")
        # ------------------------------------------------------------

        #?????? --------------------------------------------------------
        #self.status_box = QHBoxLayout()
        #self.status_box.setContentsMargins(0,0,0,0)
        #self.status_box.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.status_frame = QFrame()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)

        # ?????????
        h_box1 = QHBoxLayout()
        h_box1.setContentsMargins(0,status_margin,0,0)
        h_box1.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.hpicon = QLabel(self)
        self.hpicon.setFixedSize(statbar_h,statbar_h)
        image = QImage()
        image.load('res/icons/HP_icon.png')
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(QPixmap.fromImage(image))
        self.hpicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box1.addWidget(self.hpicon)
        self.pet_hp = DP_HpBar(self, minimum=0, maximum=100, objectName='PetHP')
        #self.pet_hp.setFormat('0/100')
        #self.pet_hp.setValue(0)
        #self.pet_hp.setAlignment(Qt.AlignCenter)
        h_box1.addWidget(self.pet_hp)

        # ?????????
        h_box2 = QHBoxLayout()
        h_box2.setContentsMargins(0,status_margin,0,0)
        h_box2.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.emicon = QLabel(self)
        self.emicon.setFixedSize(statbar_h,statbar_h)
        image = QImage()
        image.load('res/icons/Fv_icon.png')
        self.emicon.setScaledContents(True)
        self.emicon.setPixmap(QPixmap.fromImage(image))
        self.emicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box2.addWidget(self.emicon)
        self.pet_fv = DP_FvBar(self, minimum=0, maximum=100, objectName='PetEM')
        self.pet_hp.hptier_changed.connect(self.hpchange)
        self.pet_fv.fvlvl_changed.connect(self.fvchange)
        #self.pet_fv.setFormat('0/100')
        #self.pet_fv.setValue(0)
        #self.pet_fv.setAlignment(Qt.AlignCenter)
        h_box2.addWidget(self.pet_fv)

        # ????????????
        h_box3 = QHBoxLayout()
        h_box3.setContentsMargins(0,0,0,0)
        h_box3.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.tomatoicon = QLabel(self)
        self.tomatoicon.setFixedSize(statbar_h,statbar_h)
        image = QImage()
        image.load('res/icons/Tomato_icon.png')
        self.tomatoicon.setScaledContents(True)
        self.tomatoicon.setPixmap(QPixmap.fromImage(image))
        self.tomatoicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box3.addWidget(self.tomatoicon)
        self.tomato_time = QProgressBar(self, minimum=0, maximum=25, objectName='PetTM')
        self.tomato_time.setFormat('???')
        self.tomato_time.setValue(0)
        self.tomato_time.setAlignment(Qt.AlignCenter)
        self.tomato_time.hide()
        self.tomatoicon.hide()
        h_box3.addWidget(self.tomato_time)

        # ????????????
        h_box4 = QHBoxLayout()
        h_box4.setContentsMargins(0,status_margin,0,0)
        h_box4.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.focusicon = QLabel(self)
        self.focusicon.setFixedSize(statbar_h,statbar_h)
        image = QImage()
        image.load('res/icons/Timer_icon.png')
        self.focusicon.setScaledContents(True)
        self.focusicon.setPixmap(QPixmap.fromImage(image))
        self.focusicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box4.addWidget(self.focusicon)
        self.focus_time = QProgressBar(self, minimum=0, maximum=100, objectName='PetFC')
        self.focus_time.setFormat('???')
        self.focus_time.setValue(0)
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

        # ???????????? - ?????????????????? --------------------------------------
        '''
        self.dialogue_box = QHBoxLayout()
        self.dialogue_box.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.dialogue_box.setContentsMargins(0,0,0,0)
        
        self.dialogue = QLabel(self)
        self.dialogue.setAlignment(Qt.AlignCenter)

        image = QImage()
        image.load('res/icons/text_framex2.png')
        self.dialogue.setFixedWidth(image.width())
        self.dialogue.setFixedHeight(image.height())
        QFontDatabase.addApplicationFont('res/font/MFNaiSi_Noncommercial-Regular.otf')
        self.dialogue.setFont(QFont('????????????????????????????????????', int(11/screen_scale)))
        self.dialogue.setWordWrap(False) # ????????????8?????????????????????????????????function????????????
        self._set_dialogue_dp()
        self.dialogue.setStyleSheet("background-image : url(res/icons/text_framex2.png)") #; border : 2px solid blue")
        
    

        self.dialogue_box.addWidget(self.dialogue)
        #self.dialogue.hide()
        '''
        
        # ------------------------------------------------------------

        #Layout_1
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
        '''
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addLayout(self.layout_1, Qt.AlignBottom | Qt.AlignHCenter)
        self.layout.addLayout(layout_2, Qt.AlignBottom | Qt.AlignLeft)
        '''

        self.setLayout(self.layout)
        # ------------------------------------------------------------

        # ???????????????
        self.tomato_window = Tomato()
        self.tomato_window.close_tomato.connect(self.show_tomato)
        self.tomato_window.confirm_tomato.connect(self.run_tomato)
        self.tomato_window.cancelTm.connect(self.cancel_tomato)

        # ????????????
        self.focus_window = Focus()
        self.focus_window.close_focus.connect(self.show_focus)
        self.focus_window.confirm_focus.connect(self.run_focus)
        self.focus_window.cancelFocus.connect(self.cancel_focus)
        self.focus_window.pauseTimer_focus.connect(self.pause_focus)

        # ?????????
        self.remind_window = Remindme()
        self.remind_window.close_remind.connect(self.show_remind)
        self.remind_window.confirm_remind.connect(self.run_remind)

        #self.setStyleSheet("border : 2px solid blue")




    def _set_menu(self, pets=()):
        """
        ???????????????
        """
        menu = QMenu(self)

        # ?????????????????????
        change_menu = QMenu(menu)
        change_menu.setTitle('????????????')
        change_acts = [_build_act(name, change_menu, self._change_pet) for name in pets]
        change_menu.addActions(change_acts)
        menu.addMenu(change_menu)

        # ??????
        open_invent = QAction('????????????', menu)
        open_invent.triggered.connect(self.show_inventory)
        menu.addAction(open_invent)


        # ????????????
        task_menu = QMenu(menu)
        task_menu.setTitle('????????????')
        self.tomato_clock = QAction('????????????', task_menu)
        self.tomato_clock.triggered.connect(self.show_tomato)
        task_menu.addAction(self.tomato_clock)
        self.focus_clock = QAction('????????????', task_menu)
        self.focus_clock.triggered.connect(self.show_focus)
        task_menu.addAction(self.focus_clock)
        self.remind_clock = QAction('?????????', task_menu)
        self.remind_clock.triggered.connect(self.show_remind)
        task_menu.addAction(self.remind_clock)
        menu.addMenu(task_menu)

        # ????????????
        self.act_menu = QMenu(menu)
        self.act_menu.setTitle('????????????')

        if self.pet_conf.act_name is not None:
            #select_acts = [_build_act(name, act_menu, self._show_act) for name in self.pet_conf.act_name]
            select_acts = [_build_act(self.pet_conf.act_name[i], self.act_menu, self._show_act) for i in range(len(self.pet_conf.act_name)) if (self.pet_conf.act_type[i][1] <= settings.pet_data.fv_lvl) and self.pet_conf.act_name[i] is not None]
            self.act_menu.addActions(select_acts)
        
        if self.pet_conf.acc_name is not None:
            select_accs = [_build_act(self.pet_conf.acc_name[i], self.act_menu, self._show_acc) for i in range(len(self.pet_conf.acc_name)) if (self.pet_conf.accessory_act[self.pet_conf.acc_name[i]]['act_type'][1] <= settings.pet_data.fv_lvl) ]
            self.act_menu.addActions(select_accs)

        menu.addMenu(self.act_menu)


        # ??????/????????????
        switch_fall = QAction('????????????', menu)
        switch_fall.triggered.connect(self.fall_onoff)
        menu.addAction(switch_fall)

        menu.addSeparator()

        # Settings
        open_setting = QAction('??????', menu)
        open_setting.triggered.connect(self.show_settings)
        menu.addAction(open_setting)

        #menu.addSeparator()

        # ??????
        
        about_menu = QMenu(menu)
        about_menu.setTitle('??????')
        global dyberpet_version
        about_menu.addAction('DyberPet v%s'%dyberpet_version)
        about_menu.addSeparator()
        webpage = QAction('?????????GitHub@ChaozhongLiu', about_menu)
        webpage.triggered.connect(lambda: webbrowser.open('https://github.com/ChaozhongLiu/DyberPet'))
        about_menu.addAction(webpage)
        menu.addMenu(about_menu)
        

        # ????????????
        quit_act = QAction('??????', menu)
        quit_act.triggered.connect(self.quit)
        menu.addAction(quit_act)
        self.menu = menu

    def _update_animations(self):
        select_acts = []
        for i in range(len(self.pet_conf.act_name)):
            if self.pet_conf.act_name[i] is None:
                continue

            if self.pet_conf.act_type[i][1] == settings.pet_data.fv_lvl:
                select_acts.append(_build_act(self.pet_conf.act_name[i], self.act_menu, self._show_act))

        self.act_menu.addActions(select_acts)
        #menu.addMenu(self.act_menu)

    def _show_right_menu(self):
        """
        ??????????????????
        :return:
        """
        # ????????????????????????
        self.menu.popup(QCursor.pos())

    def _change_pet(self, pet_name: str) -> None:
        """
        ????????????
        :param pet_name: ????????????
        :return:
        """
        if self.curr_pet_name == pet_name:
            return
        # stop animation thread and start again
        self.stop_thread('Animation')
        self.stop_thread('Interaction')
        self.stop_thread('Scheduler')
        self.init_conf(pet_name)
        self.change_note.emit()
        self.repaint()
        self.runAnimation()
        self.runInteraction()
        self.runScheduler()
        self._setup_ui(self.pic_dict)

    def init_conf(self, pet_name: str) -> None:
        """
        ???????????????????????????
        :param pet_name: ????????????
        :return:
        """
        self.curr_pet_name = pet_name
        self.pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, self.pic_dict, settings.size_factor)

        self.margin_value = 0.5 * max(self.pet_conf.width, self.pet_conf.height) # ?????????widgets????????????????????????
        
        #settings.pet_data = PetData(self.curr_pet_name)
        settings.init_pet(self.curr_pet_name)

        self.items_data = ItemData()
        #self.label.resize(self.pet_conf.width, self.pet_conf.height)
        #self.petlayout.setFixedSize(self.pet_conf.width, 1.1 * self.pet_conf.height)
        self._set_menu(self.pets)
        self._set_tray()


    def _setup_ui(self, pic_dict):

        self.pet_hp.setFixedSize(0.75*self.pet_conf.width, statbar_h)
        self.pet_fv.setFixedSize(0.75*self.pet_conf.width, statbar_h)
        self.tomato_time.setFixedSize(0.75*self.pet_conf.width, statbar_h)
        self.focus_time.setFixedSize(0.75*self.pet_conf.width, statbar_h)

        #self.setFixedSize(self.pet_conf.width+self.margin_value,
        #                  self.margin_value+self.pet_conf.height) #+self.dialogue.height()
        self.reset_size()

        self.pet_hp.init_HP(settings.pet_data.hp, self.pet_conf.hp_interval)

        self.pet_fv.init_FV(settings.pet_data.fv, settings.pet_data.fv_lvl)

        self.tomato_time.setFormat('???')
        self.tomato_time.setValue(0)
        self.tomato_time.hide()
        self.tomatoicon.hide()

        self.focus_time.setFormat('???')
        self.focus_time.setValue(0)
        self.focus_time.hide()
        self.focusicon.hide()

        #global current_img, previous_img
        settings.previous_img = settings.current_img
        settings.current_img = self.pet_conf.default.images[0] #list(pic_dict.values())[0]
        self.set_img()
        self.border = self.pet_conf.width/2
        self.hpicon.adjustSize()

        
        # ????????????
        screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = screen_geo.width()
        work_height = screen_geo.height()
        x=int(screen_width*0.8)
        y=work_height-self.height()
        # make sure that for all stand png, png bottom is the ground
        #self.floor_pos = work_height-self.height()
        self.move(x,y)
        

        # ???????????????????????????
        self.remind_window.initial_task()

        # ???????????????
        self.inventory_window = Inventory(self.items_data)
        self.inventory_window.close_inventory.connect(self.show_inventory)
        self.inventory_window.use_item_inven.connect(self.use_item)
        self.inventory_window.item_note.connect(self.register_notification)
        self.addItem_toInven.connect(self.inventory_window.add_items)
        self.fvlvl_changed_main_inve.connect(self.inventory_window.fvchange)

        # Settings
        self.setting_window = SettingUI()
        self.setting_window.close_setting.connect(self.show_settings)
        self.setting_window.scale_changed.connect(self.set_img)
        self.setting_window.scale_changed.connect(self.reset_size)



    def eventFilter(self, object, event):
        if event.type() == QEvent.Enter:
            self.status_frame.show()
            return True
        elif event.type() == QEvent.Leave:
            self.status_frame.hide()
        return False



    def _set_tray(self) -> None:
        """
        ?????????????????????
        :return:
        """
        if self.tray is None:
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(QIcon('res/icons/icon.png'))
            self.tray.setContextMenu(self.menu)
            self.tray.show()
            #self.tray.showMessage("Input Something", "Enter your notification tittle and message", msecs=3000)
        else:
            self.tray.setContextMenu(self.menu)
            self.tray.show()

    def reset_size(self):
        self.setFixedSize((self.pet_conf.width+self.margin_value)*max(1.0,settings.tunable_scale),
                          (self.margin_value+self.pet_conf.height)*max(1.0, settings.tunable_scale))

        # ????????????
        screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = screen_geo.width()
        work_height = screen_geo.height()
        x=self.pos().x()
        y=work_height-self.height()
        # make sure that for all stand png, png bottom is the ground
        self.floor_pos = work_height-self.height()
        self.move(x,y)

    def set_img(self): #, img: QImage) -> None:
        """
        ?????????????????????
        :param img: ??????
        :return:
        """
        #global current_img
        width_tmp = settings.current_img.width()*settings.tunable_scale
        height_tmp = settings.current_img.height()*settings.tunable_scale
        self.label.resize(width_tmp, height_tmp)
        self.label.setPixmap(QPixmap.fromImage(settings.current_img.scaled(width_tmp, height_tmp, aspectRatioMode=Qt.KeepAspectRatio)))
        #print(self.size())
        self.image = settings.current_img
    '''
    def _set_dialogue_dp(self, texts='None'):
        if texts == 'None':
            self.dialogue.hide()
        else:
            texts_wrapped = text_wrap(texts)
            self.dialogue.setText(texts_wrapped)
            self.dialogue.show()
    '''

    def register_notification(self, note_type, message):

        self.setup_notification.emit(note_type, message)

    '''
    def show_notification(self, note_index, message, icon):
        Toaster_tmp = QToaster(note_index)
        Toaster_tmp.closed_note.connect(self.remove_notification)
        height_margin = sum(self.note_height_dict.values()) + 10*(len(self.note_height_dict.keys()))
        #print(height_margin)
        #print(message)
        height_tmp = Toaster_tmp.showMessage(message=message, #parent
                                             icon=icon,
                                             corner=Qt.BottomRightCorner, #????????????
                                             height_margin=height_margin,
                                             closable=True, #????????????
                                             timeout=5000) #????????????
        self.note_height_dict[note_index] = height_tmp
        #self.sig_addHeight.emit(note_index, height_tmp)
        if not self.player.isPlaying():
            self.player.play()

    def remove_notification(self, note_index):
        self.note_height_dict.pop(note_index)
        #self.sig_rmNote.emit(note_index)
    '''

    def register_accessory(self, accs):
        self.setup_acc.emit(accs, self.pos().x()+self.width()//2, self.pos().y()+self.height())


    def _change_status(self, status, change_value, from_mod='Scheduler', send_note=False):
        if status not in ['hp','fv']:
            return
        elif status == 'hp':
            #before_value = self.pet_hp.value()
            '''
            if change_value > 0:
                current_value = min(self.pet_hp.value() + change_value, 100)
                self.pet_hp.setValue(current_value)
                current_value = self.pet_hp.value()
                self.pet_hp.setFormat('%s/100'%(int(current_value)))
                settings.pet_data.change_hp(current_value) #.hp = current_value
            else:
                prev_value = self.pet_hp.value()
                current_value = self.pet_hp.value() + change_value
                self.pet_hp.setValue(current_value)
                current_value = self.pet_hp.value()
                if current_value == prev_value:
                    return
                else:
                    self.pet_hp.setFormat('%s/100'%(int(current_value)))
                    settings.pet_data.change_hp(current_value) #.hp = current_value
            '''
            diff = self.pet_hp.updateValue(change_value, from_mod)
            #after_value = self.pet_hp.value()

        elif status == 'fv':
            #before_value = self.pet_fv.value()
            '''
            if change_value > 0:
                current_value = min(self.pet_em.value() + change_value, 100)
                self.pet_em.setValue(current_value)
                current_value = self.pet_em.value()
                self.pet_em.setFormat('%s/100'%(int(current_value)))
                settings.pet_data.change_em(current_value) #.em = current_value
            elif settings.pet_data.hp < 60:
                prev_value = self.pet_em.value()
                current_value = self.pet_em.value() + change_value
                self.pet_em.setValue(current_value)
                current_value = self.pet_em.value()
                if current_value == prev_value:
                    return
                else:
                    self.pet_em.setFormat('%s/100'%(int(current_value)))
                    settings.pet_data.change_em(current_value) #.em = current_value
            else:
                return
            '''
            diff = self.pet_fv.updateValue(change_value, from_mod)
            #after_value = self.pet_fv.value()

        if send_note:
            #diff = after_value - before_value
            if diff > 0:
                diff = '+%s'%diff
            elif diff < 0:
                diff = str(diff)
            else:
                return
            if status == 'hp':
                message = '????????? %s'%diff
            else:
                message = '????????? %s'%diff
            self.register_notification('status_%s'%status, message)
        #settings.pet_data.save_data()

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
            self.tomato_time.setFormat('???')
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
            self.focus_time.setFormat('???')
            self.focus_window.endFocus()

    def use_item(self, item_name):
        # ???????????????????????????
        self.workers['Animation'].pause()
        self.workers['Interaction'].start_interact('use_item', item_name)

        # ???????????????????????? ???????????? ??????????????????????????? ??????????????????????????????????????????????????????
        # ??????????????????????????????thread????????????

        # ???????????? ????????????
        self._change_status('hp', self.items_data.item_dict[item_name]['effect_HP'], from_mod='inventory', send_note=True)
        if item_name in self.pet_conf.item_favorite:
            self._change_status('fv', self.items_data.item_dict[item_name]['effect_FV']+3, from_mod='inventory', send_note=True)
        elif item_name in self.pet_conf.item_dislike:
            self._change_status('fv', max(0,self.items_data.item_dict[item_name]['effect_FV']-2), from_mod='inventory', send_note=True)
        else:
            self._change_status('fv', self.items_data.item_dict[item_name]['effect_FV'], from_mod='inventory', send_note=True)

    def add_item(self, n_items, item_names=[]):
        self.addItem_toInven.emit(n_items, item_names)


    def quit(self) -> None:
        """
        ????????????, ????????????
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
        if sender.text()=="????????????":
            sender.setText("????????????")
            settings.set_fall=0
        else:
            sender.setText("????????????")
            settings.set_fall=1

    def show_tomato(self):
        if self.tomato_window.isVisible():
            self.tomato_window.hide()

        else:
            self.tomato_window.move(max(0,self.pos().x()-self.tomato_window.width()//2),
                                    max(0,self.pos().y()-self.tomato_window.height()))
            self.tomato_window.show()

        '''
        elif self.tomato_clock.text()=="??????????????????":
            self.tomato_clock.setText("????????????")
            self.workers['Scheduler'].cancel_tomato()
            self.tomatoicon.hide()
            self.tomato_time.hide()
        '''

    def run_tomato(self, nt):
        if self.tomato_clock.text()=="????????????":
            #self.tomato_clock.setText("??????????????????")
            #self.tomato_window.hide()
            self.workers['Scheduler'].add_tomato(n_tomato=int(nt))
            self.tomatoicon.show()
            self.tomato_time.show()

    def cancel_tomato(self):
        self.workers['Scheduler'].cancel_tomato()
        #self.tomatoicon.hide()
        #self.tomato_time.hide()

    def change_tomato_menu(self):
        #if self.tomato_clock.text()=="??????????????????":
        #    self.tomato_clock.setText("????????????")
        self.tomatoicon.hide()
        self.tomato_time.hide()

    def show_focus(self):
        if self.focus_window.isVisible():
            self.focus_window.hide()
        
        else:
            self.focus_window.move(max(0,self.pos().x()-self.focus_window.width()//2),
                                   max(0,self.pos().y()-self.focus_window.height()))
            self.focus_window.show()
        '''
        elif self.focus_clock.text()=="??????????????????":
            self.focus_clock.setText("????????????")
            self.workers['Scheduler'].cancel_focus()
            self.focusicon.hide()
            self.focus_time.hide()
        '''

    def run_focus(self, task, hs, ms):
        #sender = self.sender()
        #print(self.focus_clock.text())
        if self.focus_clock.text()=="????????????":
            #self.focus_clock.setText("??????????????????")
            #self.focus_window.hide()
            if task == 'range':
                self.workers['Scheduler'].add_focus(time_range=[hs,ms])
            elif task == 'point':
                self.workers['Scheduler'].add_focus(time_point=[hs,ms])
            self.focusicon.show()
            self.focus_time.show()
        #else:
        #    self.focus_clock.setText("????????????")
        #    self.workers['Scheduler'].cancel_focus()

    def pause_focus(self, state):
        if state: # ??????
            self.workers['Scheduler'].pause_focus()
        else: # ??????
            self.workers['Scheduler'].resume_focus(int(self.focus_time.value()), int(self.focus_time.maximum()))


    def cancel_focus(self):
        self.workers['Scheduler'].cancel_focus(int(self.focus_time.maximum()-self.focus_time.value()))

    def change_focus_menu(self):
        #if self.focus_clock.text()=="??????????????????":
            #self.focus_clock.setText("????????????")
        self.focusicon.hide()
        self.focus_time.hide()


    def show_remind(self):
        if self.remind_window.isVisible():
            self.remind_window.hide()
        else:
            self.remind_window.move(max(0,self.pos().x()-self.remind_window.width()//2),
                                    max(0,self.pos().y()-self.remind_window.height()))
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
            self.inventory_window.move(max(0, self.pos().x()-self.inventory_window.width()//2),
                                    max(0, self.pos().y()-self.inventory_window.height()))
            self.inventory_window.show()
            #print(self.inventory_window.size())

    def show_settings(self):
        if self.setting_window.isVisible():
            self.setting_window.hide()
        else:
            self.setting_window.move(max(0, self.pos().x()-self.setting_window.width()//2),
                                    max(0, self.pos().y()-self.setting_window.height()))
            self.setting_window.show()
    

    
    '''
    def runNotification(self):
        self.threads['Notification'] = QThread()
        self.workers['Notification'] = Notification_worker(self.items_data)
        self.workers['Notification'].moveToThread(self.threads['Notification'])
        self.setup_notification.connect(self.workers['Notification'].setup_notification)
        self.hptier_changed_main_note.connect(self.workers['Notification'].hpchange_note)
        self.fvlvl_changed_main_note.connect(self.workers['Notification'].fvchange_note)
        #self.sig_rmNote.connect(self.workers['Notification'].remove_note)
        #self.sig_addHeight.connect(self.workers['Notification'].add_height)
        self.workers['Notification'].send_notification.connect(self.show_notification)

        self.threads['Notification'].start()
        self.threads['Notification'].setTerminationEnabled()
    '''

    def runAnimation(self):
        # Create thread for Animation Module
        self.threads['Animation'] = QThread()
        self.workers['Animation'] = Animation_worker(self.pet_conf)
        #self.animation_thread = QThread()
        #self.animation_worker = Animation_worker(self.pet_conf)
        self.workers['Animation'].moveToThread(self.threads['Animation'])
        # Connect signals and slots
        self.threads['Animation'].started.connect(self.workers['Animation'].run)
        #self.pet_hp.hptier_changed.connect(self.workers['Animation'].hpchange_note)
        #self.pet_fv.fvlvl_changed.connect(self.workers['Animation'].fvchange_note)
        self.workers['Animation'].sig_setimg_anim.connect(self.set_img)
        self.workers['Animation'].sig_move_anim.connect(self._move_customized)
        self.workers['Animation'].sig_repaint_anim.connect(self.repaint)
        #self.animation_worker.finished.connect(self.animation_thread.quit)
        #self.animation_worker.finished.connect(self.animation_worker.deleteLater)
        #self.animation_thread.finished.connect(self.animation_thread.deleteLater)
        #self.animation_worker.progress.connect(self.reportProgress)
        # Start the thread
        self.threads['Animation'].start()
        self.threads['Animation'].setTerminationEnabled()

        # backup codes for future use
        '''
        self.longRunningBtn.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.longRunningBtn.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.stepLabel.setText("Long-Running Step: 0")
        )
        '''
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
            self._update_animations()

    def runInteraction(self):
        # Create thread for Interaction Module
        self.threads['Interaction'] = QThread()
        self.workers['Interaction'] = Interaction_worker(self.pet_conf)
        #self.animation_thread = QThread()
        #self.animation_worker = Animation_worker(self.pet_conf)
        self.workers['Interaction'].moveToThread(self.threads['Interaction'])
        # Connect signals and slots
        #self.threads['Interaction'].started.connect(self.workers['Interaction'].run)
        self.workers['Interaction'].sig_setimg_inter.connect(self.set_img)
        self.workers['Interaction'].sig_move_inter.connect(self._move_customized)
        #self.workers['Interaction'].sig_repaint_inter.connect(self.repaint)
        self.workers['Interaction'].sig_act_finished.connect(self.resume_animation)
        self.workers['Interaction'].sig_interact_note.connect(self.register_notification)
        self.workers['Interaction'].acc_regist.connect(self.register_accessory)

        # Start the thread
        self.threads['Interaction'].start()
        self.threads['Interaction'].setTerminationEnabled()

    def runScheduler(self):
        # Create thread for Scheduler Module
        self.threads['Scheduler'] = QThread()
        self.workers['Scheduler'] = Scheduler_worker(self.pet_conf)
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

        if new_x+self.width()//2 < 0: #self.border:
            new_x = -self.width()//2 #self.screen_width + self.border - self.width()

        elif new_x+self.width()//2 > self.screen_width: # + self.border:
            new_x = self.screen_width-self.width()//2 #self.border-self.width()

        if new_y+self.height()-self.label.height() < 0: #self.border:
            new_y = self.label.height() - self.height() #self.floor_pos

        elif new_y >= self.floor_pos:
            new_y = self.floor_pos
            #global onfloor
            if settings.onfloor == 0:
                settings.onfloor = 1
                ##global current_img
                #settings.current_img = self.pet_conf.default.images[0]
                #self.set_img()
                ##print('on floor check')
                #self.workers['Animation'].resume()

        self.move(new_x, new_y)


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
    ??????????????????????????????
    :param pet_name: ????????????
    :return: {????????????: ????????????}
    """
    img_dir = 'res/role/{}/action/'.format(pet_name)
    images = os.listdir(img_dir)
    return {image.split('.')[0]: _get_q_img(img_dir + image) for image in images}


def _build_act(name: str, parent: QObject, act_func) -> QAction:
    """
    ????????????????????????
    :param pet_name: ??????????????????
    :param parent ????????????
    :param act_func: ??????????????????
    :return:
    """
    act = QAction(name, parent)
    act.triggered.connect(lambda: act_func(name))
    return act


def _get_q_img(img_path: str) -> QImage:
    """
    ???????????????????????? QImage
    :param img_path: ????????????
    :return: QImage
    """
    image = QImage()
    image.load(img_path)
    return image
'''
def text_wrap(texts):
    n_char = len(texts)
    n_line = int(n_char//7 + 1)
    texts_wrapped = ''
    for i in range(n_line):
        texts_wrapped += texts[(7*i):min((7*i + 7),n_char)] + '\n'
    texts_wrapped = texts_wrapped.rstrip('\n')

    return texts_wrapped
'''

if __name__ == '__main__':
    # ??????????????????, ????????????????????????????????????
    pets = read_json('data/pets.json')
    app = QApplication(sys.argv)
    p = PetWidget(pets=pets)
    sys.exit(app.exec_())



