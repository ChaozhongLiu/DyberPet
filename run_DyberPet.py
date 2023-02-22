import sys
from sys import platform
import ctypes
from tendo import singleton
import os
from DyberPet.utils import read_json
from DyberPet.DyberPet import PetWidget
from DyberPet.Notification import DPNote
from DyberPet.Accessory import DPAccessory

from PyQt5.QtWidgets import QApplication

try:
    size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
except:
    size_factor = 1

StyleSheet = f"""
#PetHP {{
    font-family: "Times";
    border: {int(2*size_factor)}px solid #535053;
    border-radius: {int(7*size_factor)}px;
}}
#PetHP::chunk {{
    background-color: #FAC486;
    border-radius: {int(5*size_factor)}px;
}}

#PetTM {{
    font-family: "Times";
    border: {int(2*size_factor)}px solid #535053;
    border-radius: {int(7*size_factor)}px;
}}
#PetTM::chunk {{
    background-color: #ef4e50;
    border-radius: {int(5*size_factor)}px;
}}

#PetEM {{
    font-family: "Times";
    border: {int(2*size_factor)}px solid #535053;
    border-radius: {int(7*size_factor)}px;
}}
#PetEM::chunk {{
    background-color: #F69290;
    border-radius: {int(5*size_factor)}px;
}}

#PetFC {{
    font-family: "Times";
    border: {int(2*size_factor)}px solid #535053;
    border-radius: {int(7*size_factor)}px;
}}
#PetFC::chunk {{
    background-color: #47c0d2;
    border-radius: {int(5*size_factor)}px;
}}
"""

# For .exe:
# pyinstaller -F --noconsole --hidden-import="pynput.mouse._win32" --hidden-import="pynput.keyboard._win32" run_DyberPet.py

if platform == 'win32':
    basedir = ''
else:
    basedir = os.path.dirname(__file__)

if __name__ == '__main__':

    # Avoid multiple process
    try:
        me = singleton.SingleInstance()
    except:
        sys.exit()

    # Load pet list
    pets = read_json(os.path.join(basedir, 'res/role/pets.json'))

    # Create App
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    screens = app.screens()

    # Pet Object
    p = PetWidget(pets=pets, screens=screens)
    # Notification System
    note = DPNote()
    # Accessory System
    acc = DPAccessory()

    # Signal Links
    p.setup_notification.connect(note.setup_notification)
    p.change_note.connect(note.change_pet)
    p.hptier_changed_main_note.connect(note.hpchange_note)
    p.fvlvl_changed_main_note.connect(note.fvchange_note)
    p.setup_acc.connect(acc.setup_accessory)
    p.move_sig.connect(acc.send_main_movement)
    p.setting_window.ontop_changed.connect(acc.ontop_changed)
    p.setting_window.scale_changed.connect(acc.reset_size_sig)

    acc.acc_withdrawed.connect(p.acc_withdrawed)
    
    sys.exit(app.exec_())