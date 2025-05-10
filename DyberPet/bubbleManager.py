import os
import re
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

[1] The 'icon' is configured within the code, please keep it as null
[2] To cusomize this, add any number of pat_random_[0-9]* in configuration file
    


Config Structure
-------------------------
{
    BEHAVIOR: {
        "icon": "system",
        "message": "The text shown in the bubble",
        "countdown": 300, # if specified, a countdown will be triggered and shown on the bubble
        气泡的倒计时
        "start_audio" "system", # the string points to the note_type in note_icon.json
        "end_audio": null
    }
}

"""

# TODO: feed_required 相关翻译 更新开发文档

class BubbleManager(QObject):
    """
    Class to manage all behaviors of bubbleText
    """

    register_bubble = Signal(dict, name='register_bubble')

    attr_list = ["icon", "message", "countdown", "start_audio", "end_audio"]

    bubble_hp_tier = {0: ["fv_drop", "hp_zero", "feed_required"],
                      1: ["hp_low", "feed_required"],
                      2: ["hp_low", "feed_required"]}

    def __init__(self,
                 parent=None):
        super().__init__(parent=parent)
        self.bubble_conf = self.load_bubble_config()


    def load_bubble_config(self) -> dict:
        system_conf_file = os.path.join(basedir, 'res/icons/bubble_conf.json')
        pet_bb_conf_file = os.path.join(basedir, f'res/role/{settings.petname}/note/bubble_conf.json')
        bubble_conf = dict(json.load(open(system_conf_file, 'r', encoding='UTF-8')))

        # Load any changes made in pet config
        if os.path.exists(pet_bb_conf_file):
            pet_bb_conf = dict(json.load(open(pet_bb_conf_file, 'r', encoding='UTF-8')))
            # Default buble type config changes
            for k in bubble_conf.keys():
                if k in pet_bb_conf.keys():
                    bubble_conf[k].update(pet_bb_conf[k])
            
            # Any newly added bubble type in pet bubble config
            for k in pet_bb_conf.keys():
                if k not in bubble_conf.keys():
                    bubble_conf[k] = self._format_bubble_type_conf(pet_bb_conf[k])

        return bubble_conf
    
    def _format_bubble_type_conf(self, bubble_type_conf):
        final_conf = {}
        for k in self.attr_list:
            v = bubble_type_conf.get(k, None)
            final_conf[k] = v
        return final_conf

    def trigger_bubble(self, bb_type):
        bubble_dict = self.bubble_conf.get(bb_type, {}).copy()
        if not bubble_dict:
            return
        
        if bb_type == "feed_required":
            bubble_dict = self.prepare_feed_required()
            if not bubble_dict:
                return
        
        # change bubble type like 'pat_random_1' into 'pat_random'
        bb_type = "_".join(bb_type.split("_")[:2])
        bubble_dict['bubble_type'] = bb_type

        # Translate message
        message = bubble_dict.get('message', '')
        message = self.tr(message)

        # Change the nickname of user
        message = self._replace_usertag(message)
        bubble_dict['message'] = message

        if settings.bubble_on:
            self.register_bubble.emit(bubble_dict)

    def trigger_scheduled(self):
        # Randomly select bubble type
        cand_bubbles = self.bubble_hp_tier.get(settings.pet_data.hp_tier, [])
        if not cand_bubbles:
            return
        bb_type = random.choice(cand_bubbles)
        self.trigger_bubble(bb_type)
    
    def trigger_patpat_random(self):
        candidates = [k for k in self.bubble_conf.keys() if k.startswith("pat_random_")]
        if candidates:
            bb_type = random.choice(candidates)
            self.trigger_bubble(bb_type)

    def prepare_feed_required(self):
        # Check if hp and fv are already full
        hp_full = settings.pet_data.hp >= ((settings.HP_TIERS[-1]-1)*settings.HP_INTERVAL)
        fv_full = (settings.pet_data.fv_lvl == (len(settings.LVL_BAR)-1)) and (settings.pet_data.fv==settings.LVL_BAR[settings.pet_data.fv_lvl])
        if hp_full and fv_full:
            return {}
        
        bubble_dict = self.bubble_conf['feed_required'].copy()

        # List all candidate items
        all_items = settings.items_data.item_dict.keys()
        candidate_items = [i for i in all_items if settings.items_data.item_dict[i]['item_type'] == 'consumable']
        # exclude dislike items
        dislike_items = set(settings.pet_conf.item_dislike.keys())
        candidate_items = [i for i in candidate_items if i not in dislike_items and i != 'coin']
        # exclude items with negative effect
        candidate_items = [i for i in candidate_items if settings.items_data.item_dict[i]['effect_HP'] > 0 or settings.items_data.item_dict[i]['effect_FV'] > 0]
        # check if list empty
        if not candidate_items:
            return {}
        # Choose one
        selected_item = random.choice(candidate_items)
        
        # Update the bubble_dict
        bubble_dict['icon'] = selected_item
        bubble_dict['item'] = selected_item
        bubble_dict['message'] = self.tr(bubble_dict['message'])
        bubble_dict['message'] = bubble_dict['message'].replace("ITEMNAME", f"[{selected_item}]")

        return bubble_dict
    
    def add_usertag(self, bubble_dict:dict, position:str = 'front', send:bool = False):
        # add USERTAG in string
        message = bubble_dict.get('message', '')
        if position == 'front':
            message = f'USERTAG {message}'
        elif position == 'end':
            message = f'{message} USERTAG'

        # replace usertag
        message = self._replace_usertag(message)
        bubble_dict['message'] = message

        if send and settings.bubble_on:
            self.register_bubble.emit(bubble_dict)
        else:
            return bubble_dict
    
    def _replace_usertag(self, message):
        usertag = settings.usertag_dict.get(settings.petname, "")
        if usertag:
            message = message.replace('USERTAG', usertag)
        else:
            message = message.replace('USERTAG', usertag)
        message = message.strip(' ')
        # Remove consecutive spaces
        message = re.sub(r'\s{2,}', ' ', message)
        return message
    
    def _trigger_HP(self):
        return
    
    def _trigger_FV(self):
        return
    
    def _trigger_feed(self):
        return
    
    def _trigger_focus(self):
        return





