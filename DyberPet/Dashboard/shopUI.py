# coding:utf-8
import os
import json
import random
import math

from qfluentwidgets import (InfoBar, ScrollArea, ExpandLayout, PushButton,
                            TransparentToolButton, SegmentedToggleToolWidget,
                            MessageBox, ComboBox, LineEdit)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale, QSize
from PySide6.QtGui import QDesktopServices, QIcon, QImage
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QHBoxLayout

from .dashboard_widgets import BPStackedWidget, coinWidget, ShopView, ShopItemWidget, filterView
from DyberPet.utils import get_MODs
from DyberPet.conf import ItemData
import DyberPet.settings as settings
import os
from sys import platform
basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/Dashboard/')



class shopInterface(ScrollArea):
    """ Shop interface """

    def __init__(self, sizeHintdb: tuple[int, int], parent=None):
        super().__init__(parent=parent)

        # Function Attributes ----------------------------------------------------------
        self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        self.tab_dict = {'consumable':0, 'collection':1, 'dialogue':1, 'subpet':2}
        #self.calculate_droprate()

        # UI Design --------------------------------------------------------------------
        self.setObjectName("shopInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # Header
        self.headerWidget = QWidget(self)
        self.headerWidget.setFixedWidth(sizeHintdb[0]-165)
        self.panelLabel = QLabel(self.tr("Shop"), self.headerWidget)
        self.panelLabel.setFixedWidth(100)
        self.panelHelp = TransparentToolButton(QIcon(os.path.join(basedir, 'res/icons/question.svg')), self.headerWidget)
        self.panelHelp.setFixedSize(25,25)
        self.panelHelp.setIconSize(QSize(25,25))
        self.coinWidget = coinWidget(self.headerWidget)
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(5)

        self.headerLayout.addWidget(self.panelLabel, Qt.AlignLeft | Qt.AlignVCenter)
        self.headerLayout.addStretch(0.1)
        self.headerLayout.addWidget(self.panelHelp, Qt.AlignLeft | Qt.AlignVCenter)
        self.headerLayout.addStretch(1)
        self.headerLayout.addWidget(self.coinWidget, Qt.AlignRight | Qt.AlignVCenter)

        # Filtering and Search Line
        self.header2Widget = QWidget(self)
        self.header2Widget.setFixedWidth(sizeHintdb[0]-165)
        self.filterButton = PushButton(text = self.tr("Filter"),
                                       parent = self.header2Widget,
                                       icon = QIcon(os.path.join(basedir, 'res/icons/Dashboard/expand.svg')))
        self.filterButton.setFixedWidth(100)
        self._init_filter()
        self.searchLineEdit = LineEdit(self)
        self._init_searchLine()
        
        self.header2Layout = QHBoxLayout(self.header2Widget)
        self.header2Layout.setContentsMargins(0, 0, 0, 0)
        self.header2Layout.setSpacing(5)
        self.header2Layout.addWidget(self.searchLineEdit, Qt.AlignRight | Qt.AlignVCenter)
        self.header2Layout.addStretch(1)
        self.header2Layout.addWidget(self.filterButton, Qt.AlignLeft | Qt.AlignVCenter)

        self.ShopView = ShopView(self.items_data.item_dict, sizeHintdb, self.scrollWidget)


        self.__initWidget()

    def _init_filter(self):
        '''
        self.filterView = QLabel('This is a test.', self)
        self.filterView.setFixedSize(80,80)
        self.filterView.setAlignment(Qt.AlignCenter)
        self.filterView.setStyleSheet("background-color: red")
        '''
        self.filterView = filterView(self)
        self.filterView.addFilter(title=self.tr('Type'),
                                    options=[self.tr('Food'),self.tr('Collection'),self.tr('Pet'),
                                             self.tr('Food'),self.tr('Collection'),self.tr('Collection')])
        mods = get_MODs(os.path.join(basedir,'res/items'))
        self.filterView.addFilter(title=self.tr('MOD'),
                                    options=mods)
        self.filterView.addFilter(title=self.tr('MOD2'),
                                    options=mods)
        
        self.filterView.hide()

    def _init_searchLine(self):
        content = self.tr('Search by name, MOD...')
        self.searchLineEdit.setPlaceholderText(content)
        self.searchLineEdit.setClearButtonEnabled(True)
        self.searchLineEdit.setFixedWidth(250)


    def __initWidget(self):
        #self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 130, 0, 20)
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
        self.header2Widget.move(60, 80)
        self.filterView.move(60, 130)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)

        self.expandLayout.addWidget(self.ShopView)


    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.panelLabel.setObjectName('panelLabel')

        theme = 'light' #if isDarkTheme() else 'light'
        with open(os.path.join(basedir, 'res/icons/Dashboard/qss/', theme, 'status_interface.qss'), encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        self.panelHelp.clicked.connect(self._showInstruction)
        self.filterButton.clicked.connect(self._toggleFilters)
        return

    
    def _toggleFilters(self):
        visible = not self.filterView.isVisible()
        self.filterView.setVisible(visible)

        if visible:
            self.filterButton.setIcon(os.path.join(basedir, 'res/icons/Dashboard/collapse.svg'))
            self.setViewportMargins(0, 130+self.filterView.height()+10, 0, 20)
        else:
            self.filterButton.setIcon(os.path.join(basedir, 'res/icons/Dashboard/expand.svg'))
            self.setViewportMargins(0, 130, 0, 20)

    def _showInstruction(self):
        title = self.tr("Backpack Guide")
        content = self.tr("""Backpack keeps all the items pet got.

There are in total 3 tabs and the coins display:
    - Consumable items (food, etc.)
    - Collections (Dialogue, etc.)
    - Subpet
(All tabs have infinite volume.)

Items have different effects, such as adding HP. Some of them also have Buff effects. Please position your cursor over the item to see details.""")
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

    def refresh_shop(self):

        # Update coin number
        self.coinWidget._updateCoin(settings.pet_data.coins)
        # update backpack tabs
        self.foodInterface._refreshBag()
        self.clctInterface._refreshBag()
        self.petsInterface._refreshBag()
        # disable the confirm button
        self._buttonUpdate(0, 0)

    def fvchange(self, fv_lvl):

        if fv_lvl in self.items_data.reward_dict:
            for item_i in self.items_data.reward_dict[fv_lvl]:
                if settings.petname in self.items_data.item_dict[item_i]['pet_limit'] \
                   or self.items_data.item_dict[item_i]['pet_limit']==[]:
                    self.add_item(item_i, 1)

        self.calculate_droprate()

