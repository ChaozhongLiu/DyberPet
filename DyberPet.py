import sys
import time
import math
import random
import inspect
import types

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from typing import List

from utils import *
from conf import *


#repaint() to update()?

# version
dyberpet_version = '0.1.1'

# Make img-to-show a global variable for multi-thread behaviors
current_img = QImage()
previous_img = QImage()

# Drag and fall related global variable
onfloor = 1
draging = 0
set_fall = 1 # default is allow drag
playid = 0
mouseposx1,mouseposx2,mouseposx3,mouseposx4,mouseposx5=0,0,0,0,0
mouseposy1,mouseposy2,mouseposy3,mouseposy4,mouseposy5=0,0,0,0,0
dragspeedx,dragspeedy=0,0
fixdragspeedx, fixdragspeedy = 4.0, 2.5
fall_right = 0
        



class Animation_worker(QObject):
    sig_setimg_anim = pyqtSignal(name='sig_setimg_anim')
    sig_move_anim = pyqtSignal(float, float, name='sig_move_anim')
    sig_repaint_anim = pyqtSignal()

    def __init__(self, pet_conf, parent=None):
        """
        Animation Module
        Display user-defined animations randomly
        :param pet_conf: PetConfig class object in Main Widgets

        """
        super(Animation_worker, self).__init__(parent)
        self.pet_conf = pet_conf
        self.is_killed = False
        self.is_paused = False

    def run(self):
        """Run animation in a separate thread"""
        print('start running pet %s'%(self.pet_conf.petname))
        while not self.is_killed:
            self.random_act()

            while self.is_paused:
                time.sleep(0.2)
            if self.is_killed:
                break

            time.sleep(self.pet_conf.refresh)
    
    def kill(self):
        self.is_paused = False
        self.is_killed = True

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False
    

    def random_act(self) -> None:
        """
        随机执行动作
        :return:
        """

        # 选取随机动作执行
        prob_num = random.uniform(0, 1)
        act_index = sum([int(prob_num > self.pet_conf.act_prob[i]) for i in range(len(self.pet_conf.act_prob))])
        acts = self.pet_conf.random_act[act_index] #random.choice(self.pet_conf.random_act)
        self._run_acts(acts)

    def _run_acts(self, acts: List[Act]) -> None:
        """
        执行动画, 将一个动作相关的图片循环展示
        :param acts: 一组关联动作
        :return:
        """
        for act in acts:
            self._run_act(act)
        #self.is_run_act = False

    def _run_act(self, act: Act) -> None:
        """
        加载图片执行移动
        :param act: 动作
        :return:
        """
        for i in range(act.act_num):

            while self.is_paused:
                time.sleep(0.2)
            if self.is_killed:
                break

            for img in act.images:

                while self.is_paused:
                    time.sleep(0.2)
                if self.is_killed:
                    break

                global current_img, previous_img
                previous_img = current_img
                current_img = img
                self.sig_setimg_anim.emit()
                time.sleep(act.frame_refresh)

                self._move(act) #self.pos(), act)

                self.sig_repaint_anim.emit()
    '''
    def _static_act(self, pos: QPoint) -> None:
        """
        静态动作判断位置 - 目前舍弃不用
        :param pos: 位置
        :return:
        """
        screen_geo = QDesktopWidget().screenGeometry()
        screen_width = screen_geo.width()
        screen_height = screen_geo.height()
        border = self.pet_conf.size
        new_x = pos.x()
        new_y = pos.y()
        if pos.x() < border:
            new_x = screen_width - border
        elif pos.x() > screen_width - border:
            new_x = border
        if pos.y() < border:
            new_y = screen_height - border
        elif pos.y() > screen_height - border:
            new_y = border
        self.move(new_x, new_y)
    '''

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

        self.sig_move_anim.emit(plus_x, plus_y)






class Interaction_worker(QObject):

    sig_setimg_inter = pyqtSignal(name='sig_setimg_inter')
    sig_move_inter = pyqtSignal(float, float, name='sig_move_inter')
    sig_repaint_inter = pyqtSignal()

    def __init__(self, pet_conf, parent=None):
        """
        Interaction Module
        Respond immediately to signals and run functions defined
        
        pet_conf: PetConfig class object in Main Widgets

        """
        super(Interaction_worker, self).__init__(parent)
        self.pet_conf = pet_conf
        self.is_killed = False
        self.is_paused = False
        self.act_name = None # everytime making act_name to None, don't forget to set playid to 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.run)
        self.timer.start(self.pet_conf.interact_speed)

    def run(self):
        #print('start_run')
        if self.act_name is None:
            return
        else:
            getattr(self,self.act_name)()

    def start_interact(self, act_name):
        self.act_name = act_name
    
    def kill(self):
        self.is_paused = False
        self.is_killed = True
        self.timer.stop()
        # terminate thread

    def pause(self):
        self.is_paused = True
        self.timer.stop()

    def resume(self):
        self.is_paused = False

    def img_from_act(self, acts):
        global playid
        global current_img, previous_img

        n_repeat = math.ceil(acts.frame_refresh / (self.pet_conf.interact_speed / 1000))
        img_list_expand = [item for item in acts.images for i in range(n_repeat)]
        img = img_list_expand[playid]

        playid += 1
        if playid >= len(img_list_expand):
            playid = 0
        img = acts.images[0]
        previous_img = current_img
        current_img = img
        #print(previous_img)
        #print(current_img)
        

    def mousedrag(self):
        global dragging, onfloor, set_fall
        global playid
        global current_img, previous_img
        # Falling is OFF
        if not set_fall:
            if draging==1:
                acts = self.pet_conf.drag

                self.img_from_act(acts)
                if previous_img != current_img:
                    self.sig_setimg_inter.emit()
                
            else:
                self.act_name = None
                playid = 0

        # Falling is ON
        elif set_fall==1 and onfloor==0:
            if draging==1:
                acts = self.pet_conf.drag
                self.img_from_act(acts)
                if previous_img != current_img:
                    self.sig_setimg_inter.emit()

            elif draging==0:
                acts = self.pet_conf.fall
                self.img_from_act(acts)

                global fall_right
                if fall_right:
                    previous_img = current_img
                    current_img = current_img.mirrored(True, False)
                if previous_img != current_img:
                    self.sig_setimg_inter.emit()

                self.drop()

        else:
            self.act_name = None
            playid = 0

        self.sig_repaint_inter.emit()

                
            

        #elif set_fall==0 and onfloor==0:

    def drop(self):
        #掉落
        #print("Dropping")
        #global petleft,pettop
        global dragspeedx, dragspeedy

        ##print(dragspeedx)
        ##print(dragspeedy)
        #dropnext=pettop+info.gravity*dropa-info.gravity/2
        plus_y = dragspeedy #+ self.pet_conf.dropspeed
        plus_x = dragspeedx
        dragspeedy = dragspeedy + self.pet_conf.gravity

        self.sig_move_inter.emit(plus_x, plus_y)




class PetWidget(QWidget):
    def __init__(self, parent=None, curr_pet_name='', pets=()):
        """
        宠物组件
        :param parent: 父窗口
        :param curr_pet_name: 当前宠物名称
        :param pets: 全部宠物列表
        """
        super(PetWidget, self).__init__(parent, flags=Qt.WindowFlags())
        self.curr_pet_name = ''
        self.pet_conf = PetConfig()
        self.image = None
        self.label = QLabel(self)

        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

        # Some geo info
        self.screen_geo = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()

        self._init_widget()
        self.init_conf(curr_pet_name if curr_pet_name else pets[0])

        self._set_menu(pets)
        self._set_tray()
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
            global onfloor,draging
            onfloor=0
            draging=1
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
        global mouseposx1,mouseposx2,mouseposx3,mouseposx4,mouseposx5
        global mouseposy1,mouseposy2,mouseposy3,mouseposy4,mouseposy5

        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            
            #mouseposx5=mouseposx4
            mouseposx4=mouseposx3
            mouseposx3=mouseposx2
            mouseposx2=mouseposx1
            mouseposx1=QCursor.pos().x()
            #mouseposy5=mouseposy4
            mouseposy4=mouseposy3
            mouseposy3=mouseposy2
            mouseposy2=mouseposy1
            mouseposy1=QCursor.pos().y()
            

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

            global onfloor,draging,playid,set_fall
            #playid=0
            onfloor=0
            draging=0
            if set_fall == 1:
                global dragspeedx,dragspeedy,mouseposx1,mouseposx3,mouseposy1,mouseposy3,fixdragspeedx,fixdragspeedy
                dragspeedx=(mouseposx1-mouseposx3)/2*fixdragspeedx
                dragspeedy=(mouseposy1-mouseposy3)/2*fixdragspeedy
                mouseposx1=mouseposx3=0
                mouseposy1=mouseposy3=0
                global fall_right
                if dragspeedx > 0:
                    fall_right = 1
                else:
                    fall_right = 0

            else:
                self._move_customized(0,0)
                global current_img
                current_img = self.pet_conf.default.images[0]
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
        self.resize(self.pet_conf.width, self.pet_conf.height)
    '''
    def _init_img(self, img: QImage) -> None:
        """
        初始化窗体图片
        :param img:
        :return:
        """
        global current_img
        current_img = img
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
        change_acts = [_build_change_act(name, change_menu, self._change_pet) for name in pets]
        change_menu.addActions(change_acts)
        menu.addMenu(change_menu)

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
        self.init_conf(pet_name)
        # stop animation thread and start again
        self.stop_thread('Animation')
        self.stop_thread('Interaction')
        
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
        pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, pic_dict)
        #self.label.resize(self.pet_conf.width, self.pet_conf.height)

        # 初始位置
        screen_geo = QDesktopWidget().availableGeometry()
        screen_width = screen_geo.width()
        work_height = screen_geo.height()
        x=int(screen_width*0.8)
        y=work_height-self.pet_conf.default.images[0].height() #64
        # make sure that for all stand png, png bottom is the ground
        self.floor_pos = work_height-self.pet_conf.default.images[0].height()
        self.move(x,y)

        global current_img, previous_img
        previous_img = current_img
        current_img = list(pic_dict.values())[0] 
        self.set_img()
        self.border = self.pet_conf.width/2


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
        global current_img
        self.label.resize(current_img.width(), current_img.height())
        self.label.setPixmap(QPixmap.fromImage(current_img))
        self.image = current_img


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
        global set_fall
        sender = self.sender()
        if sender.text()=="禁用掉落":
            sender.setText("开启掉落")
            set_fall=0
        else:
            sender.setText("禁用掉落")
            set_fall=1 

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
        self.workers['Interaction'].sig_repaint_inter.connect(self.repaint)

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
            global onfloor
            if onfloor == 0:
                onfloor = 1
                global current_img
                current_img = self.pet_conf.default.images[0]
                self.set_img()
                #print('on floor check')
                self.workers['Animation'].resume()

        self.move(new_x, new_y)




def _load_all_pic(pet_name: str) -> dict:
    """
    加载宠物所有动作图片
    :param pet_name: 宠物名称
    :return: {动作编码: 动作图片}
    """
    img_dir = 'res/role/{}/action/'.format(pet_name)
    images = os.listdir(img_dir)
    return {image.split('.')[0]: _get_q_img(img_dir + image) for image in images}


def _build_change_act(pet_name: str, parent: QObject, act_func) -> QAction:
    """
    构建改变菜单动作
    :param pet_name: 菜单动作名称
    :param parent 父级菜单
    :param act_func: 菜单动作函数
    :return:
    """
    act = QAction(pet_name, parent)
    act.triggered.connect(lambda: act_func(pet_name))
    return act


def _get_q_img(img_path: str) -> QImage:
    """
    将图片路径加载为 QImage
    :param img_path: 图片路径
    :return: QImage
    """
    image = QImage()
    image.load(img_path)
    #image = image.scaled(int(image.width()*self.pet_conf.scale), 
    #                     int(image.height()*self.pet_conf.scale),
    #                     aspectRatioMode=Qt.KeepAspectRatio)
    return image


if __name__ == '__main__':
    # 加载所有角色, 启动应用并展示第一个角色
    pets = read_json('res/pets.json')
    app = QApplication(sys.argv)
    p = PetWidget(pets=pets)
    sys.exit(app.exec_())



