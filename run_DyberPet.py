import sys
import ctypes
from tendo import singleton

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
    border: {int(2*size_factor)}px solid #535053;
    border-radius: {int(7*size_factor)}px;
}}
#PetHP::chunk {{
    background-color: #FAC486;
    border-radius: {int(5*size_factor)}px;
}}

#PetTM {{
    border: {int(2*size_factor)}px solid #535053;
    border-radius: {int(7*size_factor)}px;
}}
#PetTM::chunk {{
    background-color: #ef4e50;
    border-radius: {int(5*size_factor)}px;
}}

#PetEM {{
    border: {int(2*size_factor)}px solid #535053;
    border-radius: {int(7*size_factor)}px;
}}
#PetEM::chunk {{
    background-color: #F69290;
    border-radius: {int(5*size_factor)}px;
}}

#PetFC {{
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

if __name__ == '__main__':

    # Avoid multiple process
    try:
        me = singleton.SingleInstance()
    except:
        sys.exit()

    # Load pet list
    pets = read_json('data/pets.json')

    # Create App
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)

    # Pet Object
    p = PetWidget(pets=pets)
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
    
    sys.exit(app.exec_())