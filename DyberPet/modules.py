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

from DyberPet.utils import *
from DyberPet.conf import *

#from win32api import GetMonitorInfo, MonitorFromPoint


import DyberPet.settings as settings



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
        # 如果菜单已打开, 则关闭菜单
        #if self.menu.isEnabled():
        #    self.menu.close()

        #if self.is_run_act:
        #    return

        #self.is_run_act = True
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

                #global current_img, previous_img
                settings.previous_img = settings.current_img
                settings.current_img = img
                self.sig_setimg_anim.emit()
                time.sleep(act.frame_refresh) ######## sleep 和 move 是不是应该反过来？
                #if act.need_move:
                self._move(act) #self.pos(), act)
                #else:
                #    self._static_act(self.pos())
                self.sig_repaint_anim.emit()

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

    def _move(self, act: QAction) -> None: #pos: QPoint, act: QAction) -> None:
        """
        移动动作
        :param pos: 当前位置
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
    #sig_repaint_inter = pyqtSignal()
    sig_act_finished = pyqtSignal()

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
        self.interact = None
        self.act_name = None # everytime making act_name to None, don't forget to set settings.playid to 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.run)
        self.timer.start(self.pet_conf.interact_speed)

    def run(self):
        #print('start_run')
        if self.interact is None:
            return
        elif self.interact not in dir(self):
            self.interact = None
        else:
            getattr(self,self.interact)(self.act_name)

    def start_interact(self, interact, act_name=None):
        self.interact = interact
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

    def img_from_act(self, act):
        #global playid
        #global current_img, previous_img
        #global current_act, previous_act

        if settings.current_act != act:
            settings.previous_act = settings.current_act
            settings.current_act = act
            settings.playid = 0

        n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
        img_list_expand = [item for item in act.images for i in range(n_repeat)]
        img = img_list_expand[settings.playid]

        settings.playid += 1
        if settings.playid >= len(img_list_expand):
            settings.playid = 0
        #img = act.images[0]
        settings.previous_img = settings.current_img
        settings.current_img = img
        #print(previous_img)
        #print(current_img)

    def animat(self, act_name):

        #global playid, act_id
        #global current_img, previous_img

        acts_index = self.pet_conf.random_act_name.index(act_name)
        acts = self.pet_conf.random_act[acts_index]

        if settings.act_id >= len(acts):
            settings.act_id = 0
            self.interact = None
            self.sig_act_finished.emit()
        else:
            act = acts[settings.act_id]
            n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if settings.playid >= n_repeat-1:
                settings.act_id += 1

            if settings.previous_img != settings.current_img:
                self.sig_setimg_inter.emit()
                self._move(act)
        

    def mousedrag(self, act_name):
        #global dragging, onfloor, set_fall
        #global playid
        #global current_img, previous_img
        # Falling is OFF
        if not settings.set_fall:
            if settings.draging==1:
                acts = self.pet_conf.drag

                self.img_from_act(acts)
                if settings.previous_img != settings.current_img:
                    self.sig_setimg_inter.emit()
                
            else:
                self.act_name = None
                settings.playid = 0

        # Falling is ON
        elif settings.set_fall==1 and settings.onfloor==0:
            if settings.draging==1:
                acts = self.pet_conf.drag
                self.img_from_act(acts)
                if settings.previous_img != settings.current_img:
                    self.sig_setimg_inter.emit()

            elif settings.draging==0:
                acts = self.pet_conf.fall
                self.img_from_act(acts)

                #global fall_right
                if settings.fall_right:
                    previous_img = settings.current_img
                    settings.current_img = settings.current_img.mirrored(True, False)
                if settings.previous_img != settings.current_img:
                    self.sig_setimg_inter.emit()

                self.drop()

        else:
            self.act_name = None
            settings.playid = 0

        #self.sig_repaint_inter.emit()

                
            

        #elif set_fall==0 and onfloor==0:

    def drop(self):
        #掉落
        #print("Dropping")
        #global dragspeedx, dragspeedy

        ##print(dragspeedx)
        ##print(dragspeedy)
        #dropnext=pettop+info.gravity*dropa-info.gravity/2
        plus_y = settings.dragspeedy #+ self.pet_conf.dropspeed
        plus_x = settings.dragspeedx
        settings.dragspeedy = settings.dragspeedy + self.pet_conf.gravity

        self.sig_move_inter.emit(plus_x, plus_y)

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

        self.sig_move_inter.emit(plus_x, plus_y)
