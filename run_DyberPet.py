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
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QLocale

from qfluentwidgets import  FluentTranslator
from DyberPet.DyberSettings.DyberControlPanel import ControlMainWindow

try:
    size_factor = 1 #ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
except:
    size_factor = 1

import DyberPet.settings as settings

"""
#PetHP {{
    font-family: "Times";
    border: {int(2*size_factor)}px solid #535053;
    border-radius: {int(7*size_factor)}px;
}}
#PetHP::chunk {{
    background-color: #FAC486;
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

"""


StyleSheet = f"""
#PetTM {{
    font-family: "Segoe UI";
    border: 1px solid #08060f;
    border-radius: 7px;
}}
#PetTM::chunk {{
    background-color: #ef4e50;
    border-radius: 5px;
}}
#PetFC {{
    font-family: "Segoe UI";
    border: 1px solid #08060f;
    border-radius: 7px;
}}
#PetFC::chunk {{
    background-color: #47c0d2;
    border-radius: 5px;
}}
"""
# For translation:
# pylupdate5 langs.pro
# lrelease langs.zh_CN.ts

# For .exe:
# pyinstaller -F --noconsole --hidden-import="pynput.mouse._win32" --hidden-import="pynput.keyboard._win32" run_DyberPet.py

class DyberPetApp(QApplication):

    def __init__(self, *args, **kwargs):
        super(DyberPetApp, self).__init__(*args, **kwargs)
        
        # Connect the signal to a slot
        self.setStyleSheet(StyleSheet)

        self.setQuitOnLastWindowClosed(False)
        screens = self.screens()

        # internationalization
        fluentTranslator = FluentTranslator(QLocale(settings.language_code))
        self.installTranslator(fluentTranslator)
        self.installTranslator(settings.translator)
        

        # Pet Object
        self.p = PetWidget(screens=screens)

        # Notification System
        self.note = DPNote()

        # Accessory System
        self.acc = DPAccessory()

        # Control Panel
        self.conp = ControlMainWindow()

        # Signal Links
        self.__connectSignalToSlot()

    def __connectSignalToSlot(self):
        self.p.setup_notification.connect(self.note.setup_notification)
        self.p.change_note.connect(self.note.change_pet)
        self.p.change_note.connect(self.conp.charCardInterface._finishStateTooltip)
        self.p.hptier_changed_main_note.connect(self.note.hpchange_note)
        self.p.fvlvl_changed_main_note.connect(self.note.fvchange_note)
        self.p.setup_acc.connect(self.acc.setup_accessory)
        self.p.move_sig.connect(self.acc.send_main_movement)

        self.acc.acc_withdrawed.connect(self.p.acc_withdrawed)
        self.conp.settingInterface.ontop_changed.connect(self.acc.ontop_changed)
        self.conp.settingInterface.scale_changed.connect(self.acc.reset_size_sig)

        self.conp.settingInterface.ontop_changed.connect(self.p.ontop_update)
        self.conp.settingInterface.scale_changed.connect(self.p.set_img)
        self.conp.settingInterface.scale_changed.connect(self.p.reset_size)
        self.conp.settingInterface.lang_changed.connect(self.p.lang_changed)

        self.conp.charCardInterface.change_pet.connect(self.p._change_pet)
        #self.conp.gamesaveInterface.freeze_pet.connect(self.p.freeze_pet)
        self.p.show_controlPanel.connect(self.conp.show_window)

        self.conp.gamesaveInterface.refresh_pet.connect(self.p.refresh_pet)

        




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


    # Create App
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = DyberPetApp(sys.argv)

    sys.exit(app.exec_())


