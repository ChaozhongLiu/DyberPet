import sys
import time
import math
import uuid
import types
import random
import inspect
from typing import List
from datetime import datetime, timedelta

from apscheduler.schedulers.qt import QtScheduler
from apscheduler.triggers import interval, date, cron

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from DyberPet.utils import *
from DyberPet.conf import *
from DyberPet.extra_windows import QToaster


import DyberPet.settings as settings



##############################
#          动画模块
##############################
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
        self.hp_cut_off = [0,50,80,100]
        self.current_status = [settings.pet_data.hp_tier,settings.pet_data.fv_lvl] #self._cal_status_type()
        self.nonDefault_prob_list = [1, 0.05, 0.125, 0.25]
        self.nonDefault_prob = self.nonDefault_prob_list[self.current_status[0]]
        self.act_cmlt_prob = self._cal_prob(self.current_status)
        self.is_killed = False
        self.is_paused = False


    def run(self):
        """Run animation in a separate thread"""
        print('start running pet %s'%(self.pet_conf.petname))
        time.sleep(5)
        while not self.is_killed:
            #if self.is_hp:
            #    print(self.is_hp, self.is_fv)
            self.random_act()

            while self.is_paused:
                time.sleep(0.2)
            if self.is_killed:
                break

            #time.sleep(self.pet_conf.refresh)
    
    def kill(self):
        self.is_paused = False
        self.is_killed = True

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False


    def _cal_prob(self, current_status):
        act_prob = self.pet_conf.act_prob
        act_type = self.pet_conf.act_type

        new_prob = []
        for i in range(len(act_prob)):
            if (current_status[0] == 0) and (act_type[i][0] != 0):
                new_prob.append(0)
                continue
            elif current_status[1] < act_type[i][1]:
                new_prob.append(0)

            elif act_type[i][0] == 0:
                new_prob.append(act_prob[i] * int(current_status[0] == 0))

            elif act_type[i][0] == 1:
                new_prob.append(act_prob[i] * int(current_status[0] == 1))

            else:
                new_prob.append(act_prob[i] * (1/4)**(abs(act_type[i][0]-current_status[0])))

        if sum(new_prob) != 0:
            new_prob = [i/sum(new_prob) for i in new_prob]
            #print(new_prob)
            total = 0
            act_cmlt_prob = []
            for i in range(len(new_prob)):
                total += new_prob[i]
                act_cmlt_prob.append(total)
            act_cmlt_prob[-1] = 1.0
        else:
            act_cmlt_prob = [0] * len(new_prob)

        #print(self.pet_conf.act_name)
        #print(act_cmlt_prob)

        return act_cmlt_prob

        

    def hpchange(self, hp_tier, direction):
        self.current_status[0] = int(hp_tier)
        self.act_cmlt_prob = self._cal_prob(self.current_status)
        self.nonDefault_prob = self.nonDefault_prob_list[self.current_status[0]]
        #print('animation module is aware of the hp tier change!')

    def fvchange(self, fv_lvl):
        self.current_status[1] = int(fv_lvl)
        self.act_cmlt_prob = self._cal_prob(self.current_status)
        self.nonDefault_prob = self.nonDefault_prob_list[self.current_status[0]]
        #print('animation module is aware of the fv lvl change! %i'%fv_lvl)


    

    def random_act(self) -> None:
        """
        随机执行动作
        :return:
        """
        # 选取随机动作执行
        prob_num_0 = random.uniform(0, 1)
        if prob_num_0 < self.nonDefault_prob:
            prob_num = random.uniform(0, 1)
            act_index = sum([int(prob_num > self.act_cmlt_prob[i]) for i in range(len(self.act_cmlt_prob))])
            if act_index >= len(self.act_cmlt_prob):
                acts = [self.pet_conf.default]
            else:
                acts = self.pet_conf.random_act[act_index] #random.choice(self.pet_conf.random_act)
        else:
            acts = [self.pet_conf.default]
        self._run_acts(acts)

    def _run_acts(self, acts: List[Act]) -> None:
        """
        执行动画, 将一个动作相关的图片循环展示
        :param acts: 一组关联动作
        :return:
        """
        #start = time.time()
        for act in acts:
            self._run_act(act)
        #print('%.2fs'%(time.time()-start))
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
                settings.previous_anchor = settings.current_anchor
                settings.current_anchor = act.anchor
                #print('anim', settings.previous_anchor, settings.current_anchor)
                self.sig_setimg_anim.emit()
                #time.sleep(act.frame_refresh) ######## sleep 和 move 是不是应该反过来？
                #if act.need_move:
                self._move(act) #self.pos(), act)
                time.sleep(act.frame_refresh) 
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
        if plus_x == 0 and plus_y == 0:
            pass
        else:
            self.sig_move_anim.emit(plus_x, plus_y)




##############################
#          交互模块
##############################

class Interaction_worker(QObject):

    sig_setimg_inter = pyqtSignal(name='sig_setimg_inter')
    sig_move_inter = pyqtSignal(float, float, name='sig_move_inter')
    #sig_repaint_inter = pyqtSignal()
    sig_act_finished = pyqtSignal()
    sig_interact_note = pyqtSignal(str, str, name='sig_interact_note')

    acc_regist = pyqtSignal(dict, name='acc_regist')

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
        self.interact_altered = False
        self.hptier = [0, 50, 80, 100]

        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.run)
        #print(self.pet_conf.interact_speed)
        self.timer.start(self.pet_conf.interact_speed)
        #self.start = time.time()


    def run(self):
        #print(time.time()-self.start)
        #self.start = time.time()
        #print('start_run')
        if self.interact is None:
            return
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
    
    def kill(self):
        self.is_paused = False
        self.is_killed = True
        #self.timer.stop()
        # terminate thread

    def pause(self):
        self.is_paused = True
        #self.timer.stop()

    def resume(self):
        self.is_paused = False

    def stop_interact(self):
        self.interact = None
        self.act_name = None
        self.first_acc = False
        settings.playid = 0
        settings.act_id = 0
        self.sig_act_finished.emit()

    def empty_interact(self):
        settings.playid = 0
        settings.act_id = 0

    def img_from_act(self, act):

        if settings.current_act != act:
            settings.previous_act = settings.current_act
            settings.current_act = act
            settings.playid = 0

        n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
        img_list_expand = [item for item in act.images for i in range(n_repeat)] * act.act_num
        img = img_list_expand[settings.playid]

        settings.playid += 1
        if settings.playid >= len(img_list_expand):
            settings.playid = 0
        #img = act.images[0]
        settings.previous_img = settings.current_img
        settings.current_img = img
        settings.previous_anchor = settings.current_anchor
        settings.current_anchor = act.anchor
        #print(previous_img)
        #print(current_img)

    def animat(self, act_name):
        #if act_name == 'on_floor':
        #    print(settings.playid)

        #start = time.time()
        try:
            acts_index = self.pet_conf.act_name.index(act_name)
        except:
            self.stop_interact()
            return
        
        # 判断是否满足动作饱食度要求
        if settings.pet_data.hp_tier < self.pet_conf.act_type[acts_index][0]:
            self.sig_interact_note.emit('status_hp','[%s] 需要饱食度%i以上哦'%(act_name, self.hptier[self.pet_conf.act_type[acts_index][0]-1]))
            self.stop_interact()
            return
        
        acts = self.pet_conf.random_act[acts_index]
        #print(settings.act_id, len(acts))
        if settings.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            self.stop_interact()
            #self.sig_act_finished.emit()
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
        #print('%.5fs'%(time.time()-start))
        
    def anim_acc(self, acc_name):

        # 判断是否满足动作饱食度要求
        if settings.pet_data.hp_tier < self.pet_conf.accessory_act[acc_name]['act_type'][0]:
            self.sig_interact_note.emit('status_hp','[%s] 需要饱食度%i以上哦'%(acc_name, self.hptier[self.pet_conf.accessory_act[acc_name]['act_type'][0]-1]))
            self.stop_interact()
            return

        if self.first_acc:
            accs = self.pet_conf.accessory_act[acc_name]
            self.acc_regist.emit(accs)
            self.first_acc = False

        acts = self.pet_conf.accessory_act[acc_name]['act_list']

        if settings.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            self.stop_interact()
            #self.sig_act_finished.emit()
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

    def patpat(self, act_name):
        acts = [self.pet_conf.patpat]
        #print(settings.act_id, len(acts))
        if settings.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            self.stop_interact()
            #self.sig_act_finished.emit()
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

        # Falling is OFF
        if not settings.set_fall:
            if settings.draging==1:
                acts = self.pet_conf.drag

                self.img_from_act(acts)
                if settings.previous_img != settings.current_img:
                    self.sig_setimg_inter.emit()
                
            else:
                self.stop_interact()
                #self.interact = None
                #self.act_name = None
                #settings.playid = 0

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
                    settings.previous_img = settings.current_img
                    settings.current_img = settings.current_img.mirrored(True, False)
                if settings.previous_img != settings.current_img:
                    self.sig_setimg_inter.emit()

                self.drop()

        else:
            #self.stop_interact()
            self.interact = 'animat' #None
            self.act_name = 'onfloor' #None
            settings.playid = 0
            settings.act_id = 0

        #self.sig_repaint_inter.emit()

                
            

        #elif set_fall==0 and onfloor==0:

    def drop(self):
        #掉落
        #print("Dropping")

        ##print(dragspeedx)
        ##print(dragspeedy)
        #dropnext=pettop+info.gravity*dropa-info.gravity/2
        plus_y = settings.dragspeedy #+ self.pet_conf.dropspeed
        plus_x = settings.dragspeedx
        settings.dragspeedy = settings.dragspeedy + settings.gravity

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

        #self.sig_move_inter.emit(plus_x, plus_y)
        if plus_x == 0 and plus_y == 0:
            pass
        else:
            self.sig_move_inter.emit(plus_x, plus_y)

    def use_item(self, item):
        # 宠物进行 喂食动画
        if item in self.pet_conf.item_favorite:
            #print('animation 1 here!')
            self.start_interact('animat','feed_1')
        elif item in self.pet_conf.item_dislike:
            #print('animation 3 here!')
            self.start_interact('animat','feed_3')
        else:
            #print('animation 2 here!')
            self.start_interact('animat','feed_2')

        '''
        self.interact = 'animat' #None
        self.act_name = 'onfloor' #None
        settings.playid = 0
        settings.act_id = 0
        '''
        #self.stop_interact()
        return

    def use_clct(self, item):
        if item in self.pet_conf.act_name:
            self.start_interact('animat', item)
        elif item in self.pet_conf.acc_name:
            self.start_interact('anim_acc', item)
        else:
            self.stop_interact()

        return




##############################
#          计划任务
##############################
class Scheduler_worker(QObject):
    sig_settext_sche = pyqtSignal(str, str, name='sig_settext_sche')
    sig_setact_sche = pyqtSignal(str, name='sig_setact_sche')
    sig_setstat_sche = pyqtSignal(str, int, name='sig_setstat_sche')
    sig_focus_end = pyqtSignal(name='sig_focus_end')
    sig_tomato_end = pyqtSignal(name='sig_tomato_end')
    sig_settime_sche = pyqtSignal(str, int, name='sig_settime_sche')
    sig_addItem_sche = pyqtSignal(int, name='sig_addItem_sche')


    def __init__(self, parent=None):
        """
        Scheduler Module
        Time-related processor

        """
        super(Scheduler_worker, self).__init__(parent)
        #self.pet_conf = pet_conf
        self.is_killed = False
        self.is_paused = False
        #self.activated_times = 0
        self.new_task = False
        self.task_name = None
        self.n_tomato = None
        self.n_tomato_now = None
        self.focus_on = False
        self.tomato_list = []
        self.focus_time = 0
        #self.time_wait=None
        #self.time_torun=None

        self.scheduler = QtScheduler()
        #self.scheduler.add_job(self.change_hp, 'interval', minutes=self.pet_conf.hp_interval)
        self.scheduler.add_job(self.change_hp, interval.IntervalTrigger(minutes=1)) #self.pet_conf.hp_interval))
        #self.scheduler.add_job(self.change_em, 'interval', minutes=self.pet_conf.em_interval)
        self.scheduler.add_job(self.change_fv, interval.IntervalTrigger(minutes=1)) #self.pet_conf.fv_interval))
        self.scheduler.start()


    def run(self):
        """Run Scheduler in a separate thread"""
        #time.sleep(10)
        now_time = datetime.now().hour
        greet_type, greet_text = self.greeting(now_time)
        self.show_dialogue(greet_type, greet_text)
        
    
    def kill(self):
        self.is_paused = False
        self.is_killed = True
        self.scheduler.shutdown()


    def pause(self):
        self.is_paused = True
        self.scheduler.pause()


    def resume(self):
        self.is_paused = False
        self.scheduler.resume()


    def greeting(self, time):
        if 11 >= time >= 0:
            return 'greeting_1', '早上好!'
        elif 13 >= time >= 12:
            return 'greeting_2', '中午好!'
        elif 18 >= time >= 14:
            return 'greeting_3', '下午好！'
        elif 22 >= time >= 19:
            return 'greeting_4', '晚上好!'
        elif 24 >= time >= 23:
            return 'greeting_5', '该睡觉啦!'
        else:
            return 'None','None'


    def show_dialogue(self, note_type, texts_toshow):
        # 排队 避免对话显示冲突
        while settings.showing_dialogue_now:
            time.sleep(1)
        settings.showing_dialogue_now = True
        #print('show_dialogue check')

        #for text_toshow in texts_toshow:
        self.sig_settext_sche.emit(note_type, texts_toshow) #text_toshow)
        #    time.sleep(3)
        #self.sig_settext_sche.emit('None')
        settings.showing_dialogue_now = False

    def item_drop(self, n_minutes):
        #print(n_minutes)
        nitems = n_minutes // 10
        remains = n_minutes % 10
        chance_drop = random.choices([0,1], weights=(1-remains/10, remains/10))
        #print(chance_drop)
        nitems += chance_drop[0]
        #for test -----
        #nitems = 4
        #---------------
        if nitems > 0:
            self.sig_addItem_sche.emit(nitems)

    def add_tomato(self, n_tomato=None):

        if self.focus_on == False and self.n_tomato_now is None:
            self.n_tomato_now = n_tomato
            time_plus = 0 #25

            # 1-start
            task_text = 'tomato_first'
            time_torun = datetime.now() + timedelta(seconds=1)
            #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
            self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text])
            
            time_plus += 25
            #1-end
            if n_tomato == 1:
                task_text = 'tomato_last'
            else:
                task_text = 'tomato_end'
            time_torun = datetime.now() + timedelta(minutes=time_plus) #minutes=time_plus)
            #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
            self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text], id='tomato_0_end')
            self.tomato_list.append('tomato_0_end')
            time_plus += 5

            # others start and end
            if n_tomato > 1:
                for i in range(1, n_tomato):
                    #start
                    task_text = 'tomato_start'
                    time_torun = datetime.now() + timedelta(minutes=time_plus) #minutes=time_plus)
                    #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
                    self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text], id='tomato_%s_start'%i)
                    time_plus += 25
                    #end
                    if i == (n_tomato-1):
                        task_text = 'tomato_last'
                    else:
                        task_text = 'tomato_end'
                    time_torun = datetime.now() + timedelta(minutes=time_plus) #minutes=time_plus)
                    #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
                    self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text], id='tomato_%s_end'%i)
                    time_plus += 5
                    self.tomato_list.append('tomato_%s_start'%i)
                    self.tomato_list.append('tomato_%s_end'%i)

        elif self.focus_on:
            task_text = "focus_on"
            time_torun = datetime.now() + timedelta(seconds=1)
            self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text])
        else:
            task_text = "tomato_exist"
            time_torun = datetime.now() + timedelta(seconds=1)
            #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
            self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text])



    def run_tomato(self, task_text):
        text_toshow = ''
        finished = False

        if task_text == 'tomato_start':
            self.tomato_timeleft = 25
            self.scheduler.add_job(self.change_tomato, interval.IntervalTrigger(minutes=1), id='tomato_timer', replace_existing=True)
            self.sig_settime_sche.emit('tomato_start', self.tomato_timeleft)
            self.tomato_list = self.tomato_list[1:]
            text_toshow = '新的番茄时钟开始了哦！加油！'

        elif task_text == 'tomato_first':
            self.scheduler.add_job(self.change_tomato, interval.IntervalTrigger(minutes=1), id='tomato_timer', replace_existing=True)
            self.tomato_timeleft = 25
            self.sig_settime_sche.emit('tomato_start', self.tomato_timeleft)
            text_toshow = "%s个番茄时钟设定完毕！开始了哦！"%(int(self.n_tomato_now))

        elif task_text == 'tomato_end':
            self.tomato_timeleft = 5
            self.scheduler.add_job(self.change_tomato, interval.IntervalTrigger(minutes=1), id='tomato_timer', replace_existing=True)
            self.sig_settime_sche.emit('tomato_rest', self.tomato_timeleft)
            self.tomato_list = self.tomato_list[1:]
            text_toshow = '叮叮~ 番茄时间到啦！休息5分钟！'
            finished = True

        elif task_text == 'tomato_last':
            try:
                self.scheduler.remove_job('tomato_timer')
            except:
                pass
            self.tomato_timeleft = 0
            self.n_tomato_now=None
            self.tomato_list = []
            self.sig_tomato_end.emit()
            self.sig_settime_sche.emit('tomato_end', self.tomato_timeleft)
            text_toshow = '叮叮~ 番茄时间全部结束啦！'
            finished = True

        elif task_text == 'tomato_exist':
            self.sig_tomato_end.emit()
            self.sig_settime_sche.emit('tomato_end', 0)
            text_toshow = "不行！还有番茄钟在进行哦~"

        elif task_text == 'focus_on':
            self.sig_tomato_end.emit()
            self.sig_settime_sche.emit('tomato_end', 0)
            text_toshow = "不行！还有专注任务在进行哦~"

        elif task_text == 'tomato_cancel':
            self.n_tomato_now=None
            for iidd in self.tomato_list:
                self.scheduler.remove_job(iidd)
            self.tomato_list = []
            try:
                self.scheduler.remove_job('tomato_timer')
            except:
                pass
            self.tomato_timeleft = 0
            self.sig_settime_sche.emit('tomato_end', self.tomato_timeleft)
            self.sig_tomato_end.emit()
            text_toshow = "你的番茄时钟取消啦！"

        self.show_dialogue('clock_tomato',text_toshow)
        if finished:
            time.sleep(1)
            self.item_drop(n_minutes=30)
        #else:
        #    text_toshow = '叮叮~ 你的任务 [%s] 到时间啦！'%(task_text)

    def cancel_tomato(self):
        task_text = "tomato_cancel"
        time_torun_2 = datetime.now() + timedelta(seconds=1)
        self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun_2), args=[task_text])

    def change_hp(self):
        self.sig_setstat_sche.emit('hp', -1)

    def change_fv(self):
        self.sig_setstat_sche.emit('fv', 1)

    def change_tomato(self):
        self.tomato_timeleft += -1
        if self.tomato_timeleft <= 1:
            self.scheduler.remove_job('tomato_timer')
        self.sig_settime_sche.emit('tomato', self.tomato_timeleft)

    def change_focus(self):
        self.focus_time += -1
        if self.focus_time <= 1:
            self.scheduler.remove_job('focus_timer')
        self.sig_settime_sche.emit('focus', self.focus_time)


    def add_focus(self, time_range=None, time_point=None):
        if self.n_tomato_now is not None:
            task_text = "tomato_exist"
            time_torun = datetime.now() + timedelta(seconds=1)
            self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text])

        elif self.focus_on:
            task_text = "focus_exist"
            time_torun = datetime.now() + timedelta(seconds=1)
            self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text])

        elif time_range is not None:
            if sum(time_range) == 0:
                return
            else:
                self.focus_on = True
                task_text = "focus_start"
                time_torun = datetime.now() + timedelta(seconds=1)
                self.focus_time = int(time_range[0]*60 + time_range[1])
                self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text])

                task_text = "focus_end"
                time_torun = datetime.now() + timedelta(hours=time_range[0], minutes=time_range[1])
                self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text,self.focus_time], id='focus')

        elif time_point is not None:
            now = datetime.now()
            time_torun = datetime(year=now.year, month=now.month, day=now.day,
                                  hour=time_point[0], minute=time_point[1], second=0) #now.second)
            time_diff = time_torun - now
            self.focus_time = time_diff.total_seconds() // 60
            '''
            if focus_time >= 1:
                self.focus_time = focus_time
            else:
                self.focus_time = time_diff.total_seconds() / 60
            '''

            if time_diff <= timedelta(0):
                time_torun = time_torun + timedelta(days=1)
                self.focus_time += 24*60

                self.focus_on = True
                task_text = "focus_start_tomorrow"
                time_torun_2 = datetime.now() + timedelta(seconds=1)
                self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun_2), args=[task_text])

                task_text = "focus_end"
                self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text,self.focus_time], id='focus')
            else:
                self.focus_on = True
                task_text = "focus_start"
                time_torun_2 = datetime.now() + timedelta(seconds=1)
                self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun_2), args=[task_text])

                task_text = "focus_end"
                self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text,self.focus_time], id='focus')

    def run_focus(self, task_text, n_minutes=0):
        text_toshow = ''
        finished = False

        if task_text == 'tomato_exist':
            self.sig_focus_end.emit()
            self.sig_settime_sche.emit('focus_end', 0)
            text_toshow = '不行！还有番茄钟在进行哦~'

        elif task_text == 'focus_exist':
            self.sig_focus_end.emit()
            self.sig_settime_sche.emit('focus_end', 0)
            text_toshow = "不行！还有专注任务在进行哦~"

        elif task_text == 'focus_start':
            if self.focus_time > 1:
                self.scheduler.add_job(self.change_focus, interval.IntervalTrigger(minutes=1), id='focus_timer', replace_existing=True)
            #elif self.focus_time < 1:
            #    print(self.focus_time)
                #focus_time_sec = int()
            self.sig_settime_sche.emit('focus_start', self.focus_time)
            text_toshow = "你的专注任务开始啦！"

        elif task_text == 'focus_start_tomorrow':
            if self.focus_time > 1:
                self.scheduler.add_job(self.change_focus, interval.IntervalTrigger(minutes=1), id='focus_timer', replace_existing=True)
            self.sig_settime_sche.emit('focus_start', self.focus_time)
            text_toshow = "专注任务开始啦！\n但设定在明天，请确认无误哦~"

        elif task_text == 'focus_end':
            self.focus_time = 0
            try:
                self.scheduler.remove_job('focus_timer')
            except:
                pass
            self.sig_settime_sche.emit('focus_end', self.focus_time)
            self.focus_on = False
            self.sig_focus_end.emit()
            text_toshow = "你的专注任务结束啦！"
            finished = True

        elif task_text == 'focus_cancel':
            self.focus_time = 0
            try:
                self.scheduler.remove_job('focus_timer')
            except:
                pass
            self.sig_settime_sche.emit('focus_end', self.focus_time)
            self.sig_focus_end.emit()
            self.focus_on = False
            text_toshow = "你的专注任务取消啦！"
            finished = True

        elif task_text == 'focus_pause':
            try:
                self.scheduler.remove_job('focus_timer')
            except:
                pass
            #self.sig_settime_sche.emit('focus_end', self.focus_time)
            #self.sig_focus_end.emit()
            #self.focus_on = False
            text_toshow = "你的专注任务暂停啦！"

        elif task_text == 'focus_resume':
            if self.focus_time > 1:
                self.scheduler.add_job(self.change_focus, interval.IntervalTrigger(minutes=1), id='focus_timer', replace_existing=True)

            self.sig_settime_sche.emit('focus', self.focus_time)
            text_toshow = "你的专注任务继续进行啦！"
        
        self.show_dialogue('clock_focus', text_toshow)
        if finished:
            time.sleep(1)
            self.item_drop(n_minutes)

    def pause_focus(self):
        self.scheduler.remove_job('focus')
        task_text = "focus_pause"
        time_torun_2 = datetime.now() + timedelta(seconds=1)
        self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun_2), args=[task_text])

    def resume_focus(self, remains, total):
        task_text = "focus_resume"
        self.focus_time = remains
        time_torun = datetime.now() + timedelta(seconds=1)
        self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text])

        task_text = "focus_end"
        time_torun = datetime.now() + timedelta(minutes=remains)
        self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text,total], id='focus')

    def cancel_focus(self, time_past):
        try:
            self.scheduler.remove_job('focus')
        except:
            pass
        task_text = "focus_cancel"
        time_torun_2 = datetime.now() + timedelta(seconds=1)
        self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun_2), args=[task_text,time_past])


    def add_remind(self, texts, time_range=None, time_point=None, repeat=False):
        if time_point is not None:
            if repeat:
                certain_minute = int(time_point[1])
                self.scheduler.add_job(self.run_remind,
                                       cron.CronTrigger(minute=certain_minute),
                                       args=[texts])
            else:
                certain_day = datetime.now().day
                certain_hour = int(time_point[0])
                certain_minute = int(time_point[1])
                if certain_hour < datetime.now().hour:
                    certain_day = (datetime.now() + timedelta(days=1)).day
                self.scheduler.add_job(self.run_remind,
                                       cron.CronTrigger(day=certain_day,
                                                        hour=certain_hour,
                                                        minute=certain_minute),
                                       args=[texts])

        elif time_range is not None:
            if repeat:
                interval_minute = int(time_range[1])
                self.scheduler.add_job(self.run_remind,
                                       interval.IntervalTrigger(minutes=interval_minute),
                                       args=[texts])
            else:
                if sum(time_range) == 0:
                    return
                else:
                    time_torun = datetime.now() + timedelta(hours=time_range[0], minutes=time_range[1])
                    self.scheduler.add_job(self.run_remind,
                                           date.DateTrigger(run_date=time_torun),
                                           args=[texts])

        time_torun_2 = datetime.now() + timedelta(seconds=1)
        self.scheduler.add_job(self.run_remind,
                               date.DateTrigger(run_date=time_torun_2),
                               args=['remind_start'])

    def run_remind(self, task_text):
        if task_text == 'remind_start':
            text_toshow = "提醒事项设定完成！"
        else:
            text_toshow = '叮叮~ 时间到啦\n[ %s ]'%task_text
        
        self.show_dialogue('clock_remind',text_toshow)

        





