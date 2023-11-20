# coding:utf-8
import os
import json
import random

from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, HyperlinkCard, InfoBar,
                            ComboBoxSettingCard, ScrollArea, ExpandLayout, InfoBarPosition,
                            PushButton, TransparentToolButton, SegmentedToggleToolWidget)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale, QSize
from PySide6.QtGui import QDesktopServices, QIcon, QImage
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QHBoxLayout

from .dashboard_widgets import BPStackedWidget, coinWidget, itemTabWidget

from DyberPet.conf import ItemData
import DyberPet.settings as settings
import os
from sys import platform
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



class backpackInterface(ScrollArea):
    """ Backpack interface """

    confirmClicked = Signal(int, name='confirmClicked')

    def __init__(self, sizeHintdb: tuple[int, int], parent=None):
        super().__init__(parent=parent)

        # Function Attributes ----------------------------------------------------------
        ##################
        # Load item data
        ##################
        self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        self.selected_cell = None
        #self.inven_shape = (5,3)
        self.items_numb = {}
        self.cells_dict = {}
        self.empty_cell = {}
        self.tab_dict = {'consumable':0, 'collection':1, 'dialogue':1}


        # UI Design --------------------------------------------------------------------
        self.setObjectName("backpackInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # Header
        self.headerWidget = QWidget(self)
        self.headerWidget.setFixedWidth(sizeHintdb[0]-175)
        self.panelLabel = QLabel(self.tr("Backpack"), self.headerWidget)
        self.panelLabel.setFixedWidth(150)
        self.panelHelp = TransparentToolButton(QIcon(os.path.join(basedir, 'res/icons/question.svg')), self.headerWidget)
        self.panelHelp.setFixedSize(25,25)
        self.panelHelp.setIconSize(QSize(25,25))
        self.panelHelp.clicked.connect(self._showInstruction)
        self.coinWidget = coinWidget(self.headerWidget)
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(5)

        self.headerLayout.addWidget(self.panelLabel, Qt.AlignLeft | Qt.AlignVCenter)
        self.headerLayout.addWidget(self.panelHelp, Qt.AlignLeft | Qt.AlignVCenter)
        self.headerLayout.addStretch(1)
        self.headerLayout.addWidget(self.coinWidget, Qt.AlignRight | Qt.AlignVCenter)

        # Navigation and Button Line
        self.header2Widget = QWidget(self)
        self.header2Widget.setFixedWidth(sizeHintdb[0]-175)
        self.pivot = SegmentedToggleToolWidget(self)
        self.confirmButton = PushButton(text = self.tr("Use"),
                                        parent = self.header2Widget,
                                        icon = QIcon(os.path.join(basedir, 'res/icons/Dashboard/confirm.svg')))
        self.confirmButton.setDisabled(True)
        self.confirmButton.setFixedWidth(100)
        self.header2Layout = QHBoxLayout(self.header2Widget)
        self.header2Layout.setContentsMargins(0, 0, 0, 0)
        self.header2Layout.setSpacing(5)

        self.header2Layout.addWidget(self.pivot, Qt.AlignLeft | Qt.AlignVCenter)
        self.header2Layout.addStretch(1)
        self.header2Layout.addWidget(self.confirmButton, Qt.AlignRight | Qt.AlignVCenter)


        # add items to pivot
        self.stackedWidget = BPStackedWidget(self.scrollWidget)

        self.foodInterface = itemTabWidget(self.items_data, ['consumable'], sizeHintdb, 0)
        self.clctInterface = itemTabWidget(self.items_data, ['collection'], sizeHintdb, 1)
        self.artistInterface = QLabel('Artist Interface', self)

        self.addSubInterface(self.foodInterface, 'songInterface', QIcon(os.path.join(basedir, 'res/icons/tab_1.svg')))
        self.addSubInterface(self.clctInterface, 'albumInterface', QIcon(os.path.join(basedir, 'res/icons/tab_2.svg')))
        self.addSubInterface(self.artistInterface, 'artistInterface', QIcon(os.path.join(basedir, 'res/icons/tab_pet.svg')))

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.foodInterface)
        self.pivot.setCurrentItem(self.foodInterface.objectName())



        #self.noteStream = NoteFlowGroup(self.tr('Status Log'), sizeHintdb, self.scrollWidget)

        self.__initWidget()


    def addSubInterface(self, widget: QLabel, objectName, icon):
        widget.setObjectName(objectName)
        #widget.setAlignment(Qt.AlignCenter)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
            icon=icon
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        if widget.selected_cell is None:
            self.confirmButton.setDisabled(True)
        else:
            self.confirmButton.setDisabled(False)


    def __initWidget(self):
        #self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 125, 0, 20)
        self.setWidget(self.scrollWidget)
        #self.scrollWidget.resize(1000, 800)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.headerWidget.move(50, 20)
        self.header2Widget.move(50, 80)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)

        self.expandLayout.addWidget(self.stackedWidget)


    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.panelLabel.setObjectName('panelLabel')

        theme = 'light' #if isDarkTheme() else 'light'
        with open(os.path.join(basedir, 'res/icons/Dashboard/qss/', theme, 'status_interface.qss'), encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        self.confirmButton.clicked.connect(self._confirmClicked)

        self.confirmClicked.connect(self.foodInterface._confirmClicked)
        self.foodInterface.set_confirm.connect(self._buttonUpdate)

        self.confirmClicked.connect(self.clctInterface._confirmClicked)
        self.clctInterface.set_confirm.connect(self._buttonUpdate)

    def _showInstruction(self):
        
        return

    def _confirmClicked(self):
        index = self.stackedWidget.currentIndex()
        self.confirmClicked.emit(index)


    def _buttonUpdate(self, text_index, state):
        textDic = {0: self.tr('Use'), 1: self.tr('Withdraw')}
        self.confirmButton.setText(textDic[text_index])
        if state:
            self.confirmButton.setDisabled(False)
        else:
            self.confirmButton.setDisabled(True)

