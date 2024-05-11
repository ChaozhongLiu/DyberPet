# coding:utf-8
import os
import sys
import math
import json
import glob
import uuid
import datetime
from collections import defaultdict
from typing import Union, List

from PySide6 import QtGui
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QObject, QEvent, QModelIndex, QRectF, QRect, QTime
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QProgressBar, QFrame, QStyleOptionViewItem,
                             QSizePolicy, QStackedWidget, QLayout, QSpacerItem)
from PySide6.QtGui import (QPixmap, QImage, QImageReader, QPainter, QBrush, QPen, QColor, QIcon,
                        QFont, QPainterPath, QCursor, QAction, QFontMetrics, QPalette)

from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCard, Slider, FluentIconBase, SimpleCardWidget, PushButton
from qfluentwidgets import (SegmentedToolWidget, TransparentToolButton, PillPushButton,
                            InfoBar, InfoBarPosition, InfoBarIcon, 
                            RoundMenu, FluentIcon, Action, AvatarWidget, BodyLabel, ToolButton,
                            HyperlinkButton, CaptionLabel, setFont, setTheme, Theme, isDarkTheme,
                            FluentStyleSheet, FlowLayout, IconWidget, getFont,
                            TransparentDropDownToolButton, DropDownPushButton,
                            ScrollArea, PrimaryPushButton, LineEdit,
                            FlipImageDelegate, HorizontalPipsPager, HorizontalFlipView,
                            TextWrap, InfoBadge, PushButton, ScrollArea, ImageLabel, ToolTipFilter,
                            MessageBoxBase, SpinBox, SubtitleLabel, CardWidget, TimePicker,
                            StrongBodyLabel, CheckBox, InfoBarIcon, LargeTitleLabel, ProgressRing, 
                            Flyout, FlyoutViewBase, FlyoutAnimationType, TitleLabel, ComboBox, ProgressBar)

import DyberPet.settings as settings
from DyberPet.DyberSettings.custom_utils import AvatarImage
from DyberPet.custom_widgets import RoundBarBase
from DyberPet.utils import MaskPhrase, TimeConverter

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



#===========================================================
#    Separator with customized color choice
#===========================================================

class HorizontalSeparator(QWidget):
    """ Horizontal separator """

    def __init__(self, color, height=3, parent=None):
        self.color = color
        super().__init__(parent=parent)
        self.setFixedHeight(height)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 51))
        else:
            #painter.setPen(QColor(0, 0, 0, 22))
            painter.setPen(self.color)

        painter.drawLine(0, 1, self.width(), 1)


class VerticalSeparator(QWidget):
    """ Vertical separator """

    def __init__(self, color, height=3, parent=None):
        self.color = color
        super().__init__(parent=parent)
        self.setFixedWidth(height)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 51))
        else:
            #painter.setPen(QColor(0, 0, 0, 22))
            painter.setPen(self.color)

        painter.drawLine(1, 0, 1, self.height())





###########################################################################
#                            Status UI Widgets                            
###########################################################################

NOTE_H = 40

class NoteFlowGroup(QWidget):
    """ Notification Stream (log system) """

    def __init__(self, title: str, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.sizeHintDyber = sizeHintDyber
        self.nrow = 0

        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.noteLayout = QVBoxLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)

        self.noteLayout.setSpacing(3)
        self.noteLayout.setContentsMargins(15, 0, 15, 15)
        self.noteLayout.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.noteLayout, 1)
        self.vBoxLayout.addStretch(1)

        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        setFont(self.titleLabel, 20)
        self.titleLabel.adjustSize()
        self.resize(self.width(), 60)

    def addNote(self, icon: QPixmap, content: str):
        """ add new notification to stream """
        time = datetime.datetime.now().strftime("%H:%M:%S")
        notification = NotificationWidget(icon, time, content)
        self.noteLayout.insertWidget(0, HorizontalSeparator(QColor(20,20,20,125), 1))
        self.noteLayout.insertWidget(0, notification)
        self.nrow += 1
        self.adjustSize()
    
    def adjustSize(self):
        h = self.nrow * (NOTE_H+8) + 60
        return self.resize(self.width(), h)
    
    


class NotificationWidget(QWidget):
    def __init__(self, icon: QPixmap, time: str, content: str):
        super().__init__()

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.setContentsMargins(5, 5, 5, 5)

        self.__init_Note(icon, time, content)
        self.setFixedHeight(NOTE_H)

    def __init_Note(self, icon, time, content):

        Icon = QLabel()
        Icon.setFixedSize(int(24), int(24))
        Icon.setScaledContents(True)
        Icon.setPixmap(icon) #QPixmap.fromImage(icon))

        timeLabel = CaptionLabel(time)
        setFont(timeLabel, 14, QFont.Normal)
        timeLabel.setFixedWidth(75)

        self.content = content
        self.noteLabel = CaptionLabel(content)
        setFont(self.noteLabel, 15, QFont.Normal)
        self.noteLabel.adjustSize()

        self.hBoxLayout.addWidget(Icon, Qt.AlignLeft)
        #self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(timeLabel, Qt.AlignLeft)
        #self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.noteLabel, Qt.AlignLeft)
        self.hBoxLayout.addStretch(1)



STATUS_W, STATUS_H = 450, 125

class StatusCard(SimpleCardWidget):
    """ Status card """

    def __init__(self, parent=None):
        self.petname = settings.petname
        super().__init__(parent)
        self.setBorderRadius(5)
        self.setObjectName("StatusCard")

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setContentsMargins(30, 5, 30, 5)
        self.hBoxLayout.setSpacing(15)

        self.setFixedSize(STATUS_W, STATUS_H)

        self.__init_Card()


    def _normalBackgroundColor(self):
        
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _updateBackgroundColor(self):

        color = self._normalBackgroundColor()
        self.backgroundColorAni.stop()
        self.backgroundColorAni.setEndValue(color)
        self.backgroundColorAni.start()

    def _clear_layout(self, layout):

        while layout.count():
            child = layout.takeAt(0)
            
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
            else:
                pass
            
            

    def __init_Card(self):

        # Pfp -----------
        info_file = os.path.join(basedir, 'res/role', self.petname, 'info', 'info.json')
        pfp_file = None
        if os.path.exists(info_file):
            info = json.load(open(info_file, 'r', encoding='UTF-8'))
            pfp_file = info.get('pfp', None)

        if pfp_file is None:
            # use the first image of default action
            actJson = json.load(open(os.path.join(basedir, 'res/role', self.petname, 'act_conf.json'),
                                'r', encoding='UTF-8'))
            pfp_file = f"{actJson['default']['images']}_0.png"
            pfp_file = os.path.join(basedir, 'res/role', self.petname, 'action', pfp_file)
        else:
            pfp_file = os.path.join(basedir, 'res/role', self.petname, 'info', pfp_file)

        image = QImage()
        image.load(pfp_file)
        '''
        pixmap = AvatarImage(image, edge_size=80, frameColor="#ffffff")
        self.pfpLabel = QLabel()
        self.pfpLabel.setPixmap(pixmap)
        
        pfpImg = AvatarImage(image, edge_size=80, frameColor="#ffffff")
        self.pfpLabel = QLabel(self)
        self.pfpLabel.setPixmap(QPixmap.fromImage(pfpImg))
        '''
        self.pfpLabel = AvatarImage(image, edge_size=80, frameColor="#ffffff")

        # Pet Name -----------
        hbox_title = QHBoxLayout()
        hbox_title.setContentsMargins(0, 0, 0, 0)
        self.nameLabel = CaptionLabel(self.petname)
        setFont(self.nameLabel, 18, QFont.DemiBold)
        self.nameLabel.adjustSize()
        self.nameLabel.setFixedHeight(25)

        daysText = self.tr(" (Fed for ") + str(settings.pet_data.days) +\
                   self.tr(" days)")
        self.daysLabel = CaptionLabel(daysText)
        setFont(self.daysLabel, 15, QFont.Normal)
        self.daysLabel.setFixedHeight(25)

        hbox_title.addWidget(self.nameLabel, Qt.AlignLeft | Qt.AlignVCenter)
        hbox_title.addWidget(self.daysLabel, Qt.AlignRight | Qt.AlignVCenter)
        hbox_title.addStretch(1)


        # Status Bar -----------
        self.hpStatus = HPWidget()
        self.fvStatus = FVWidget()


        # Assemble all widgets -----------
        vBoxLayout = QVBoxLayout()
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.setSpacing(5)

        vBoxLayout.addStretch(1)
        vBoxLayout.addLayout(
            hbox_title, Qt.AlignLeft | Qt.AlignVCenter)
        vBoxLayout.addWidget(HorizontalSeparator(QColor(20,20,20,125), 1))
        #vBoxLayout_status.addStretch(1)
        vBoxLayout.addWidget(self.hpStatus, 1, Qt.AlignLeft | Qt.AlignVCenter)
        vBoxLayout.addWidget(self.fvStatus, 1, Qt.AlignLeft | Qt.AlignVCenter)
        vBoxLayout.addStretch(1)

        # Assemble main body
        
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.pfpLabel, Qt.AlignRight | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addLayout(vBoxLayout, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(1)
    
    def _changePet(self):
        self._clear_layout(self.hBoxLayout)
        self.petname = settings.petname
        self.__init_Card()
        #self._updateBackgroundColor()
    '''
    def _deleteSave(self):
        self._clear_layout(self.vBoxLayout)
        self.jsonPath = None
        self.cardTitle = None
        self.__init_EmptyCard()
        self._updateBackgroundColor()
    '''
    def _updateHP(self, hp: int):
        self.hpStatus._updateHP(hp)

    def _updateFV(self, fv: int, fv_lvl: int):
        self.fvStatus._updateFV(fv, fv_lvl)
        


class HPWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        self.setObjectName("HPWidget")
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(2, 0, 2, 0)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setSpacing(5)

        self._init_widget()
        self.adjustSize()
        self.setFixedWidth(300)

    def _init_widget(self):

        hpLable = CaptionLabel(self.tr("Satiety"))
        setFont(hpLable, 13, QFont.Normal)
        hpLable.adjustSize()
        hpLable.setFixedSize(43, hpLable.height())

        self.hpicon = QLabel(self)
        self.hpicon.setFixedSize(20,20)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/HP_icon.png'))
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(image)
        self.hpicon.setAlignment(Qt.AlignCenter)

        self.hp_tier = settings.pet_data.hp_tier
        hpText = f"{settings.TIER_NAMES[self.hp_tier]}"
        self.statusLabel = CaptionLabel(hpText, self)
        setFont(self.statusLabel, 12, QFont.DemiBold)
        self.statusLabel.setFixedSize(55,16)

        self.hp_tiers = settings.HP_TIERS
        self.statusBar = RoundBarBase(fill_color="#abf1b7", parent=self) #QProgressBar(self)
        self.statusBar.setMinimum(0)
        self.statusBar.setMaximum(100)
        self._setBarStyle()
        hpShown = math.ceil(round(settings.pet_data.hp/settings.HP_INTERVAL))
        self.statusBar.setFormat(f'{hpShown}/100')
        self.statusBar.setValue(hpShown)
        self.statusBar.setAlignment(Qt.AlignCenter)
        self.statusBar.setFixedSize(145, 15)
        
        self.hBoxLayout.addWidget(hpLable)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.hpicon)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.statusLabel, 1, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.statusBar, 1, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(1)

    def _updateHP(self, hp):
        self.statusBar.setFormat(f'{hp}/100')
        self.statusBar.setValue(hp)
        self._setBarStyle()

        if self.hp_tier != settings.pet_data.hp_tier:
            self.hp_tier = settings.pet_data.hp_tier
            hpText = f"{settings.TIER_NAMES[self.hp_tier]}"
            self.statusLabel.setText(hpText)

    def _setBarStyle(self):
        colors = ["#f8595f", "#f8595f", "#FAC486", "#abf1b7"]
        self.statusBar.setBarColor(colors[settings.pet_data.hp_tier])
        stylesheet = f'''QProgressBar {{
                                        font-family: "Segoe UI";
                                        border: 1px solid #08060f;
                                        border-radius: 7px;
                                      }}
                        QProgressBar::chunk {{
                                        background-color: {colors[settings.pet_data.hp_tier]};
                                        border-radius: 5px;}}'''
        #self.statusBar.setStyleSheet(stylesheet)



class FVWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        self.setObjectName("FVWidget")
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(2, 0, 2, 0)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setSpacing(5)

        self._init_widget()
        self.setFixedWidth(300)

    def _init_widget(self):

        fvLable = CaptionLabel(self.tr("Favor"))
        setFont(fvLable, 13, QFont.Normal)
        fvLable.adjustSize()
        fvLable.setFixedSize(43, fvLable.height())

        fvicon = QLabel(self)
        fvicon.setFixedSize(20,20)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/Fv_icon.png'))
        fvicon.setScaledContents(True)
        fvicon.setPixmap(image)
        fvicon.setAlignment(Qt.AlignCenter)

        fv = settings.pet_data.fv
        self.fv_lvl = settings.pet_data.fv_lvl
        fvText = f"Lv{self.fv_lvl}"
        self.statusLabel = CaptionLabel(fvText, self)
        setFont(self.statusLabel, 12, QFont.DemiBold)
        self.statusLabel.setFixedSize(55,16)

        self.statusBar = RoundBarBase(fill_color="#F4665C", parent=self) #QProgressBar(self)
        #self._setBarStyle()
        self.lvl_max = settings.LVL_BAR[self.fv_lvl]
        self.statusBar.setMinimum(0)
        self.statusBar.setMaximum(self.lvl_max)
        self.statusBar.setFormat(f'{fv}/{self.lvl_max}')
        self.statusBar.setValue(fv)
        self.statusBar.setAlignment(Qt.AlignCenter)
        self.statusBar.setFixedSize(145, 15)
        
        self.hBoxLayout.addWidget(fvLable)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(fvicon)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.statusLabel, 1, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.statusBar, 1, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(1)

    def _updateFV(self, fv, fv_lvl):
        if self.fv_lvl != fv_lvl:
            self.fv_lvl = fv_lvl
            self.lvl_max = settings.LVL_BAR[fv_lvl]
            self.statusBar.setMinimum(0)
            self.statusBar.setMaximum(self.lvl_max)
            self.statusBar.setFormat(f'{fv}/{self.lvl_max}')
            self.statusBar.setValue(fv)

            self.statusLabel.setText(f"Lv{fv_lvl}")
        else:
            self.statusBar.setFormat(f'{fv}/{self.lvl_max}')
            self.statusBar.setValue(fv)





BUFF_W, BUFF_H = 450, 45
BUFF_SIZE = 25

class BuffCard(SimpleCardWidget):
    """  Buff status UI """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.buff_dict = {}

        HScroll = ScrollArea(self)
        HScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        HScroll.setWidgetResizable(True)
        HScroll.setStyleSheet("""QScrollArea {
                                            background-color:  transparent;
                                            border: none;
                                        }""")

        BuffFlow = QWidget()
        BuffFlow.setStyleSheet("""background-color:  transparent;
                                            border: none;""")
        self.hBoxLayout = QHBoxLayout(BuffFlow)
        self.hBoxLayout.setContentsMargins(10, 0, 10, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.hBoxLayout.setSpacing(15)
        #self._init_buff()

        HScroll.setWidget(BuffFlow)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addWidget(HScroll)

        self.setFixedSize(BUFF_W, BUFF_H)
    
    def addBuff(self, itemName, item_conf, idx):

        if idx == 0:
            w = BuffWidget(item_conf)
            self.buff_dict[itemName] = w
            self.hBoxLayout.addWidget(self.buff_dict[itemName])
            self.buff_dict[itemName].bf_removed.connect(self.removeBuffSlot)
            
        elif idx > 0:
            self.buff_dict[itemName].addBuff()

    def removeBuff(self, itemName, idx=None):
        self.buff_dict[itemName].removeBuff(idx)
    
    def removeBuffSlot(self, itemName):
        self.buff_dict.pop(itemName)

        for i in reversed(range(self.hBoxLayout.count())):
            try:
                widget = self.hBoxLayout.itemAt(i).widget()
            except:
                continue
            if widget.buffName == itemName:
                self.hBoxLayout.removeWidget(widget)
                widget.deleteLater()
    
    def _clearBuff(self):
        self.buff_dict = {}
        for i in reversed(range(self.hBoxLayout.count())):
            try:
                widget = self.hBoxLayout.itemAt(i).widget()
            except:
                continue

            self.hBoxLayout.removeWidget(widget)
            widget.deleteLater()




    '''
    def adjustSize(self):
        h = self.nrow * (NOTE_H+8) + 60
        return self.resize(self.width(), h)
    '''


class BuffWidget(QLabel):
    bf_removed = Signal(str, name="Ii_removed")

    '''Single Buff Widget'''

    def __init__(self, item_config=None):

        super().__init__()
        self.item_config = item_config
        self.buffName = item_config['name']
        self.image = item_config['image']
        self.buff_num = 1

        self.size_wh = BUFF_SIZE
        self.setFixedSize(self.size_wh,self.size_wh)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignCenter)

        self.font = QFont('Consolas') #'Consolas') #'Segoe UI')
        self.font.setPointSize(8) #self.size_wh/8)
        self.font.setBold(True)

        ###################################################
        #  Mac and Windows scaling behavior are different
        #  Could be because of HighDPI?
        ###################################################
        self.image = self.image #.scaled(self.size_wh,self.size_wh, mode=Qt.SmoothTransformation)
        self.setPixmap(self.image) #QPixmap.fromImage(self.image))

        self.item_type = self.item_config.get('item_type', 'consumable')
        self._setQss(self.item_type)

        #self.tooltip = 
        self.installEventFilter(ToolTipFilter(self, showDelay=500))
        self.setToolTip(item_config['hint'])


    def paintEvent(self, event):
        super().paintEvent(event)
        if self.buff_num > 1:
            text_printer = QPainter(self)
            text_printer.setFont(self.font)

            text_pen = QPen(QColor("#333333"))
            text_printer.setPen(text_pen)

            text_printer.drawText(QRect(0, 0, int(self.size_wh-2), int(self.size_wh-2)), 
                                  Qt.AlignBottom | Qt.AlignRight, str(self.buff_num))
            text_printer.end()
            

    def _setQss(self, item_type):

        bgc = settings.ITEM_BGC.get(item_type, settings.ITEM_BGC_DEFAULT)
        bdc = bgc

        BuffStyle = f"""
        QLabel{{
            border : 2px solid {bdc};
            border-radius: 5px;
            background-color: {bgc}
        }}
        """
        self.setStyleSheet(BuffStyle)

    def addBuff(self):
        self.buff_num += 1
        self.setPixmap(self.image) #QPixmap.fromImage(self.image))

    def removeBuff(self, idx=None):
        self.buff_num += -1
        if self.buff_num == 0:
            self.deleteBuff()
        else:
            self.setPixmap(self.image) #QPixmap.fromImage(self.image))

    def deleteBuff(self):
        # Send signal to notify related widget
        self.bf_removed.emit(self.buffName)





###########################################################################
#                          Inventory UI Widgets                            
###########################################################################


class BPStackedWidget(QStackedWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentChanged.connect(self.adjustSizeToCurrentWidget)
        self.height_dict = {}

    def adjustSizeToCurrentWidget(self):
        current_widget = self.currentWidget()
        if current_widget:
            height = current_widget.height()
            #print(height)
            self.resize(self.width(), height)
    
    def subWidget_sizeChange(self, tab_idx, h):
        self.height_dict[tab_idx] = h
        h = max(self.height_dict.values())
        self.resize(self.width(), h)

    def resizeEvent(self, event):
        self.adjustSizeToCurrentWidget()
        super().resizeEvent(event)

    def showEvent(self, event):
        self.adjustSizeToCurrentWidget()
        super().showEvent(event)




class coinWidget(QWidget):
    """
    Display number of coins
    """
    coinUpdated = Signal(name='coinUpdated')

    def __init__(self, parent=None):

        super().__init__(parent)
        self.setObjectName("coinWidget")
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(2, 0, 2, 0)
        self.hBoxLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.hBoxLayout.setSpacing(5)

        self._init_widget()
        self.adjustSize()

    def _init_widget(self):
        #self.label = CaptionLabel(self.tr('DyberCoin'))
        #setFont(self.label, 14, QFont.Normal)

        self.icon = QLabel(self)
        self.icon.setFixedSize(25,25)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/Dashboard/coin.svg'))
        self.icon.setScaledContents(True)
        self.icon.setPixmap(image)
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.installEventFilter(ToolTipFilter(self.icon, showDelay=500))
        self.icon.setToolTip(self.tr('Dyber Coin'))

        self.coinAmount = LineEdit(self)
        self.coinAmount.setClearButtonEnabled(False)
        self.coinAmount.setEnabled(False)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.icon, Qt.AlignRight | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.coinAmount, Qt.AlignRight | Qt.AlignVCenter)
        coin_value = settings.pet_data.coins
        self._updateCoin(int(coin_value))

    def _updateCoin(self, coinNumber: int):
        num_str = f"{coinNumber:,}"
        self.coinAmount.setText(num_str)
        self.coinAmount.setFixedWidth(len(num_str)*7 + 29)
        self.coinUpdated.emit()
    
    def _update2data(self):
        coinNumber = settings.pet_data.coins
        num_str = f"{coinNumber:,}"
        self.coinAmount.setText(num_str)
        self.coinAmount.setFixedWidth(len(num_str)*7 + 29)




ITEM_SIZE = 56

class PetItemWidget(QLabel):
    Ii_selected = Signal(int, bool, name="Ii_selected")
    Ii_removed = Signal(int, name="Ii_removed")

    '''Single Item Widget
    
    - Fixed-size square
    - Display the item icon
    - Right bottom corner shows number of the item
    - When clicked, border color change
    - When hover, show item information
    - Keep track of item numbers
    - Able to change / refresh

    - Able to drag and switch (not finished)

    '''
    def __init__(self, cell_index, item_config=None, item_num=0):

        '''item_config
        
        name: str
        img: Pixmap object
        number: int
        effect_HP: int
        effect_FV: int
        drop_rate: float
        fv_lock: int
        hint: str
        item_type: str
        pet_limit: List

        '''
        super().__init__()
        self.cell_index = cell_index

        self.item_config = item_config
        self.item_name = 'None'
        self.image = None
        self.item_num = item_num
        self.selected = False
        self.item_inuse = False
        self.size_wh = ITEM_SIZE #int(56) #*size_factor)

        self.setFixedSize(self.size_wh,self.size_wh)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignCenter)

        self.font = QFont('Consolas') #'Consolas') #'Segoe UI')
        self.font.setPointSize(9) #self.size_wh/8)
        self.font.setBold(True)
        

        if item_config is not None:
            self.item_name = item_config['name']
            self.image = item_config['image']
            ##############################################################
            #  Mac and Windows scaling behavior are different
            #  Could be because of HighDPI?
            #  Actually they are the same, MacOS highlighted the problem.
            #  Now scaling method has been updated in all codes.
            ##############################################################
            #self.image = self.image.scaled(self.size_wh,self.size_wh, mode=Qt.SmoothTransformation)
            self.setPixmap(self.image) #QPixmap.fromImage(self.image))
            self.installEventFilter(ToolTipFilter(self, showDelay=500))
            self.setToolTip(item_config['hint'])

            self.item_type = self.item_config.get('item_type', 'consumable')
            
        else:
            self.item_type = 'Empty'
        
        self._setQss(self.item_type)

    def mousePressEvent(self, event):
        return

    def mouseReleaseEvent(self, event):
        if self.item_config is not None:
            self.selected = not self.selected
            self.Ii_selected.emit(self.cell_index, self.item_inuse)
            self._setQss(self.item_type)


    def paintEvent(self, event):
        super().paintEvent(event)
        if self.item_num > 1:
            text_printer = QPainter(self)
            text_printer.setFont(self.font)

            text_pen = QPen(QColor("#333333"))
            text_printer.setPen(text_pen)

            text_printer.drawText(QRect(0, 0, int(self.size_wh-3), int(self.size_wh-3)), 
                                  Qt.AlignBottom | Qt.AlignRight, str(self.item_num))
            text_printer.end()
            

    def _setQss(self, item_type):

        bgc = settings.ITEM_BGC.get(item_type, settings.ITEM_BGC_DEFAULT)
        bdc = settings.ITEM_BDC if self.selected else bgc

        ItemStyle = f"""
        QLabel{{
            border : 2px solid {bdc};
            border-radius: 5px;
            background-color: {bgc}
        }}
        """
        self.setStyleSheet(ItemStyle)


    def unselected(self):
        self.selected = False
        self._setQss(self.item_type)

    def registItem(self, item_config, n_items):
        self.item_config = item_config
        self.item_num = n_items
        self.item_name = item_config['name']
        self.image = item_config['image']
        #self.image = self.image.scaled(self.size_wh,self.size_wh, mode=Qt.SmoothTransformation)
        self.setPixmap(self.image) #QPixmap.fromImage(self.image))
        self.installEventFilter(ToolTipFilter(self, showDelay=500))
        self.setToolTip(item_config['hint'])
        self.item_type = self.item_config.get('item_type', 'consumable')
        self._setQss(self.item_type)

    def addItem(self, add_n):
        self.item_num += add_n
        self.setPixmap(self.image) #QPixmap.fromImage(self.image))

    def consumeItem(self):
        if self.item_type in ['collection', 'dialogue', 'subpet']:
            self.item_inuse = not self.item_inuse
        else:
            self.item_num += -1
            if self.item_num == 0:
                self.removeItem()
            else:
                self.setPixmap(self.image) #QPixmap.fromImage(self.image))

    def removeItem(self):
        # Send signal to notify related widget
        self.Ii_removed.emit(self.cell_index)

        self.item_config = None
        self.item_name = 'None'
        self.image = None
        self.item_num = 0
        self.selected = False
        self.item_type = 'Empty'

        self.clear()
        self.setToolTip('')
        self._setQss(self.item_type)



class itemTabWidget(QWidget):

    set_confirm = Signal(int, int, name='set_confirm')
    use_item_inven = Signal(str, name='use_item_inven')
    item_num_changed = Signal(str, name='item_num_changed')
    item_note = Signal(str, str, name='item_note')
    item_drop = Signal(str, name='item_drop')
    size_changed = Signal(int, int, name='size_changed')
    addBuff = Signal(str, name='addBuff')
    rmBuff = Signal(str, name='rmBuff')

    def __init__(self, items_data, item_types, sizeHintDyber, tab_index, parent=None):
        super().__init__(parent=parent)

        self.sizeHintDyber = sizeHintDyber
        self.tab_index = tab_index
        self.items_data = items_data
        self.item_types = item_types
        self.cells_dict = {}
        self.empty_cell = []
        self.selected_cell = None
        self.minItemWidget = 36

        self.cardLayout = FlowLayout(self)
        self.cardLayout.setSpacing(9)
        self.cardLayout.setContentsMargins(15, 0, 15, 15)
        self.cardLayout.setAlignment(Qt.AlignVCenter)

        self.resize(self.sizeHintDyber[0] - 150, self.height())
        self._init_items()
        #FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        self.adjustSize()

    def _init_items(self):
        
        keys = settings.pet_data.items.keys()
        keys = [i for i in keys if i in self.items_data.item_dict.keys()]
        keys = [i for i in keys if self.items_data.item_dict[i]['item_type'] in self.item_types]

        # Sort items (after drag function complete, delete it)
        keys_lvl = [self.items_data.item_dict[i]['fv_lock'] for i in keys]
        keys = [x for _, x in sorted(zip(keys_lvl, keys))]

        index_item = 0

        for item in keys:
            if self.items_data.item_dict[item]['item_type'] not in self.item_types:
                continue
            if settings.pet_data.items[item] <= 0:
                continue

            #n_row = index_item // self.tab_shape[1]
            #n_col = (index_item - (n_row-1)*self.tab_shape[1]) % self.tab_shape[1]
            self._addItemCard(index_item, item, settings.pet_data.items[item])
            index_item += 1
        

        if index_item < self.minItemWidget:

            for j in range(index_item, self.minItemWidget):
                #n_row = j // self.inven_shape[1]
                #n_col = (j - (n_row-1)*self.inven_shape[1]) % self.inven_shape[1]

                self._addItemCard(j)
                self.empty_cell.append(j)


    def _addItemCard(self, index_item, item=None, item_number=0):
        if item:
            self.cells_dict[index_item] = PetItemWidget(index_item, self.items_data.item_dict[item], int(item_number))
            
        else:
            self.cells_dict[index_item] = PetItemWidget(index_item)
        
        self.cells_dict[index_item].Ii_selected.connect(self.change_selected)
        self.cells_dict[index_item].Ii_removed.connect(self.item_removed)
        self.cardLayout.addWidget(self.cells_dict[index_item])
        self.adjustSize()

    def adjustSize(self):

        width = self.width()
        n = self.cardLayout.count()
        ncol = (width-39) // (ITEM_SIZE+9) #math.ceil(SACECARD_WH*n / width)
        nrow = math.ceil(n / ncol)
        h = (ITEM_SIZE+10)*nrow + 49
        #print(width, n, ncol, nrow, h)
        self.size_changed.emit(self.tab_index, h)
        #h = self.cardLayout.heightForWidth(self.width()) #+ 6
        return self.resize(self.width(), h)
    
    def _clear_cardlayout(self, layout):

        while layout.count():
            child = layout.takeAt(0)
            try:
                child.deleteLater()
            except:
                pass
            '''
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
            else:
                pass
            '''
    
    def _refreshBag(self):
        self.cells_dict = {}
        self.empty_cell = []
        self.selected_cell = None
        # clear layout
        self._clear_cardlayout(self.cardLayout)
        # load in new items
        self._init_items()


    def change_selected(self, selected_index, item_inuse):
        if self.selected_cell == selected_index:
            self.selected_cell = None
            self.changeButton(item_inuse)
        elif self.selected_cell is not None:
            self.cells_dict[self.selected_cell].unselected()
            self.selected_cell = selected_index
            self.changeButton(item_inuse)
        else:
            self.selected_cell = selected_index
            self.changeButton(item_inuse)

    def item_removed(self, rm_index):
        self.empty_cell.append(rm_index)
        self.empty_cell.sort()
        if rm_index == self.selected_cell:
            self.selected_cell = None
        self.changeButton()

    def changeButton(self, item_inuse=False):
        if self.selected_cell is None:
            self.set_confirm.emit(0, 0)
            #self.button_confirm.setText(self.tr('使用'))
            #self.button_confirm.setDisabled(True)
    
        else:
            if item_inuse:
                self.set_confirm.emit(1, 1)
                #self.button_confirm.setText(self.tr('收回'))
            else:
                self.set_confirm.emit(0, 1)
                #self.button_confirm.setText(self.tr('使用'))
            #self.button_confirm.setDisabled(False)

    def acc_withdrawed(self, item_name):
        cell_index = [i for i in self.cells_dict.keys() if self.cells_dict[i].item_name==item_name]
        if not cell_index:
            return
        cell_index = cell_index[0]
        self.cells_dict[cell_index].consumeItem()
        if cell_index == self.selected_cell:
            self.changeButton()
        
        if self.items_data.item_dict[item_name]['buff']:
            self.rmBuff.emit(item_name)


    def _confirmClicked(self, tab_index):
        if self.tab_index != tab_index:
            return
        
        if self.selected_cell is None: #无选择
            return

        item_name_selected = self.cells_dict[self.selected_cell].item_name

        # Check if the item is character-specific
        if len(self.items_data.item_dict[item_name_selected]['pet_limit']) != 0:
            pet_list = self.items_data.item_dict[item_name_selected]['pet_limit']
            if settings.petname not in pet_list:
                self.item_note.emit('system', f"[{item_name_selected}] {self.tr('仅能在切换至')}' [{'、'.join(pet_list)}] {self.tr('后使用哦')}")
                return

        # Check item type
        if self.items_data.item_dict[item_name_selected]['item_type'] == 'consumable':
            # Item adds HP, but HP is already full / 数值已满 且物品为正向效果
            if (settings.pet_data.hp == (settings.HP_TIERS[-1]*settings.HP_INTERVAL) and self.items_data.item_dict[item_name_selected]['effect_HP'] >= 0):
                # Item doesn't have effect on FV, return without use item
                if self.items_data.item_dict[item_name_selected]['effect_FV'] == 0:
                    return
                # FV already full, return
                elif ((settings.pet_data.fv_lvl == (len(settings.LVL_BAR)-1)) and (settings.pet_data.fv==settings.LVL_BAR[settings.pet_data.fv_lvl]) and self.items_data.item_dict[item_name_selected]['effect_FV'] > 0):
                    return

            # Item HP cost > current HP / 使用物品所消耗的数值不足 （当有负向效果时）
            if (settings.pet_data.hp + self.items_data.item_dict[item_name_selected]['effect_HP']) < 0: # or\
                #(settings.pet_data.em + self.items_data.item_dict[item_name_selected]['effect_FV']) < 0:
                return

            # Item can be used --------
            # Change pet_data
            settings.pet_data.change_item(item_name_selected, item_change=-1)
            self.item_num_changed.emit(item_name_selected)

            # Signal to item label
            #self.cells_dict[self.selected_cell].unselected()
            self.cells_dict[self.selected_cell].consumeItem()

            # signal to act feed animation
            self.use_item_inven.emit(item_name_selected)
            self.item_note.emit(item_name_selected, '[%s] -1'%item_name_selected)

            # change button
            #self.selected_cell = None
            #self.changeButton()

        elif self.items_data.item_dict[item_name_selected]['item_type'] == 'collection':
            #print('collection used')
            #self.cells_dict[self.selected_cell].unselected()
            self.cells_dict[self.selected_cell].consumeItem()
            self.use_item_inven.emit(item_name_selected)
            #self.selected_cell = None
            self.changeButton(self.cells_dict[self.selected_cell].item_inuse)

        elif self.items_data.item_dict[item_name_selected]['item_type'] == 'dialogue':
            #print('collection used')
            #self.cells_dict[self.selected_cell].unselected()
            self.use_item_inven.emit(item_name_selected)
            #self.selected_cell = None
            #self.changeButton()

        elif self.items_data.item_dict[item_name_selected]['item_type'] == 'subpet':
            self.cells_dict[self.selected_cell].consumeItem()
            self.use_item_inven.emit(item_name_selected)
            self.changeButton(self.cells_dict[self.selected_cell].item_inuse)
        
        # Buff-related operation
        if self.items_data.item_dict[item_name_selected]['buff']:
            if self.items_data.item_dict[item_name_selected]['item_type'] in ['subpet','collection']:
                if self.cells_dict[self.selected_cell].item_inuse:
                    self.addBuff.emit(item_name_selected)
                else:
                    self.rmBuff.emit(item_name_selected)
            else:
                self.addBuff.emit(item_name_selected)

        return


    def add_item(self, item_name, n_items):
        
        item_exist = False
        for i in self.cells_dict.keys():
            if self.cells_dict[i].item_name == item_name:
                item_index = i
                item_exist = True
                break
            else:
                continue

        if item_exist:
            # signal to item label
            self.cells_dict[item_index].addItem(n_items)

        elif n_items <= 0:
            return

        elif self.empty_cell:
            item_index = self.empty_cell[0]
            self.empty_cell = self.empty_cell[1:]
            self.cells_dict[item_index].registItem(self.items_data.item_dict[item_name], n_items)

        else:
            item_index = len(self.cells_dict)
            self._addItemCard(item_index, item_name, n_items)

        if n_items > 0:
            self.item_note.emit(item_name, '[%s] +%s'%(item_name, n_items))
            self.item_drop.emit(item_name)
        else:
            self.item_note.emit(item_name, '[%s] %s'%(item_name, n_items))
        # change pet_data
        settings.pet_data.change_item(item_name, item_change=n_items)
        self.item_num_changed.emit(item_name)





###########################################################################
#                             Shop UI Widgets                            
###########################################################################

SHOPITEM_W, SHOPITEM_H = 210, 120
SHOPITEM_WH = 50

class ShopItemWidget(SimpleCardWidget):

    buyClicked = Signal(str, name="buyClicked")
    sellClicked = Signal(str, name="sellClicked")

    '''Shop Item Widget
    
    - Fixed-size square
    - Display the item icon, cost, condition/numbers in backpack
    - button to buy and sell
    - item cost should not exceed 9,999

    '''
    def __init__(self, cell_index, item_config, parent=None):

        super().__init__(parent)
        self.setBorderRadius(5)
        self.setObjectName("ShopCard")

        self.cell_index = cell_index
        self.item_config = item_config

        self.item_name = item_config['name']
        self.image = item_config['image']
        self.description = self.item_config['hint']
        self.cost = self.item_config['cost']
        self.item_type = self.item_config.get('item_type', 'consumable')
        self.fv_lock = self.item_config['fv_lock']
        self.pet_limit = self.item_config['pet_limit']
        if not self.pet_limit:
            self.pet_limit = settings.pets

        self.unlocked = False
        self.locked_reason = 'NONE'
        self._getLockStat()

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.setContentsMargins(15, 5, 15, 5)
        self.vBoxLayout.setSpacing(5)

        self.hBox_description = QHBoxLayout()
        self.hBox_description.setContentsMargins(0, 0, 0, 0)
        self.hBox_description.setSpacing(15)

        self.vBox_description = QVBoxLayout()
        self.vBox_description.setContentsMargins(0, 0, 0, 0)
        self.vBox_description.setSpacing(5)

        self.hBox_button = QHBoxLayout()
        self.hBox_button.setAlignment(Qt.AlignCenter)
        self.hBox_button.setContentsMargins(0, 0, 0, 0)
        self.hBox_button.setSpacing(10)

        self.setFixedSize(SHOPITEM_W, SHOPITEM_H)

        self._init_Card()

    def _getLockStat(self):
        unlocked = settings.pet_data.fv_lvl >= self.fv_lock and settings.petname in self.pet_limit
        if settings.petname not in self.pet_limit:
            self.locked_reason = 'PETLIMIT'
        elif settings.pet_data.fv_lvl < self.fv_lock:
            self.locked_reason = 'FVLOCK'
        else:
            self.locked_reason = 'NONE'

        if self.unlocked == unlocked:
            lockChanged = False
        else:
            self.unlocked = unlocked
            lockChanged = True

        return lockChanged


    def _normalBackgroundColor(self):
        
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _updateBackgroundColor(self):

        color = self._normalBackgroundColor()
        self.backgroundColorAni.stop()
        self.backgroundColorAni.setEndValue(color)
        self.backgroundColorAni.start()

    def _clear_layout(self, layout):

        while layout.count():
            child = layout.takeAt(0)
            
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
            else:
                pass
            

    def _init_Card(self):

        # Item image
        self.imgLabel = QLabel()
        self.imgLabel.setFixedSize(SHOPITEM_WH, SHOPITEM_WH)
        self.imgLabel.setScaledContents(True)
        self.imgLabel.setAlignment(Qt.AlignCenter)
        pixmap = self.image #QPixmap.fromImage(self.image)
        if not self.unlocked:
            pixmap = Silhouette(pixmap)
        self.imgLabel.setPixmap(pixmap)
        if self.unlocked:
            self.imgLabel.installEventFilter(ToolTipFilter(self.imgLabel, showDelay=500))
            self.imgLabel.setToolTip(self.description)
        
        self._setQss(self.item_type)


        # Item name
        if self.unlocked:
            title = self.item_name
        else:
            title = MaskPhrase(self.item_name)
        self.nameLabel = CaptionLabel(title)
        setFont(self.nameLabel, 14, QFont.DemiBold)
        self.nameLabel.adjustSize()
        #self.nameLabel.setFixedHeight(25)


        # Item info
        if self.unlocked:
            self.info_text = f"{self.tr('Owned')}: {settings.pet_data.items.get(self.item_name, 0)}"
            fontCol = 'black'
        elif self.locked_reason == 'FVLOCK':
            self.info_text = f"{self.tr('Favor Req')}: {self.fv_lock}"
            fontCol = QColor("#ff333d")
        elif self.locked_reason == 'PETLIMIT':
            self.info_text = f"{self.tr('Other Chars Only')}"
            fontCol = QColor("#636363")

        self.infoLabel = CaptionLabel(self.info_text)
        setFont(self.infoLabel, 14, QFont.Normal)

        #if fontCol:
        palette = self.infoLabel.palette()
        palette.setColor(QPalette.WindowText, fontCol)  # Example: blue color
        self.infoLabel.setPalette(palette)
        self.infoLabel.adjustSize()
        #self.infoLabel.setFixedHeight(25)

        self.vBox_description.addStretch(1)
        self.vBox_description.addWidget(self.nameLabel, Qt.AlignVCenter | Qt.AlignLeft)
        #self.vBox_description.addStretch(1)
        self.vBox_description.addWidget(self.infoLabel, Qt.AlignVCenter | Qt.AlignLeft)
        self.vBox_description.addStretch(1)

        self.hBox_description.addStretch(1)
        self.hBox_description.addWidget(self.imgLabel, Qt.AlignRight | Qt.AlignVCenter)
        self.hBox_description.addStretch(1)
        self.hBox_description.addLayout(self.vBox_description, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBox_description.addStretch(1)


        # Buy Button
        self.buyButton = PushButton(text = f"{self.cost}",
                                    icon = QIcon(os.path.join(basedir, 'res/icons/Dashboard/coin.svg')))
        self.buyButton.setFixedWidth(85)
        self.buyButton.clicked.connect(self._buyClicked)


        # Sell Button
        self.sellButton = PushButton(text = self.tr("Sell"),
                                     icon = QIcon(os.path.join(basedir, 'res/icons/Dashboard/sell.svg')))
        self.sellButton.setFixedWidth(85)
        self.sellButton.clicked.connect(self._sellClicked)

        if not self.unlocked:
            self.buyButton.setDisabled(True)
            self.sellButton.setDisabled(True)

        #self.hBox_button.addStretch(1)
        self.hBox_button.addWidget(self.buyButton)
        #self.hBox_button.addStretch(1)
        self.hBox_button.addWidget(self.sellButton)
        #self.hBox_button.addStretch(1)

        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.hBox_description)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.hBox_button)
        self.vBoxLayout.addStretch(1)
            

    def _setQss(self, item_type):

        bgc = settings.ITEM_BGC.get(item_type, settings.ITEM_BGC_DEFAULT)
        bdc = bgc

        ItemStyle = f"""
        QLabel{{
            border : 2px solid {bdc};
            border-radius: 5px;
            background-color: {bgc}
        }}
        """
        self.imgLabel.setStyleSheet(ItemStyle)

    def _update_Own(self):
        if not self.unlocked:
            return
        self.info_text = f"{self.tr('Owned')}: {settings.pet_data.items.get(self.item_name, 0)}"
        self.infoLabel.setText(self.info_text)
        self.infoLabel.adjustSize()

    def _update_UI(self):
        lockChanged = self._getLockStat()

        if lockChanged:
            # Item image
            pixmap = self.image #QPixmap.fromImage(self.image)
            if not self.unlocked:
                pixmap = Silhouette(pixmap)
            self.imgLabel.setPixmap(pixmap)
            if self.unlocked:
                self.imgLabel.installEventFilter(ToolTipFilter(self.imgLabel, showDelay=500))
                self.imgLabel.setToolTip(self.description)
            ############################################################
            # To-do: if locked, should uninstall the even filter 
            ############################################################
        
            # Item name
            if self.unlocked:
                title = self.item_name
            else:
                title = MaskPhrase(self.item_name)
            self.nameLabel.setText(title)
            self.nameLabel.adjustSize()

        # Item info
        if self.unlocked:
            self.info_text = f"{self.tr('Owned')}: {settings.pet_data.items.get(self.item_name, 0)}"
            fontCol = 'black'
        elif self.locked_reason == 'FVLOCK':
            self.info_text = f"{self.tr('Favor Req')}: {self.fv_lock}"
            fontCol = QColor("#ff333d")
        elif self.locked_reason == 'PETLIMIT':
            self.info_text = f"{self.tr('Other Chars Only')}"
            fontCol = QColor("#636363")

        self.infoLabel.setText(self.info_text)

        #if fontCol:
        palette = self.infoLabel.palette()
        palette.setColor(QPalette.WindowText, fontCol)  # Example: blue color
        self.infoLabel.setPalette(palette)
        self.infoLabel.adjustSize()

        # Button
        disableBtn = not self.unlocked
        self.buyButton.setDisabled(disableBtn)
        self.sellButton.setDisabled(disableBtn)

    def _buyClicked(self):
        self.buyClicked.emit(self.item_name)

    def _sellClicked(self):
        self.sellClicked.emit(self.item_name)



    

class ShopView(QWidget):
    buyItem = Signal(str, name='buyItem')
    sellItem = Signal(str, name='sellItem')

    def __init__(self, items_data, sizeHintDyber, parent=None):
        super().__init__(parent=parent)

        self.sizeHintDyber = sizeHintDyber
        self.items_data = items_data
        self.search_dict = defaultdict(list)
        self.cards = {}
        self._Items = []
        self.searchDict = defaultdict(list)
        self.filterDict = {self.tr('Type'): defaultdict(list),
                           self.tr('MOD'): defaultdict(list)}
        #self.modDict = defaultdict(list)
        self.conf2uiMap = {'consumable':self.tr('Food'),
                           'collection':self.tr('Collection'),
                           'dialogue':self.tr('Collection'),
                           'subpet':self.tr('Pet')}

        self.cardLayout = FlowLayout(self)
        self.cardLayout.setSpacing(9)
        self.cardLayout.setContentsMargins(15, 0, 15, 15)
        self.cardLayout.setAlignment(Qt.AlignVCenter)

        self.resize(self.sizeHintDyber[0] - 140, self.height())
        self._init_items()
        #FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        self.adjustSize()


    def _init_items(self):

        # Sort items (after drag function complete, delete it)
        keys = self.items_data.keys()
        keys = [i for i in keys if self.items_data[i]['cost'] != -1]
        keys_lvl = [self.items_data[i]['fv_lock'] for i in keys]
        keys = [x for _, x in sorted(zip(keys_lvl, keys))]

        item_idx = 0
        for item in keys:
            self._addItemCard(item_idx, item)
            item_idx += 1


    def _addItemCard(self, item_idx, item):
        item_config = self.items_data[item]
        card = ShopItemWidget(item_idx, item_config)
        self.cards[item_idx] = card
        self._Items.append(item)
        
        # Signal Connection
        self.cards[item_idx].buyClicked.connect(self.buyItem)
        self.cards[item_idx].sellClicked.connect(self.sellItem)

        self.cardLayout.addWidget(self.cards[item_idx])
        self.adjustSize()

        # Add into search dictionary
        self._addToDict(item_idx, item)

    def _addToDict(self, item_idx, itemName):
        # Search Dict
        for i in range(len(itemName)):
            self.searchDict[itemName[0:i+1]].append(item_idx)
        # Type Dict
        confType = self.items_data[itemName]['item_type']
        uiType = self.conf2uiMap[confType]
        self.filterDict[self.tr('Type')][uiType].append(item_idx)
        # MOD Dict
        modName = self.items_data[itemName]['modName']
        self.filterDict[self.tr('MOD')][modName].append(item_idx)

    def adjustSize(self):
        width = self.width()
        n = self.cardLayout.count()
        ncol = (width-9) // (SHOPITEM_W+9) #math.ceil(SACECARD_WH*n / width)
        nrow = math.ceil(n / ncol)
        #print(width,ncol,nrow)
        h = (SHOPITEM_H+9)*nrow + 49

        return self.resize(self.width(), h)
    
    def _clear_cardlayout(self, layout):

        while layout.count():
            child = layout.takeAt(0)
            try:
                child.deleteLater()
            except:
                pass

    def _updateList(self, tagDict, searchText):
        #print(tagDict, searchText)
        if searchText != '':
            idxToShow = self.searchDict[searchText]
        else:
            idxToShow = list(self.cards.keys())

        for title, tags in tagDict.items():
            if not tags:
                continue
            else:
                idxInTags = []
                for tag in tags:
                    idxInTags += self.filterDict[title][tag]
            idxInTags = set(idxInTags)
            idxToShow = [i for i in idxToShow if i in idxInTags]

        #print([self._Items[i] for i in idxToShow])
        self.cardLayout.removeAllWidgets()

        for i, card in self.cards.items():
            isVisible = i in idxToShow
            card.setVisible(isVisible)
            if isVisible:
                self.cardLayout.addWidget(card)
                self.adjustSize()

    def _updateItemNum(self, item_name):
        potential_idx = self.searchDict[item_name]
        for idx in potential_idx:
            card = self.cards[idx]
            if card.item_name == item_name:
                card._update_Own()
                break

    def _updateAllItemUI(self):
        for idx, card in self.cards.items():
            card._update_UI()

    def _fvchange(self, fv_lvl):
        for idx, card in self.cards.items():
            if fv_lvl >= card.fv_lock and not card.unlocked and card.locked_reason == 'FVLOCK':
                card._update_UI()





FILTER_W = 450
class filterView(SimpleCardWidget):
    """ Filter Options Widget """
    filterChanged = Signal(name='filterChanged')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(5)
        self.setObjectName("filterView")
        self.filter_dict = {}

        self.vBoxLayout = QVBoxLayout(self)
        #self.vBoxLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.vBoxLayout.setContentsMargins(25, 15, 15, 15)
        self.vBoxLayout.setSpacing(5)

        self.setFixedWidth(FILTER_W)


    def _normalBackgroundColor(self):
        
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _updateBackgroundColor(self):

        color = self._normalBackgroundColor()
        self.backgroundColorAni.stop()
        self.backgroundColorAni.setEndValue(color)
        self.backgroundColorAni.start()

    def _clear_layout(self, layout):

        while layout.count():
            child = layout.takeAt(0)
            
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
            else:
                pass 

    def addFilter(self, title: str, options: List):

        titleW = CaptionLabel(title)
        setFont(titleW, 15, QFont.DemiBold)
        #titleW.adjustSize()
        #titleW.setFixedHeight(25)

        filterW = filterWidget(title, options)
        self.filter_dict[title] = filterW
        self.filter_dict[title].tagClicked.connect(self.filterChanged)

        #Signal Connection
        # TO-DO
        #if len(self.filter_dict) > 1:
        #    self.vBoxLayout.addWidget(HorizontalSeparator(QColor(20,20,20,125), 1))
        self.vBoxLayout.addWidget(titleW)
        self.vBoxLayout.addWidget(filterW)
        
        self.adjustSize()
    
    def adjustSize(self):
        w = [w.height() for _,w in self.filter_dict.items()]
        #print(w)
        h = sum(w) + (2*len(w)-1)*5 + 30 + len(w)*20
        return self.resize(self.width(), h)

    def _getSelectedTags(self):

        selectedTags = defaultdict(list)

        for title, widget in self.filter_dict.items():
            for btn in widget.opt_btn:
                if btn.isChecked():
                    selectedTags[title].append(btn.text())

        return selectedTags

    



class filterWidget(QWidget):

    tagClicked = Signal(name='tagClicked')

    def __init__(self, title, options, parent=None):
        super().__init__(parent=parent)

        self.title = title
        self.options = options
        self.opt_btn = []

        self.cardLayout = FlowLayout(self)
        self.cardLayout.setSpacing(5)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.cardLayout.setAlignment(Qt.AlignVCenter)

        self.resize(FILTER_W-40, self.height())
        self._init_opts()
        self.adjustSize()


    def _init_opts(self):
        for opt in self.options:
            btn = PillPushButton(opt)
            self.cardLayout.addWidget(btn)
            self.opt_btn.append(btn)
            btn.adjustSize()
            btn.setFixedHeight(25)
            self.adjustSize()

            btn.clicked.connect(self.tagClicked)


    def adjustSize(self):
        width = self.width()
        nrow = self._calculate_nrow()
        btnH = self.opt_btn[0].height()
        h = (btnH+10)*nrow + 5*(nrow-1)
        #print(nrow)
        return self.resize(self.width(), h)


    def _calculate_nrow(self):
        nrow = 1
        lenRecord = FILTER_W-40+5
        for btn in self.opt_btn:
            lenRecord -= (btn.width() + 5)
            if lenRecord < 0:
                lenRecord = FILTER_W-40 - btn.width()
                nrow += 1

        return nrow




class ShopMessageBox(MessageBoxBase):
    """ Custom message box """
    bill = Signal(int, name='bill')

    def __init__(self, option, item_name, maxNum, cost, parent=None):
        super().__init__(parent)
        self.setObjectName("ShopMessageBox")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.cost = cost
        self.option = option
        self.itemNum = 0
        if self.option == 'buy':
            self.titleLabel = SubtitleLabel(self.tr('Buy') + f' [{item_name}]', self)
        elif self.option == 'sell':
            self.titleLabel = SubtitleLabel(self.tr('Sell') + f' [{item_name}]', self)
        self.numSpinBox = SpinBox(self)
        self.numSpinBox.setMinimum(0)
        self.numSpinBox.setMaximum(maxNum)

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.numSpinBox)

        # change the text of button
        self.yesButton.setIcon(os.path.join(basedir, 'res/icons/Dashboard/coin.svg'))
        self.yesButton.setText('0')
        self.cancelButton.setText(self.tr('Cancel'))

        self.widget.setMinimumWidth(350)
        self.numSpinBox.textChanged.connect(self._updateCost)

    def _updateCost(self, num):
        self.itemNum = int(num)
        self.bill.emit(self.itemNum)
        if self.option == 'buy':
            self.yesButton.setText(f'-{self.cost * self.itemNum}')
        elif self.option == 'sell':
            self.yesButton.setText(f'+{self.cost * self.itemNum}')

    def __onYesButtonClicked(self):
        self.accept()
        self.accepted.emit()




def Silhouette(pixmap):
    # Create a new QPixmap to draw the silhouette
    silhouette = QPixmap(pixmap.size())
    silhouette.fill(Qt.transparent)  # Start with a transparent pixmap

    # Create a QPainter to draw on the pixmap
    painter = QPainter(silhouette)
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)

    # Set the composition mode to colorize with black
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(silhouette.rect(), QColor('#787878'))
    # Finalize the painting and save the silhouette
    painter.end()

    return silhouette







###########################################################################
#                          Animation UI Widgets                            
###########################################################################

class AnimationGroup(QWidget):
    """ Animation card group """

    updateList = Signal(name="updateList")
    playAct = Signal(str, name='playAct')
    addNew = Signal(name="addNew")
    deleteAct = Signal(str, name='deleteAct')

    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.sizeHintDyber = sizeHintDyber
        self.setObjectName("AnimationGroup")
        self.actCards = {}
        self.current_pet = settings.petname

        self.__init_ui()
        self.add_actions()
        #self.__connectSignalToSlot()


    def __init_ui(self):
        '''
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        '''
        self.setFixedSize(QSize(self.sizeHintDyber[0]-150, 800))

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout.setSpacing(10)

        # Section Label 1
        self.horizontalLayout_0 = QHBoxLayout()
        self.horizontalLayout_0.setContentsMargins(0, 0, 0, 0)
        self.SectionLabel1 = CaptionLabel(self)
        self.SectionLabel1.setText(self.tr("Action List"))
        setFont(self.SectionLabel1, 24, QFont.Normal)
        self.horizontalLayout_0.addWidget(self.SectionLabel1)
        spacerItem0 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_0.addItem(spacerItem0)
        self.verticalLayout.addLayout(self.horizontalLayout_0)

        # Playlist label
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.setContentsMargins(0, 0, 0, 0)
        self.col_label_1 = StrongBodyLabel()
        self.col_label_1.setText(self.tr("Playlist"))
        setFont(self.col_label_1, 15, QFont.Normal)
        self.col_label_1.setTextColor(QColor(140, 140, 140))
        self.horizontalLayout_1.addWidget(self.col_label_1)
        spacerItem1 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_1)

        # Action layout 1
        self.action_layout_1 = QVBoxLayout()
        self.action_layout_1.setContentsMargins(0, 0, 0, 0)
        self.action_layout_1.setSpacing(10)
        self.verticalLayout.addLayout(self.action_layout_1)
        spacerItem2 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem2)

        # Section Label 2
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.SectionLabel2 = CaptionLabel(self)
        self.SectionLabel2.setText(self.tr("Customized"))
        setFont(self.SectionLabel2, 24, QFont.Normal)
        self.horizontalLayout_2.addWidget(self.SectionLabel2)
        spacerItem3 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        # Action layout 2
        self.action_layout_2 = QVBoxLayout()
        self.action_layout_2.setContentsMargins(0, 0, 0, 0)
        self.action_layout_2.setSpacing(10)

        # Add action button
        self.addButton = PushButton()
        self.addButton.setText(self.tr("Add New Animation"))
        self.addButton.setIcon(FIF.ADD)
        self.addButton.setFixedWidth(self.width())
        self.addButton.clicked.connect(self.addNew)
        self.action_layout_2.addWidget(self.addButton)

        self.verticalLayout.addLayout(self.action_layout_2)
        spacerItem4 = QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem4)

    def add_actions(self):
        act_configs = settings.act_data.allAct_params[settings.petname]
        # Some system actions are not callable
        act_names = [k for k,v in act_configs.items() if -1 not in v['status_type']]
        act_fv = [v['status_type'][1] for k,v in act_configs.items() if -1 not in v['status_type']]
        # rank actions by fv lock
        indexed_fv = list(enumerate(act_fv))
        sorted_indices = sorted(indexed_fv, key=lambda x: (x[1], x[0]))
        sorted_act_names = [act_names[idx] for idx, _ in sorted_indices]

        for act_name in sorted_act_names:
            act_conf = act_configs[act_name]
            if act_conf['act_type'] == 'random_act' or act_conf['act_type'] == 'accessory_act':
                self._addCard(act_name, act_conf, 0)
            elif act_conf['act_type'] == 'customized':
                self._addCard(act_name, act_conf, 1)

    def _addCard(self, act_name, act_conf, layout_idx):
        card = ActionCard(act_name, act_conf, self.width(), True if layout_idx else False)
        self.actCards[act_name] = card
        if layout_idx == 0:
            self.action_layout_1.addWidget(card)
        elif layout_idx == 1:
            self.action_layout_2.insertWidget(self.action_layout_2.count() - 1, card)
            self.actCards[act_name].deleteAct.connect(self._deleteAct)
        
        self.adjustSize()

        self.actCards[act_name].updateList.connect(self._updateList)
        self.actCards[act_name].playAct.connect(self._playAct)

    def _deleteCard(self, act_name, layout_idx):
        card = self.actCards.pop(act_name)
        if layout_idx == 0:
            self.action_layout_1.removeWidget(card)
        elif layout_idx == 1:
            self.action_layout_2.removeWidget(card)
        
        card.deleteLater()
        self.adjustSize()
    
    def adjustSize(self):
        n = self.action_layout_1.count() + self.action_layout_2.count() - 1
        h = 200 + n*60
        return self.setFixedSize(self.width(), h)
    
    def _updateList(self, act_name, inlist_bool):
        settings.act_data.allAct_params[settings.petname][act_name]['in_playlist'] = inlist_bool
        settings.act_data.save_data()
        self.updateList.emit()

    def _playAct(self, act_name):
        self.playAct.emit(act_name)

    def _deleteAct(self, act_name):
        self.deleteAct.emit(act_name)

    def updateAct(self):
        if self.current_pet == settings.petname:
            # Character refreshed
            for _, card in self.actCards.items():
                card.update_info()
        else:
            # Character changed
            self.current_pet = settings.petname
            for _, card in self.actCards.items():
                card.setParent(None)
                card.deleteLater()
            self.actCards = {}
            self.add_actions()

    


class ActionCard(SimpleCardWidget):

    updateList = Signal(str, bool, name='updateList')
    playAct = Signal(str, name='playAct')
    deleteAct = Signal(str, name='deleteAct')

    def __init__(self, act_name, act_config, card_width, customized, parent=None):

        super().__init__(parent)
        self.setBorderRadius(5)
        self.setObjectName("ActionCard")

        self.act_name = act_name
        self.act_config = act_config
        self.card_width = card_width
        self.customized = customized

        self.hBoxLayout = QHBoxLayout(self)
        #self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setContentsMargins(10, 5, 10, 5)
        self.hBoxLayout.setSpacing(0)

        self.setFixedSize(self.card_width, 50)
        
        self._init_Card()
        self.update_info()
        self.checkBox.clicked.connect(self._checkClicked)

    def _init_Card(self):
        self.checkBox = CheckBox("")
        self.checkBox.setFixedSize(20, 20)
        self.actLabel = BodyLabel()
        #self.actLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.commentLabel = BodyLabel()

        self.playBtn = TransparentToolButton(self)
        self.playBtn.setIcon(FIF.PLAY)
        self.playBtn.setFixedSize(25,25)
        self.playBtn.setIconSize(QSize(16,16))
        self.playBtn.clicked.connect(self._playClicked)

        if self.customized:
            self.deleteBtn = TransparentToolButton(self)
            self.deleteBtn.setIcon(FIF.DELETE)
            self.deleteBtn.setFixedSize(25,25)
            self.deleteBtn.setIconSize(QSize(16,16))
            self.deleteBtn.clicked.connect(self._deleteClicked)

        self.hBoxLayout.addWidget(self.checkBox, 0, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem1 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.hBoxLayout.addItem(spacerItem1)
        self.hBoxLayout.addWidget(self.actLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem2 = QSpacerItem(30, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.hBoxLayout.addItem(spacerItem2)
        self.hBoxLayout.addWidget(self.commentLabel, 0, Qt.AlignRight | Qt.AlignVCenter)
        if self.customized:
            spacerItem3 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
            self.hBoxLayout.addItem(spacerItem3)
            self.hBoxLayout.addWidget(self.deleteBtn, 0, Qt.AlignRight | Qt.AlignVCenter)
            spacerItem4 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
            self.hBoxLayout.addItem(spacerItem4)
            self.hBoxLayout.addWidget(self.playBtn, 0, Qt.AlignRight | Qt.AlignVCenter)
        else:
            spacerItem3 = QSpacerItem(50, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
            self.hBoxLayout.addItem(spacerItem3)
            self.hBoxLayout.addWidget(self.playBtn, 0, Qt.AlignRight | Qt.AlignVCenter)


    def update_info(self):
        
        self.inlist = self.act_config['in_playlist']
        self.unlocked = self.act_config['unlocked']

        # In-playlist Check
        self.checkBox.setChecked(self.inlist)
        if not self.unlocked or self.act_config['special_act']:
            self.checkBox.setEnabled(False)
        else:
            self.checkBox.setEnabled(True)

        # Action name
        self.actLabel.setText(self.act_name)
        if not self.unlocked:
            self.actLabel.setTextColor(QColor(140, 140, 140))
            self.playBtn.setEnabled(False)
        else:
            self.actLabel.setTextColor(QColor(0, 0, 0))
            self.playBtn.setEnabled(True)

        # Comments
        comment = self._get_comment()
        self.commentLabel.setText(comment)
        self.commentLabel.setTextColor(QColor(140, 140, 140))


    
    def _get_comment(self):
        if not self.unlocked:
            return self.tr("Action Locked")
        
        hp_type = self.act_config['status_type'][0]
        if not self.act_config['special_act']:
            return f"{settings.TIER_NAMES[hp_type]}"
        else:
            return self.tr("Special action") + " | " + f"{settings.TIER_NAMES[hp_type]}"


    def _checkClicked(self):
        self.inlist = not self.inlist
        self.checkBox.setChecked(self.inlist)
        #self.checkBox.setEnabled(False)
        self.updateList.emit(self.act_name, self.inlist)


    def _playClicked(self):
        self.playAct.emit(self.act_name)

    def _deleteClicked(self):
        self.deleteAct.emit(self.act_name)



###########################################################################
#                             Task UI Widgets                            
###########################################################################

PANEL_W, PANEL_H = 420, 300

class FocusPanel(CardWidget):

    start_pomodoro = Signal(int, name="start_pomodoro")
    cancel_pomodoro = Signal(name="cancel_pomodoro")
    start_focus = Signal(str, int, int, name="start_focus")
    cancel_focus = Signal(name="cancel_focus")
    addCoins = Signal(int, bool, bool, str, name="addCoins")
    addProgress = Signal(name="addProgress")

    """Focus Panel UI"""
    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.sizeHintDyber = sizeHintDyber
        self.setObjectName("FocusPanel")
        #settings.current_tm_option = 'pomodoro'
        self.n_pomo = 0
        self.min_focus = 0

        self.__init_UI()
        self.__connectSignalToSlot()


    def __init_UI(self):

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(PANEL_W, PANEL_H))
        self.setMaximumSize(QSize(PANEL_W, PANEL_H))
        
        self.verticalLayout_3 = QVBoxLayout(self)
        self.verticalLayout_3.setSizeConstraint(QLayout.SetDefaultConstraint)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        spacerItem1 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)

        # Top Bar -----------------------------------------------------------------------------------------------------
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(5, -1, -1, -1)

        # Panel Icon
        self.focusCardIcon = IconWidget(self)
        self.focusCardIcon.setMinimumSize(QSize(20, 20))
        self.focusCardIcon.setMaximumSize(QSize(20, 20))
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(os.path.join(basedir,'res/icons/Dashboard/timer.svg')), QIcon.Normal, QIcon.Off)
        self.focusCardIcon.setIcon(icon1)

        # Panel TopBar Title
        self.focusPeriodLabel = StrongBodyLabel(self)
        self.focusPeriodLabel.setText(self.tr("Focus Session"))

        self.manualButton = TransparentToolButton(self)
        self.manualButton.setIcon(os.path.join(basedir,'res/icons/Dashboard/manual.svg'))
        self.manualButton.setFixedSize(20,20)
        self.manualButton.setIconSize(QSize(20,20))

        self.horizontalLayout_2.addWidget(self.focusCardIcon)
        spacerItem = QSpacerItem(2, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.horizontalLayout_2.addWidget(self.focusPeriodLabel)
        spacerItem2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.horizontalLayout_2.addWidget(self.manualButton, 0, Qt.AlignRight)
        
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)

        # Panel Title -------------------------------------------------------------------------------------------------
        self.prepareFocusLabel = SubtitleLabel(self.tr("Lauch Focus"), self)
        self.prepareFocusLabel.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.prepareFocusLabel)
        spacerItem4 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem4)


        # Timer Picker ------------------------------------------------------------------------------------------------
        self.timePicker = TimePicker(self)
        self.timePicker.setSecondVisible(False)

        self.verticalLayout.addWidget(self.timePicker, 0, Qt.AlignHCenter)
        spacerItem5 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem5)


        # skip Relax CheckBox
        self.pomodoroCheckBox = CheckBox(self)
        self.pomodoroCheckBox.setEnabled(True)
        self.pomodoroCheckBox.setText(self.tr("Break by Pomodoro"))

        self.verticalLayout.addWidget(self.pomodoroCheckBox, 0, Qt.AlignHCenter)
        spacerItem7 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem7)

        # Bottom Hint Label
        self.bottomHintLabel = BodyLabel(self)
        self.bottomHintLabel.setAlignment(Qt.AlignCenter)
        self.bottomHintLabel.setText(self.tr("You will not have break time."))

        self.verticalLayout.addWidget(self.bottomHintLabel, 0, Qt.AlignHCenter)
        spacerItem6 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem6)

        # Buttons ------------------------------------------------------------------------------------
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(5, -1, -1, -1)

        self.startFocusButton = PushButton(self)
        self.startFocusButton.setAutoDefault(True)
        self.startFocusButton.setText(self.tr("Start"))
        self.startFocusButton.setIcon(FIF.PLAY)
        self.startFocusButton.setFixedWidth(110)

        self.cancelFocusButton = PushButton(self)
        self.cancelFocusButton.setAutoDefault(False)
        self.cancelFocusButton.setText(self.tr("Cancel"))
        self.cancelFocusButton.setIcon(os.path.join(basedir,'res/icons/Dashboard/stop.svg'))
        self.cancelFocusButton.setFixedWidth(110)
        self.cancelFocusButton.setDisabled(True)

        
        spacerItem9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem9)
        self.horizontalLayout_3.addWidget(self.startFocusButton)
        spacerItem10 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem10)
        self.horizontalLayout_3.addWidget(self.cancelFocusButton)
        spacerItem11 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem11)

        self.verticalLayout.addLayout(self.horizontalLayout_3) #, 0, Qt.AlignHCenter)
        spacerItem8 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem8)
        self.verticalLayout_3.addLayout(self.verticalLayout)


    def __connectSignalToSlot(self):

        self.manualButton.clicked.connect(self._showTips)
        self.pomodoroCheckBox.stateChanged.connect(self._checkClicked)
        self.startFocusButton.clicked.connect(self._startClicked)
        self.cancelFocusButton.clicked.connect(self._cancelClicked)


    def _showTips(self):
        Flyout.create(
            target=self.manualButton,
            icon=os.path.join(basedir,'res/icons/Dashboard/info.svg'),
            title=self.tr('Usage Help'),
            content=self.tr("""Please set up a period to focus on the work/study.

Once this focus task is done, you will get coin rewarded.

Even if you stopped the clock in the middle, you will still get rewarded accordingly.

Choose 'Break by Pomodoro' will adjust the time to fit closest number of pomodoro.
Everytime you finish a 25min Pomodoro, you get coin rewarded"""),
            #isClosable=True,
            #tailPosition=TeachingTipTailPosition.BOTTOM,
            #duration=-1,
            parent=self
        )


    def _checkClicked(self, state):
        if self.pomodoroCheckBox.isChecked():
            self.bottomHintLabel.setText(self.tr("You will take a 5-minute break every 25 minutes."))
            self._adjust_time_to_pomodoro()
        else:
            self.bottomHintLabel.setText(self.tr("You will not have break time."))


    def _adjust_time_to_pomodoro(self):
        time_picked = self.timePicker.getTime()
        hour_picked, minute_picked = time_picked.hour(), time_picked.minute()
        if hour_picked == -1 or minute_picked == -1:
            return

        time_total = 60*hour_picked + minute_picked
        n_pomo = (time_total+5) // 30
        n_pomo = min(max(1,n_pomo), 48)

        new_total = n_pomo*30 - 5
        new_hour = new_total // 60
        new_minute = new_total % 60

        time_adjusted = QTime(new_hour, new_minute)
        self.timePicker.setTime(time_adjusted)


    def _startClicked(self):
        if self.pomodoroCheckBox.isChecked():
            self._adjust_time_to_pomodoro()
            self._start_Pomodoro()
        else:
            self._start_Focus()


    def _start_Pomodoro(self):
        time_picked = self.timePicker.getTime()
        hour_picked, minute_picked = time_picked.hour(), time_picked.minute()
        n_pomo = (60*hour_picked + minute_picked + 5) // 30
        if n_pomo <= 0:
            return

        # UI changes
        self.prepareFocusLabel.setText(self.tr("Pomodoro Time Remaining"))
        self.timePicker.setDisabled(True)
        self.pomodoroCheckBox.setDisabled(True)
        self.startFocusButton.setDisabled(True)
        self.cancelFocusButton.setDisabled(False)

        # Send Signal to start Pomodoro
        self.start_pomodoro.emit(n_pomo)
        self.n_pomo = n_pomo


    def _start_Focus(self):
        time_picked = self.timePicker.getTime()
        hour_picked, minute_picked = time_picked.hour(), time_picked.minute()

        if hour_picked==-1 or minute_picked == -1:
            return

        if hour_picked + minute_picked <= 0:
            return

        # UI changes
        self.prepareFocusLabel.setText(self.tr("Focus Time Remaining"))
        self.timePicker.setDisabled(True)
        self.pomodoroCheckBox.setDisabled(True)
        self.startFocusButton.setDisabled(True)
        self.cancelFocusButton.setDisabled(False)

        # Send Signal to start Focus
        self.start_focus.emit("range", hour_picked, minute_picked)
        self.min_focus = hour_picked*60 + minute_picked


    def taskFinished(self):
        # Calcualte reward
        if self.pomodoroCheckBox.isChecked():
            self.reward_coins(30)
            
        else:
            self.reward_coins(self.min_focus)
            
        self._endTask_UIChanges()


    def _cancelClicked(self):
        
        if self.pomodoroCheckBox.isChecked():
            self.pomodoroCanceled()
            
        else:
            self.focusCanceled()
            
        self._endTask_UIChanges()


    def pomodoroCanceled(self):
        # Stop signal to Timer
        self.cancel_pomodoro.emit()

        # Calcualte reward
        time_left = self.timePicker.getTime()
        hour_left, minute_left = time_left.hour(), time_left.minute()
        half_done_pomo_minutes = self.n_pomo*25 + 5*(self.n_pomo-1) - hour_left*60 - minute_left
        if half_done_pomo_minutes >= 0:
            self.reward_coins(half_done_pomo_minutes)


    def focusCanceled(self):
        # Stop signal to Timer
        self.cancel_focus.emit()

        # Calcualte reward
        time_left = self.timePicker.getTime()
        hour_left, minute_left = time_left.hour(), time_left.minute()
        half_done_focus_minutes = self.min_focus - hour_left*60 - minute_left
        if half_done_focus_minutes >= 0:
            self.reward_coins(half_done_focus_minutes)


    def _endTask_UIChanges(self):
        # UI Changes
        self.prepareFocusLabel.setText(self.tr("Lauch Focus"))
        self.timePicker.setDisabled(False)
        self.pomodoroCheckBox.setDisabled(False)
        self.startFocusButton.setDisabled(False)
        self.cancelFocusButton.setDisabled(True)

        # Property reset
        self.n_pomo = 0
        self.min_focus = 0


    def update_Timer(self):

        time_picked = self.timePicker.getTime()
        hour_picked, minute_picked = time_picked.hour(), time_picked.minute()

        if minute_picked == 0:
            hour_picked -= 1
            minute_picked = 59
        else:
            minute_picked -= 1

        time_updated = QTime(hour_picked, minute_picked)
        self.timePicker.setTime(time_updated)
        self.addProgress.emit()


    def single_pomo_done(self):
        if self.pomodoroCheckBox.isChecked():
            self.n_pomo -= 1
            self.reward_coins(30)


    def reward_coins(self, nminutes):
        #print(f"Reward {nminutes} minutes")
        if nminutes <= 0:
            return
        n_coins = nminutes*25
        self.addCoins.emit(n_coins, True, False, self.tr("Focus task reward:"))


        


class ProgressPanel(CardWidget):
    addCoins = Signal(int, bool, bool, str, name="addCoins")

    """Focus Panel UI"""
    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.sizeHintDyber = sizeHintDyber
        self.setObjectName("ProgressPanel")
        self.daily_goal = 180
        self.date_today = settings.task_data.taskData['history'][-1][0]
        self.goal_met = settings.task_data.taskData['goal_completed']

        self.__init_ui()
        self._loadValues()
        self.__connectSignalToSlot()


    def __init_ui(self):

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(PANEL_W, PANEL_H+25))
        self.setMaximumSize(QSize(PANEL_W, PANEL_H+25)) 

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSizeConstraint(QLayout.SetMinAndMaxSize)

        # Top Bar -----------------------------------------------------------------------------------------------------
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.setContentsMargins(5, -1, -1, -1)

        # Panel Icon
        self.progressIcon = IconWidget(self)
        self.progressIcon.setMinimumSize(QSize(20, 20))
        self.progressIcon.setMaximumSize(QSize(20, 20))
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(os.path.join(basedir,'res/icons/Dashboard/goal.svg')), QIcon.Normal, QIcon.Off)
        self.progressIcon.setIcon(icon1)

        # Panel TopBar Title
        self.dailyProgressLabel = StrongBodyLabel(self)
        self.dailyProgressLabel.setText(self.tr("Daily Goal"))

        self.editButton = TransparentToolButton(self)
        self.editButton.setIcon(os.path.join(basedir,'res/icons/Dashboard/edit.svg'))
        self.editButton.setFixedSize(20,20)
        self.editButton.setIconSize(QSize(20,20))

        self.horizontalLayout_1.addWidget(self.progressIcon)
        spacerItem1 = QSpacerItem(2, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem1)
        self.horizontalLayout_1.addWidget(self.dailyProgressLabel)
        spacerItem2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem2)
        self.horizontalLayout_1.addWidget(self.editButton, 0, Qt.AlignRight)        

        self.verticalLayout_2.addLayout(self.horizontalLayout_1)
        spacerItem3 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem3)



        # Progress Panel -----------------------------------------------------------------------------------------------------

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetMinAndMaxSize)

        # Yesterday
        self.verticalLayout_3 = QVBoxLayout()
        
        self.yesterdayLabel = BodyLabel(self)
        self.yesterdayLabel.setText(self.tr("Yesterday"))

        self.yesterdayTimeLabel = LargeTitleLabel(self)
        self.yesterdayTimeLabel.setText("0")

        self.hourLabel1 = BodyLabel(self)
        self.hourLabel1.setText(self.tr("Minutes"))

        spacerItem4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem4)
        self.verticalLayout_3.addWidget(self.yesterdayLabel, 0, Qt.AlignHCenter | Qt.AlignVCenter)
        self.verticalLayout_3.addWidget(self.yesterdayTimeLabel, 0, Qt.AlignHCenter | Qt.AlignVCenter)
        self.verticalLayout_3.addWidget(self.hourLabel1, 0, Qt.AlignHCenter | Qt.AlignVCenter)
        spacerItem5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem5)
        self.horizontalLayout_2.addLayout(self.verticalLayout_3)


        # Target and Progress
        self.verticalLayout_4 = QVBoxLayout()
        spacerItem6 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem6)

        self.targetLabel = SubtitleLabel(self)
        self.targetLabel.setAlignment(Qt.AlignCenter)
        self.targetLabel.setText(self.tr("Progress"))

        self.progressRing = ProgressRing(self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.progressRing.sizePolicy().hasHeightForWidth())
        self.progressRing.setSizePolicy(sizePolicy)
        self.progressRing.setMinimumSize(QSize(150, 150))
        self.progressRing.setMaximumSize(QSize(220, 220))
        font = QFont()
        font.setFamilies(['Segoe UI', 'Microsoft YaHei', 'PingFang SC'])
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(QFont.Weight.Medium)
        self.progressRing.setFont(font)

        self.daily_goal = settings.task_data.taskData['goal']
        self.progressRing.setMaximum(self.daily_goal)
        
        self.progressRing.setAlignment(Qt.AlignCenter)
        self.progressRing.setTextVisible(True)
        self.progressRing.setOrientation(Qt.Orientation.Horizontal)
        self.progressRing.setTextDirection(QProgressBar.Direction.TopToBottom)
        self.progressRing.setUseAni(True)
        self.progressRing.setStrokeWidth(15)

        self.finishTimeLabel = BodyLabel(self)
        self.finishTimeLabel.setText(self.tr("Daily Goal: 180 Minutes"))

        self.verticalLayout_4.addWidget(self.targetLabel, 0, Qt.AlignHCenter | Qt.AlignVCenter)
        spacerItem11 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout_4.addItem(spacerItem11)
        self.verticalLayout_4.addWidget(self.progressRing, 0, Qt.AlignHCenter | Qt.AlignVCenter)
        spacerItem7 = QSpacerItem(20, 3, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout_4.addItem(spacerItem7)
        self.verticalLayout_4.addWidget(self.finishTimeLabel, 0, Qt.AlignHCenter)
        spacerItem8 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem8)
        self.verticalLayout_4.setStretch(2, 1)
        self.horizontalLayout_2.addLayout(self.verticalLayout_4)


        # Tracking
        self.verticalLayout_5 = QVBoxLayout()
        spacerItem9 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem9)

        self.continousDaysLabel = BodyLabel(self)
        self.continousDaysLabel.setText(self.tr("Completed"))

        self.compianceDayLabel = LargeTitleLabel(self)
        self.compianceDayLabel.setText("5")

        self.dayLabel = BodyLabel(self)
        self.dayLabel.setText(self.tr("Days in a row"))

        self.verticalLayout_5.addWidget(self.continousDaysLabel, 0, Qt.AlignHCenter | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.compianceDayLabel, 0, Qt.AlignHCenter)
        self.verticalLayout_5.addWidget(self.dayLabel, 0, Qt.AlignHCenter)
        spacerItem10 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem10)

        self.horizontalLayout_2.addLayout(self.verticalLayout_5)
        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 2)
        self.horizontalLayout_2.setStretch(2, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.verticalLayout_2)

        # Editor -------------------------------------------------------------------------
        title = self.tr("Set The Goal")
        content = self.tr("""Upon reaching your set time, you'll be rewarded with coins. Earn extra rewards by completing certain streaks of consecutive days!""")
        icon = os.path.join(basedir,'res/icons/Dashboard/edit.svg')
        self.goalEditor = GoalFlyoutView(title, content, icon,
                                    isClosable=True, parent=None)
        

    def __connectSignalToSlot(self):
        self.editButton.clicked.connect(self._showFlyout)
        self.goalEditor.goalChanged.connect(self.updateGoal)


    def _showFlyout(self):
        
        Flyout.make(self.goalEditor, self.editButton, self.window(),
                    FlyoutAnimationType.SLIDE_RIGHT, isDeleteOnClose=False)


    def _loadValues(self):

        # Yesterday
        progress_yesterday = settings.task_data.yesterday
        self.yesterdayTimeLabel.setText(f"{progress_yesterday:.0f}")

        # Days-in-a-row
        self.compianceDayLabel.setText(f"{settings.task_data.taskData['n_days']}")

        # Goals
        self.finishTimeLabel.setText(self.tr("Daily Goal:") + " " +  f"{self.daily_goal:.0f} " + self.tr("Minutes"))

        # Daily Progress
        progress_today = settings.task_data.taskData['history'][-1][1]
        self.progressRing.setFormat(f"{progress_today:.0f}" + " " + self.tr("Minutes"))
        self.progressRing.setValue(min(self.daily_goal, progress_today))


    def updateProgress(self, add_value=1):
        # Check if date changed
        self.checkDate()

        # Calculate new value
        newVal = settings.task_data.taskData['history'][-1][1] + add_value

        # Update UI
        #print('check', add_value, newVal, settings.task_data.taskData['history'][-1][1])
        self.progressRing.setFormat(f"{newVal}" + " " + self.tr("Minutes"))
        self.progressRing.setValue(min(self.daily_goal, newVal))

        # Update settings.task_data
        settings.task_data.update_progress(newVal) #taskData['history'][-1][1] = newVal
        settings.task_data.save_data()

        # Check if goal met
        if not self.goal_met:
            self.checkGoal()


    def updateGoal(self, new_qtime):
        # check if date changed
        self.checkDate()

        # update self.daily_goal
        new_goal = TimeConverter(new_qtime, from_format='qtime', to_format='min')
        self.daily_goal = new_goal

        # update settings.task_data
        settings.task_data.taskData['goal'] = new_goal
        settings.task_data.save_data()

        # update UI
        self.progressRing.setMaximum(new_goal)
        progress_today = settings.task_data.taskData['history'][-1][1]
        self.progressRing.setFormat(f"{progress_today:.0f}" + " " + self.tr("Minutes"))
        self.progressRing.setValue(min(new_goal, progress_today))
        self.finishTimeLabel.setText(self.tr("Daily Goal:") + " " +  f"{self.daily_goal:.0f} " + self.tr("Minutes"))

        # check if goal met
        if not self.goal_met:
            self.checkGoal()


    def checkDate(self):
        now = datetime.datetime.now()
        date_now = f"{now.year}-{now.month}-{now.day}"
        if self.date_today != date_now:

            # Update attributes
            self.date_today = date_now
            self.goal_met = False

            # Update task data
            settings.task_data.checkDate()
            settings.task_data.save_data()

            # Update UI
            self._loadValues()


    def checkGoal(self):
        progress_today = settings.task_data.taskData['history'][-1][1]
        if progress_today >= self.daily_goal:
            self.goal_met = True
            settings.task_data.taskData['goal_completed'] = True
            settings.task_data.taskData['n_days'] += 1
            settings.task_data.save_data()
            self.compianceDayLabel.setText(f"{settings.task_data.taskData['n_days']}")
            self.getReward()


    def getReward(self):
        # Need to optimize the reward formula
        goal = self.daily_goal
        n_days = settings.task_data.taskData['n_days']

        # Daily Goal Reward
        n_coins = int(25*goal)
        self.addCoins.emit(n_coins, True, False, self.tr("Daily Goal Completed:"))

        # Consecutive days reward
        n_coins = 1000 * n_days
        self.addCoins.emit(n_coins, True, False, f'{n_days} '+self.tr("days in a row reward:"))




class GoalFlyoutView(FlyoutViewBase):
    """ Daily Goal Flyout view """

    closed = Signal()
    goalChanged = Signal(QTime)

    def __init__(self, title: str, content: str, icon: str = None,
                 isClosable=False, parent=None):
        super().__init__(parent=parent)

        self.icon = icon
        self.title = title
        self.content = content
        self.isClosable = isClosable

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setContentsMargins(5, -1, -1, -1)
        #self.viewLayout = QVBoxLayout()
        #self.widgetLayout = QVBoxLayout()

        self.__initWidgets()

    def __initWidgets(self):

        # Title
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText(self.title)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setVisible(bool(self.title))

        # Goal Time Picker
        self.timePicker = TimePicker(self)
        self.timePicker.setSecondVisible(False)
        self.setPicker()
        self.timePicker.timeChanged.connect(self.goalChanged)

        # Hint

        # Instruction
        self.contentLabel = BodyLabel(self.content, self)
        #self.contentLabel.setAlignment(Qt.AlignCenter)
        self.contentLabel.setWordWrap(True)
        self.contentLabel.setProperty("lightColor", QtGui.QColor(96, 96, 96))
        self.contentLabel.setProperty("darkColor", QtGui.QColor(206, 206, 206))
        self.contentLabel.setVisible(True)
        
        # Set style
        #self.titleLabel.setObjectName('titleLabel')
        ##self.contentLabel.setObjectName('contentLabel')
        FluentStyleSheet.TEACHING_TIP.apply(self)

        self.__initLayout()

    def __initLayout(self):
        # Header
        spacerItem1 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.vBoxLayout.addItem(spacerItem1)
        self.vBoxLayout.addWidget(self.titleLabel)
        spacerItem3 = QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.vBoxLayout.addItem(spacerItem3)
        

        self.vBoxLayout.addWidget(self.timePicker, 0, Qt.AlignHCenter)
        spacerItem4 = QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.vBoxLayout.addItem(spacerItem4)


        # add instruction
        self.vBoxLayout.addWidget(self.contentLabel)
        spacerItem5 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.vBoxLayout.addItem(spacerItem5)


    def setPicker(self):
        daily_goal = settings.task_data.taskData['goal']
        time_adjusted = TimeConverter(daily_goal, from_format='min', to_format='qtime')
        self.timePicker.setTime(time_adjusted)

    def showEvent(self, e):
        super().showEvent(e)
        self.adjustSize()






class TaskPanel(CardWidget):
    """To-do Task Panel UI"""

    addCoins = Signal(int, bool, bool, str, name='addCoins')

    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.sizeHintDyber = sizeHintDyber
        self.setObjectName("TaskPanel")
        self.taskCards = {}

        self.__init_ui()
        self.__connectSignalToSlot()


    def __init_ui(self):

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setFixedSize(QSize(PANEL_W, 200))

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)


        # Top Bar -----------------------------------------------------------------------------------------------------
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.setContentsMargins(5, -1, -1, -1)

        # Panel Icon
        self.taskIcon = IconWidget(self)
        self.taskIcon.setMinimumSize(QSize(20, 20))
        self.taskIcon.setMaximumSize(QSize(20, 20))
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(os.path.join(basedir,'res/icons/Dashboard/dailyTask.svg')), QIcon.Normal, QIcon.Off)
        self.taskIcon.setIcon(icon1)

        # Panel TopBar Title
        self.taskLabel = StrongBodyLabel(self)
        self.taskLabel.setText(self.tr("To-do Tasks"))

        '''
        self.addButton = TransparentToolButton(self)
        self.addButton.setIcon(os.path.join(basedir,'res/icons/Dashboard/add.svg'))
        self.addButton.setFixedSize(20,20)
        self.addButton.setIconSize(QSize(20,20))
        #self.addButton.clicked.connect()
        

        self.progressButton = TransparentToolButton(self)
        self.progressButton.setIcon(os.path.join(basedir,'res/icons/Dashboard/progressTask.svg'))
        self.progressButton.setFixedSize(20,20)
        self.progressButton.setIconSize(QSize(20,20))
        '''

        self.progressLabel_1 = BodyLabel(self)
        self.progressLabel_1.setText(self.tr("Completed "))
        self.progressLabel_2 = StrongBodyLabel(self)
        self.progressLabel_2.setText(str(settings.task_data.taskData['n_tasks']))
        self.progressLabel_3 = BodyLabel(self)
        self.progressLabel_3.setText(self.tr(" tasks"))

        self.horizontalLayout_1.addWidget(self.taskIcon)
        spacerItem1 = QSpacerItem(2, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem1)
        self.horizontalLayout_1.addWidget(self.taskLabel)
        spacerItem2 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem2)
        #self.horizontalLayout_1.addWidget(self.addButton, 0, Qt.AlignRight)

        self.horizontalLayout_1.addWidget(self.progressLabel_1)
        spacerItem3 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem3)
        self.horizontalLayout_1.addWidget(self.progressLabel_2)
        spacerItem7 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem7)
        self.horizontalLayout_1.addWidget(self.progressLabel_3, 0, Qt.AlignRight)

        self.verticalLayout.addLayout(self.horizontalLayout_1)
        spacerItem3 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem3)

        # Add task bar
        self.emptyCard = EmptyTaskCard()
        self.verticalLayout.addWidget(self.emptyCard)
        spacerItem6 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem6)


        # On-going tabs
        self.verticalLayout_1 = QVBoxLayout()
        self.verticalLayout_1.setContentsMargins(5, -1, -1, -1)
        self.hintLabel_1 = BodyLabel(self)
        self.hintLabel_1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.hintLabel_1.setWordWrap(True)
        self.hintLabel_1.setProperty("lightColor", QtGui.QColor(96, 96, 96))
        self.hintLabel_1.setProperty("darkColor", QtGui.QColor(206, 206, 206))
        self.hintLabel_1.setText(self.tr("On-Going"))
        self.verticalLayout_1.addWidget(self.hintLabel_1)
        self.verticalLayout_1.addWidget(HorizontalSeparator(QColor(20,20,20,125), 1))

        # Completed tabs
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setContentsMargins(5, -1, -1, -1)
        self.hintLabel_2 = BodyLabel(self)
        self.hintLabel_2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.hintLabel_2.setWordWrap(True)
        self.hintLabel_2.setProperty("lightColor", QtGui.QColor(96, 96, 96))
        self.hintLabel_2.setProperty("darkColor", QtGui.QColor(206, 206, 206))
        self.hintLabel_2.setText(self.tr("Completed"))
        self.verticalLayout_2.addWidget(self.hintLabel_2)
        self.verticalLayout_2.addWidget(HorizontalSeparator(QColor(20,20,20,125), 1))

        # Initialize task cards
        for task_id, task_text in settings.task_data.taskData['tasks_todo'].items():
            self.addTodoCard(task_text, task_id)
             
        self.verticalLayout.addLayout(self.verticalLayout_1)
        spacerItem4 = QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem4)

        
        for task_id, task_text in settings.task_data.taskData['tasks_done'].items():
            self.addDoneCard(task_text, task_id)
    
        self.verticalLayout.addLayout(self.verticalLayout_2)
        spacerItem5 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem5)

        self.adjustSize()

    def adjustSize(self):
        base_height = 200
        nCards = len(settings.task_data.taskData['tasks_todo']) + len(settings.task_data.taskData['tasks_done'])
        h = nCards*(TASKCARD_H+5) + base_height + 10
        self.setFixedHeight(h)

    def __connectSignalToSlot(self):
        self.emptyCard.new_task.connect(self.addTodoCard)


    def addTodoCard(self, task_text, task_id=None):
        if not task_id:
            task_id = str(uuid.uuid4())
            # save new task
            settings.task_data.taskData['tasks_todo'][task_id] = task_text
            settings.task_data.save_data()

        card = TaskCard(task_id, task_text)
        self.verticalLayout_1.insertWidget(2, card)
        self.taskCards[task_id] = card
        self.adjustSize()

        card.completed.connect(self._onTaskCompleted)
        card.deleted.connect(self._onTaskDeleted)

    def addDoneCard(self, task_text, task_id=None):
        if not task_id:
            settings.task_data.taskData['tasks_done'][task_id] = task_text
            settings.task_data.save_data()

        card = TaskCard(task_id, task_text, True)
        self.verticalLayout_2.insertWidget(2, card)
        self.taskCards[task_id] = card
        self.adjustSize()

        card.deleted.connect(self._onTaskDeleted)

    def _onTaskCompleted(self, task_id):
        # change and save task data
        task_text = settings.task_data.taskData['tasks_todo'][task_id]
        del settings.task_data.taskData['tasks_todo'][task_id]
        settings.task_data.taskData['tasks_done'][task_id] = task_text
        settings.task_data.taskData['n_tasks'] += 1
        settings.task_data.save_data()

        # move widget from todo to done
        card = self.taskCards[task_id]
        card.setParent(None)
        self.verticalLayout_2.insertWidget(2, card)

        # update UI
        self.progressLabel_2.setText(str(settings.task_data.taskData['n_tasks']))

        # submit reward
        self.getReward()


    def _onTaskDeleted(self, task_id, done):
        # change and save task data
        if done:
            task_text = settings.task_data.taskData['tasks_done'][task_id]
            del settings.task_data.taskData['tasks_done'][task_id]
        else:
            task_text = settings.task_data.taskData['tasks_todo'][task_id]
            del settings.task_data.taskData['tasks_todo'][task_id]
        settings.task_data.save_data()

        # move widget from todo to done
        if done:
            card = self.taskCards[task_id]
        else:
            card = self.taskCards[task_id]
        card.setParent(None)
        card.deleteLater()
        self.adjustSize()

    def getReward(self):
        self.addCoins.emit(settings.SINGLETASK_REWARD, True, False, 
                           self.tr("Task completed! "))
        if settings.task_data.taskData['n_tasks'] % 5 == 0:
            self.addCoins.emit(settings.FIVETASK_REWARD, True, False, 
                           self.tr("You completed another 5 tasks! "))


        


TASKCARD_W, TASKCARD_H = 390, 40

class TaskCard(SimpleCardWidget):

    completed = Signal(str, name='completed')
    deleted = Signal(str, bool, name='deleted')

    def __init__(self, task_id, text, done=False, parent=None):

        super().__init__(parent)
        self.setBorderRadius(5)

        self.task_id = task_id
        self.task_text = text
        self.done = done

        self.hBoxLayout = QHBoxLayout(self)
        #self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setContentsMargins(10, 5, 5, 5)
        self.hBoxLayout.setSpacing(0)

        self.setFixedSize(TASKCARD_W, TASKCARD_H)

        self._init_Card()

    def _init_Card(self):
        self.checkBox = CheckBox("")
        self.checkBox.setFixedSize(20, 20)
        self.taskLabel = BodyLabel(self.task_text)
        self.taskLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if self.done:
            self._taskDone()
        self.checkBox.stateChanged.connect(self._checkClicked)

        #self.editBtn = TransparentToolButton(self)
        #self.editBtn.setIcon(os.path.join(basedir,'res/icons/Dashboard/edit.svg'))
        #self.editBtn.setFixedSize(20,20)
        #self.editBtn.setIconSize(QSize(20,20))

        self.deleteBtn = TransparentToolButton(self)
        self.deleteBtn.setIcon(os.path.join(basedir,'res/icons/Dashboard/delete.svg'))
        self.deleteBtn.setFixedSize(20,20)
        self.deleteBtn.setIconSize(QSize(20,20))
        self.deleteBtn.clicked.connect(self._deleteClicked)

        self.hBoxLayout.addWidget(self.checkBox, 0, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem2 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.hBoxLayout.addItem(spacerItem2)
        self.hBoxLayout.addWidget(self.taskLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem1 = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.hBoxLayout.addItem(spacerItem1)

        #self.hBoxLayout.addWidget(self.editBtn, 0, Qt.AlignRight | Qt.AlignVCenter)
        #spacerItem3 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        #self.hBoxLayout.addItem(spacerItem3)
        self.hBoxLayout.addWidget(self.deleteBtn, 0, Qt.AlignRight | Qt.AlignVCenter)


    def _checkClicked(self, state):
        if self.checkBox.isChecked():
            self.completed.emit(self.task_id)
            self._taskDone()

    def _taskDone(self):
        self.done = True
        self.checkBox.setChecked(True)
        self.checkBox.setEnabled(False)

        self.taskLabel.setTextColor(QColor(140, 140, 140))
        font = self.taskLabel.font()
        font.setStrikeOut(True)
        self.taskLabel.setFont(font)
        self.taskLabel.setText(self.task_text)
        self.taskLabel.update()


    def _deleteClicked(self):
        self.deleted.emit(self.task_id, self.done)




class EmptyTaskCard(QWidget):
    new_task = Signal(str, name="new_task")

    def __init__(self, parent=None):

        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(10, 5, 5, 5)
        self.hBoxLayout.setSpacing(5)

        self.setFixedSize(TASKCARD_W, TASKCARD_H)

        self._init_Empty()

    def _init_Empty(self):
        # LineEdit
        self.taskEdit = LineEdit(self)
        self.taskEdit.setClearButtonEnabled(True)
        self.taskEdit.setPlaceholderText(self.tr("Add New Task"))
        self.taskEdit.setFixedWidth(TASKCARD_W-50)
        #self.coinAmount.setEnabled(False)
        # Yes button
        self.yesBtn = TransparentToolButton(self)
        self.yesBtn.setIcon(FIF.ACCEPT)
        self.yesBtn.setFixedSize(20,20)
        self.yesBtn.setIconSize(QSize(18,18))
        self.yesBtn.clicked.connect(self.submit_task)

        self.hBoxLayout.addWidget(self.taskEdit, 0, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem2 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.hBoxLayout.addItem(spacerItem2)
        self.hBoxLayout.addWidget(self.yesBtn, 0, Qt.AlignRight | Qt.AlignVCenter)
        spacerItem3 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.hBoxLayout.addItem(spacerItem3)

    def submit_task(self):
        task_text = self.taskEdit.text()
        if task_text:
            self.new_task.emit(task_text)
            self.taskEdit.setText('')





