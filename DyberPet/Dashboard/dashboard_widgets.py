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
                             QVBoxLayout, QProgressBar, QFrame, QStyleOptionViewItem)
from PySide6.QtGui import (QPixmap, QImage, QImageReader, QPainter, QBrush, QPen, QColor, QIcon,
                        QFont, QPainterPath, QCursor, QAction)

from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCard, Slider, FluentIconBase, SimpleCardWidget, PushButton
from qfluentwidgets import (InfoBar, InfoBarPosition, InfoBarIcon, 
                            RoundMenu, FluentIcon, Action, AvatarWidget, BodyLabel, ToolButton,
                            HyperlinkButton, CaptionLabel, setFont, setTheme, Theme, isDarkTheme,
                            FluentStyleSheet, FlowLayout, IconWidget, getFont,
                            TransparentDropDownToolButton, DropDownPushButton, TransparentToolButton,
                            SingleDirectionScrollArea, PrimaryPushButton, LineEdit,
                            FlipImageDelegate, HorizontalPipsPager, HorizontalFlipView,
                            TextWrap, InfoBadge, PushButton, ScrollArea, ImageLabel, ToolTipFilter)

import DyberPet.settings as settings

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





#############################################
#  Status UI Widgets
#############################################

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
        self.noteLayout.insertWidget(0, HorizontalSeparator(QColor("#000000"), 1))
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





























