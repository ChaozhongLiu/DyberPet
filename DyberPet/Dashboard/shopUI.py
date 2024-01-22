# coding:utf-8
import os
import json
import random
import math
from collections import defaultdict

from qfluentwidgets import (InfoBar, ScrollArea, ExpandLayout, PushButton,
                            TransparentToolButton, SegmentedToggleToolWidget,
                            MessageBox, ComboBox, SearchLineEdit, InfoBar, InfoBarPosition)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale, QSize
from PySide6.QtGui import QDesktopServices, QIcon, QImage
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QHBoxLayout

from .dashboard_widgets import BPStackedWidget, coinWidget, ShopView, ShopItemWidget, filterView, ShopMessageBox
from DyberPet.utils import get_MODs
from DyberPet.conf import ItemData
import DyberPet.settings as settings
import os
from sys import platform
basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/Dashboard/')



class shopInterface(ScrollArea):
    """ Shop interface """
    buyItem = Signal(str, int, name='buyItem')
    sellItem = Signal(str, int, name='sellItem')
    updateCoin = Signal(int, bool, bool,name='updateCoin')

    def __init__(self, sizeHintdb: tuple[int, int], parent=None):
        super().__init__(parent=parent)

        # Function Attributes ----------------------------------------------------------
        self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        self.tab_dict = {'consumable':0, 'collection':1, 'dialogue':1, 'subpet':2}
        self.selectedTags = defaultdict(list)
        self.searchText = ''
        self.NumItemInDeal = 0

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
        self.searchLineEdit = SearchLineEdit(self)
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
                                    options=[self.tr('Food'),self.tr('Collection'),self.tr('Pet')])
        mods = get_MODs(os.path.join(basedir,'res/items'))
        self.filterView.addFilter(title=self.tr('MOD'),
                                    options=mods)
        
        self.filterView.hide()
        self.filterView.filterChanged.connect(self._updateList_filter)

    def _init_searchLine(self):
        content = self.tr('Search by name, MOD...')
        self.searchLineEdit.setPlaceholderText(content)
        self.searchLineEdit.setClearButtonEnabled(True)
        self.searchLineEdit.setFixedWidth(250)
        #self.searchLineEdit.textChanged.connect(self.searchLineEdit.search)
        self.searchLineEdit.clearSignal.connect(self._updateList_All)
        self.searchLineEdit.searchSignal.connect(self._updateList_search)


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
        self.filterView.move(60, 125)

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
        self.ShopView.sellItem.connect(self._sellItem)
        self.ShopView.buyItem.connect(self._buyItem)
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


    def _updateList_filter(self):
        # check all tags
        selectedTags = self.filterView._getSelectedTags()
        self.selectedTags = selectedTags
        self.ShopView._updateList(self.selectedTags, self.searchText)

    def _updateList_search(self, searchText=''):
        # get text
        if self.searchText == searchText:
            return
        self.searchText = searchText
        self.ShopView._updateList(self.selectedTags, self.searchText)

    def _updateList_All(self):
        if self.searchText == '':
            return
        self.searchText = ''
        self.ShopView._updateList(self.selectedTags, self.searchText)



    def _showInstruction(self):
        title = self.tr("Shop Guide")
        content = self.tr("""Not Implemented""")
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

    def __showSystemNote(self, content, type_code):
        """ show restart tooltip """
        notMethods = [InfoBar.success, InfoBar.warning, InfoBar.error]
        notMethods[type_code](
            '',
            content,
            duration=3000,
            position=InfoBarPosition.BOTTOM,
            parent=self.window()
        )

    def _updateItemNum(self, item_name):
        self.ShopView._updateItemNum(item_name)

    def refresh_shop(self):

        # Updating coin number in Inventory automatically linked to shop coin number
        # update items UI
        self.ShopView._updateAllItemUI()

    def fvchange(self, fv_lvl):
        self.ShopView._fvchange(fv_lvl)

    def _sellItem(self, item_name):
        item_conf = self.items_data.item_dict[item_name]

        # Check how many the char owns
        if settings.pet_data.items.get(item_name, 0) <= 0:
            return

        # Calculate the max Number of items to sell
        cost = int(item_conf['cost'] * settings.ITEM_DEPRECIATION)
        maxNum = settings.pet_data.items.get(item_name, 0)

        # Pop-up dialogue to choose number of items to buy
        w = ShopMessageBox(option='sell', item_name=item_name, maxNum=maxNum, cost=cost, parent=self)
        w.bill.connect(self._getNum)
        if w.exec():
            pass
        else:
            return

        if self.NumItemInDeal > 0:
            # Add items to bag
            self.sellItem.emit(item_name, -self.NumItemInDeal)

            # Deduct the coins
            self.updateCoin.emit(cost * self.NumItemInDeal, True, False)

        self.NumItemInDeal = 0

    def _buyItem(self, item_name):
        item_conf = self.items_data.item_dict[item_name]

        # Except food, only one item is allowed for other type of items
        if item_conf['item_type'] != 'consumable' and settings.pet_data.items.get(item_name, 0) > 0:
            content = self.tr('One Char can have only one ') + f"[{item_name}]"
            self.__showSystemNote(content, 1)
            return

        # Calculate the max Number of items to buy
        cost = item_conf['cost']
        maxNum = settings.pet_data.coins // cost

        # Pop-up dialogue to choose number of items to buy
        w = ShopMessageBox(option='buy', item_name=item_name, maxNum=maxNum, cost=cost, parent=self)
        w.bill.connect(self._getNum)
        if w.exec():
            pass
        else:
            return

        if self.NumItemInDeal > 0:
            # Add items to bag
            self.buyItem.emit(item_name, self.NumItemInDeal)

            # Deduct the coins
            self.updateCoin.emit(-cost * self.NumItemInDeal, True, False)

        self.NumItemInDeal = 0

    def _getNum(self, num):
        self.NumItemInDeal = num





