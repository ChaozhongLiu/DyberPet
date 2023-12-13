# coding:utf-8
import os
import json
import random

from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, HyperlinkCard, InfoBar,
                            ComboBoxSettingCard, ScrollArea, ExpandLayout, InfoBarPosition,
                            PushButton)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale
from PySide6.QtGui import QDesktopServices, QIcon, QImage
from PySide6.QtWidgets import QWidget, QLabel, QApplication

from .dashboard_widgets import NoteFlowGroup, StatusCard, BuffCard
from .buffModule import BuffThread

import DyberPet.settings as settings
import os
from sys import platform
basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/Dashboard/')
'''
if platform == 'win32':
    basedir = ''
    module_path = 'DyberPet/Dashboard/'
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-2])

    module_path = os.path.join(basedir, 'DyberPet/Dashboard/')
'''


class statusInterface(ScrollArea):
    """ Character status and logs interface """
    addBuff2Thread = Signal(dict, name='addBuff2Thread')
    changeStatus = Signal(str, int, name='changeStatus')
    addCoins = Signal(int, bool,name='addCoins')

    def __init__(self, sizeHintdb: tuple[int, int], parent=None):
        super().__init__(parent=parent)
        self.setObjectName("statusInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.buffThread = None

        # setting label
        self.panelLabel = QLabel(self.tr("Status"), self)
        self.StatusCard = StatusCard(self)
        self.BuffCard = BuffCard(self)
        self.noteStream = NoteFlowGroup(self.tr('Status Log'), sizeHintdb, self.scrollWidget)

        self.__initWidget()

    def __initWidget(self):
        #self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 270, 0, 20)
        self.setWidget(self.scrollWidget)
        #self.scrollWidget.resize(1000, 800)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.panelLabel.move(50, 20)
        self.StatusCard.move(50, 75)
        self.BuffCard.move(50, 205)

        # add cards to group
        #self.ModeGroup.addSettingCard(self.noteStream)
        #self.ModeGroup.addSettingCard(self.AllowDropCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)

        self.expandLayout.addWidget(self.noteStream)


    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.panelLabel.setObjectName('panelLabel')

        theme = 'light' #if isDarkTheme() else 'light'
        with open(os.path.join(basedir, 'res/icons/Dashboard/qss/', theme, 'status_interface.qss'), encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        
        return

    def _addNote(self, icon, content):
        '''
        pfpPath = os.path.join(basedir, 'res/icons/unknown.svg')
        icon = QImage()
        icon.load(pfpPath)
        content = "这是一个测试 This is a test " * random.randint(1,10)
        '''
        self.noteStream.addNote(icon, content)

    def _addBuff(self, item_config):
        if not self.buffThread:
            self.startBuffThread()

        self.addBuff2Thread.emit(item_config)
    
    def startBuffThread(self):
        self.buffThread = BuffThread()
        self.buffThread.start()
        self.buffThread.setTerminationEnabled()

        self.buffThread.addBuffUI.connect(self._addBuffUI)
        self.buffThread.takeEffect.connect(self._takeEffect)
        self.buffThread.removeBuffUI.connect(self._removeBuffUI)
        self.addBuff2Thread.connect(self.buffThread._addBuff_fromItem)

    def stopBuffThread(self):
        if self.buffThread:
            self.buffThread.terminate()
            self.buffThread.wait()
    
    def _addBuffUI(self, itemName, item_conf, idx):
        self.BuffCard.addBuff(itemName, item_conf, idx)

    def _takeEffect(self, effect, value):
        if effect == 'hp' or effect == 'fv':
            self.changeStatus.emit(effect, value, 'Buff')
        elif effect == 'coin':
            self.addCoins.emit(value, False)

    def _removeBuffUI(self, itemName, idx):
        self.BuffCard.removeBuff(itemName, idx)
