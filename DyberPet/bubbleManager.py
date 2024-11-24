import os
import json
import random
from PySide6.QtCore import QObject, Signal

import DyberPet.settings as settings
basedir = settings.BASEDIR

"""
List of buble behavior
-------------------------
1. Favorability
    - fv_lvlup
    - fv_drop

2. HP (Satiety)
    - hp_low
    - hp_zero

3. Feed
    - feed_done
    - feed_required [1]

4. patpat
    - pat_focus
    - pat_frequent
    - pat_random [2]

[1] This is triggered inside the code, no configuration needed
[2] To cusomize this, add any number of pat_random_[0-9]* in configuration file
    


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

# TODO: implement pat_focus, pat_frequent, pat_random, feed_required
# TODO: limit the number of bubbles displayed

class BubbleManager(QObject):
    """
    Class to manage all behaviors of bubbleText
    """

    register_bubble = Signal(dict, name='register_bubble')

    bubble_hp_tier = {0: ["fv_drop", "hp_zero"],
                      1: ["hp_low"],
                      2: ["hp_low"]}

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

    def trigger_scheduled(self):
        # Randomly select bubble type
        cand_bubbles = self.bubble_hp_tier.get(settings.pet_data.hp_tier, [])
        if not cand_bubbles:
            return
        bb_type = random.choice(cand_bubbles)
        self.trigger_bubble(bb_type)
    
    def trigger_patpat(self):
        return
    
    def _trigger_HP(self):
        return
    
    def _trigger_FV(self):
        return
    
    def _trigger_feed(self):
        return
    
    def _trigger_focus(self):
        return





