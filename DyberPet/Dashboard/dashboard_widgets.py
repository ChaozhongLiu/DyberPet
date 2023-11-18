# coding:utf-8
import os
import sys
import math
import json
import glob
import datetime

from typing import Union, List

from PySide6 import QtGui
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QObject, QEvent, QModelIndex, QRectF
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QProgressBar, QFrame, QStyleOptionViewItem,
                             QSizePolicy)
from PySide6.QtGui import (QPixmap, QImage, QImageReader, QPainter, QBrush, QPen, QColor, QIcon,
                        QFont, QPainterPath, QCursor, QAction)

from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCard, Slider, FluentIconBase, SimpleCardWidget, PushButton
from qfluentwidgets import (SegmentedToolWidget, TransparentToolButton,
                            InfoBar, InfoBarPosition, InfoBarIcon, 
                            RoundMenu, FluentIcon, Action, AvatarWidget, BodyLabel, ToolButton,
                            HyperlinkButton, CaptionLabel, setFont, setTheme, Theme, isDarkTheme,
                            FluentStyleSheet, FlowLayout, IconWidget, getFont,
                            TransparentDropDownToolButton, DropDownPushButton,
                            SingleDirectionScrollArea, PrimaryPushButton, LineEdit,
                            FlipImageDelegate, HorizontalPipsPager, HorizontalFlipView,
                            TextWrap, InfoBadge, PushButton, ScrollArea, ImageLabel, ToolTipFilter)

import DyberPet.settings as settings
from DyberPet.DyberSettings.custom_utils import AvatarImage

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
        pixmap = AvatarImage(image, edge_size=80, frameColor="#ffffff")
        self.pfpLabel = QLabel()
        self.pfpLabel.setPixmap(pixmap)

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




###########################################################################
#                          Inventory UI Widgets                            
###########################################################################


class coinWidget(QWidget):
    """
    Display number of coins
    """

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
        self.icon.setToolTip(self.tr('DyberCoin'))

        self.coinAmount = LineEdit(self)
        self.coinAmount.setClearButtonEnabled(False)
        self.coinAmount.setEnabled(False)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.icon, Qt.AlignRight | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.coinAmount, Qt.AlignRight | Qt.AlignVCenter)
        self._updateCoin(8)

    def _updateCoin(self, coinNumber: int):
        num_str = f"{coinNumber:,}"
        self.coinAmount.setText(num_str)
        self.coinAmount.setFixedWidth(len(num_str)*7 + 29)
        self.adjustSize()




ItemStyle = """
QLabel{
    border : 2px solid #EFEBDF;
    border-radius: 5px;
    background-color: #EFEBDF
}
"""

CollectStyle = """
QLabel{
    border : 2px solid #e1eaf4;
    border-radius: 5px;
    background-color: #e1eaf4
}
"""

EmptyStyle = """
QLabel{
    border : 2px solid #EFEBDF;
    border-radius: 5px;
    background-color: #EFEBDF
}
"""

ItemClick = """
QLabel{
    border : 2px solid #B1C790;
    border-radius: 5px;
    background-color: #EFEBDF
}
"""

CollectClick = """
QLabel{
    border : 2px solid #B1C790;
    border-radius: 5px;
    background-color: #e1eaf4
}
"""


class PetItemWidget(QLabel):
    clicked = Signal()
    Ii_selected = Signal(tuple, bool, name="Ii_selected")
    Ii_removed = Signal(tuple, name="Ii_removed")

    '''Single Item Wiget
    
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
        self.size_wh = int(56) #*size_factor)

        self.setFixedSize(self.size_wh,self.size_wh)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignCenter)
        #self.installEventFilter(self)
        #self.setPixmap(QPixmap.fromImage())
        self.font = QFont()
        self.font.setPointSize(self.size_wh/8)
        self.font.setBold(True)
        self.clct_inuse = False

        if item_config is not None:
            self.item_name = item_config['name']
            self.image = item_config['image']
            self.image = self.image.scaled(self.size_wh,self.size_wh, mode=Qt.SmoothTransformation)
            self.setPixmap(QPixmap.fromImage(self.image))
            self.installEventFilter(ToolTipFilter(self, showDelay=500))
            self.setToolTip(item_config['hint'])
            if self.item_config.get('item_type', 'consumable') in ['collection', 'dialogue']:
                self.setStyleSheet(CollectStyle)
            else:
                self.setStyleSheet(ItemStyle) #"QLabel{border : 3px solid #4c9bf7; border-radius: 5px}")
        else:
            self.setStyleSheet(EmptyStyle) #"QLabel{border : 3px solid #6d6f6d; border-radius: 5px}")

    def mousePressEvent(self, ev):
        self.clicked.emit()

    def mouseReleaseEvent(self, event):
        if self.item_config is not None:
            if self.selected:
                self.Ii_selected.emit(self.cell_index, self.clct_inuse)
                if self.item_config.get('item_type', 'consumable') in ['collection', 'dialogue']:
                    self.setStyleSheet(CollectStyle)
                else:
                    self.setStyleSheet(ItemStyle)
                #self.setStyleSheet(ItemStyle) #"QLabel{border : 3px solid #4c9bf7; border-radius: 5px}")
                self.selected = False
            else:
                if self.item_config.get('item_type', 'consumable') in ['collection', 'dialogue']:
                    self.setStyleSheet(CollectClick)
                else:
                    self.setStyleSheet(ItemClick)
                #self.setStyleSheet(ItemClick) #"QLabel{border : 3px solid #ee171d; border-radius: 5px}")
                self.Ii_selected.emit(self.cell_index, self.clct_inuse)
                self.selected = True
        #pass # change background, enable Feed bottom

    def paintEvent(self, event):
        super(Inventory_item, self).paintEvent(event)
        if self.item_num > 1:
            text_printer = QPainter(self)
            text_printer.setFont(self.font)
            text_printer.drawText(QRect(0, 0, int(self.size_wh-3), int(self.size_wh-3)), Qt.AlignBottom | Qt.AlignRight, str(self.item_num))
            #text_printer.drawText(QRect(0, 0, int(self.size_wh-3*size_factor), int(self.size_wh-3*size_factor)), Qt.AlignBottom | Qt.AlignRight, str(self.item_num))



    def unselected(self):
        self.selected = False
        if self.item_config.get('item_type', 'consumable') in ['collection', 'dialogue']:
            self.setStyleSheet(CollectStyle)
        else:
            self.setStyleSheet(ItemStyle)
        #self.setStyleSheet(ItemStyle) #"QLabel{border : 3px solid #4c9bf7; border-radius: 5px}")

    def registItem(self, item_config, n_items):
        self.item_config = item_config
        self.item_num = n_items
        self.item_name = item_config['name']
        self.image = item_config['image']
        self.image = self.image.scaled(self.size_wh,self.size_wh, mode=Qt.SmoothTransformation)
        self.setPixmap(QPixmap.fromImage(self.image))
        self.setToolTip(item_config['hint'])
        if self.item_config.get('item_type', 'consumable') in ['collection', 'dialogue']:
            self.setStyleSheet(CollectStyle)
        else:
            self.setStyleSheet(ItemStyle)
        #self.setStyleSheet(ItemStyle) #"QLabel{border : 3px solid #4c9bf7; border-radius: 5px}")

    def addItem(self, add_n):
        self.item_num += add_n
        self.setPixmap(QPixmap.fromImage(self.image))

    def consumeItem(self):
        if self.item_config.get('item_type', 'consumable') in ['collection', 'dialogue']:
            self.clct_inuse = not self.clct_inuse
        else:
            self.item_num += -1
            if self.item_num == 0:
                self.removeItem()
            else:
                self.setPixmap(QPixmap.fromImage(self.image))

    def removeItem(self):
        # 告知Inventory item被移除
        self.Ii_removed.emit(self.cell_index)

        self.item_config = None
        self.item_name = 'None'
        self.image = None
        self.item_num = 0
        self.selected = False

        self.clear()
        self.setToolTip('')
        self.setStyleSheet(EmptyStyle) #"QLabel{border : 3px solid #6d6f6d; border-radius: 5px}")



