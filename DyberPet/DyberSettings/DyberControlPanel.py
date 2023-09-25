# coding:utf-8
import sys
import os
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget,  SplitFluentWindow, FluentTranslator)
from qfluentwidgets import FluentIcon as FIF

from .BasicSettingUI import SettingInterface
from .GameSaveUI import SaveInterface
from .CharCardUI import CharInterface

from sys import platform
if platform == 'win32':
    basedir = ''
    module_path = 'DyberPet/DyberSettings/'
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-2])

    module_path = os.path.join(basedir, 'DyberPet/DyberSettings/')

class ControlMainWindow(FluentWindow):

    def __init__(self, minWidth=800, minHeight=800):
        super().__init__()

        # create sub interface
        self.settingInterface = SettingInterface(self)
        self.gamesaveInterface = SaveInterface(sizeHintDyber=(minWidth, minHeight), parent=self)
        self.charCardInterface = CharInterface(sizeHintDyber=(minWidth, minHeight), parent=self)
        #self.charCardInterface.change_pet.connect(self._onCharChange)

        self.initNavigation()
        self.setMinimumSize(minWidth, minHeight)
        self.initWindow()

    def initNavigation(self):
        # add sub interface
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Settings'))
        self.addSubInterface(self.gamesaveInterface,
                             FIF.SAVE, #QIcon(os.path.join(module_path, 'resource/saveIcon.svg')), 
                             self.tr('Game Save'))
        self.addSubInterface(self.charCardInterface,
                             FIF.ROBOT,
                             self.tr('Characters'))

        self.navigationInterface.setExpandWidth(200)

    def initWindow(self):
        #self.setMinimumSize(minWidth, minHeight)
        #self.resize(1000, 800)
        self.setWindowIcon(QIcon(os.path.join(basedir, "res/icons/SystemPanel.png")))
        self.setWindowTitle(self.tr('System'))

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def show_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    #def _onCharChange(self, char):
    #    self.hide()


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # setTheme(Theme.DARK)

    app = QApplication(sys.argv)

    # install translator
    translator = FluentTranslator()
    app.installTranslator(translator)

    w = ControlMainWindow()
    w.show()
    app.exec_()



















