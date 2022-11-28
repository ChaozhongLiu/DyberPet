import sys
import time
import math
import random
import inspect
import types

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QEvent
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontDatabase
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from typing import List

from DyberPet.modules import *
from DyberPet.utils import *
from DyberPet.conf import *

#repaint() to update()?

# version
dyberpet_version = '0.1.5'

import DyberPet.settings as settings
settings.init()



class Tomato(QWidget):
    close_tomato = pyqtSignal(name='close_tomato')
    confirm_tomato = pyqtSignal(int, name='confirm_tomato')

    def __init__(self, parent=None):
        super(Tomato, self).__init__(parent)
        # tomato clock window

        vbox_t = QVBoxLayout()

        hbox_t1 = QHBoxLayout()
        self.n_tomato = QSpinBox()
        self.n_tomato.setMinimum(1)
        n_tomato_label = QLabel("请选择要进行番茄钟的个数:")
        QFontDatabase.addApplicationFont('res/font/MFNaiSi_Noncommercial-Regular.otf')
        n_tomato_label.setFont(QFont('宋体', 10))
        hbox_t1.addWidget(n_tomato_label)
        hbox_t1.addWidget(self.n_tomato)

        hbox_t = QHBoxLayout()
        self.button_confirm = QPushButton("确定")
        self.button_confirm.setFont(QFont('宋体', 10))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_cancel = QPushButton("取消")
        self.button_cancel.setFont(QFont('宋体', 10))
        self.button_cancel.clicked.connect(self.close_tomato)
        hbox_t.addWidget(self.button_confirm)
        hbox_t.addWidget(self.button_cancel)

        vbox_t.addLayout(hbox_t1)
        vbox_t.addLayout(hbox_t)
        self.setLayout(vbox_t)
        self.setFixedSize(250,100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)


    def confirm(self):
        self.confirm_tomato.emit(self.n_tomato.value())



class PetWidget(QWidget):
    def __init__(self, parent=None, curr_pet_name='', pets=()):
        """
        宠物组件
        :param parent: 父窗口
        :param curr_pet_name: 当前宠物名称
        :param pets: 全部宠物列表
        """
        super(PetWidget, self).__init__(parent, flags=Qt.WindowFlags())
        self.pets = pets
        self.curr_pet_name = ''
        self.pet_conf = PetConfig()
        #self.pet_data = PetData()
        self.image = None
        self.tray = None
        

        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

        # Some geo info
        self.screen_geo = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()

        self._init_ui()
        self._init_widget()
        self.init_conf(curr_pet_name if curr_pet_name else pets[0])
        #self._setup_ui(self.pic_dict)

        #self._set_menu(pets)
        #self._set_tray()
        self.show()

        # 开始动画模块和交互模块
        self.threads = {}
        self.workers = {}
        self.runAnimation()
        self.runInteraction()
        self.runScheduler()
        '''
        self.timer = QTimer()
        self.timer.timeout.connect(self.random_act)
        self.timer.start(self.pet_conf.refresh)
        '''

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
        鼠标移动事件, 左键且绑定跟随, 移动窗体
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
        松开鼠标操作
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

    '''
    def _init_img(self, img: QImage) -> None:
        """
        初始化窗体图片
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
        #动画 --------------------------------------------------------
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.label.installEventFilter(self)
        #self.label.setStyleSheet("border : 2px solid blue")
        # ------------------------------------------------------------

        #数值 --------------------------------------------------------
        #self.status_box = QHBoxLayout()
        #self.status_box.setContentsMargins(0,0,0,0)
        #self.status_box.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.status_frame = QFrame()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)

        h_box1 = QHBoxLayout()
        h_box1.setContentsMargins(0,0,0,0)
        h_box1.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.hpicon = QLabel(self)
        self.hpicon.setFixedSize(17,15)
        image = QImage()
        image.load('res/icons/HP_icon.png')
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(QPixmap.fromImage(image))
        self.hpicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box1.addWidget(self.hpicon)
        self.pet_hp = QProgressBar(self, minimum=0, maximum=100, objectName='PetHP')
        self.pet_hp.setFormat('50/100')
        self.pet_hp.setValue(50)
        self.pet_hp.setAlignment(Qt.AlignCenter)
        h_box1.addWidget(self.pet_hp)

        h_box2 = QHBoxLayout()
        h_box2.setContentsMargins(0,0,0,0)
        h_box2.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.emicon = QLabel(self)
        self.emicon.setFixedSize(17,15)
        image = QImage()
        image.load('res/icons/emotion_icon.png')
        self.emicon.setScaledContents(True)
        self.emicon.setPixmap(QPixmap.fromImage(image))
        self.emicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box2.addWidget(self.emicon)
        self.pet_em = QProgressBar(self, minimum=0, maximum=100, objectName='PetEM')
        self.pet_em.setFormat('50/100')
        self.pet_em.setValue(50)
        self.pet_em.setAlignment(Qt.AlignCenter)
        h_box2.addWidget(self.pet_em)

        vbox.addLayout(h_box1)
        vbox.addLayout(h_box2)

        self.status_frame.setLayout(vbox)
        #self.status_frame.setStyleSheet("border : 2px solid blue")
        self.status_frame.setContentsMargins(0,0,0,0)
        #not_resize = self.status_frame.sizePolicy()
        #not_resize.setRetainSizeWhenHidden(True)
        #self.status_frame.setSizePolicy(not_resize)
        #self.status_box.addWidget(self.status_frame)
        self.status_frame.hide()
        # ------------------------------------------------------------

        # 对话界面 - 位于宠物左侧 --------------------------------------
        
        self.dialogue_box = QHBoxLayout()
        self.dialogue_box.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.dialogue_box.setContentsMargins(0,0,0,0)
        
        self.dialogue = QLabel(self)
        self.dialogue.setAlignment(Qt.AlignCenter)
        #self.dialogue.setStyleSheet("border : 2px solid blue")
        '''
        not_resize = self.dialogue.sizePolicy();
        not_resize.setRetainSizeWhenHidden(True);
        self.dialogue.setSizePolicy(not_resize)
        '''
        #self.text_printer = QPainter(image)
        #self.text_printer.drawText(10,10,'早上好')
        #self.text_printer.end()
        #self.dialogue.setPixmap(QPixmap.fromImage(image))
        image = QImage()
        image.load('res/icons/text_framex2.png')
        self.dialogue.setFixedWidth(image.width())
        self.dialogue.setFixedHeight(image.height())
        QFontDatabase.addApplicationFont('res/font/MFNaiSi_Noncommercial-Regular.otf')
        self.dialogue.setFont(QFont('造字工房奈思体（非商用）', 11))
        self.dialogue.setWordWrap(False) # 每行最多8个汉字长度，需要自定义function进行换行
        self._set_dialogue_dp()
        self.dialogue.setStyleSheet("background-image : url(res/icons/text_framex2.png)") #; border : 2px solid blue")
        
        '''
        self.dialogue = QLabel(self)
        self.dialogue.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        not_resize = self.dialogue.sizePolicy();
        not_resize.setRetainSizeWhenHidden(True);
        self.dialogue.setSizePolicy(not_resize)
        image = QImage()
        image.load('res/text_framex2.png')
        self.text_printer = QPainter(image)
        self.text_printer.drawText(10,50,'早上好aaaaaaaaaaaaa')
        self.text_printer.end()
        #self.dialogue.setFixedWidth(image.width())
        #self.dialogue.setFixedHeight(image.height())
        self.dialogue.setPixmap(QPixmap.fromImage(image))
        #self.dialogue.setText('早上好')
        self.dialogue.setStyleSheet("border : 2px solid blue")
        '''
        

        self.dialogue_box.addWidget(self.dialogue)
        #self.dialogue.hide()
        
        # ------------------------------------------------------------

        #Layout
        self.layout = QVBoxLayout()
        #self.layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.layout.setContentsMargins(0,0,0,0)

        self.petlayout = QVBoxLayout()
        self.petlayout.addWidget(self.status_frame)
        self.petlayout.addWidget(self.label)
        self.petlayout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        #self.petlayout.setAlignment(Qt.AlignBottom)
        self.petlayout.setContentsMargins(0,0,0,0)
        self.layout.addLayout(self.dialogue_box, Qt.AlignBottom | Qt.AlignHCenter)
        #self.layout.addWidget(self.dialogue, Qt.AlignBottom | Qt.AlignRight)
        self.layout.addLayout(self.petlayout, Qt.AlignBottom | Qt.AlignHCenter)
        self.setLayout(self.layout)
        # ------------------------------------------------------------

        self.tomato_window = Tomato()
        self.tomato_window.close_tomato.connect(self.show_tomato)
        self.tomato_window.confirm_tomato.connect(self.run_tomato)



    def _set_menu(self, pets=()):
        """
        初始化菜单
        """
        menu = QMenu(self)

        # 切换角色子菜单
        change_menu = QMenu(menu)
        change_menu.setTitle('切换角色')
        change_acts = [_build_act(name, change_menu, self._change_pet) for name in pets]
        change_menu.addActions(change_acts)
        menu.addMenu(change_menu)

        # 计划任务
        task_menu = QMenu(menu)
        task_menu.setTitle('计划任务')
        tomato_clock = QAction('番茄时钟', task_menu)
        tomato_clock.triggered.connect(self.show_tomato)
        task_menu.addAction(tomato_clock)
        #task_menu.addAction()
        #task_menu.addAction()
        menu.addMenu(task_menu)

        # 选择动作
        if self.pet_conf.random_act_name is not None:
            act_menu = QMenu(menu)
            act_menu.setTitle('选择动作')
            select_acts = [_build_act(name, act_menu, self._show_act) for name in self.pet_conf.random_act_name]
            act_menu.addActions(select_acts)
            menu.addMenu(act_menu)


        # 开启/关闭掉落
        switch_fall = QAction('禁用掉落', menu)
        switch_fall.triggered.connect(self.fall_onoff)
        menu.addAction(switch_fall)

        menu.addSeparator()

        # 关于
        about_menu = QMenu(menu)
        about_menu.setTitle('关于')
        global dyberpet_version
        about_menu.addAction('DyberPet v%s'%dyberpet_version)
        about_menu.addSeparator()
        about_menu.addAction('作者：GitHub@ChaozhongLiu')
        menu.addMenu(about_menu)

        # 退出动作
        quit_act = QAction('退出', menu)
        quit_act.triggered.connect(self.quit)
        menu.addAction(quit_act)
        self.menu = menu

    def _show_right_menu(self):
        """
        展示右键菜单
        :return:
        """
        # 光标位置弹出菜单
        self.menu.popup(QCursor.pos())

    def _change_pet(self, pet_name: str) -> None:
        """
        改变宠物
        :param pet_name: 宠物名称
        :return:
        """
        # stop animation thread and start again
        self.stop_thread('Animation')
        self.stop_thread('Interaction')
        self.stop_thread('Scheduler')
        self.init_conf(pet_name)
        self.repaint()
        self.runAnimation()
        self.runInteraction()
        self.runScheduler()

    def init_conf(self, pet_name: str) -> None:
        """
        初始化宠物窗口配置
        :param pet_name: 宠物名称
        :return:
        """
        self.curr_pet_name = pet_name
        self.pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, self.pic_dict)
        self.margin_value = 0.5 * max(self.pet_conf.width, self.pet_conf.height) # 用于将widgets调整到合适的大小
        self.pet_data = PetData(self.curr_pet_name)
        self._setup_ui(self.pic_dict)
        #self.label.resize(self.pet_conf.width, self.pet_conf.height)
        #self.petlayout.setFixedSize(self.pet_conf.width, 1.1 * self.pet_conf.height)
        self._set_menu(self.pets)
        self._set_tray()


    def _setup_ui(self, pic_dict):

        self.pet_hp.setFixedSize(0.75*self.pet_conf.width, 15)
        self.pet_em.setFixedSize(0.75*self.pet_conf.width, 15)
        #self.petlayout.setFixedSize(self.petlayout.width, self.petlayout.height)
        self.setFixedSize(self.pet_conf.width+self.margin_value, self.dialogue.height()+self.margin_value+self.pet_conf.height)
        #self.setFixedHeight(self.dialogue.height()+50+self.pet_conf.height)

        self.pet_hp.setFormat('%s/100'%(int(self.pet_data.hp)))
        self.pet_hp.setValue(int(self.pet_data.hp))
        self.pet_em.setFormat('%s/100'%(int(self.pet_data.em)))
        self.pet_em.setValue(int(self.pet_data.em))

        
        #global current_img, previous_img
        settings.previous_img = settings.current_img
        settings.current_img = list(pic_dict.values())[0] 
        self.set_img()
        self.border = self.pet_conf.width/2
        self.hpicon.adjustSize()

        # 初始位置
        screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = screen_geo.width()
        work_height = screen_geo.height()
        x=int(screen_width*0.8)
        y=work_height-self.height()
        # make sure that for all stand png, png bottom is the ground
        self.floor_pos = work_height-self.height()
        self.move(x,y)



    def eventFilter(self, object, event):
        if event.type() == QEvent.Enter:
            self.status_frame.show()
            #self.dialogue.show()
            return True
        elif event.type() == QEvent.Leave:
            self.status_frame.hide()
            #self.dialogue.hide()
        return False



    def _set_tray(self) -> None:
        """
        设置最小化托盘
        :return:
        """
        if self.tray is None:
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(QIcon('res/icons/icon.png'))
            self.tray.setContextMenu(self.menu)
            self.tray.show()
        else:
            self.tray.setContextMenu(self.menu)
            self.tray.show()

    def set_img(self): #, img: QImage) -> None:
        """
        为窗体设置图片
        :param img: 图片
        :return:
        """
        #global current_img
        self.label.resize(settings.current_img.width(), settings.current_img.height())
        self.label.setPixmap(QPixmap.fromImage(settings.current_img))
        #print(self.size())
        self.image = settings.current_img

    def _set_dialogue_dp(self, texts='None'):
        if texts == 'None':
            self.dialogue.hide()
        else:
            texts_wrapped = text_wrap(texts)
            self.dialogue.setText(texts_wrapped)
            self.dialogue.show()

    def _change_status(self, status, change_value):
        if status not in ['hp','em']:
            return
        elif status == 'hp':
            current_value = self.pet_hp.value() + change_value
            self.pet_hp.setValue(current_value)
            current_value = self.pet_hp.value()
            self.pet_hp.setFormat('%s/100'%(int(current_value)))
            self.pet_data.hp = current_value

        elif status == 'em':
            if change_value > 0:
                current_value = self.pet_em.value() + change_value
                self.pet_em.setValue(current_value)
                current_value = self.pet_em.value()
                self.pet_em.setFormat('%s/100'%(int(current_value)))
                self.pet_data.em = current_value
            elif self.pet_data.hp < 60:
                current_value = self.pet_em.value() + change_value
                self.pet_em.setValue(current_value)
                current_value = self.pet_em.value()
                self.pet_em.setFormat('%s/100'%(int(current_value)))
                self.pet_data.em = current_value
            else:
                return
        self.pet_data.save_data()


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

    def show_tomato(self):
        if self.tomato_window.isVisible():
            self.tomato_window.hide()
        else:
            self.tomato_window.move(self.pos())
            self.tomato_window.show()

    def run_tomato(self, nt):
        self.tomato_window.hide()
        self.workers['Scheduler'].add_task(task_name='tomato',n_tomato=int(nt))
        #print('main check!')
        

    def runAnimation(self):
        # Create thread for Animation Module
        self.threads['Animation'] = QThread()
        self.workers['Animation'] = Animation_worker(self.pet_conf)
        #self.animation_thread = QThread()
        #self.animation_worker = Animation_worker(self.pet_conf)
        self.workers['Animation'].moveToThread(self.threads['Animation'])
        # Connect signals and slots
        self.threads['Animation'].started.connect(self.workers['Animation'].run)
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
        self.workers['Scheduler'].sig_settext_sche.connect(self._set_dialogue_dp)
        self.workers['Scheduler'].sig_setact_sche.connect(self._show_act)
        self.workers['Scheduler'].sig_setstat_sche.connect(self._change_status)

        # Start the thread
        self.threads['Scheduler'].start()
        self.threads['Scheduler'].setTerminationEnabled()



    def _move_customized(self, plus_x, plus_y):

        #print(act_list)
        #direction, frame_move = str(act_list[0]), float(act_list[1])
        pos = self.pos()
        new_x = pos.x() + plus_x
        new_y = pos.y() + plus_y

        if new_x+self.width() < self.border:
            new_x = self.screen_width + self.border - self.width()
        elif new_x+self.width() > self.screen_width + self.border:
            new_x = self.border-self.width()

        if new_y+self.border < 0: #self.border:
            new_y = self.floor_pos
        elif new_y >= self.floor_pos:
            new_y = self.floor_pos
            #global onfloor
            if settings.onfloor == 0:
                settings.onfloor = 1
                #global current_img
                settings.current_img = self.pet_conf.default.images[0]
                self.set_img()
                #print('on floor check')
                self.workers['Animation'].resume()

        self.move(new_x, new_y)


    def _show_act(self, random_act_name):
        self.workers['Animation'].pause()
        self.workers['Interaction'].start_interact('animat', random_act_name)


    def resume_animation(self):
        self.workers['Animation'].resume()




def _load_all_pic(pet_name: str) -> dict:
    """
    加载宠物所有动作图片
    :param pet_name: 宠物名称
    :return: {动作编码: 动作图片}
    """
    img_dir = 'res/role/{}/action/'.format(pet_name)
    images = os.listdir(img_dir)
    return {image.split('.')[0]: _get_q_img(img_dir + image) for image in images}


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


def _get_q_img(img_path: str) -> QImage:
    """
    将图片路径加载为 QImage
    :param img_path: 图片路径
    :return: QImage
    """
    image = QImage()
    image.load(img_path)
    return image

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
    pets = read_json('data/pets.json')
    app = QApplication(sys.argv)
    p = PetWidget(pets=pets)
    sys.exit(app.exec_())



