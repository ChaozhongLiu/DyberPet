import sys
from sys import platform
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

from PySide6.QtCore import Qt, QTimer, QObject, QPoint
from PySide6.QtGui import QImage, QPixmap, QIcon, QCursor, QAction, QTransform
from PySide6.QtWidgets import *
from PySide6.QtCore import QObject, QThread, Signal

from DyberPet.utils import *
from DyberPet.conf import *
from DyberPet.llm_client import LLMClient

import DyberPet.settings as settings
basedir = settings.BASEDIR

# system config
sys_hp_tiers = settings.HP_TIERS #[0,50,80,100] #Line 48, 289
sys_nonDefault_prob = [1, 0.125, 0.25, 0.5] #Line 50


##############################
#       Animation Module
##############################

class Animation_worker(QObject):
    sig_setimg_anim = Signal(name='sig_setimg_anim')
    sig_move_anim = Signal(float, float, name='sig_move_anim')
    sig_repaint_anim = Signal()
    acc_regist = Signal(dict, name='acc_regist')

    def __init__(self, pet_conf, parent=None):
        """
        Animation Module
        Display user-defined animations randomly
        :param pet_conf: PetConfig class object in Main Widgets

        """
        super(Animation_worker, self).__init__(parent)
        self.pet_conf = pet_conf
        self.hp_cut_off = sys_hp_tiers #[0,50,80,100]
        self.current_status = [settings.pet_data.hp_tier,settings.pet_data.fv_lvl] #self._cal_status_type()
        self.nonDefault_prob_list = sys_nonDefault_prob #[1, 0.05, 0.125, 0.25]
        self.nonDefault_prob = self.nonDefault_prob_list[self.current_status[0]]
        self.act_cmlt_prob = self._cal_prob(self.current_status)
        self.is_killed = False
        self.is_paused = False


        # 用于存储LLM相关状态
        self.llm_enabled = hasattr(settings, 'llm_config') and settings.llm_config.get('enabled', False)
        self.last_llm_interaction_time = time.time() - 3600  # 初始化为一小时前
        self.llm_interaction_cooldown = 300  # 默认5分钟冷却时间
        # #/

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
        """
        恢复交互动画
        
        功能说明：
        - 清除暂停标志，使动画继续更新
        - 与pause()方法配对使用
        """
        self.is_paused = False

    def update_prob(self):
        self.current_status = [settings.pet_data.hp_tier,settings.pet_data.fv_lvl] #self._cal_status_type()
        self.nonDefault_prob = self.nonDefault_prob_list[self.current_status[0]]
        self.act_cmlt_prob = self._cal_prob(self.current_status)

    def _cal_prob(self, current_status):
        act_conf = settings.act_data.allAct_params[settings.petname]
        act_name = [ k for k,v in act_conf.items() ]
        act_prob = [ act_conf[k]['act_prob'] for k in act_name ] #self.pet_conf.act_prob
        act_type = [ act_conf[k]['status_type'] for k in act_name ]
        act_unlocked = [ act_conf[k]['unlocked'] for k in act_name ]
        act_inlist = [ act_conf[k]['in_playlist'] for k in act_name ]

        #if v['in_playlist'] and v['status_type'][1]<= current_status[1]

        new_prob = []
        for i in range(len(act_name)):
            if not act_unlocked[i]:
                new_prob.append(0)
                continue

            if (current_status[0] == 0) and (act_type[i][0] != 0):
                new_prob.append(0)
                
            elif current_status[1] < act_type[i][1]:
                new_prob.append(0)

            elif act_type[i][0] == 0:
                new_prob.append(act_prob[i] * int(current_status[0] == 0))

            else:
                new_prob.append(act_prob[i] * (1/4)**(abs(act_type[i][0]-current_status[0])) * int(act_inlist[i]))

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

        act_cmlt_prob = [round(i,3) for i in act_cmlt_prob]
        #print(act_name)
        #print(act_cmlt_prob)
        return act_cmlt_prob

        

    def hpchange(self, hp_tier, direction):
        self.current_status[0] = int(hp_tier)
        self.act_cmlt_prob = self._cal_prob(self.current_status)
        self.nonDefault_prob = self.nonDefault_prob_list[self.current_status[0]]
        #print('animation module is aware of the hp tier change!')

    def fvchange(self, fv_lvl):
        self.current_status[1] = int(fv_lvl)
        settings.act_data._pet_refreshed(fv_lvl)
        self.act_cmlt_prob = self._cal_prob(self.current_status)
        self.nonDefault_prob = self.nonDefault_prob_list[self.current_status[0]]
        #print('animation module is aware of the fv lvl change! %i'%fv_lvl)


    def random_act(self) -> None:
        """
        随机执行动作的核心方法
        该方法根据当前状态(专注模式、饱食度等)选择并执行宠物动画

        主要功能：
        1. 判断是否处于专注模式，如是则播放专注动画
        2. 根据动画概率表选择要播放的动画
        3. 处理动画和配件的执行
        4. 根据LLM响应选择智能行为（如果启用）

        执行流程：
        1. 初始化动作和配件变量
        2. 根据不同条件选择动画
        3. 执行选中的动画序列

        :return: None
        """
        # 初始化动作和配件列表
        acts = None  # 存储将要执行的动作序列
        accs = None  # 存储动作相关的配件
        # print("[+] self.act_cmlt_prob",self.act_cmlt_prob)

        # 判断是否处于专注模式，如果是且有专注动画，则播放专注动画
        # 对应act_conf中的focus动作，通常是一个单独的动作序列
        if settings.focus_timer_on and self.pet_conf.focus:
            acts = [self.pet_conf.focus]

        # 如果只有一个动画(概率表中只有0和1)，则选择默认动画模式
        # 对应act_conf中的default动作，通常是角色的待机动画
        
        elif set(self.act_cmlt_prob) == set([0,1]):
            # 计算动画索引并获取动画名称
            act_idx = sum([i < 1.0 for i in self.act_cmlt_prob])
            act_name = list(settings.act_data.allAct_params[settings.petname].keys())[act_idx]
            # 获取动作和配件信息
            # 这里会调用_get_acts获取动作序列和配件信息
            acts, accs = self._get_acts(act_name)

        # 随机动画模式
        else:
            # 生成随机数决定是否播放随机动画
            # 对应act_conf中random_act部分的动作概率计算
            prob_num_0 = random.uniform(0, 1)
            # 如果随机数大于非默认动画概率，播放默认动画
            if prob_num_0 > self.nonDefault_prob:
                acts = [self.pet_conf.default]
            # 选择随机动画
            else:
                # 生成新的随机数用于选择具体的动画
                prob_num = random.uniform(0, 1)
                # 根据累积概率选择动画索引
                # 这里使用act_conf中每个动作的act_prob进行加权选择
                act_idx = sum([ i < prob_num for i in self.act_cmlt_prob])
                # 如果没有找到合适的动画(例如没有随机动画)，使用默认动画
                if act_idx >= len(self.act_cmlt_prob):
                    acts = [self.pet_conf.default]
                else:
                    # 获取选中动画的名称和相关信息
                    act_name = list(settings.act_data.allAct_params[settings.petname].keys())[act_idx]
                    acts, accs = self._get_acts(act_name)

        # 执行选中的动画序列和配件
        self._run_acts(acts, accs)

    
    def _get_acts(self, act_name):
        # 从act_conf中获取动作配置
        act_conf = settings.act_data.allAct_params[settings.petname][act_name]
        act_type = act_conf['act_type']
        if act_type == 'random_act':
            # 对应act_conf中random_act部分的动作列表
            # 包含act_list(动作序列)、act_prob(概率)等参数
            act_index = self.pet_conf.act_name.index(act_name)
            acts = self.pet_conf.random_act[act_index]
            accs = None
        
        elif act_type == 'accessory_act':
            # 对应act_conf中accessory_act部分
            # 包含act_list(主体动作)、acc_list(配件动作)、anchor(锚点)等参数
            acts = self.pet_conf.accessory_act[act_name]['act_list']
            accs = {'acc_list': self.pet_conf.accessory_act[act_name]['acc_list'],
                    'anchor': self.pet_conf.accessory_act[act_name]['anchor'],
                    'follow_main': self.pet_conf.accessory_act[act_name].get('follow_main', False),
                    'speed_follow_main': self.pet_conf.accessory_act[act_name].get('speed_follow_main', 5),
                    'follow_mouse': self.pet_conf.accessory_act[act_name].get('follow_mouse', False)}
        elif act_type == 'customized':
            # 对应用户自定义的动作
            # 可以包含自定义的动作序列和配件
            acts = self.pet_conf.custom_act[act_name]['act_list']
            if self.pet_conf.custom_act[act_name]['acc_list']:
                accs = {'acc_list': self.pet_conf.custom_act[act_name]['acc_list'],
                        'anchor': self.pet_conf.custom_act[act_name]['anchor'],
                        'name': 'customized_acc' # For Accessory module to judge the type
                        }
            else:
                accs = None
        else:
            acts = None
            accs = None

        return acts, accs


    def _run_acts(self, acts: List[Act], accs: List[Act] = None) -> None:
        """
        执行动画, 将一个动作相关的图片循环展示
        :param acts: 一组关联动作
        :return:
        """
        #start = time.time()
        if accs:
            self.acc_regist.emit(accs)
        for act in acts:
            self._run_act(act)
        #print('%.2fs'%(time.time()-start))
        #self.is_run_act = False
        
    # def trigger_llm_interaction(self):
    #     """
    #     触发与LLM的交互，生成宠物的自主行为
    #     """
    #     if not self.llm_enabled:
    #         return
            
    #     # 准备上下文信息
    #     pet_status = {
    #         'hp': settings.pet_data.hp,
    #         'fv': settings.pet_data.fv,
    #         'hp_tier': settings.pet_data.hp_tier,
    #         'fv_lvl': settings.pet_data.fv_lvl,
    #         'time': datetime.now().strftime("%H:%M"),
    #         'pet_name': settings.petname
    #     }
        
    #     # 构建提示语
    #     context = f"你是{settings.petname}，一个可爱的桌面宠物。现在是{pet_status['time']}，"
    #     context += f"你的饱食度是{pet_status['hp']}，好感度是{pet_status['fv']}。"
        
    #     # 根据状态添加额外信息
    #     if pet_status['hp_tier'] == 0:
    #         context += "你现在非常饿，需要食物。"
    #     elif pet_status['hp_tier'] == 1:
    #         context += "你有点饿了。"
        
    #     context += "请生成一句简短的对话气泡内容，表达你当前的心情或想法，并指定一个合适的动作。"
        
    #     # 异步获取LLM响应
    #     self.llm_client.get_pet_response(context)
    
    # def handle_llm_response(self, response):
    #     """
    #     处理LLM的响应，触发相应的气泡和行为
        
    #     Args:
    #         response: 可以是字符串或字典（结构化输出）
    #     """
    #     if not response:
    #         return
        
    #     # 检查是否为结构化响应
    #     if isinstance(response, dict):
    #         # 处理结构化响应
    #         self._handle_structured_response(response)
    #     else:
    #         # 处理普通文本响应
    #         # 限制响应长度
    #         if len(response) > 50:
    #             response = response[:47] + "..."
                
    #         # 触发气泡显示
    #         bubble_data = {
    #             "icon": None,
    #             "message": response,
    #             "countdown": None,
    #             "start_audio": None,
    #             "end_audio": None
    #         }
            
    #         # 如果BubbleManager存在，则触发气泡
    #         if hasattr(settings, 'bubble_manager'):
    #             settings.bubble_manager.register_bubble.emit(bubble_data)
                
    # def _handle_structured_response(self, response_dict):
    #     """
    #     处理结构化的LLM响应
        
    #     Args:
    #         response_dict: 包含text、emotion、action和priority字段的字典
    #     """
    #     # 提取响应内容
    #     text = response_dict.get("text", "")
    #     emotion = response_dict.get("emotion", "正常")
    #     action = response_dict.get("action", "")
    #     priority = response_dict.get("priority", 1)
        
    #     # 限制文本长度
    #     if len(text) > 50:
    #         text = text[:47] + "..."
        
    #     # 触发气泡显示
    #     bubble_data = {
    #         "icon": None,
    #         "message": text,
    #         "countdown": None,
    #         "start_audio": None,
    #         "end_audio": None
    #     }
        
    #     # 如果BubbleManager存在，则触发气泡
    #     if hasattr(settings, 'bubble_manager'):
    #         settings.bubble_manager.register_bubble.emit(bubble_data)
        
    #     # 根据情绪和动作触发相应行为
    #     self._trigger_emotion_action(emotion, action, priority)
    
    # def _trigger_emotion_action(self, emotion, action, priority):
    #     """
    #     根据情绪和动作触发相应的宠物行为
        
    #     Args:
    #         emotion: 情绪状态，如'高兴'、'难过'、'生气'、'惊讶'、'正常'
    #         action: 动作指令，如'跳跃'、'睡觉'等
    #         priority: 优先级，1-5的数字
    #     """
    #     # 根据情绪选择合适的动作
    #     emotion_act_map = {
    #         "高兴": ["happy", "jump"],
    #         "难过": ["sad", "cry"],
    #         "生气": ["angry"],
    #         "惊讶": ["surprise"],
    #         "正常": ["default"]
    #     }
        
    #     # 获取与情绪相关的动作列表
    #     candidate_acts = emotion_act_map.get(emotion, ["default"])
        
    #     # 如果指定了具体动作，尝试匹配
    #     if action and priority >= 3:  # 只有优先级较高时才考虑指定动作
    #         # 尝试在动作字典中查找匹配的动作
    #         for act_name in self.pet_conf.act_dict.keys():
    #             if action.lower() in act_name.lower():
    #                 # 找到匹配的动作，执行它
    #                 act = self.pet_conf.act_dict[act_name]
    #                 self._run_act(act)
    #                 return
        
    #     # 如果没有找到匹配的动作或优先级不够，从情绪相关动作中随机选择
    #     for act_name in candidate_acts:
    #         for key in self.pet_conf.act_dict.keys():
    #             if act_name.lower() in key.lower():
    #                 act = self.pet_conf.act_dict[key]
    #                 self._run_act(act)
    #                 return
        
    #     # 如果没有找到任何匹配的动作，执行默认动作
    #     self._run_act(self.pet_conf.default)

    def _run_act(self, act: Act) -> None:
        """
        加载并执行动画动作
        
        主要功能:
        1. 处理跳过动作(skip acts)
        2. 按序列播放动画帧
        3. 处理暂停和终止状态
        4. 触发移动和重绘
        
        参数:
            act (Act): 要执行的动作对象,包含:
                - act_num: 动作重复次数
                - images: 动画帧序列
                - frame_refresh: 帧刷新间隔
                - anchor: 锚点位置
                - direction: 移动方向
                - frame_move: 移动距离
        
        执行流程:
        1. 检查是否为跳过动作
        2. 循环执行动作指定次数
        3. 按顺序显示动画帧
        4. 处理移动和重绘
        5. 根据状态控制执行
        """
        # if this is a skipping act
        
        if isinstance(act, list):
            for i in range(act[1]):
                if self.is_paused:
                    break
                if self.is_killed:
                    break
                time.sleep(act[0]/1000)
            return

        for i in range(act.act_num):

            #while self.is_paused:
            #    time.sleep(0.2)
            if self.is_paused:
                print('paused')
                break
            if self.is_killed:
                print('killed')
                break

            for img in act.images:

                #while self.is_paused:
                #    time.sleep(0.2)
                if self.is_paused:
                    break
                if self.is_killed:
                    break

                #global current_img, previous_img
                settings.previous_img = settings.current_img
                settings.current_img = img
                settings.previous_anchor = settings.current_anchor
                settings.current_anchor =  [int(i * settings.tunable_scale) for i in act.anchor]
                #print('anim', settings.previous_anchor, settings.current_anchor)
                self.sig_setimg_anim.emit()
                #time.sleep(act.frame_refresh) ######## sleep 和 move 是不是应该反过来？
                #if act.need_move:
                self._move(act) #self.pos(), act)
                time.sleep(act.frame_refresh) 
                #else:
                #    self._static_act(self.pos())
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
#      Interaction Module
##############################

class Interaction_worker(QObject):
    """
    交互动画系统的核心类，负责处理宠物的所有交互动画和状态管理
    主要功能包括:
    1. 动画播放控制(暂停、恢复、停止)
    2. 交互状态管理(切换动作、判断条件)
    3. 动画帧计算和渲染
    4. 声音效果触发
    5. 饱食度等级检查
    """

    # 用于设置当前显示的图片帧
    sig_setimg_inter = Signal(name='sig_setimg_inter')
    # 用于移动宠物位置的信号
    sig_move_inter = Signal(float, float, name='sig_move_inter')
    #sig_repaint_inter = Signal()
    # 动作播放完成的信号
    sig_act_finished = Signal()
    # 触发交互提示音效和文字的信号
    sig_interact_note = Signal(str, str, name='sig_interact_note')

    # 注册配件动画的信号
    acc_regist = Signal(dict, name='acc_regist')
    # 查询宠物位置的信号
    query_position = Signal(str, name='query_position')
    # 停止跟随鼠标的信号
    stop_trackMouse = Signal(name='stop_trackMouse')

    def __init__(self, pet_conf, parent=None):
        # Interaction Module
        # Respond immediately to signals and run functions defined
        
        # pet_conf: PetConfig class object in Main Widgets
        """
        交互模块的初始化函数
        
        Args:
            pet_conf (PetConfig): 主窗口中的宠物配置对象，包含动画、声音等资源
            parent (QObject, optional): 父对象. Defaults to None.
        
        属性说明:
            self.pet_conf: 存储宠物配置信息
            self.is_killed: 标记线程是否被终止
            self.is_paused: 标记动画是否暂停
            self.interact: 当前交互类型(如'animat','patpat'等)
            self.act_name: 当前动作名称
            self.interact_altered: 标记交互是否被改变
            self.hptier: 饱食度等级阈值列表
            self.pat_idx: 拍拍动画的索引
            
        初始化流程:
            1. 继承父类
            2. 设置初始状态标记
            3. 创建精确计时器
            4. 连接定时器到run函数
            5. 启动交互刷新循环
        """
        super(Interaction_worker, self).__init__(parent)
        self.pet_conf = pet_conf
        self.is_killed = False
        self.is_paused = False
        self.interact = None
        self.act_name = None # 每次将act_name设为None时，都需要将settings.playid重置为0
        self.interact_altered = False
        self.hptier = sys_hp_tiers #[0, 50, 80, 100]
        self.pat_idx = None

        # 创建精确计时器用于动画刷新
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.run)
          #print(self.pet_conf.interact_speed)
        self.timer.start(self.pet_conf.interact_speed) # 按配置的刷新间隔启动
        #self.start = time.time()

    def run(self):
        """
        交互动画的主循环函数，由定时器定期调用
        
        主要功能：
        1. 检查当前交互状态
        2. 执行对应的交互动画方法
        3. 处理交互状态变化
        
        执行流程：
        1. 如果没有交互(interact为None)，直接返回
        2. 如果交互类型不是类的方法，重置交互状态
        3. 如果交互状态被改变，重置播放ID
        4. 通过反射机制调用对应的交互方法
        
        注意：
        - 使用getattr动态调用方法，支持多种交互类型
        - 交互状态改变时会重置动画计数器
        """
        #print(time.time()-self.start)
        #self.start = time.time()
        #print('start_run')

        # print("[调式] run方法 interact:",self.interact,"act_name:",self.act_name)
        if self.interact is None:
            return
        elif self.interact not in dir(self):
            self.interact = None
        else:
            if self.interact_altered:
                self.empty_interact()
                self.interact_altered = False
            getattr(self,self.interact)(self.act_name)

    def _get_animation_type(self, act_name):
        """
        根据动作名称获取对应的动画类型
        
        参数：
            act_name (str): 动作名称
            
        返回：
            str or None: 动画类型，可能是'animat'(普通动画)、'anim_acc'(配件动画)、
                        'customized'(自定义动画)或None(未找到)
        
        功能说明：
        - 从配置中查找动作的类型
        - 根据动作类型返回对应的交互处理方法名
        - 如果动作不存在则返回None
        """
        act_conf = settings.act_data.allAct_params[settings.petname]
        if act_name not in act_conf:
            return None
        act_type = act_conf[act_name]['act_type']
        if act_type == 'random_act':
            return 'animat'
    
        elif act_type == 'accessory_act':
            return 'anim_acc'
        
        elif act_type == 'customized':
            return 'customized'

    def start_interact(self, interact, act_name=None):
        """
        启动一个交互动画
        
        参数：
            interact (str): 交互类型，如'animat'(普通动画)、'patpat'(拍拍)、'anim_acc'(配件动画)等
            act_name (str, optional): 动作名称. Defaults to None.
        
        功能说明：
        1. 根据交互类型和动作名称设置当前交互状态
        2. 播放对应的音效
        3. 处理特殊交互类型的初始化
        
        执行流程：
        1. 如果是从菜单选择的动作(actlist)，先判断动画类型
        2. 根据交互类型和动作名称获取音效列表和饱食度要求
        3. 如果有音效且满足饱食度要求，随机播放一个音效
        4. 设置交互状态标记
        5. 处理特殊交互类型(如配件、自定义动画、拍拍等)
        6. 更新当前交互类型和动作名称
        """
        # If Act selected from menu/panel, judge animation type first
        print("start_interact=",interact,"act_name=",act_name)
        if interact == "actlist":
            interact = self._get_animation_type(act_name)
            if not interact:
                self.stop_interact()
                return
            #elif interact == 'customized':
            #    print("Not implemented")
            #    self.stop_interact()
            #    return

        sound_list = []
        if interact == 'animat' and act_name in self.pet_conf.act_name:
            sound_list = self.pet_conf.act_sound[self.pet_conf.act_name.index(act_name)]
            hp_lvl = self.pet_conf.act_type[self.pet_conf.act_name.index(act_name)][0]

        elif interact == 'anim_acc' and act_name in self.pet_conf.acc_name:
            sound_list = self.pet_conf.accessory_act[act_name]['sound']
            hp_lvl = self.pet_conf.accessory_act[act_name]['act_type'][0]
        
        # Customized animation currently doesn't have sound

        if len(sound_list) > 0 and settings.pet_data.hp_tier >= hp_lvl:
            sound_name = random.choice(sound_list)
            self.sig_interact_note.emit(sound_name, '')

        self.interact_altered = True
        if interact == 'anim_acc' or interact == 'customized':
            self.first_acc = True

        if self.interact == 'followTarget':
            if self.act_name == 'mouse':
                self.stop_trackMouse.emit()

        # sample pat animation
        if interact == 'patpat':
            self.pat_idx = self.sample_pat_anim()
        self.interact = interact
        self.act_name = act_name
    
    def kill(self):
        """
        终止交互线程
        
        功能说明：
        - 设置终止标志，使线程可以安全退出
        - 确保线程不处于暂停状态
        
        注意：
        - 此方法不直接停止定时器，而是通过标志控制线程行为
        - 实际线程终止逻辑在调用此方法的上层实现
        """
        self.is_paused = False
        self.is_killed = True
        #self.timer.stop()
        # terminate thread

    def pause(self):
        """
        暂停交互动画
        
        功能说明：
        - 设置暂停标志，使动画暂时停止更新
        - 不会停止定时器，只是通过标志控制动画更新
        """
        self.is_paused = True
        #self.timer.stop()

    def resume(self):
        """
        恢复交互动画
        
        功能说明：
        - 清除暂停标志，使动画继续更新
        - 与pause()方法配对使用
        """
        self.is_paused = False

    def stop_interact(self):
        """
        停止当前交互动画
        
        功能说明：
        1. 重置交互状态和动作名称
        2. 重置动画播放计数器
        3. 不再发送动作完成信号（由dict_act方法负责发送）
        
        执行流程：
        1. 清除当前交互类型和动作名称
        2. 重置配件初始化标志
        3. 重置全局播放ID和动作ID
        """
        self.interact = None
        self.act_name = None
        self.first_acc = False
        settings.playid = 0
        settings.act_id = 0
        # 移除信号发送，避免与dict_act中的信号发送重复
        # self.sig_act_finished.emit()

    def empty_interact(self):
        """
        重置交互动画的播放进度
        
        功能说明：
        - 重置全局播放ID和动作ID
        - 在交互类型改变时调用，确保新动画从头开始播放
        - 与stop_interact不同，不会清除交互状态和发送信号
        """
        settings.playid = 0
        settings.act_id = 0

    def sample_pat_anim(self):
        """
        根据当前饱食度等级随机选择拍拍动画
        
        返回：
            int: 选中的拍拍动画索引
        
        功能说明：
        1. 根据当前饱食度等级计算各个拍拍动画的概率权重
        2. 使用加权随机选择一个动画索引
        
        算法说明：
        - 饱食度等级越接近某个动画对应的等级，该动画被选中的概率越高
        - 使用指数衰减(0.25的幂)计算权重，确保概率分布合理
        - 最终返回一个0到HP_TIERS长度-1之间的索引
        """
        hp_tier = settings.pet_data.hp_tier
        prob = [1*(0.25**(abs(i-hp_tier))) for i in range(len(settings.HP_TIERS))]
        prob = [i/sum(prob) for i in prob]
        act_idx = random.choices([i for i in range(len(settings.HP_TIERS))], weights=prob, k=1)[0]
        return act_idx

    def img_from_act(self, act):
        """
        从动作对象中获取当前帧的图像
        
        参数：
            act: 动作对象或跳过动作的列表
        
        功能说明：
        1. 处理动作切换，重置播放计数器
        2. 根据动作类型(普通动作或跳过动作)计算重复次数
        3. 更新当前显示的图像和锚点位置
        
        执行流程：
        1. 检查动作是否变化，如变化则重置播放ID
        2. 根据动作类型计算重复次数：
           - 跳过动作：直接增加计数器
           - 普通动作：获取当前帧图像并更新显示
        3. 更新全局图像和锚点信息
        
        注意：
        - 跳过动作是一个列表，用于控制动画暂停或特殊效果
        - 普通动作包含图像列表、刷新率和重复次数等信息
        - 锚点会根据全局缩放比例进行调整
        """

        if settings.current_act != act:
            settings.previous_act = settings.current_act
            settings.current_act = act
            settings.playid = 0

        # if this is a skipping act
        if isinstance(act, list):
            n_repeat = math.ceil(act[0]/self.pet_conf.interact_speed) * act[1]
            settings.playid += 1
            if settings.playid >= n_repeat:
                settings.playid = 0
        else:
            n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
            img_list_expand = [item for item in act.images for i in range(n_repeat)] * act.act_num
            img = img_list_expand[settings.playid]

            settings.playid += 1
            if settings.playid >= len(img_list_expand):
                settings.playid = 0
            settings.previous_img = settings.current_img
            settings.current_img = img
            settings.previous_anchor = settings.current_anchor
            settings.current_anchor = [int(i * settings.tunable_scale) for i in act.anchor]

    def dict_act(self, act_name):
        """
        执行 act_dict 中的动作
        
        参数：
            act_name (str): 动作名称，必须在 pet_conf.act_dict 中存在
        
        功能说明：
        1. 直接从 act_dict 中获取动作对象并执行
        2. 支持所有类型的动作（普通动作、配件动作等）
        3. 适用于大模型直接控制宠物行为的场景
        
        执行流程：
        1. 检查动作是否存在于 act_dict 中
        2. 获取动作对象并执行
        3. 处理动画帧的更新和显示
        4. 发送图像更新信号并执行移动
        5. 只有在整个动作序列执行完毕后才发出sig_act_finished信号
        """
        # print(f"[调试] 执行 act_dict 中的动作: {self.act_name}")

        if not hasattr(self, 'action_group_index') or self.act_name != act_name:
           self.action_group_index = 0
            

        if self.action_group_index >= len(act_name):
            # 所有动作都执行完毕
            self.action_group_index = 0
            # 修改：先发出动作完成信号，再停止交互
            # 这样确保在整个动作序列执行完毕后才发出信号
            self.sig_act_finished.emit()
            self.stop_interact()
            return

        # 获取当前要执行的动作
        current_action = act_name[self.action_group_index]
            
            # 检查当前动作是否存在
        if current_action not in self.pet_conf.act_dict:
            print(f"[错误] 动作 '{current_action}' 不存在于 act_dict 中")
            # 尝试执行下一个动作
            self.action_group_index += 1
            
            # 不要递归调用，让下一个定时器周期处理下一个动作
            return
         
            
            # 获取动作对象
        act = self.pet_conf.act_dict.get(current_action)
            
            # 计算重复次数
        n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
        n_repeat *= len(act.images) * act.act_num
            
            # 更新图像
        self.img_from_act(act)
            
            # 检查是否播放完毕
        if settings.playid >= n_repeat-1:
            # 当前动作播放完毕，准备执行下一个动作
            self.action_group_index += 1
            # 重置播放ID，准备执行下一个动作
            settings.playid = 0
        
        # 更新图像和位置
        if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
            self.sig_setimg_inter.emit()
            self._move(act)


    def animat(self, act_name):
        """
        执行普通动画交互
        
        参数：
            act_name (str): 动作名称
        
        功能说明：
        1. 播放指定名称的普通动画序列
        2. 检查饱食度要求并处理不满足条件的情况
        3. 处理动画帧的更新和显示
        4. 支持特殊动画效果(如落地时的镜像翻转)
        
        执行流程：
        1. 查找动作在配置中的索引位置
        2. 检查当前饱食度是否满足动作要求
        3. 获取动作对应的动画序列
        4. 判断动画是否播放完毕
        5. 更新当前显示的图像帧
        6. 处理特殊效果(如落地动画的左右翻转)
        7. 发送图像更新信号并执行移动
        
        注意：
        - 如果饱食度不满足要求，会发出提示并停止交互
        - 动画播放完毕后会自动停止交互
        - 落地动画有特殊的镜像处理逻辑
        """
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
            message = f"[{act_name}]" + " " + self.tr("needs Satiety be larger than") + f" {self.hptier[self.pet_conf.act_type[acts_index][0]-1]}"
            self.sig_interact_note.emit('status_hp', message) #'[%s] 需要饱食度%i以上哦'%(act_name, self.hptier[self.pet_conf.act_type[acts_index][0]-1]))
            self.stop_interact()
            return
        
        acts = self.pet_conf.random_act[acts_index]
        #print(settings.act_id, len(acts))
        if settings.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            # 修改：先发出动作完成信号，再停止交互
            # 这样确保在整个动作序列执行完毕后才发出信号
            self.sig_act_finished.emit()
            self.stop_interact()
        else:
            act = acts[settings.act_id]
            n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if settings.playid >= n_repeat-1:
                settings.act_id += 1

            if act_name == 'onfloor' and settings.fall_right:
                settings.previous_img = settings.current_img
                transform = QTransform()
                transform.scale(-1, 1)
                settings.current_img = settings.current_img.transformed(transform) #.mirrored(True, False)
                settings.current_anchor = [int(i * settings.tunable_scale) for i in act.anchor]
                settings.current_anchor = [-settings.current_anchor[0], settings.current_anchor[1]]

            if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
                self.sig_setimg_inter.emit()
                self._move(act)
        #print('%.5fs'%(time.time()-start))
        
    def anim_acc(self, acc_name):
        """
        执行配件动画交互
        
        参数：
            acc_name (str): 配件动作名称
        
        功能说明：
        1. 播放与配件相关的动画序列
        2. 检查饱食度要求并处理不满足条件的情况
        3. 注册配件到配件管理系统
        4. 处理动画帧的更新和显示
        
        执行流程：
        1. 检查当前饱食度是否满足配件动作要求
        2. 首次执行时注册配件到配件系统
        3. 获取配件动作对应的动画序列
        4. 判断动画是否播放完毕
        5. 更新当前显示的图像帧
        6. 发送图像更新信号并执行移动
        
        注意：
        - 配件动画需要先注册配件，然后才能正常显示
        - 如果饱食度不满足要求，会发出提示并停止交互
        - 动画播放完毕后会自动停止交互
        """

        # 判断是否满足动作饱食度要求
        if settings.pet_data.hp_tier < self.pet_conf.accessory_act[acc_name]['act_type'][0]:
            message = f"[{acc_name}]" + " " + self.tr("needs Satiety be larger than") + f" {self.hptier[self.pet_conf.accessory_act[acc_name]['act_type'][0]-1]}"
            self.sig_interact_note.emit('status_hp', message) #'[%s] 需要饱食度%i以上哦'%(acc_name, self.hptier[self.pet_conf.accessory_act[acc_name]['act_type'][0]-1]))
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
            # 修改：先发出动作完成信号，再停止交互
            # 这样确保在整个动作序列执行完毕后才发出信号
            self.sig_act_finished.emit()
            self.stop_interact()
        else:
            act = acts[settings.act_id]
            n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if settings.playid >= n_repeat-1:
                settings.act_id += 1

            if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
                self.sig_setimg_inter.emit()
                self._move(act)

    def customized(self, act_name):
        """
        执行自定义动画交互
        
        参数：
            act_name (str): 自定义动作名称
        
        功能说明：
        1. 播放用户自定义的动画序列
        2. 检查饱食度要求并处理不满足条件的情况
        3. 支持配件列表的注册和显示
        4. 处理普通动画和跳过动画两种类型
        
        执行流程：
        1. 检查当前饱食度是否满足自定义动作要求
        2. 首次执行时注册相关配件(如果有)
        3. 获取自定义动作对应的动画序列
        4. 判断动画是否播放完毕
        5. 根据动画类型(普通/跳过)计算重复次数
        6. 更新当前显示的图像帧
        7. 发送图像更新信号并执行移动
        
        注意：
        - 自定义动画支持普通动画和跳过动画两种类型
        - 跳过动画用于实现暂停或特殊效果
        - 如果饱食度不满足要求，会发出提示并停止交互
        """

        # 判断是否满足动作饱食度要求
        if settings.pet_data.hp_tier < self.pet_conf.custom_act[act_name]['act_type'][0]:
            message = f"[{act_name}]" + " " + self.tr("needs Satiety be larger than") + f" {self.hptier[self.pet_conf.custom_act[act_name]['act_type'][0]-1]}"
            self.sig_interact_note.emit('status_hp', message)
            self.stop_interact()
            return

        if self.first_acc:
            if self.pet_conf.custom_act[act_name]['acc_list']:
                accs = {'acc_list': self.pet_conf.custom_act[act_name]['acc_list'],
                        'anchor': self.pet_conf.custom_act[act_name]['anchor'],
                        'name': 'customized_acc' # For Accessory module to judge the type
                        }
                self.acc_regist.emit(accs)
            self.first_acc = False

        acts = self.pet_conf.custom_act[act_name]['act_list']

        if settings.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            # 修改：先发出动作完成信号，再停止交互
            # 这样确保在整个动作序列执行完毕后才发出信号
            self.sig_act_finished.emit()
            self.stop_interact()
        else:
            act = acts[settings.act_id]
            # if this is a skipping act
            if isinstance(act, list):
                n_repeat = math.ceil(act[0]/self.pet_conf.interact_speed) * act[1]
            else:
                n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
                n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if settings.playid >= n_repeat-1:
                settings.act_id += 1

            if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
                self.sig_setimg_inter.emit()
                self._move(act)

    def patpat(self, act_name):
        """
        执行拍拍交互动画
        
        参数：
            act_name (str): 动作名称，在此函数中实际未使用
        
        功能说明：
        1. 播放与当前饱食度等级相关的拍拍动画
        2. 处理动画帧的更新和显示
        
        执行流程：
        1. 根据之前在start_interact中选择的pat_idx获取对应的拍拍动画
        2. 判断动画是否播放完毕
        3. 计算动画重复次数
        4. 更新当前显示的图像帧
        5. 发送图像更新信号并执行移动
        
        注意：
        - 拍拍动画是根据当前饱食度等级随机选择的
        - 动画播放完毕后会自动停止交互
        """
        # print(f"[调试] 执行 patpat 中的动作: {self.act_name}")
        acts = [self.pet_conf.patpat[self.pat_idx]]
        #print(settings.act_id, len(acts))
        if settings.act_id >= len(acts):
            #settings.act_id = 0
            #self.interact = None
            # 修改：先发出动作完成信号，再停止交互
            # 这样确保在整个动作序列执行完毕后才发出信号
            self.sig_act_finished.emit()
            self.stop_interact()
        else:
            act = acts[settings.act_id]
            n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
            n_repeat *= len(act.images) * act.act_num
            self.img_from_act(act)
            if settings.playid >= n_repeat-1:
                settings.act_id += 1

            if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
                self.sig_setimg_inter.emit()
                self._move(act)

    def mousedrag(self, act_name):
        """
        处理鼠标拖拽交互动画
        
        参数：
            act_name (str): 动作名称，在此函数中实际未使用
        
        功能说明：
        1. 根据当前拖拽状态和掉落设置显示不同的动画
        2. 支持三种主要状态：拖拽中、掉落中、落地
        3. 处理掉落动画的方向和特效
        
        执行流程：
        1. 根据掉落设置(set_fall)和当前状态分支处理：
           - 掉落功能关闭时：显示拖拽动画或停止交互
           - 掉落功能开启且未在地面时：显示拖拽、预备掉落或掉落动画
           - 其他情况：切换到落地动画
        2. 更新当前显示的图像帧
        3. 处理掉落方向的镜像翻转
        4. 如果正在掉落，调用drop()方法处理掉落物理效果
        
        注意：
        - 掉落动画有左右方向区分，通过镜像翻转实现
        - 掉落过程包含预备掉落和实际掉落两个阶段
        - 落地后会切换到onfloor动画
        """

        # Falling is OFF
        if not settings.set_fall:
            if settings.draging==1:
                acts = self.pet_conf.drag

                self.img_from_act(acts)
                if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
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
                if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
                    self.sig_setimg_inter.emit()

            elif settings.draging==0:
                if settings.prefall == 1:
                    acts = self.pet_conf.prefall
                else:
                    acts = self.pet_conf.fall

                n_repeat = math.ceil(acts.frame_refresh / (self.pet_conf.interact_speed / 1000))
                n_repeat *= len(acts.images) * acts.act_num

                self.img_from_act(acts)
                if settings.playid >= n_repeat-1:
                    settings.prefall = 0

                #global fall_right
                if settings.fall_right:
                    settings.previous_img = settings.current_img
                    transform = QTransform()
                    transform.scale(-1, 1)
                    settings.current_img = settings.current_img.transformed(transform)
                    settings.current_anchor = [int(i * settings.tunable_scale) for i in acts.anchor]
                    settings.current_anchor = [-settings.current_anchor[0], settings.current_anchor[1]]

                if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
                    self.sig_setimg_inter.emit()

                self.drop()
                # print('掉落 mousedrag',settings.dragspeedy,settings.dragspeedx)
        else:
            #self.stop_interact()
            #self.interact = 'animat' #None
            #self.act_name = 'onfloor' #None
            print('落地 mousedrag')
            self.start_interact('animat', 'onfloor')
            #settings.playid = 0
            #settings.act_id = 0

        #self.sig_repaint_inter.emit()


        #elif set_fall==0 and onfloor==0:

    def drop(self):
        """
        处理宠物掉落的物理效果
        
        功能说明：
        1. 实现简单的重力物理效果
        2. 计算宠物在掉落过程中的水平和垂直位移
        3. 更新掉落速度并发送移动信号
        
        执行流程：
        1. 获取当前的水平和垂直速度
        2. 根据重力加速度更新垂直速度
        3. 发送移动信号使宠物按计算的位移移动
        
        物理模型：
        - 水平方向保持匀速运动
        - 垂直方向受重力加速度影响，速度不断增加
        - 通过累加重力值模拟加速下落效果
        """
        #掉落
        #print("Dropping")

        # print(settings.dragspeedy,settings.dragspeedx)
        # print(dragspeedy)
        #dropnext=pettop+info.gravity*dropa-info.gravity/2
        plus_y = settings.dragspeedy #+ self.pet_conf.dropspeed
        plus_x = settings.dragspeedx
        settings.dragspeedy = settings.dragspeedy + settings.gravity

        self.sig_move_inter.emit(plus_x, plus_y)

    def _move(self, act: QAction) ->  None: #pos: QPoint, act: QAction) -> None:
        """
                加载图片执行移动
        :param act: 动作
        :return:
        在 Thread 中发出移动Signal
        :param act: 动作
        :return
       
        #print(act.direction, act.frame_move)
        处理角色移动动画
        
        主要功能:
        1. 根据动作方向计算移动距离
        2. 发送移动信号到主线程
        
        参数:
            act (QAction): 包含移动信息的动作对象
                - direction: 移动方向('right','left','up','down')
                - frame_move: 每帧移动距离
        
        移动计算:
        - 右移: +frame_move
        - 左移: -frame_move 
        - 上移: -frame_move
        - 下移: +frame_move
        
        执行流程:
        1. 获取动作方向
        2. 根据方向计算x,y轴移动距离
        3. 发送移动信号
        
        注意事项:
        - 通过Signal异步发送移动指令
        - 实际移动在主线程执行
        """
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
        # 宠物进行 三个等级的喂食动画
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

    def followTarget(self, act_name):

        self.query_position.emit(act_name)
        distance = abs(self.main_pos[0] - self.target_pos[0])

        if distance < 5*self.pet_conf.left.frame_move:
            act = self.pet_conf.default
            self.img_from_act(act)
            if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
                self.sig_setimg_inter.emit()

        else:
            act = [self.pet_conf.left, self.pet_conf.right][int(self.main_pos[0] < self.target_pos[0])]
            self.img_from_act(act)
            if settings.previous_img != settings.current_img or settings.previous_anchor != settings.current_anchor:
                self.sig_setimg_inter.emit()
                self._move(act)


    def receive_pos(self, main_pos, target_pos):
        self.main_pos = main_pos
        self.target_pos = target_pos




##############################
#          计划任务
##############################
class Scheduler_worker(QObject):
    sig_settext_sche = Signal(str, str, name='sig_settext_sche')
    sig_setact_sche = Signal(str, name='sig_setact_sche')
    sig_setstat_sche = Signal(str, int, name='sig_setstat_sche')
    sig_focus_end = Signal(name='sig_focus_end')
    sig_tomato_end = Signal(name='sig_tomato_end')
    sig_settime_sche = Signal(str, int, name='sig_settime_sche')
    sig_addItem_sche = Signal(int, name='sig_addItem_sche')
    sig_setup_bubble = Signal(dict, name='sig_setup_bubble')


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
        self.tm_interval = 25
        self.tm_break = 5

        ''' Customized Pomodoro function deleted from v0.3.7
        pomodoro_conf = os.path.join(basedir, 'res/icons/Pomodoro.json')
        if os.path.isfile(pomodoro_conf):
            self.tm_config = json.load(open(pomodoro_conf, 'r', encoding='UTF-8'))
        else:
            self.tm_config = {"title":"番茄钟",
                        "Description": "番茄工作法是一种时间管理方法，该方法使用一个定时器来分割出25分钟的工作时间和5分钟的休息时间，提高效率。",
                        "option_text": "想要执行",
                        "options":{"pomodoro": {
                                             "note_start":"新的番茄时钟开始了哦！加油！",
                                             "note_first":"个番茄时钟设定完毕！开始了哦！",
                                             "note_end":"叮叮~ 番茄时间到啦！休息5分钟！",
                                             "note_last":"叮叮~ 番茄时间全部结束啦！"
                                             }
                                  }
                        }
        '''
        self.pomodoro_text = {"name": self.tr("Pomodoro"),
                              "note_start": self.tr("The new Pomodoro has started! Let's go!"),
                              "note_first": self.tr(" Pomodoros have been set! Let's dive in!"),
                              "note_end": self.tr("Ding ding~ Pomodoro finished! Time for a 5-minute break!"),
                              "note_last": self.tr("Ding ding~ All Pomodoros completed! Great job!"),
                              "note_cancel": self.tr("Your Pomodoros have all been canceled!")}

        self.focus_text = {"name": self.tr("Focus Session"),
                           "note_start": self.tr("Your focus session has started!"),
                           "note_end": self.tr("Your focus session has completed!"),
                           "note_cancel": self.tr("Your focus session has been canceled!")}

        self.scheduler = QtScheduler()
        #self.scheduler.add_job(self.change_hp, 'interval', minutes=self.pet_conf.hp_interval)
        self.scheduler.add_job(self.change_hp, interval.IntervalTrigger(minutes=1)) #self.pet_conf.hp_interval))
        #self.scheduler.add_job(self.change_em, 'interval', minutes=self.pet_conf.em_interval)
        self.scheduler.add_job(self.change_fv, interval.IntervalTrigger(minutes=1)) #self.pet_conf.fv_interval))
        self.scheduler.start()


    def run(self):
        """Run Scheduler in a separate thread"""
        #time.sleep(10)
        """
        调度器的主循环函数，负责初始化和启动问候系统
        
        主要功能:
        1. 获取当前时间并生成问候语
        2. 检查配置文件和存档状态
        3. 显示系统通知和问候气泡
        
        执行流程:
        1. 获取当前小时数
        2. 根据时间生成问候类型和文本
        3. 检查设置文件状态
        4. 检查存档文件状态
        5. 发送问候气泡
        """
        now_time = datetime.now().hour
        greet_type, greet_text = self.greeting(now_time)
        #comp_days = '这是陪伴你的第 %i 天 <3'%(settings.pet_data.days)
        if not settings.settingGood:
            settingBrokeNote = self.tr("*Setting config file broken. Setting is re-initialized.")
            self.show_dialogue('system', settingBrokeNote)
        else:
            settingBrokeNote = ""
            
        if not settings.pet_data.saveGood:
            saveBrokeNote = self.tr("*Game save file broken. Data is re-initialized.\nPlease load previous saved data to recover.")
            self.show_dialogue('system', saveBrokeNote)
        else:
            saveBrokeNote = ""
        #self.show_dialogue(greet_type, f'{greet_text}')
        self.sig_setup_bubble.emit({'message':greet_text, 'start_audio':greet_type, 'icon':None})
        
    
    def kill(self):
        self.is_paused = False
        self.is_killed = True
        self.scheduler.shutdown()


    def pause(self):
        self.is_paused = True
        self.scheduler.pause()


    def resume(self):
        """
        恢复交互动画
        
        功能说明：
        - 清除暂停标志，使动画继续更新
        - 与pause()方法配对使用
        """
        self.is_paused = False
        self.scheduler.resume()

    def send_greeting(self):
        now_time = datetime.now().hour
        greet_type, greet_text = self.greeting(now_time)
        #comp_days = '这是陪伴你的第 %i 天 <3'%(settings.pet_data.days)
        #self.show_dialogue(greet_type, '%s'%(greet_text))
        self.sig_setup_bubble.emit({'message':greet_text, 'start_audio':greet_type, 'icon':None})


    def greeting(self, time):
        if 11 >= time >= 6:
            return 'greeting_1', self.tr("Good Morning!") #'早上好!'
        elif 13 >= time >= 12:
            return 'greeting_2', self.tr("Good Afternoon!") #'中午好!'
        elif 18 >= time >= 14:
            return 'greeting_3', self.tr("Good Afternoon!") #'下午好！'
        elif 22 >= time >= 19:
            return 'greeting_4', self.tr("Good Evening!") #'晚上好!'
        elif 24 >= time >= 23:
            return 'greeting_5', self.tr("Time to sleep!") #'该睡觉啦!'
        elif 5 >= time >= 0:
            return 'greeting_5', self.tr("Time to sleep!") #'该睡觉啦!'
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

    '''
    def item_drop(self, n_minutes):
        #print(n_minutes)
        nitems = n_minutes // 5
        remains = max(0, n_minutes % 5 - 1)
        chance_drop = random.choices([0,1], weights=(1-remains/5, remains/5))
        #print(chance_drop)
        nitems += chance_drop[0]
        #for test -----
        #nitems = 4
        #---------------
        if nitems > 0:
            self.sig_addItem_sche.emit(nitems)
    '''

    def add_tomato(self, n_tomato=None):

        if self.focus_on == False and self.n_tomato_now is None:
            self.n_tomato_now = n_tomato
            time_plus = 0 #25

            # 1-start
            task_text = 'tomato_first'
            time_torun = datetime.now() + timedelta(seconds=1)
            #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
            self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text])
            
            time_plus += self.tm_interval #25
            #1-end
            if n_tomato == 1:
                task_text = 'tomato_last'
            else:
                task_text = 'tomato_end'
            time_torun = datetime.now() + timedelta(minutes=time_plus) #minutes=time_plus)
            #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
            self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text], id='tomato_0_end')
            self.tomato_list.append('tomato_0_end')
            time_plus += self.tm_break #5

            # others start and end
            if n_tomato > 1:
                for i in range(1, n_tomato):
                    #start
                    task_text = 'tomato_start'
                    time_torun = datetime.now() + timedelta(minutes=time_plus) #minutes=time_plus)
                    #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
                    self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text], id='tomato_%s_start'%i)
                    time_plus += self.tm_interval #25
                    #end
                    if i == (n_tomato-1):
                        task_text = 'tomato_last'
                    else:
                        task_text = 'tomato_end'
                    time_torun = datetime.now() + timedelta(minutes=time_plus) #minutes=time_plus)
                    #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
                    self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text], id='tomato_%s_end'%i)
                    time_plus += self.tm_break #5
                    self.tomato_list.append('tomato_%s_start'%i)
                    self.tomato_list.append('tomato_%s_end'%i)

        ''' From v0.3.7, situations below won't happen
        elif self.focus_on:
            task_text = "focus_on"
            time_torun = datetime.now() + timedelta(seconds=1)
            self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text])
        else:
            task_text = "tomato_exist"
            time_torun = datetime.now() + timedelta(seconds=1)
            #self.scheduler.add_job(self.run_task, run_date=time_torun, args=[task_text])
            self.scheduler.add_job(self.run_tomato, date.DateTrigger(run_date=time_torun), args=[task_text])
        '''



    def run_tomato(self, task_text):
        text_toshow = ''
        #finished = False

        if task_text == 'tomato_start':
            self.tomato_timeleft = self.tm_interval #25
            self.scheduler.add_job(self.change_tomato, interval.IntervalTrigger(minutes=1), id='tomato_timer', replace_existing=True)
            self.sig_settime_sche.emit('tomato_start', self.tomato_timeleft)
            self.tomato_list = self.tomato_list[1:]
            text_toshow = self.pomodoro_text['note_start']

        elif task_text == 'tomato_first':
            self.scheduler.add_job(self.change_tomato, interval.IntervalTrigger(minutes=1), id='tomato_timer', replace_existing=True)
            self.tomato_timeleft = self.tm_interval #25
            self.sig_settime_sche.emit('tomato_start', self.tomato_timeleft)
            text_toshow = "%s%s"%(int(self.n_tomato_now), self.pomodoro_text['note_first'])

        elif task_text == 'tomato_end':
            self.tomato_timeleft = self.tm_break #5
            self.scheduler.add_job(self.change_tomato, interval.IntervalTrigger(minutes=1), id='tomato_timer', replace_existing=True)
            self.sig_settime_sche.emit('tomato_rest', self.tomato_timeleft)
            self.tomato_list = self.tomato_list[1:]
            text_toshow = self.pomodoro_text['note_end'] #'叮叮~ 番茄时间到啦！休息5分钟！'
            #finished = True

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
            text_toshow = self.pomodoro_text['note_last']
            #finished = True

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
            self.sig_settime_sche.emit('tomato_cencel', self.tomato_timeleft)
            self.sig_tomato_end.emit()
            text_toshow = self.pomodoro_text['note_cancel']

        ''' Theoretically, such situation won't exist from v0.3.7 on.
        elif task_text == 'tomato_exist':
            self.sig_tomato_end.emit()
            self.sig_settime_sche.emit('tomato_end', 0)
            text_toshow = "不行！还有 [%s] 在进行哦~"%(settings.current_tm_option)

        elif task_text == 'focus_on':
            self.sig_tomato_end.emit()
            self.sig_settime_sche.emit('tomato_end', 0)
            text_toshow = "不行！还有专注任务在进行哦~"
        '''
        if text_toshow:
            if task_text in ['tomato_start', 'tomato_first']:
                self.show_dialogue('start_tomato', text_toshow)

            elif task_text in ['tomato_end', 'tomato_last']:
                self.show_dialogue('end_tomato', text_toshow)

            elif task_text == 'tomato_cancel':
                self.show_dialogue('cancel_tomato', text_toshow)
        '''
        if finished:
            time.sleep(1)
            self.item_drop(n_minutes=30)
        '''
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
        ''' From v0.3.7, situations below won't happen
        if self.n_tomato_now is not None:
            task_text = "tomato_exist"
            time_torun = datetime.now() + timedelta(seconds=1)
            self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text])

        elif self.focus_on:
            task_text = "focus_exist"
            time_torun = datetime.now() + timedelta(seconds=1)
            self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun), args=[task_text])
        '''

        if time_range is not None:
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

        ''' From v0.3.7, setting up by time_point has been deleted from UI
        elif time_point is not None:
            now = datetime.now()
            time_torun = datetime(year=now.year, month=now.month, day=now.day,
                                  hour=time_point[0], minute=time_point[1], second=0) #now.second)
            time_diff = time_torun - now
            self.focus_time = time_diff.total_seconds() // 60

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
        '''

    def run_focus(self, task_text, n_minutes=0):
        text_toshow = ''
        #finished = False
        ''' From v0.3.7, situations below won't happen
        if task_text == 'tomato_exist':
            self.sig_focus_end.emit()
            self.sig_settime_sche.emit('focus_end', 0)
            text_toshow = '不行！还有 [%s] 在进行哦~'%(settings.current_tm_option)

        elif task_text == 'focus_exist':
            self.sig_focus_end.emit()
            self.sig_settime_sche.emit('focus_end', 0)
            text_toshow = "不行！还有专注任务在进行哦~"
        '''
        if task_text == 'focus_start':
            if self.focus_time > 1:
                self.scheduler.add_job(self.change_focus, interval.IntervalTrigger(minutes=1), id='focus_timer', replace_existing=True)
            #elif self.focus_time < 1:
            #    print(self.focus_time)
                #focus_time_sec = int()
            self.sig_settime_sche.emit('focus_start', self.focus_time)
            text_toshow = self.focus_text['note_start'] #"你的专注任务开始啦！"


        elif task_text == 'focus_end':
            self.focus_time = 0
            try:
                self.scheduler.remove_job('focus_timer')
            except:
                pass
            self.sig_settime_sche.emit('focus_end', self.focus_time)
            self.focus_on = False
            self.sig_focus_end.emit()
            text_toshow = self.focus_text['note_end'] #"你的专注任务结束啦！"
            #finished = True


        elif task_text == 'focus_cancel':
            self.focus_time = 0
            try:
                self.scheduler.remove_job('focus_timer')
            except:
                pass
            self.sig_settime_sche.emit('focus_cancel', self.focus_time)
            self.sig_focus_end.emit()
            self.focus_on = False
            text_toshow = self.focus_text['note_cancel'] #"你的专注任务取消啦！"
            #finished = True
        
        if text_toshow:
            if task_text == 'focus_start':
                self.show_dialogue('start_focus', text_toshow)

            elif task_text == 'focus_end':
                self.show_dialogue('end_focus', text_toshow)

            elif task_text == 'focus_cancel':
                self.show_dialogue('cancel_focus', text_toshow)

        ''' From v0.3.7, situations below won't happen
        elif task_text == 'focus_start_tomorrow':
            if self.focus_time > 1:
                self.scheduler.add_job(self.change_focus, interval.IntervalTrigger(minutes=1), id='focus_timer', replace_existing=True)
            self.sig_settime_sche.emit('focus_start', self.focus_time)
            text_toshow = "专注任务开始啦！\n但设定在明天，请确认无误哦~"

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
        '''

    ''' Pause function deleted from v0.3.7
    def pause_focus(self):
        try:
            self.scheduler.remove_job('focus')
        except:
            pass
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
    '''
    def cancel_focus(self, time_past):
        try:
            self.scheduler.remove_job('focus')
        except:
            pass
        task_text = "focus_cancel"
        time_torun_2 = datetime.now() + timedelta(seconds=1)
        self.scheduler.add_job(self.run_focus, date.DateTrigger(run_date=time_torun_2), args=[task_text,time_past])

    ''' Reminder function deleted from v0.3.7
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
    '''

        





