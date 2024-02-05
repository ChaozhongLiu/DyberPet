# coding:utf-8
import os
import json
import random

from qfluentwidgets import (InfoBar,ScrollArea, ExpandLayout,
                            InfoBarPosition)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale
from PySide6.QtGui import QDesktopServices, QIcon, QImage
from PySide6.QtWidgets import QWidget, QLabel, QApplication

from .dashboard_widgets import FocusPanel, ProgressPanel, TaskPanel

import DyberPet.settings as settings
import os
from sys import platform
basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/Dashboard/')



class taskInterface(ScrollArea):
    """ Character animations management interface """

    def __init__(self, sizeHintdb: tuple[int, int], parent=None):
        super().__init__(parent=parent)
        self.setObjectName("taskInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.panelLabel = QLabel(self.tr("Daily Tasks"), self)
        self.focusPanel = FocusPanel(sizeHintdb, self.scrollWidget)
        self.progressPanel = ProgressPanel(sizeHintdb, self.scrollWidget)
        self.taskPanel = TaskPanel(sizeHintdb, self.scrollWidget)

        self.__initWidget()

    def __initWidget(self):
        #self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 75, 0, 20)
        self.setWidget(self.scrollWidget)
        #self.scrollWidget.resize(1000, 800)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.panelLabel.move(60, 20)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(70, 10, 70, 0)

        self.expandLayout.addWidget(self.focusPanel)
        self.expandLayout.addWidget(self.progressPanel)
        self.expandLayout.addWidget(self.taskPanel)


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
    
    def _changePet(self):
        self.changePet.emit()
        settings.HP_stop = False
        settings.FV_stop = False
        self.stopBuffThread()
