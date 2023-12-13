# coding:utf-8
import os
import json
import random
import math

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


class backpackInterface(ScrollArea):
    """ Backpack interface """

    confirmClicked = Signal(int, name='confirmClicked')
    use_item_inven = Signal(str, name='use_item_inven')
    item_note = Signal(str, str, name='item_note')
    item_drop = Signal(str, name='item_drop')
    acc_withdrawed = Signal(str, name='acc_withdrawed')
    addBuff = Signal(dict, name='addBuff')

    def __init__(self, sizeHintdb: tuple[int, int], parent=None):
        super().__init__(parent=parent)

        # Function Attributes ----------------------------------------------------------
        self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        self.tab_dict = {'consumable':0, 'collection':1, 'dialogue':1, 'subpet':2}
        self.calculate_droprate()

        # UI Design --------------------------------------------------------------------
        self.setObjectName("backpackInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # Header
        self.headerWidget = QWidget(self)
        self.headerWidget.setFixedWidth(sizeHintdb[0]-175)
        self.panelLabel = QLabel(self.tr("Backpack"), self.headerWidget)
        #self.panelLabel.adjustSize() #setFixedWidth(150)
        self.panelHelp = TransparentToolButton(QIcon(os.path.join(basedir, 'res/icons/question.svg')), self.headerWidget)
        self.panelHelp.setFixedSize(25,25)
        self.panelHelp.setIconSize(QSize(25,25))
        self.panelHelp.clicked.connect(self._showInstruction)
        self.coinWidget = coinWidget(self.headerWidget)
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(5)

        self.headerLayout.addWidget(self.panelLabel, Qt.AlignLeft | Qt.AlignVCenter)
        self.headerLayout.addStretch(0.1)
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
        self.confirmButton.setFixedWidth(120)
        self.header2Layout = QHBoxLayout(self.header2Widget)
        self.header2Layout.setContentsMargins(0, 0, 0, 0)
        self.header2Layout.setSpacing(5)

        self.header2Layout.addWidget(self.pivot, Qt.AlignLeft | Qt.AlignVCenter)
        self.header2Layout.addStretch(1)
        self.header2Layout.addWidget(self.confirmButton, Qt.AlignRight | Qt.AlignVCenter)


        # add items to pivot
        self.stackedWidget = BPStackedWidget(self.scrollWidget)

        self.foodInterface = itemTabWidget(self.items_data, ['consumable'], sizeHintdb, 0)
        self.clctInterface = itemTabWidget(self.items_data, ['collection','dialogue'], sizeHintdb, 1)
        self.petsInterface = itemTabWidget(self.items_data, ['subpet'], sizeHintdb, 2)

        self.addSubInterface(self.foodInterface, 'foodInterface', QIcon(os.path.join(basedir, 'res/icons/tab_1.svg')))
        self.addSubInterface(self.clctInterface, 'clctInterface', QIcon(os.path.join(basedir, 'res/icons/tab_2.svg')))
        self.addSubInterface(self.petsInterface, 'petsInterface', QIcon(os.path.join(basedir, 'res/icons/tab_pet.svg')))

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
            self._buttonUpdate(0, 0)
            #self.confirmButton.setDisabled(True)
        else:
            if widget.cells_dict[widget.selected_cell].item_inuse:
                self._buttonUpdate(1, 1)
            else:
                self._buttonUpdate(0, 1)
            #self._buttonUpdate(0, 1)
            #self.confirmButton.setDisabled(False)


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
        self.foodInterface.use_item_inven.connect(self._use_item_inven)
        self.foodInterface.item_note.connect(self._item_note)
        self.foodInterface.item_drop.connect(self.item_drop)
        self.foodInterface.size_changed.connect(self.stackedWidget.subWidget_sizeChange)
        self.foodInterface.addBuff.connect(self._addBuff)

        self.confirmClicked.connect(self.clctInterface._confirmClicked)
        self.acc_withdrawed.connect(self.clctInterface.acc_withdrawed)
        self.clctInterface.set_confirm.connect(self._buttonUpdate)
        self.clctInterface.use_item_inven.connect(self._use_item_inven)
        self.clctInterface.item_note.connect(self._item_note)
        self.clctInterface.item_drop.connect(self.item_drop)
        self.clctInterface.size_changed.connect(self.stackedWidget.subWidget_sizeChange)
        self.clctInterface.addBuff.connect(self._addBuff)

        self.confirmClicked.connect(self.petsInterface._confirmClicked)
        self.acc_withdrawed.connect(self.petsInterface.acc_withdrawed)
        self.petsInterface.set_confirm.connect(self._buttonUpdate)
        self.petsInterface.use_item_inven.connect(self._use_item_inven)
        self.petsInterface.item_note.connect(self._item_note)
        self.petsInterface.item_drop.connect(self.item_drop)
        self.petsInterface.size_changed.connect(self.stackedWidget.subWidget_sizeChange)
        self.petsInterface.addBuff.connect(self._addBuff)
        

    def _showInstruction(self):
        
        return

    def refresh_bag(self):
        # drop rate
        self.calculate_droprate()
        # Update coin number
        self.coinWidget._updateCoin(settings.pet_data.coins)
        # update backpack tabs
        self.foodInterface._refreshBag()
        self.clctInterface._refreshBag()
        self.petsInterface._refreshBag()
        # disable the confirm button
        self._buttonUpdate(0, 0)

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
    
    def _use_item_inven(self, item_name):
        self.use_item_inven.emit(item_name)
    
    def _item_note(self, item_name, mssg):
        self.item_note.emit(item_name, mssg)

    def _addBuff(self, item_name):
        self.addBuff.emit(self.items_data.item_dict[item_name])
    
    def addCoins(self, value, note=True):

        # If random drop triggered by patpat
        if value == 0:
            # Gaussian distribution random sample
            value = int(random.gauss(settings.COIN_MU, settings.COIN_SIGMA))
            if value <= 0:
                return

        # update pet data
        settings.pet_data.change_coin(value)

        ##########################################
        # TODO: prevent negative amount of conins
        ##########################################

        # update Backpack UI
        self.coinWidget._updateCoin(settings.pet_data.coins)
        # trigger drop animation
        if value > 0:
            self._send_coin_anim(value)
        # trigger notification
        if value > 0:
            diff = '+%s'%value
        elif value < 0:
            diff = str(diff)
        
        if note:
            self.item_note.emit('status_coin', f"[{self.tr('Dyber Coin')}] {diff}")

    def _send_coin_anim(self, value):
        n = math.ceil(value//5)
        for _ in range(n):
            self.item_drop.emit('coin')

    def add_items(self, n_items, item_names=[]):
        # No item to drop, return
        if sum(self.all_probs) <= 0:
            return

        # 随机物品
        item_names_pendding = []
        for i in range(n_items):
            item = random.choices(self.all_items, weights=self.all_probs, k=1)[0]
            if self.items_data.item_dict[item]['item_type'] == 'collection':
                self.add_item(item, 1)
                self.calculate_droprate()
            else:
                item_names_pendding.append(item)

        #print(n_items, item_names)
        # 物品添加列表
        items_toadd = {}
        for i in range(len(item_names_pendding)):
            item_name = item_names_pendding[int(i%len(item_names_pendding))]
            if item_name in items_toadd.keys():
                items_toadd[item_name] += 1
            else:
                items_toadd[item_name] = 1

        # 依次添加物品
        for item in items_toadd.keys():
            #while self.items_data.item_dict[item]['item_type'] == 'collection' and 
            self.add_item(item, items_toadd[item])


    def add_item(self, item_name, n_items):
        
        item_type = self.items_data.item_dict[item_name]['item_type']
        tab_index = self.tab_dict[item_type]
        widget = self.stackedWidget.widget(tab_index)
        widget.add_item(item_name, n_items)

    
    def fvchange(self, fv_lvl):

        if fv_lvl in self.items_data.reward_dict:
            for item_i in self.items_data.reward_dict[fv_lvl]:
                if settings.petname in self.items_data.item_dict[item_i]['pet_limit'] \
                   or self.items_data.item_dict[item_i]['pet_limit']==[]:
                    self.add_item(item_i, 1)

        self.calculate_droprate()

    def calculate_droprate(self):

        all_items = []
        all_probs = []
        #确定物品掉落概率
        for item in self.items_data.item_dict.keys():
            all_items.append(item)
            #排除已经获得的收藏品
            if self.items_data.item_dict[item]['item_type'] != 'consumable' and settings.pet_data.items.get(item, 0)>0:
                all_probs.append(0)
            else:
                all_probs.append((self.items_data.item_dict[item]['drop_rate'])*int(self.items_data.item_dict[item]['fv_lock']<=settings.pet_data.fv_lvl))
        
        if sum(all_probs) != 0:
            all_probs = [i/sum(all_probs) for i in all_probs]

        self.all_items = all_items
        self.all_probs = all_probs

    def compensate_rewards(self):
        for fv_lvl in range(settings.pet_data.fv_lvl+1):
            for item_i in self.items_data.reward_dict.get(fv_lvl, []):

                if self.items_data.item_dict[item_i]['item_type'] != 'consumable'\
                   and settings.pet_data.items.get(item_i, 0)<=0:

                   if settings.petname in self.items_data.item_dict[item_i]['pet_limit'] \
                      or self.items_data.item_dict[item_i]['pet_limit']==[]:
                      
                        self.add_item(item_i, 1)

        self.calculate_droprate()

