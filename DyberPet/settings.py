import os
import json
import ctypes
from sys import platform

from PySide6.QtGui import QImage
from DyberPet.conf import PetData
from PySide6 import QtCore

if platform == 'win32':
    basedir = ''
    BASEDIR = ''
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-1])
    BASEDIR = basedir


HELP_URL = "https://github.com/ChaozhongLiu/DyberPet/issues"
PROJECT_URL = "https://github.com/ChaozhongLiu/DyberPet"
DEVDOC_URL = "https://github.com/ChaozhongLiu/DyberPet/blob/main/docs/art_dev.md"
VERSION = "v0.3.2"
AUTHOR = "https://github.com/ChaozhongLiu"
CHARCOLLECT_LINK = "https://github.com/ChaozhongLiu/DyberPet"
ITEMCOLLECT_LINK = "https://github.com/ChaozhongLiu/DyberPet"

HP_TIERS = [0,50,80,100]
TIER_NAMES = ['Starving', 'Hungry', 'Normal', 'Energetic']
HP_INTERVAL = 2
LVL_BAR = [20, 120, 300, 600, 1200, 1800, 2400, 3200]
PP_HEART = 0.8
PP_COIN = 0.9
COIN_MU = 10
COIN_SIGMA = 5
PP_ITEM = 0.95
PP_AUDIO = 0.8

HUNGERSTR = "Satiety"
FAVORSTR = "Favorability"

LINK_PERMIT = {"BiliBili":"https://space.bilibili.com/",
               "微博":"https://m.weibo.cn/profile/",
               "抖音": "https://www.douyin.com/user/",
               "GitHub":"https://github.com/",
               "爱发电":"https://afdian.net/a/",
               "TikTok":"https://www.tiktok.com/",
               "YouTube":"https://www.youtube.com/"}

ITEM_BGC = {'consumable': '#EFEBDF',
            'collection': '#e1eaf4',
            'Empty': '#f0f0ef',
            'dialogue': '#e1eaf4'}
ITEM_BGC_DEFAULT = '#EFEBDF'
ITEM_BDC = '#B1C790'


def init():
    # computer system ==================================================
    global platform
    platform = platform

    # check if data directory exists ===================================
    newpath = os.path.join(basedir, 'data')
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    # Image and animation related variable =============================
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
    try:
        size_factor = 1.0 #ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    except:
        size_factor = 1.0
    tunable_scale = 1.0

    # sound volumn =====================================================
    global volume
    volume = 0.4

    # pet name =========================================================
    global petname
    petname = ''

    # which screen =====================================================
    global screens, current_screen
    screens = []
    current_screen = None

    # Always on top ====================================================
    global on_top_hint, pets
    on_top_hint = True

    # Settings =========================================================
    pets = get_petlist(os.path.join(basedir, 'res/role'))
    init_settings()
    save_settings()
    pets.remove(default_pet)
    pets = [default_pet] + pets

    # Default Animation ================================================
    #global defaultAct
    #defaultAct = None

    # Pamodoro variable
    global current_tm_option
    current_tm_option = None

    # Load in pet data ================================================
    global pet_data 
    pet_data = PetData(pets)

    # Load in Language Choice ==========================================
    global language_code, lang_dict
    global translator
    lang_dict = json.load(open(os.path.join(basedir, 'res/language/language.json'), 'r', encoding='UTF-8'))
    change_translator(language_code)



'''
def init_pet():
    global pet_data 
    pet_data = PetData()
    init_settings()
    save_settings()
'''


def init_settings():
    global file_path, settingGood
    file_path = os.path.join(basedir, 'data/settings.json')

    global gravity, fixdragspeedx, fixdragspeedy, tunable_scale, volume, \
           language_code, on_top_hint, default_pet, defaultAct

    # check json file integrity
    try:
        json.load(open(file_path, 'r', encoding='UTF-8'))
        settingGood = True
    except:
        if os.path.isfile(file_path):
            settingGood = False
        else:
            settingGood = True

    if os.path.isfile(file_path) and settingGood:
        data_params = json.load(open(file_path, 'r', encoding='UTF-8'))

        fixdragspeedx, fixdragspeedy = data_params['fixdragspeedx'], data_params['fixdragspeedy']
        gravity = data_params['gravity']
        tunable_scale = data_params['tunable_scale']
        volume = data_params['volume']
        language_code = data_params.get('language_code', QtCore.QLocale().name())
        on_top_hint = data_params.get('on_top_hint', True)
        default_pet = data_params.get('default_pet', pets[0])
        defaultAct = data_params.get('defaultAct', {})

        # Fix a bug version distributed to users =============
        if defaultAct is None:
            defaultAct = {}
        elif type(defaultAct) == str:
            defaultAct = {}

        for pet in pets:
            defaultAct[pet] = defaultAct.get(pet, None)
        #=====================================================

        # update for app <= v0.2.2 ===========================
        if language_code == 'CN':
            language_code = QtCore.QLocale().name()
        #=====================================================

    else:
        fixdragspeedx, fixdragspeedy = 1.0, 1.0
        gravity = 0.1
        tunable_scale = 1.0
        volume = 0.5
        language_code = QtCore.QLocale().name()
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

def change_translator(language_code):
    global translator
    if language_code == 'en_US':
        translator = None
    else:
        translator = QtCore.QTranslator()
        translator.load(QtCore.QLocale(language_code), "langs", ".", os.path.join(basedir, "res/language/"))

        global TIER_NAMES, HUNGERSTR, FAVORSTR
        TIER_NAMES = [translator.translate("others", i) for i in TIER_NAMES] #.encode('utf-8')
        HUNGER_trans = translator.translate("others", HUNGERSTR) #.encode('utf-8'))
        if HUNGER_trans:
            HUNGERSTR = HUNGER_trans
        FAVOR_trans = translator.translate("others", FAVORSTR) #.encode('utf-8'))
        if FAVOR_trans:
            FAVORSTR = FAVOR_trans

