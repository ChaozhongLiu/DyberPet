from PyQt5.QtGui import QImage
from DyberPet.conf import PetData



def init(pet_name):
    global current_img, previous_img
    # Make img-to-show a global variable for multi-thread behaviors
    current_img = QImage()
    previous_img = QImage()

    global onfloor, draging, set_fall, playid
    global mouseposx1,mouseposx2,mouseposx3,mouseposx4,mouseposx5
    global mouseposy1,mouseposy2,mouseposy3,mouseposy4,mouseposy5
    global dragspeedx,dragspeedy,fixdragspeedx, fixdragspeedy, fall_right
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

    global act_id, current_act, previous_act
    # Select animation to show
    act_id = 0
    current_act, previous_act = None, None

    global showing_dialogue_now
    showing_dialogue_now = False

    global pet_data 
    pet_data = PetData(pet_name)


