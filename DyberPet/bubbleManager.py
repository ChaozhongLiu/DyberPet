import os
import json
from PySide6.QtCore import QObject, Signal

import DyberPet.settings as settings
basedir = settings.BASEDIR

"""
List of buble behavior
-------------------------
1. Favorability
    - fv_lvlup
    - fv_stop
    - fv_drop

2. HP (Satiety)
    - hp_low
    - hp_zero

3. Feed
    - feed_done
    - feed_required

4. patpat
    - pat_focus
    - pat_frequent
    - pat_random

5. Focus
    - focus_random

    
Config Structure
-------------------------
{
    BEHAVIOR: {
        "icon"
        "message"
        "countdown"
        "start_audio"
        "end_audio"
    }
}

"""

# TODO

class BubbleManager(QObject):
    """
    Class to manage all behaviors of bubbleText
    """

    register_bubble = Signal(dict, name='register_bubble')

    def __init__(self,
                 parent=None):
        super().__init__(parent=parent)
        self.bubble_conf = self.load_bubble_config()


    def load_bubble_config(self) -> dict:
        system_conf_file = os.path.join(basedir, 'res/icons/bubble_conf.json')
        pet_bb_conf_file = os.path.join(basedir, f'res/role/{settings.petname}/note/bubble_conf.json')
        bubble_conf = dict(json.load(open(system_conf_file, 'r', encoding='UTF-8')))

        if os.path.exists(pet_bb_conf_file):
            pet_bb_conf = dict(json.load(open(pet_bb_conf_file, 'r', encoding='UTF-8')))
            for k in bubble_conf.keys():
                if k in pet_bb_conf.keys():
                    bubble_conf[k].update(pet_bb_conf[k])

        return bubble_conf

    def trigger_bubble(self, bb_type):
        bubble_dict = self.bubble_conf.get(bb_type, {})
        if not bubble_dict:
            return
        # Translate message
        message = bubble_dict.get('message', '')
        message = self.tr(message)
        bubble_dict['message'] = message
        # TODO: Change the nickname of user
        self.register_bubble.emit(bubble_dict)
    
    def trigger_patpat(self):
        return
    
    def trigger_scheduled(self):
        return
    
    def _trigger_HP(self):
        return
    
    def _trigger_FV(self):
        return
    
    def _trigger_feed(self):
        return
    
    def _trigger_focus(self):
        return





