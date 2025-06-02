# coding:utf-8
import sys
import os
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget,  SplitFluentWindow, FluentTranslator)
from qfluentwidgets import FluentIcon as FIF

from .BasicSettingUI import SettingInterface
from .GameSaveUI import SaveInterface
from .CharCardUI import CharInterface
from .ItemCardUI import ItemInterface
from .PetCardUI import PetInterface
from .AISettingUI import AISettingInterface
from sys import platform
import DyberPet.settings as settings
basedir = settings.BASEDIR

module_path = os.path.join(basedir, 'DyberPet/DyberSettings/')


class ControlMainWindow(FluentWindow):

    def __init__(self, minWidth=800, minHeight=800):
        super().__init__()

        # create sub interface
        self.settingInterface = SettingInterface(self)
        self.gamesaveInterface = SaveInterface(sizeHintDyber=(minWidth, minHeight), parent=self)
        self.charCardInterface = CharInterface(sizeHintDyber=(minWidth, minHeight), parent=self)
        self.itemCardInterface = ItemInterface(sizeHintDyber=(minWidth, minHeight), parent=self)
        self.petCardInterface = PetInterface(sizeHintDyber=(minWidth, minHeight), parent=self)
        self.aiSettingInterface = AISettingInterface(self)
        self.aiSettingInterface.menu_update_needed.connect(self.update_pet_menu)

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
                             QIcon(os.path.join(basedir, "res/icons/system/character.svg")),
                             self.tr('Characters'))
        self.addSubInterface(self.itemCardInterface,
                             QIcon(os.path.join(basedir, "res/icons/system/itemMod.svg")),
                             self.tr('Item MOD'))
        self.addSubInterface(self.petCardInterface,
                             QIcon(os.path.join(basedir, "res/icons/system/minipet.svg")),
                             self.tr('Mini-Pets'))
        self.addSubInterface(self.aiSettingInterface,
                             FIF.ROBOT,
                             self.tr('AI Chat'))

        self.navigationInterface.setExpandWidth(200)

    def initWindow(self):
        #self.setMinimumSize(minWidth, minHeight)
        #self.resize(1000, 800)
        self.setWindowIcon(QIcon(os.path.join(basedir, "res/icons/SystemPanel.png")))
        self.setWindowTitle(self.tr('System'))

        desktop = QApplication.primaryScreen().availableGeometry() #QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def show_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def closeEvent(self, event):
        event.ignore()  # Ignore the close event
        self.hide()

    #def _onCharChange(self, char):
    #    self.hide()

    def update_pet_menu(self):
        """通知主窗口更新菜单"""
        # 发送信号到主窗口
        self.update_menu_signal.emit()

    update_menu_signal = Signal(name='update_menu_signal')


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



















