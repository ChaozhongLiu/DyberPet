from PyQt5.QtGui import QImage
from DyberPet.conf import PetData
import ctypes
import json
import os

def init():

    global current_img, previous_img
    # Make img-to-show a global variable for multi-thread behaviors
    current_img = QImage()
    previous_img = QImage()

    global onfloor, draging, set_fall, playid
    global mouseposx1,mouseposx2,mouseposx3,mouseposx4,mouseposx5
    global mouseposy1,mouseposy2,mouseposy3,mouseposy4,mouseposy5
    global dragspeedx,dragspeedy,fixdragspeedx, fixdragspeedy, fall_right, gravity
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

    global act_id, current_act, previous_act
    # Select animation to show
    act_id = 0
    current_act, previous_act = None, None

    global showing_dialogue_now
    showing_dialogue_now = False

    # size settings
    global size_factor, screen_scale, font_factor, status_margin, statbar_h, tunable_scale
    #size_factor = 1 #resolution_factor = min(width/2560, height/1440)
    size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    #font_factor = 1 #/ screen_scale
    tunable_scale = 1.0

    # sound
    global volume
    volume = 0.4

    global petname
    petname = ''
    #status_margin = 3 #int(3 * resolution_factor)
    #statbar_h = 15 #int(15 * resolution_factor)

    init_pet()



def init_pet():
    global pet_data 
    pet_data = PetData()
    init_settings()

def init_settings():
    global file_path
    file_path = 'data/settings.json'

    global gravity, fixdragspeedx, fixdragspeedy, tunable_scale, volume
    if os.path.isfile(file_path):
        data_params = json.load(open(file_path, 'r', encoding='UTF-8'))

        fixdragspeedx, fixdragspeedy = data_params['fixdragspeedx'], data_params['fixdragspeedy']
        gravity = data_params['gravity']
        tunable_scale = data_params['tunable_scale']
        volume = data_params['volume']

    else:
        fixdragspeedx, fixdragspeedy = 1.0, 1.0
        gravity = 0.1
        tunable_scale = 1.0
        volume = 0.4
        save_settings()

def save_settings():
    global file_path, gravity, fixdragspeedx, fixdragspeedy, tunable_scale, volume

    data_js = {'gravity':gravity,
               'fixdragspeedx':fixdragspeedx,
               'fixdragspeedy':fixdragspeedy,
               'tunable_scale':tunable_scale,
               'volume':volume
               }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data_js, f, ensure_ascii=False, indent=4)
