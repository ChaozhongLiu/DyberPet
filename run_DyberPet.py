from DyberPet.DyberPet import PetWidget
from DyberPet.Notification import DPNote
from DyberPet.utils import read_json
from PyQt5.QtWidgets import QApplication
import sys

import ctypes
size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

StyleSheet = f"""
#PetHP {{
    border: {2*size_factor}px solid #535053;
    border-radius: {7*size_factor}px;
}}
#PetHP::chunk {{
    background-color: #FAC486;
    border-radius: {5*size_factor}px;
}}

#PetTM {{
    border: {2*size_factor}px solid #535053;
    border-radius: {7*size_factor}px;
}}
#PetTM::chunk {{
    background-color: #ef4e50;
    border-radius: {5*size_factor}px;
}}

#PetEM {{
    border: {2*size_factor}px solid #535053;
    border-radius: {7*size_factor}px;
}}
#PetEM::chunk {{
    background-color: #F69290;
    border-radius: {5*size_factor}px;
}}

#PetFC {{
    border: {2*size_factor}px solid #535053;
    border-radius: {7*size_factor}px;
}}
#PetFC::chunk {{
    background-color: #47c0d2;
    border-radius: {5*size_factor}px;
}}
"""
'''
QPushButton#InvenButton {{
    background-color: #f184ae;
    color: #000000;
    border-style: outset;
    padding: 10px;
    font: bold 15px;
    border-width: 2px;
    border-radius: 10px;
    border-color: #facccc;
}}
QPushButton#InvenButton:hover:!pressed {{
    background-color: #ea4d8a;
}}
QPushButton#InvenButton:pressed {{
    background-color: #e72871;
}}
QPushButton#InvenButton:disabled {{
    background-color: #bcbdbc;
}}
'''




if __name__ == '__main__':
    # 加载所有角色, 启动应用并展示第一个角色
    pets = read_json('data/pets.json')
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    p = PetWidget(pets=pets)
    note = DPNote()

    p.setup_notification.connect(note.setup_notification)
    p.hptier_changed_main_note.connect(note.hpchange_note)
    p.fvlvl_changed_main_note.connect(note.fvchange_note)
    
    sys.exit(app.exec_())