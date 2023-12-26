# coding:utf-8
import os
import sys
import math
import json
import glob
import datetime

from typing import Union, List

from PySide6 import QtGui
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QObject, QEvent, QModelIndex, QRectF, QRect
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QProgressBar, QFrame, QStyleOptionViewItem,
                             QSizePolicy, QStackedWidget)
from PySide6.QtGui import (QPixmap, QImage, QImageReader, QPainter, QBrush, QPen, QColor, QIcon,
                        QFont, QPainterPath, QCursor, QAction, QFontMetrics)

from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCard, Slider, FluentIconBase, SimpleCardWidget, PushButton
from qfluentwidgets import (SegmentedToolWidget, TransparentToolButton,
                            InfoBar, InfoBarPosition, InfoBarIcon, 
                            RoundMenu, FluentIcon, Action, AvatarWidget, BodyLabel, ToolButton,
                            HyperlinkButton, CaptionLabel, setFont, setTheme, Theme, isDarkTheme,
                            FluentStyleSheet, FlowLayout, IconWidget, getFont,
                            TransparentDropDownToolButton, DropDownPushButton,
                            ScrollArea, PrimaryPushButton, LineEdit,
                            FlipImageDelegate, HorizontalPipsPager, HorizontalFlipView,
                            TextWrap, InfoBadge, PushButton, ScrollArea, ImageLabel, ToolTipFilter)

import DyberPet.settings as settings
from DyberPet.DyberSettings.custom_utils import AvatarImage

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

    def addNote(self, icon: QImage, content: str):
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
    def __init__(self, icon: QImage, time: str, content: str):
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
        Icon.setPixmap(QPixmap.fromImage(icon))

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
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/HP_icon.png'))
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(QPixmap.fromImage(image))
        self.hpicon.setAlignment(Qt.AlignCenter)

        self.hp_tier = settings.pet_data.hp_tier
        hpText = f"{settings.TIER_NAMES[self.hp_tier]}"
        self.statusLabel = CaptionLabel(hpText, self)
        setFont(self.statusLabel, 12, QFont.DemiBold)
        self.statusLabel.setFixedSize(55,16)

        self.hp_tiers = settings.HP_TIERS
        self.statusBar = QProgressBar(self)
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
        stylesheet = f'''QProgressBar {{
                                        font-family: "Segoe UI";
                                        border: 1px solid #08060f;
                                        border-radius: 7px;
                                      }}
                        QProgressBar::chunk {{
                                        background-color: {colors[settings.pet_data.hp_tier]};
                                        border-radius: 5px;}}'''
        self.statusBar.setStyleSheet(stylesheet)



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
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/Fv_icon.png'))
        fvicon.setScaledContents(True)
        fvicon.setPixmap(QPixmap.fromImage(image))
        fvicon.setAlignment(Qt.AlignCenter)

        fv = settings.pet_data.fv
        self.fv_lvl = settings.pet_data.fv_lvl
        fvText = f"Lv{self.fv_lvl}"
        self.statusLabel = CaptionLabel(fvText, self)
        setFont(self.statusLabel, 12, QFont.DemiBold)
        self.statusLabel.setFixedSize(55,16)

        self.statusBar = QProgressBar(self)
        self._setBarStyle()
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


    def _setBarStyle(self):
        stylesheet = '''QProgressBar {
                                        font-family: "Segoe UI";
                                        border: 1px solid #08060f;
                                        border-radius: 7px;
                                      }
                        QProgressBar::chunk {
                                        background-color: #F4665C;
                                        border-radius: 5px;}'''
        self.statusBar.setStyleSheet(stylesheet)



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
        self.setPixmap(QPixmap.fromImage(self.image))

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
        self.setPixmap(QPixmap.fromImage(self.image))

    def removeBuff(self, idx=None):
        self.buff_num += -1
        if self.buff_num == 0:
            self.deleteBuff()
        else:
            self.setPixmap(QPixmap.fromImage(self.image))

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
        image = QImage()
        image.load(os.path.join(basedir, 'res/icons/Dashboard/coin.svg'))
        self.icon.setScaledContents(True)
        self.icon.setPixmap(QPixmap.fromImage(image))
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
            self.setPixmap(QPixmap.fromImage(self.image))
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
        self.setPixmap(QPixmap.fromImage(self.image))
        self.setToolTip(item_config['hint'])
        self.item_type = self.item_config.get('item_type', 'consumable')
        self._setQss(self.item_type)

    def addItem(self, add_n):
        self.item_num += add_n
        self.setPixmap(QPixmap.fromImage(self.image))

    def consumeItem(self):
        if self.item_type in ['collection', 'dialogue', 'subpet']:
            self.item_inuse = not self.item_inuse
        else:
            self.item_num += -1
            if self.item_num == 0:
                self.removeItem()
            else:
                self.setPixmap(QPixmap.fromImage(self.image))

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

        elif self.empty_cell:
            item_index = self.empty_cell[0]
            self.empty_cell = self.empty_cell[1:]
            self.cells_dict[item_index].registItem(self.items_data.item_dict[item_name], n_items)

        else:
            item_index = len(self.cells_dict)
            self._addItemCard(item_index, item_name, n_items)

        self.item_note.emit(item_name, '[%s] +%s'%(item_name, n_items))
        self.item_drop.emit(item_name)
        # change pet_data
        settings.pet_data.change_item(item_name, item_change=n_items) 

    