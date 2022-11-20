import sys
import time
import math
import random
import inspect
import types

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QEvent
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from typing import List

from DyberPet.modules import *
from DyberPet.utils import *
from DyberPet.conf import *

#repaint() to update()?

# version
dyberpet_version = '0.1.4'

import DyberPet.settings as settings
settings.init()



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
        self.image = None
        

        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

        # Some geo info
        self.screen_geo = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()

        #动画
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.label.installEventFilter(self)

        #数值
        self.status_frame = QFrame()
        h_box2 = QHBoxLayout()
        h_box2.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

        self.hpicon = QLabel(self)
        self.hpicon.setFixedSize(17,15)
        image = QImage()
        image.load('res/HP_icon.png')
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(QPixmap.fromImage(image))
        self.hpicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box2.addWidget(self.hpicon)

        self.petstatus = QProgressBar(self, minimum=0, maximum=100, objectName='PetStatus')
        self.petstatus.setFormat('50/100')
        self.petstatus.setValue(50)
        self.petstatus.setAlignment(Qt.AlignCenter)
        h_box2.addWidget(self.petstatus)

        self.status_frame.setLayout(h_box2)
        self.status_frame.hide()

        #Layout
        self.petlayout = QVBoxLayout()
        #self.petlayout.addWidget(self.petstatus)
        self.petlayout.addWidget(self.status_frame)
        self.petlayout.addWidget(self.label)
        self.petlayout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        #self.petlayout.setAlignment(Qt.AlignBottom)
        self.petlayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.petlayout)


        self._init_widget()
        self.init_conf(curr_pet_name if curr_pet_name else pets[0])
        self._init_ui(self.pic_dict)

        #self._set_menu(pets)
        #self._set_tray()
        self.show()

        # 开始动画模块和交互模块
        self.threads = {}
        self.workers = {}
        self.runAnimation()
        self.runInteraction()
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
        self.init_conf(pet_name)
        self._init_ui(self.pic_dict)
        self.repaint()
        self.runAnimation()
        self.runInteraction()

    def init_conf(self, pet_name: str) -> None:
        """
        初始化宠物窗口配置
        :param pet_name: 宠物名称
        :return:
        """
        self.curr_pet_name = pet_name
        self.pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, self.pic_dict)
        self._init_ui(self.pic_dict)
        #self.label.resize(self.pet_conf.width, self.pet_conf.height)
        #self.petlayout.setFixedSize(self.pet_conf.width, 1.1 * self.pet_conf.height)
        self._set_menu(self.pets)
        self._set_tray()


    def _init_ui(self, pic_dict):

        self.petstatus.setFixedSize(0.8*self.pet_conf.width, 15)
        #self.status_frame.setFixedHeight(25)
        self.setFixedSize(50+self.pet_conf.width, 50+self.pet_conf.height)
        
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
            return True
        elif event.type() == QEvent.Leave:
            self.status_frame.hide()
        return False



    def _set_tray(self) -> None:
        """
        设置最小化托盘
        :return:
        """
        tray = QSystemTrayIcon(self)
        tray.setIcon(QIcon('res/icon.png'))
        tray.setContextMenu(self.menu)
        tray.show()

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

    def runAnimation(self):
        # Create tread for Animation Module
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
        # Create tread for Animation Module
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


    def _move_customized(self, plus_x, plus_y):

        #print(act_list)
        #direction, frame_move = str(act_list[0]), float(act_list[1])
        pos = self.pos()
        new_x = pos.x() + plus_x
        new_y = pos.y() + plus_y

        if new_x < self.border:
            new_x = self.screen_width - self.border
        elif new_x > self.screen_width - self.border:
            new_x = self.border

        if new_y < 0: #self.border:
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


if __name__ == '__main__':
    # 加载所有角色, 启动应用并展示第一个角色
    pets = read_json('res/pets.json')
    app = QApplication(sys.argv)
    p = PetWidget(pets=pets)
    sys.exit(app.exec_())



