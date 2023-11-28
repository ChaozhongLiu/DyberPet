import json
import glob
import time
import os.path
from datetime import datetime, timedelta
from sys import platform
from DyberPet.utils import text_wrap, get_child_folder

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from .utils import get_file_time

if platform == 'win32':
    basedir = ''
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-1])


class PetConfig:
    """
    宠物配置
    """

    def __init__(self):

        self.petname = None
        self.width = 128
        self.height = 128
        self.scale = 1.0

        self.refresh = 5
        self.interact_speed = 0.02
        self.dropspeed = 1.0
        #self.gravity = 4.0

        self.default = None
        self.up = None
        self.down = None
        self.left = None
        self.right = None
        self.drag = None
        self.fall = None
        self.on_floor = None
        self.patpat = None
        #self.subpet = []

        self.random_act = []
        self.act_prob = []
        self.act_name = []
        self.act_type = []
        self.act_sound = []
        #self.mouseDecor = {}
        self.accessory_act = {}
        self.acc_name = []

        #self.hp_interval = 15
        #self.fv_interval = 15

        self.item_favorite = []
        self.item_dislike = []


    @classmethod
    def init_config(cls, pet_name: str, pic_dict: dict):

        path = os.path.join(basedir, 'res/role/{}/pet_conf.json'.format(pet_name))
        with open(path, 'r', encoding='UTF-8') as f:
            o = PetConfig()
            conf_params = json.load(f)

            o.petname = pet_name
            o.scale = conf_params.get('scale', 1.0)
            o.width = conf_params.get('width', 128) * o.scale
            o.height = conf_params.get('height', 128) * o.scale

            o.refresh = conf_params.get('refresh', 5)
            o.interact_speed = conf_params.get('interact_speed', 0.02) * 1000
            o.dropspeed = conf_params.get('dropspeed', 1.0) #not needed in v0.15+
            #o.gravity = conf_params.get('gravity', 4.0)

            # 
            # 初始化所有动作
            act_path = os.path.join(basedir, 'res/role/{}/act_conf.json'.format(pet_name))
            act_conf = dict(json.load(open(act_path, 'r', encoding='UTF-8')))
            act_dict = {}
            #with open(act_path, 'r', encoding='UTF-8') as f:
            act_dict = {k: Act.init_act(v, pic_dict, o.scale, pet_name) for k, v in act_conf.items()}

            # 载入默认动作
            o.default = act_dict[conf_params['default']]
            o.up = act_dict[conf_params.get('up', 'default')]
            o.down = act_dict[conf_params.get('down', 'default')]
            o.left = act_dict[conf_params.get('left', 'default')]
            o.right = act_dict[conf_params.get('right', 'default')]
            o.drag = act_dict[conf_params['drag']]
            o.fall = act_dict[conf_params['fall']]
            o.prefall = act_dict[conf_params.get('prefall','fall')]
            o.on_floor = act_dict[conf_params.get('on_floor', 'default')]
            o.patpat = act_dict[conf_params.get('patpat', 'default')]

            # subpet now is independent from character
            '''
            subpet = conf_params.get('subpet', {})
            for name in subpet:
                subpet[name]['fv_lock'] = subpet[name].get('fv_lock',0)

            o.subpet = subpet
            '''

            
            # 初始化随机动作
            random_act = []
            act_prob = []
            act_name = []
            act_type = []
            act_sound = []

            for act_array in conf_params['random_act']:
                random_act.append([act_dict[act] for act in act_array['act_list']])
                act_prob.append(act_array.get('act_prob', 0.2))
                act_name.append(act_array.get('name', None))
                act_type.append(act_array.get('act_type', [2,1]))
                act_sound.append(act_array.get('sound', []))

            o.random_act = random_act
            if sum(act_prob) == 0:
                o.act_prob = [0] * len(act_prob)
            else:
                o.act_prob = [i/sum(act_prob) for i in act_prob]
            o.act_name = act_name
            o.act_type = act_type
            o.act_sound = act_sound


            # 初始化组件动作
            accessory_act = {}
            acc_name = []
            
            for acc_array in conf_params.get("accessory_act", []):
                act_list = [act_dict[act] for act in acc_array['act_list']]
                acc_list = [act_dict[act] for act in acc_array['acc_list']]
                acc_array['act_list'] = act_list
                acc_array['acc_list'] = acc_list
                acc_array['anchor'] = [i*o.scale for i in acc_array['anchor']]
                acc_array['sound'] = acc_array.get('sound', [])

                accessory_act[acc_array['name']] = acc_array
                acc_name.append(acc_array['name'])

            o.accessory_act = accessory_act
            o.acc_name = acc_name

            # 如果是附属宠物 其和主宠物之间的交互 - v0.3.3 subpet loading switched to another method
            #o.main_interact = conf_params.get("main_interact", {})

            o.item_favorite = conf_params.get('item_favorite', {})
            o.item_dislike = conf_params.get('item_dislike', {})
            

            # 对话列表
            msg_file = os.path.join(basedir, 'res/role/{}/msg_conf.json'.format(pet_name))
            if os.path.isfile(msg_file):
                msg_data = dict(json.load(open(msg_file, 'r', encoding='UTF-8')))

                msg_dict = conf_params.get("msg_dict", {})
                for msg in msg_dict.keys():
                    msg_dict[msg] = msg_data[msg_dict[msg]]

                o.msg_dict = msg_dict
            else:
                o.msg_dict = {}

            return o


    @classmethod
    def init_sys(cls, pic_dict: dict):
        path = os.path.join(basedir, 'res/role/sys/sys_conf.json')
        with open(path, 'r', encoding='UTF-8') as f:
            o = PetConfig()
            conf_params = json.load(f)

            o.petname = 'sys'
            o.scale = conf_params.get('scale', 1.0)
            #o.width = conf_params.get('width', 128) * o.scale
            #o.height = conf_params.get('height', 128) * o.scale

            # 
            # 初始化所有动作
            act_path = os.path.join(basedir, 'res/role/sys/act_conf.json')
            act_conf = dict(json.load(open(act_path, 'r', encoding='UTF-8')))
            act_dict = {}
            act_dict = {k: Act.init_act(v, pic_dict, o.scale, 'sys') for k, v in act_conf.items()}

            # 初始化组件动作
            accessory_act = {}
            acc_name = []
            
            for acc_array in conf_params.get("accessory_act", []):
                act_list = [act_dict[act] for act in acc_array['act_list']]
                acc_list = [act_dict[act] for act in acc_array['acc_list']]
                acc_array['act_list'] = act_list
                acc_array['acc_list'] = acc_list
                acc_array['anchor'] = [i*o.scale for i in acc_array['anchor']]
                accessory_act[acc_array['name']] = acc_array
                acc_name.append(acc_array['name'])

            o.accessory_act = accessory_act
            o.acc_name = acc_name

            # 鼠标挂件 - 暂时搁置
            '''
            mouseDecor = {}
            for Decor_array in conf_params.get("mouseDecor", []):
                Decor_array['default'] = [act_dict[act] for act in Decor_array['default']]
                Decor_array['click'] = [act_dict[act] for act in Decor_array['click']]
                #Decor_array['anchor'] = [i*o.scale for i in Decor_array['anchor']]
                mouseDecor[Decor_array['name']] = Decor_array

            o.mouseDecor = mouseDecor
            '''

            return o

    @classmethod
    def init_subpet(cls, pet_name: str, pic_dict: dict):

        path = os.path.join(basedir, 'res/pet/{}/pet_conf.json'.format(pet_name))
        with open(path, 'r', encoding='UTF-8') as f:
            o = PetConfig()
            conf_params = json.load(f)

            o.petname = pet_name
            o.scale = conf_params.get('scale', 1.0)
            o.width = conf_params.get('width', 128) * o.scale
            o.height = conf_params.get('height', 128) * o.scale
            o.interact_speed = conf_params.get('interact_speed', 0.02) * 1000

            # 初始化所有动作
            act_path = os.path.join(basedir, 'res/pet/{}/act_conf.json'.format(pet_name))
            act_conf = dict(json.load(open(act_path, 'r', encoding='UTF-8')))
            act_dict = {}
            act_dict = {k: Act.init_act(v, pic_dict, o.scale, pet_name, 'pet') for k, v in act_conf.items()}

            # 载入默认动作
            o.default = act_dict[conf_params['default']]
            o.up = act_dict[conf_params.get('up', 'default')]
            o.down = act_dict[conf_params.get('down', 'default')]
            o.left = act_dict[conf_params.get('left', 'default')]
            o.right = act_dict[conf_params.get('right', 'default')]
            o.drag = act_dict[conf_params.get('drag', 'default')]
            o.fall = act_dict[conf_params.get('fall', 'default')]
            prefall = conf_params.get('prefall', 'fall')
            o.prefall = act_dict.get(prefall, conf_params['default'])
            o.on_floor = act_dict[conf_params.get('on_floor', 'default')]
            o.patpat = act_dict[conf_params.get('patpat', 'default')]

            # Subpet position arguments
            o.follow_main_x = conf_params.get('follow_main_x', False)
            o.follow_main_y = conf_params.get('follow_main_y', False)
            o.anchor_to_main = conf_params.get('anchor_to_main', [])
            
            # Subpet Buff to chars
            o.buff_dict = conf_params.get('buff', {})
         
            # 初始化随机动作
            random_act = []
            act_prob = []
            act_name = []
            act_type = []
            act_sound = []

            for act_array in conf_params['random_act']:
                random_act.append([act_dict[act] for act in act_array['act_list']])
                act_prob.append(act_array.get('act_prob', 0.2))
                act_name.append(act_array.get('name', None))
                act_type.append(act_array.get('act_type', [2,1]))
                act_sound.append(act_array.get('sound', []))

            o.random_act = random_act
            if sum(act_prob) == 0:
                o.act_prob = [0] * len(act_prob)
            else:
                o.act_prob = [i/sum(act_prob) for i in act_prob]
            o.act_name = act_name
            o.act_type = act_type
            o.act_sound = act_sound

            # 和主宠物之间的交互
            o.main_interact = conf_params.get("main_interact", {})

            return o

def CheckCharFiles(folder):
    """ Check if the character files (under res/role/NAME/) are able to run with no potential error """
    """
    Status Code
        0: Success
        1: pet_conf.json broken or not exist
        2: act_conf.json broken or not exist
        3: action missing "images" attribute
        4: image files missing
        5: default action missing in pet_conf.json
        6: action called by pet_conf.json is missing from act_conf.json
    """
    # Check pet_conf.json and act_conf.json
    try:
        path = os.path.join(folder, 'pet_conf.json')
        pet_conf = json.load(open(path, 'r', encoding='UTF-8'))
    except:
        return 1, None

    try:
        path = os.path.join(folder, 'act_conf.json')
        act_conf = json.load(open(path, 'r', encoding='UTF-8'))
    except:
        return 2, None

    # Check if actions are well-defined, and no missing image files
    error_action = []
    missing_imgs = []
    for action, actDic in act_conf.items():
        if "images" not in actDic.keys():
            error_action.append(action)
            continue
        else:
            images = actDic['images']
            img_dir = os.path.normpath(os.path.join(folder, f'action/{images}'))
            list_images = glob.glob(f'{img_dir}_*.png')
            n_images = len(list_images)
            imgExist = [f'{img_dir}_{i}.png' for i in range(n_images) if not os.path.exists(f'{img_dir}_{i}.png')]
            if imgExist == []:
                pass
            else:
                missing_imgs += imgExist

    if error_action != []:
        return 3, error_action

    if missing_imgs != []:
        return 4, missing_imgs

    # Check if required actions exist
    reqAct = ['default','drag','fall']
    missAct = [i for i in reqAct if i not in pet_conf.keys()]
    if missAct != []:
        return 5, missAct

    # Check action in pet_conf.json are all defined in act_conf
    actionsKey = ["default", "up", "down", "left", "right", "drag", "fall", "on_floor", "patpat"]
    actions = [pet_conf[i] for i in actionsKey if i in pet_conf.keys()]

    random_act = pet_conf.get("random_act",[])
    for rndAct in random_act:
        actions += rndAct.get("act_list",[])

    accessory_act = pet_conf.get("accessory_act",[])
    for accAct in accessory_act:
        actions += accAct.get("act_list",[])
        actions += accAct.get("acc_list",[])

    missingActions = [i for i in actions if i not in act_conf.keys()]
    if missingActions != []:
        return 6, missingActions

    return 0, None




class Act:
    def __init__(self, images=(), act_num=1, need_move=False, direction=None, frame_move=10, frame_refresh=0.04, anchor=[0,0]):
        """
        动作
        :param images: 动作图像
        :param act_num 动作执行次数
        :param need_move: 是否需要移动
        :param direction: 移动方向
        :param frame_move 单帧移动距离
        :param frame_refresh 单帧刷新时间
        """
        self.images = images
        self.act_num = act_num
        self.need_move = need_move
        self.direction = direction
        self.frame_move = frame_move
        self.frame_refresh = frame_refresh
        self.anchor = anchor

    @classmethod
    def init_act(cls, conf_param, pic_dict, scale, pet_name, resFolder='role'):

        images = conf_param['images']
        img_dir = os.path.join(basedir, 'res/{}/{}/action/{}'.format(resFolder, pet_name, images))
        list_images = glob.glob('{}_*.png'.format(img_dir))
        n_images = len(list_images)
        img = []
        for i in range(n_images):
            img.append(pic_dict["%s_%s"%(images, i)])

        img = [i.scaled(int(i.width() * scale), 
                        int(i.height() * scale),
                        aspectMode=Qt.KeepAspectRatio,
                        mode=Qt.SmoothTransformation) for i in img]

        act_num = conf_param.get('act_num', 1)
        need_move = conf_param.get('need_move', False)
        direction = conf_param.get('direction', None)
        frame_move = conf_param.get('frame_move', 10) * scale
        frame_refresh = conf_param.get('frame_refresh', 0.5)
        anchor = conf_param.get('anchor', [0,0])
        return Act(img, act_num, need_move, direction, frame_move, frame_refresh, anchor)


def tran_idx_img(start_idx: int, end_idx: int, pic_dict: dict) -> list:
    """
    转化坐标与图像
    :param start_idx: 开始坐标
    :param end_idx: 结束坐标
    :param pic_dict: 图像dict
    :return: 一个动作所有的图片list
    """
    res = []
    for i in range(start_idx, end_idx + 1):
        res.append(pic_dict[str(i)])
    return res




class PetData:
    """
    宠物数据创建、读取、存储
    """

    def __init__(self, petsList):

        #self.petname = pet_name
        self.hp = 100
        self.hp_tier = 3
        self.fv = 0
        self.fv_lvl = 0
        self.items = {}
        self.coins = 0
        self.frozen_data = False

        self.file_path = os.path.join(basedir, 'data/pet_data.json') #%(self.petname)
        self.petsList = petsList
        self.current_pet = petsList[0]

        self.init_data()

    def init_data(self):

        if os.path.isfile(self.file_path):
            # Check file integrity
            try:
                allData_params = json.load(open(self.file_path, 'r', encoding='UTF-8'))
                self.saveGood = True
            except:
                #File broken (seen by a few users)
                allData_params = {}
                self.saveGood = False


            if self.current_pet in allData_params.keys():
                # Already the new version save structure
                pass

            elif 'HP' in allData_params.keys():
                # Still the old version of save structure
                new_allData_params = {}
                for pet in self.petsList:
                    new_allData_params[pet] = allData_params.copy()

                allData_params = new_allData_params

            else:
                # Already the new version save structure, but pet first loaded
                now = datetime.now()
                allData_params[self.current_pet] = {'HP':-1, 'HP_tier':3,
                                                    'FV':0, 'FV_lvl':0,
                                                    'items':{},
                                                    'coins':0,
                                                    'days':1,
                                                    'last_opened': '%i-%i-%i'%(now.year, now.month, now.day)}

        
        else:
            # First time using the App
            self.saveGood = True
            allData_params = {}
            now = datetime.now()
            for pet in self.petsList:
                allData_params[pet] = {'HP':-1, 'HP_tier':3,
                                        'FV':0, 'FV_lvl':0,
                                        'items':{},
                                        'coins':0,
                                        'days':1,
                                        'last_opened': '%i-%i-%i'%(now.year, now.month, now.day)}
            
        data_params = allData_params[self.current_pet]
        data_params = self._check_coins(data_params)
        self.hp = data_params['HP']
        self.hp_tier = data_params['HP_tier']
        self.fv = data_params['FV']
        self.fv_lvl = data_params['FV_lvl']
        self.items = data_params['items']
        self.coins = data_params['coins']
        self.days, self.last_opened = self._sumDays(data_params)
        data_params['days'] = self.days
        data_params['last_opened'] = self.last_opened
        allData_params[self.current_pet] = data_params.copy()

        self.allData_params = allData_params

        self.save_data()
        self.value_type = { key: type(data_params[key]) for key in data_params.keys() }

    def _check_coins(self, data_params):
        if 'coins' not in data_params:
            data_params['coins'] = 0
        return data_params

    def _sumDays(self, data_params):
        if 'days' in data_params:
            days = data_params['days']
            now = datetime.now()
            lp = data_params['last_opened'].split('-')
            last_opened = datetime(year=int(lp[0]), month=int(lp[1]), day=int(lp[2]),
                                   hour=now.hour, minute=now.minute, second=now.second)
            if (now - last_opened).days == 0:
                # 同一天重复打开
                days = days
                last_opened = '%i-%i-%i'%(now.year, now.month, now.day)
            else:
                days = days + 1
                last_opened = '%i-%i-%i'%(now.year, now.month, now.day)


        # 早已使用 但初次统计陪伴时间
        else:
            ct = os.path.getctime(self.file_path)
            ct = time.strptime(time.ctime(ct))
            ct = time.strftime("%Y-%m-%d", ct).split('-')

            now = datetime.now()
            ct = datetime(year=int(ct[0]), month=int(ct[1]), day=int(ct[2]),
                          hour=now.hour, minute=now.minute, second=now.second)
            time_diff = now - ct
            days = time_diff.days + 1
            last_opened = '%i-%i-%i'%(now.year, now.month, now.day)

        return days, last_opened


    def _change_pet(self, current_pet):
        self.current_pet = current_pet

        if current_pet not in self.allData_params.keys():
            now = datetime.now()
            self.allData_params[self.current_pet] = {'HP':-1, 'HP_tier':3,
                                                'FV':0, 'FV_lvl':0,
                                                'items':{},
                                                'coins':0,
                                                'days':1,
                                                'last_opened': '%i-%i-%i'%(now.year, now.month, now.day)}

        data_params = self.allData_params[self.current_pet]
        data_params = self._check_coins(data_params)
        self.hp = data_params['HP']
        self.hp_tier = data_params['HP_tier']
        self.fv = data_params['FV']
        self.fv_lvl = data_params['FV_lvl']
        self.items = data_params['items']
        self.coins = data_params['coins']
        self.days, self.last_opened = self._sumDays(data_params)
        data_params['days'] = self.days
        data_params['last_opened'] = self.last_opened
        self.allData_params[self.current_pet] = data_params.copy()

        self.save_data()


    def change_hp(self, hp_value, hp_tier=None):
        if self.frozen_data:
            return

        self.hp = hp_value
        if hp_tier is not None:
            self.hp_tier = int(hp_tier)

        self.allData_params[self.current_pet]['HP'] = self.hp
        self.allData_params[self.current_pet]['HP_tier'] = self.hp_tier

        self.save_data()

    def change_fv(self, fv_value, fv_lvl=None):
        if self.frozen_data:
            return

        self.fv = fv_value
        if fv_lvl is not None:
            self.fv_lvl = fv_lvl

        self.allData_params[self.current_pet]['FV'] = self.fv
        self.allData_params[self.current_pet]['FV_lvl'] = self.fv_lvl
        self.save_data()
    
    def change_coin(self, value_change):
        if self.frozen_data:
            return

        self.coins += value_change
        self.allData_params[self.current_pet]['coins'] = self.coins
        self.save_data()

    def change_item(self, item, item_change=None, item_num=None):
        if self.frozen_data:
            return

        if item in self.items.keys():
            if item_change is not None:
                self.items[item] += item_change
            else:
                self.items[item] = item_num
        else:
            if item_change is not None:
                self.items[item] = item_change
            else:
                self.items[item] = item_num

        self.allData_params[self.current_pet]['items'] = self.items
        self.save_data()

    def save_data(self):
        if self.frozen_data:
            return

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.allData_params, f, ensure_ascii=False, indent=4)


    def check_save_integrity(self, save_allDict, petname): #, days_info=False):

        if 'HP' in save_allDict:
            # Save to import is from old version
            save_dict = save_allDict
            try:
                check_key_value = all( key in save_dict and isinstance(save_dict[key], self.value_type[key]) for key in self.value_type.keys() )
            except:
                return 0
            if check_key_value:
                return 1
            else:
                return 0

        else:
            # Save to import is from new version
            if petname == 'all':
                for pet, save_dict in save_allDict.items():
                    try:
                        check_key_value = all( key in save_dict and isinstance(save_dict[key], self.value_type[key]) for key in self.value_type.keys() )
                    except:
                        return 0
                    if check_key_value:
                        continue
                    else:
                        return 0
                return 1
            else:
                save_dict = save_allDict.get(petname, None)
                if save_dict is None:
                    return 0
                else:
                    try:
                        check_key_value = all( key in save_dict and isinstance(save_dict[key], self.value_type[key]) for key in self.value_type.keys() )
                    except:
                        return 0
                    if check_key_value:
                        return 1
                    else:
                        return 0


    def transfer_save(self, save_allDict, petname, days_info=False):

        try:
            if 'HP' in save_allDict:
                # Save to import is from old version
                save_dict = save_allDict
                if petname == 'all':
                    for pet in self.allData_params.keys():
                        self.transfer_save_toPet(save_dict, pet)
                else:
                    self.transfer_save_toPet(save_dict, petname)
            else:
                # Save to import is from new version
                if petname == 'all':
                    for pet, save_dict in save_allDict.items():
                        self.transfer_save_toPet(save_dict, pet)
                else:
                    save_dict = save_allDict.get(petname, None) #[petname]
                    if not save_dict:
                        return 0
                    self.transfer_save_toPet(save_dict, petname)
        except:
            return 0

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.allData_params, f, ensure_ascii=False, indent=4)
        return 1

    def transfer_save_toPet(self, data_params, petname):

        data_params = self._check_coins(data_params)

        if petname not in self.allData_params.keys():
            self.allData_params[petname] = data_params.copy()
        else:
            days, last_opened = self.allData_params[petname]['days'], self.allData_params[petname]['last_opened']
            self.allData_params[petname] = data_params.copy()
            self.allData_params[petname]['days'] = days
            self.allData_params[petname]['last_opened'] = last_opened

        if petname == self.current_pet:
            data_params = self.allData_params[self.current_pet]
            self.hp = data_params['HP']
            self.hp_tier = data_params['HP_tier']
            self.fv = data_params['FV']
            self.fv_lvl = data_params['FV_lvl']
            self.items = data_params['items']
            self.coins = data_params['coins']
            self.days = data_params['days']
            self.last_opened = data_params['last_opened']


    def frozen(self):
        self.frozen_data = True




class ItemData:
    """
    物品数据的读取
    """

    def __init__(self, HUNGERSTR='Satiety', FAVORSTR='Favorability'):

        #self.file_path = os.path.join(basedir, 'res/items/items_config.json')
        self.item_dict = {}
        #self.item_conf = dict(json.load(open(self.file_path, 'r', encoding='UTF-8')))
        self.reward_dict = {}
        self.HUNGERSTR = HUNGERSTR
        self.FAVORSTR = FAVORSTR
        #self.MODs = []
        self.init_data()


    def init_data(self):
        #print("check")
        """ Load in all the item MOD """
        '''
        If one item name appears in more than 1 MOD, latest MOD will overwrite old ones
        '''

        # Load in all the MODs
        #self.item_dict = {k: self.init_item(v, k) for k, v in self.item_conf.items()}
        itemMods = get_child_folder(os.path.join(basedir,'res/items'), relative=False)
        modTimes = [get_file_time(mod) for mod in itemMods]
        paired_list = zip(modTimes, itemMods)
        # Sort the pairs
        sorted_pairs = sorted(paired_list)
        # Extract the sorted elements
        sorted_itemMods = [element for _, element in sorted_pairs]

        mod_configs = []
        for i, itemFolder in enumerate(sorted_itemMods):

            conf_file = os.path.join(itemFolder, 'items_config.json')

            if not os.path.exists(conf_file):
                continue

            item_conf = dict(json.load(open(conf_file, 'r', encoding='UTF-8')))
            MOD_dict = {k: self.init_item(v, k, itemFolder) for k, v in item_conf.items()}
            mod_configs.append(MOD_dict)


        # Union and Remove duplicates
        for mod_cnf in mod_configs:
            self.item_dict.update(mod_cnf) #MOD_dict[modKey])

        # Remove duplicates in reward_dict
        for k, v in self.reward_dict.items():
            v = list(set(v))
            self.reward_dict[k] = v

    def init_item(self, conf_param, itemName, itemFolder):
        """
        物品
        :param name: 物品名称
        :param image 物品图片路径
        :param effect_HP: 对饱食度的效果
        :param effect_FV: 对好感度的效果
        :param drop_rate 完成任务后的掉落概率
        :param fv_lock 好感度锁
        :param description 物品描述
        """
        name = itemName #conf_param['name']
        image = _load_item_img(os.path.join(itemFolder, conf_param['image']))
        effect_HP = int(conf_param.get('effect_HP', 0))
        
        if effect_HP > 0:
            effect_HP_str = '+%s'%effect_HP
        else:
            effect_HP_str = effect_HP

        effect_FV = int(conf_param.get('effect_FV', 0))
        if effect_FV > 0:
            effect_FV_str = '+%s'%effect_FV
        else:
            effect_FV_str = effect_FV

        drop_rate = float(conf_param.get('drop_rate', 0))
        fv_lock = int(conf_param.get('fv_lock', 1))
        description = text_wrap(conf_param.get('description', ''), 15) #self.wrapper(conf_param.get('description', ''))
        item_type = conf_param.get('type', 'consumable')

        if effect_FV==0 and effect_HP==0:
            hint = '{} {}\n\n{}\n'.format(name,
                                        ' '.join(['⭐']*fv_lock), 
                                        description)
        else:
            hint = f"{name} {' '.join(['⭐']*fv_lock)}\n\n{description}\n____________________________________\n\n{self.HUNGERSTR}: {effect_HP_str}\n{self.FAVORSTR}: {effect_FV_str}\n"
        fvs = conf_param.get('fv_reward',[])
        if type(fvs) == int:
            fvs = [fvs]

        if len(fvs) > 0:
            for fv in fvs:
                if fv in self.reward_dict:
                    self.reward_dict[fv].append(name)
                else:
                    self.reward_dict[fv] = []
                    self.reward_dict[fv].append(name)

        pet_limit = conf_param.get('pet_limit', [])
            

        return {'name': name,
                'image': image,
                'effect_HP': effect_HP,
                'effect_FV': effect_FV,
                'drop_rate': drop_rate,
                'fv_lock': fv_lock,
                'hint': hint,
                'item_type': item_type,
                'pet_limit': pet_limit
               }

    def wrapper(self, texts):
        n_char = len(texts)
        n_line = int(n_char//10 + 1)
        texts_wrapped = ''
        for i in range(n_line):
            texts_wrapped += texts[(10*i):min((10*i + 10),n_char)] + '\n'
        texts_wrapped = texts_wrapped.rstrip('\n')

        return texts_wrapped


def load_ItemMod(configPath, HUNGERSTR='Satiety', FAVORSTR='Favorability'):
    """ Load item configuration """
    
    item_conf = dict(json.load(open(configPath, 'r', encoding='UTF-8')))
    itemFolder = os.path.dirname(configPath)

    return {k: init_item(v, k, itemFolder, HUNGERSTR, FAVORSTR) for k, v in item_conf.items()}


def init_item(conf_param, itemName, itemFolder, HUNGERSTR, FAVORSTR):
    """
    物品
    :param name: 物品名称
    :param image 物品图片路径
    :param effect_HP: 对饱食度的效果
    :param effect_FV: 对好感度的效果
    :param drop_rate 完成任务后的掉落概率
    :param fv_lock 好感度锁
    :param description 物品描述
    """

    name = itemName #conf_param['name']
    image = _load_item_img(os.path.join(itemFolder, conf_param['image']))
    effect_HP = int(conf_param.get('effect_HP', 0))
    
    if effect_HP > 0:
        effect_HP_str = '+%s'%effect_HP
    else:
        effect_HP_str = effect_HP

    effect_FV = int(conf_param.get('effect_FV', 0))
    if effect_FV > 0:
        effect_FV_str = '+%s'%effect_FV
    else:
        effect_FV_str = effect_FV

    drop_rate = float(conf_param.get('drop_rate', 0))
    fv_lock = int(conf_param.get('fv_lock', 1))
    description = text_wrap(conf_param.get('description', ''), 15)
    item_type = conf_param.get('type', 'consumable')

    if effect_FV==0 and effect_HP==0:
        hint = '{} {}\n\n{}\n'.format(name,
                                    ' '.join(['⭐']*fv_lock), 
                                    description)
    else:
        hint = f"{name} {' '.join(['⭐']*fv_lock)}\n\n{description}\n____________________________________\n\n{HUNGERSTR}: {effect_HP_str}\n{FAVORSTR}: {effect_FV_str}\n"
    '''
    fvs = conf_param.get('fv_reward',[])
    if type(fvs) == int:
        fvs = [fvs]

    if len(fvs) > 0:
        for fv in fvs:
            if fv in self.reward_dict:
                self.reward_dict[fv].append(name)
            else:
                self.reward_dict[fv] = []
                self.reward_dict[fv].append(name)
    '''

    pet_limit = conf_param.get('pet_limit', [])
        

    return {'name': name,
            'image': image,
            'effect_HP': effect_HP,
            'effect_FV': effect_FV,
            'drop_rate': drop_rate,
            'fv_lock': fv_lock,
            'hint': hint,
            'item_type': item_type,
            'pet_limit': pet_limit
           }


def checkItemMOD(itemFolder):
    """ Check if the item MOD (under res/items/MODENAME/) are able to be loaded with no potential error """
    """
    Status Code
        0: Success
        1: items_config.json broken or not exist
        2: "image" key missing
        3: missing image files
        4: "pet_limit" is not list
    """

    # Load config file
    configFile = os.path.join(itemFolder,'items_config.json')
    try:
        item_dict = dict(json.load(open(configFile, 'r', encoding='UTF-8')))
    except:
        return 1, None

    # All necessary keys exist
    missingKey = [k for k, v in item_dict.items() if 'image' not in v.keys()]
    if missingKey:
        return 2, missingKey

    # Image should exist
    missingImage = [k for k, v in item_dict.items() if not os.path.exists(os.path.join(itemFolder, v['image']))]
    if missingImage:
        return 3, missingImage

    # pet_limit should be an list
    typeMissmatch = [k for k, v in item_dict.items() if type(v.get('pet_limit', [])) is not list]
    if typeMissmatch:
        return 4, typeMissmatch
    
    return 0, None


def _load_item_img(img_path):

    img_file = img_path #os.path.join(basedir, 'res/items/{}'.format(img_path))
    return _get_q_img(img_file)

def _get_q_img(img_file) -> QImage:

    image = QImage()
    image.load(img_file)
    return image









