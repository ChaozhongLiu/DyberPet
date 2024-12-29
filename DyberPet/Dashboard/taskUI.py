# coding:utf-8
import os
import json
import random

from qfluentwidgets import (InfoBar,ScrollArea, ExpandLayout,
                            InfoBarPosition, TransparentToolButton, MessageBox)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale, QSize
from PySide6.QtGui import QDesktopServices, QIcon, QImage
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QSpacerItem, QSizePolicy, QHBoxLayout

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
        self.headerWidget = QWidget(self)
        self.headerWidget.setFixedWidth(sizeHintdb[0]-165)
        self.panelLabel = QLabel(self.tr("Daily Tasks"), self.headerWidget)
        self.panelLabel.setSizePolicy(QSizePolicy.Maximum, self.panelLabel.sizePolicy().verticalPolicy())
        self.panelLabel.adjustSize()
        #self.panelLabel.setFixedWidth(100)
        self.panelHelp = TransparentToolButton(QIcon(os.path.join(basedir, 'res/icons/question.svg')), self.headerWidget)
        self.panelHelp.setFixedSize(25,25)
        self.panelHelp.setIconSize(QSize(25,25))
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(0)

        self.headerLayout.addWidget(self.panelLabel, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem1 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.headerLayout.addItem(spacerItem1)
        self.headerLayout.addWidget(self.panelHelp, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem2 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.headerLayout.addItem(spacerItem2)
        #self.panelLabel = QLabel(self.tr("Daily Tasks"), self)

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
        self.headerWidget.move(60, 20)

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
        self.focusPanel.addProgress.connect(self.progressPanel.updateProgress)
        self.panelHelp.clicked.connect(self._showInstruction)
    
    def _changePet(self):
        self.changePet.emit()
        settings.HP_stop = False
        settings.FV_stop = False
        self.stopBuffThread()

    def _showInstruction(self):
        title = self.tr("Daily Task Guide")
        content = self.tr("""Daily Task Panel is the place you finish task to get Coin reward.

From top to bottom, there are 3 widgets:
⏺ Focus Session
    - Focus on your work/study for a certain amount of time to get rewards.
    - You can either set a period or use Pomodoro.

⏺ Daily Goal
    - It records your daily progress towards goal.
    - You can set your own goal from the top right corner.
    - The longer your goal is, the more coins you got when you reach the daily goal.
    - Complete numbers of days in a row will get you extra coins reward.

⏺ To-do Tasks
    - Write done any to-dos you have.
    - Once finished, you will get coin reward.
    - Completing every 5 tasks will give you extra reward.""")
        self.__showMessageBox(title, content)
        return     

    def __showMessageBox(self, title, content, yesText='OK'):

        WarrningMessage = MessageBox(title, content, self)
        if yesText == 'OK':
            WarrningMessage.yesButton.setText(self.tr('OK'))
        else:
            WarrningMessage.yesButton.setText(yesText)
        WarrningMessage.cancelButton.setText(self.tr('Cancel'))
        if WarrningMessage.exec():
            return True
        else:
            #print('Cancel button is pressed')
            return False
