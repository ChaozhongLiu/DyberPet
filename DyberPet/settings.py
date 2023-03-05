import os
import json
import ctypes
from sys import platform

from PyQt5.QtGui import QImage
from DyberPet.conf import PetData

if platform == 'win32':
    basedir = ''
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-1])


def init():
    global platform
    platform = platform

    # Check data directory
    newpath = os.path.join(basedir, 'data')
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    global current_img, previous_img
    # Make img-to-show a global variable for multi-thread behaviors
    current_img = QImage()
    previous_img = QImage()
    global current_anchor, previous_anchor
    current_anchor = [0,0]
    previous_anchor = [0,0]

    global onfloor, draging, set_fall, playid
    global mouseposx1,mouseposx2,mouseposx3,mouseposx4,mouseposx5
    global mouseposy1,mouseposy2,mouseposy3,mouseposy4,mouseposy5
    global dragspeedx,dragspeedy,fixdragspeedx, fixdragspeedy, fall_right, gravity, prefall
    # Drag and fall related global variable
    onfloor = 1
    draging = 0
    set_fall = 1 # default is allow drag
    playid = 0
    mouseposx1,mouseposx2,mouseposx3,mouseposx4,mouseposx5=0,0,0,0,0
    mouseposy1,mouseposy2,mouseposy3,mouseposy4,mouseposy5=0,0,0,0,0
    dragspeedx,dragspeedy=0,0
    fixdragspeedx, fixdragspeedy = 1.0, 1.0
    fall_right = 0
    gravity = 0.1
    prefall = 0

    global act_id, current_act, previous_act
    # Select animation to show
    act_id = 0
    current_act, previous_act = None, None

    global showing_dialogue_now
    showing_dialogue_now = False

    # size settings
    global size_factor, screen_scale, font_factor, status_margin, statbar_h, tunable_scale
    #size_factor = 1 #resolution_factor = min(width/2560, height/1440)
    #size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    try:
        size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    except:
        size_factor = 1
    #font_factor = 1 #/ screen_scale
    tunable_scale = 1.0

    # sound
    global volume
    volume = 0.4

    global petname
    petname = ''
    #status_margin = 3 #int(3 * resolution_factor)
    #statbar_h = 15 #int(15 * resolution_factor)
    #global language_dict
    #language_dict = dict(json.load(open('res/language.json', 'r', encoding='UTF-8')))
    global screens, current_screen
    screens = []
    current_screen = None

    global on_top_hint
    on_top_hint = True

    global pets
    pets = get_petlist(os.path.join(basedir, 'res/role'))

    global defaultAct
    defaultAct = None

    init_pet()
    pets.remove(default_pet)
    pets = [default_pet] + pets

    #global pet_config_dict
    #pet_config_dict = {}



def init_pet():
    global pet_data 
    pet_data = PetData()
    init_settings()
    save_settings()

def init_settings():
    global file_path
    file_path = os.path.join(basedir, 'data/settings.json')

    global gravity, fixdragspeedx, fixdragspeedy, tunable_scale, volume, \
           language_code, on_top_hint, default_pet, defaultAct
    if os.path.isfile(file_path):
        data_params = json.load(open(file_path, 'r', encoding='UTF-8'))

        fixdragspeedx, fixdragspeedy = data_params['fixdragspeedx'], data_params['fixdragspeedy']
        gravity = data_params['gravity']
        tunable_scale = data_params['tunable_scale']
        volume = data_params['volume']
        language_code = data_params['language_code']
        on_top_hint = data_params.get('on_top_hint', True)
        default_pet = data_params.get('default_pet', pets[0])
        defaultAct = data_params.get('defaultAct', {})

        # 旧版本的替换
        if defaultAct is None:
            defaultAct = {}
        elif type(defaultAct) == str:
            defaultAct = {}

        for pet in pets:
            defaultAct[pet] = defaultAct.get(pet, None)



    else:
        fixdragspeedx, fixdragspeedy = 1.0, 1.0
        gravity = 0.1
        tunable_scale = 1.0
        volume = 0.4
        language_code = 'CN'
        on_top_hint = True
        default_pet = pets[0]
        defaultAct = {}
        for pet in pets:
            defaultAct[pet] = defaultAct.get(pet, None)
        save_settings()

def save_settings():
    global file_path, gravity, fixdragspeedx, fixdragspeedy, tunable_scale, volume, \
           language_code, on_top_hint, default_pet, defaultAct

    data_js = {'gravity':gravity,
               'fixdragspeedx':fixdragspeedx,
               'fixdragspeedy':fixdragspeedy,
               'tunable_scale':tunable_scale,
               'volume':volume,
               'on_top_hint':on_top_hint,
               'default_pet':default_pet,
               'defaultAct':defaultAct,
               'language_code':language_code
               }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data_js, f, ensure_ascii=False, indent=4)

def get_petlist(dirname):
    folders = os.listdir(dirname)
    pets = []
    subpets = []
    for folder in folders:
        folder_path = os.path.join(dirname, folder)
        if folder != 'sys' and os.path.isdir(folder_path):
            pets.append(folder)
            conf_path = os.path.join(folder_path, 'pet_conf.json')
            conf = dict(json.load(open(conf_path, 'r', encoding='UTF-8')))
            subpets += [i for i in conf.get('subpet',{}).keys()]
    pets = list(set(pets))
    subpets = list(set(subpets))
    for subpet in subpets:
        pets.remove(subpet)

    return pets
