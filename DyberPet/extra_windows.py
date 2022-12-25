import os
import sys
import time
import math
import random
import inspect
import types
from datetime import datetime, timedelta

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QEvent, QRect, QSize, QPropertyAnimation
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontDatabase, QColor, QPainterPath, QRegion, QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QRectF

from typing import List
import ctypes
size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
all_font_size = 10 #int(10/screen_scale)

import DyberPet.settings as settings

pushbuttonStyle = f"""
QPushButton {{
    background-color: #ffbdad;
    color: #000000;
    border-style: solid;
    padding: {int(7*size_factor)}px;
    font: {int(16*size_factor)}px;
    font-family: "黑体";
    border-width: {int(3*size_factor)}px;
    border-radius: {int(10*size_factor)}px;
    border-color: #B39C86;
}}
QPushButton:hover:!pressed {{
    background-color: #ffb19e;
}}
QPushButton:pressed {{
    background-color: #ffa48f;
}}
QPushButton:disabled {{
    background-color: #e0e1e0;
}}
"""

LineStyle = """
QHLine{
    background-color: #9f7a6a;
    border: 0.5px solid #9f7a6a;
    border-style: solid;
}

QVLine{
    background-color: #9f7a6a;
    border: 0.5px solid #9f7a6a;
    border-style: solid;
}
"""
class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        #self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet(LineStyle)

class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        #self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet(LineStyle)


##############################
#           番茄钟
##############################

TomatoTitle = f"""
QLabel {{
    border: 0;
    background-color: #F5F4EF;
    font-size: {int(15*size_factor)}px;
    font-family: "黑体";
    width: {int(10*size_factor)}px;
    height: {int(20*size_factor)}px
}}
"""

TomatoClose = f"""
QPushButton {{
    background-color: #ffbdad;
    padding: 0px;
    border-style: solid;
    border-width: {int(2*size_factor)}px;
    border-radius: {int(10*size_factor)}px;
    border-color: transparent;
    text-align:middle;
}}

QPushButton:hover:!pressed {{
    background-color: #ffb19e;
}}
QPushButton:pressed {{
    background-color: #ffa48f;
}}
QPushButton:disabled {{
    background-color: #e0e1e0;
}}
"""

TomatoStyle = f"""
QFrame {{
    background:#F5F4EF;
    border: {int(3*size_factor)}px solid #F5F4EF;
    border-radius: {int(10*size_factor)}px;
}}

QLabel {{
    font-size: {int(18*size_factor)}px;
    font-family: "黑体";
}}

{pushbuttonStyle}
"""

class Tomato(QWidget):
    close_tomato = pyqtSignal(name='close_tomato')
    cancelTm = pyqtSignal(name='cancelTm')
    confirm_tomato = pyqtSignal(int, name='confirm_tomato')

    def __init__(self, parent=None):
        super(Tomato, self).__init__(parent)
        self.is_follow_mouse = False
        self.tomato_on = False
        self.tomato_index = 0
        # tomato clock window
        self.centralwidget = QFrame()
        self.centralwidget.setStyleSheet(TomatoStyle)
        vbox_t = QVBoxLayout()

        hbox_t0 = QHBoxLayout()
        title = QLabel("番茄钟")
        title.setStyleSheet(TomatoTitle)
        icon = QLabel()
        #icon.setStyleSheet(TomatoTitle)
        image = QImage()
        image.load('res/icons/Tomato_icon.png')
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(image)) #.scaled(20,20)))
        icon.setFixedSize(25*size_factor,25*size_factor)
        hbox_t0.addWidget(icon, Qt.AlignBottom | Qt.AlignLeft)
        hbox_t0.addWidget(title, Qt.AlignVCenter | Qt.AlignLeft)
        hbox_t0.addStretch(1)

        '''
        self.button_close = QToolButton()
        closeIcon = self.style().standardIcon(QStyle.SP_TitleBarCloseButton)
        self.button_close.setIcon(closeIcon)
        iw = 15 * size_factor
        self.button_close.setIconSize(QSize(iw,iw))
        '''


        self.button_close = QPushButton()
        self.button_close.setStyleSheet(TomatoClose)
        self.button_close.setFixedSize(20*size_factor, 20*size_factor)
        self.button_close.setIcon(QIcon('res/icons/close_icon.png'))
        self.button_close.setIconSize(QSize(20*size_factor,20*size_factor))
        self.button_close.clicked.connect(self.close_tomato)
        hbox_t0.addWidget(self.button_close, Qt.AlignTop | Qt.AlignRight)
        #hbox_0.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        hbox_t1 = QHBoxLayout()
        '''
        self.n_tomato = QSpinBox()
        self.n_tomato.setMinimum(1)
        '''
        self.n_tomato = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(1,99)
        self.n_tomato.setValidator(qintv)
        self.n_tomato.setMaxLength(2)
        self.n_tomato.setAlignment(Qt.AlignCenter)
        self.n_tomato.setFont(QFont("Arial",18))
        self.n_tomato.setFixedSize(38,38)


        self.n_tomato_label1 = QLabel("开始")
        self.n_tomato_label1.setFixedSize(100,76)
        self.n_tomato_label1.setAlignment(Qt.AlignCenter)
        n_tomato_label2 = QLabel("个循环")
        #n_tomato_label2.setFixedSize(110,80)
        #QFontDatabase.addApplicationFont('res/font/MFNaiSi_Noncommercial-Regular.otf')
        #n_tomato_label.setFont(QFont('宋体', all_font_size))
        hbox_t1.addStretch()
        hbox_t1.addWidget(self.n_tomato_label1, Qt.AlignVCenter | Qt.AlignRight)
        hbox_t1.addWidget(self.n_tomato, Qt.AlignCenter)
        hbox_t1.addWidget(n_tomato_label2, Qt.AlignVCenter | Qt.AlignLeft)

        hbox_t = QHBoxLayout()
        self.button_confirm = QPushButton("确定")
        self.button_confirm.setFixedSize(80*size_factor, 40*size_factor)
        #self.button_confirm.setFont(QFont('宋体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_cancel = QPushButton("停止")
        self.button_cancel.setFixedSize(80*size_factor, 40*size_factor)
        #self.button_cancel.setFont(QFont('宋体', all_font_size))
        self.button_cancel.clicked.connect(self.cancelTomato)
        self.button_cancel.setDisabled(True)
        hbox_t.addWidget(self.button_confirm)
        hbox_t.addWidget(self.button_cancel)

        vbox_t.addLayout(hbox_t0)
        vbox_t.addWidget(QHLine())
        vbox_t.addLayout(hbox_t1)
        vbox_t.addLayout(hbox_t)
        self.centralwidget.setLayout(vbox_t)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.centralwidget)
        self.setLayout(self.layout_window)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint)
        #self.setLayout(vbox_t)
        #self.setFixedSize(250,100)
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        if event.button() == Qt.LeftButton:
            # 左键绑定拖拽
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            event.accept()
            self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件, 左键且绑定跟随, 移动窗体
        :param event:
        :return:
        """
        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        松开鼠标操作
        :param event:
        :return:
        """
        self.is_follow_mouse = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    def confirm(self):
        n_tm = self.n_tomato.text()
        if n_tm == '':
            return
        else:
            n_tm = int(n_tm)
        #print(n_tm)
        self.tomato_on = True
        self.n_tomato_label1.setText('正在进行第')
        self.n_tomato.setReadOnly(True)
        self.button_confirm.setDisabled(True)
        self.button_cancel.setDisabled(False)
        self.confirm_tomato.emit(n_tm)
    
    def newTomato(self):
        self.tomato_index += 1
        self.n_tomato.setText(str(self.tomato_index))

    def endTomato(self):
        self.tomato_on = False
        self.tomato_index = 0
        self.n_tomato_label1.setText('开始')
        self.n_tomato.setReadOnly(False)
        self.button_confirm.setDisabled(False)
        self.n_tomato.setText('')
        self.button_cancel.setDisabled(True)

    def cancelTomato(self):
        self.cancelTm.emit()



##############################
#           专注事项
##############################

checkStyle = f"""
QCheckBox {{
    padding: {int(2*size_factor)}px;
    font-size: {int(15*size_factor)}px;
    font-family: "黑体";
    height: {int(25*size_factor)}px
}}

/*CHECKBOX*/
QCheckBox:hover {{
    border-radius:{int(4*size_factor)}px;
    border-style:solid;
    border-width:{int(max(1,int(1*size_factor)))}px;
    padding-left: {int(max(1,int(1*size_factor)))}px;
    padding-right: {int(max(1,int(1*size_factor)))}px;
    padding-bottom: {int(max(1,int(1*size_factor)))}px;
    padding-top: {int(max(1,int(1*size_factor)))}px;
    border-color: #64b4c4;
    background-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 #cfe8ed, stop:1 #deeff2);
}}
QCheckBox::indicator:checked {{
    width: {int(15*size_factor)}px;
    height: {int(15*size_factor)}px;
    border-radius:{int(4*size_factor)}px;
    border-style:solid;
    border-width:{int(max(1,int(1*size_factor)))}px;
    border-color: #64b4c4;
    image: url(res/icons/check_icon.png)
}}
QCheckBox::indicator:unchecked {{
    width: {int(15*size_factor)}px;
    height: {int(15*size_factor)}px;
    border-radius:{int(4*size_factor)}px;
    border-style:solid;
    border-width:{int(max(1,int(1*size_factor)))}px;
    border-color:#64b4c4;
    background-color:qlineargradient(x1: 0, y1: 1, x2: 1, y2: 0,stop: 0 #f3d5f7, stop: 0.5 #fbf6e7,stop: 1 #e6fcf5);
}}
"""

FocusStyle = f"""
QFrame {{
    background:#F5F4EF;
    border: {int(3*size_factor)}px solid #F5F4EF;
    border-radius: {int(10*size_factor)}px;
}}
QLabel {{
    font-size: {int(18*size_factor)}px;
    font-family: "黑体";
}}

{pushbuttonStyle}

{checkStyle}
"""

class Focus(QWidget):
    close_focus = pyqtSignal(name='close_focus')
    confirm_focus = pyqtSignal(str,int,int, name='confirm_focus')
    cancelFocus = pyqtSignal(name='cancelFocus')
    pauseTimer_focus = pyqtSignal(bool, name='pauseTimer_focus')

    def __init__(self, parent=None):
        super(Focus, self).__init__(parent)
        # Focus time window
        self.is_follow_mouse = False
        self.focus_on = False
        self.focus_pause = False
        self.pausable = False
        # tomato clock window
        self.centralwidget = QFrame()
        self.centralwidget.setStyleSheet(FocusStyle)

        # 标题栏
        hbox_f0 = QHBoxLayout()
        title = QLabel("专注时间")
        title.setStyleSheet(TomatoTitle)
        icon = QLabel()
        #icon.setStyleSheet(TomatoTitle)
        image = QImage()
        image.load('res/icons/Timer_icon.png')
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(image)) #.scaled(20,20)))
        icon.setFixedSize(25*size_factor,25*size_factor)
        hbox_f0.addWidget(icon, Qt.AlignBottom | Qt.AlignLeft)
        hbox_f0.addWidget(title, Qt.AlignVCenter | Qt.AlignLeft)
        hbox_f0.addStretch(1)
        self.button_close = QPushButton()
        self.button_close.setStyleSheet(TomatoClose)
        self.button_close.setFixedSize(20*size_factor, 20*size_factor)
        self.button_close.setIcon(QIcon('res/icons/close_icon.png'))
        self.button_close.setIconSize(QSize(20*size_factor,20*size_factor))
        self.button_close.clicked.connect(self.close_focus)
        hbox_f0.addWidget(self.button_close, Qt.AlignTop | Qt.AlignRight)

        # 设定栏
        vbox_f = QVBoxLayout()
        self.checkA = QCheckBox("持续一段时间", self)
        #self.checkA.setFont(QFont('宋体', all_font_size))
        self.checkB = QCheckBox("定时结束", self)
        #self.checkB.setFont(QFont('宋体', all_font_size))
        self.checkA.stateChanged.connect(self.uncheck)
        self.checkB.stateChanged.connect(self.uncheck)

        hbox_f1 = QHBoxLayout()
        self.countdown_h = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,23)
        self.countdown_h.setValidator(qintv)
        self.countdown_h.setMaxLength(2)
        self.countdown_h.setAlignment(Qt.AlignCenter)
        self.countdown_h.setFont(QFont("Arial",18))
        self.countdown_h.setFixedSize(38,38)

        self.countdown_m = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,59)
        self.countdown_m.setValidator(qintv)
        self.countdown_m.setMaxLength(2)
        self.countdown_m.setAlignment(Qt.AlignCenter)
        self.countdown_m.setFont(QFont("Arial",18))
        self.countdown_m.setFixedSize(38,38)
        '''
        self.countdown_h = QSpinBox()
        self.countdown_h.setMinimum(0)
        self.countdown_h.setMaximum(23)
        self.countdown_m = QSpinBox()
        self.countdown_m.setMinimum(0)
        self.countdown_m.setMaximum(59)
        self.countdown_m.setSingleStep(5)
        '''
        hbox_f1.addWidget(self.countdown_h)
        label_h = QLabel('小时')
        #label_h.setFont(QFont('宋体', all_font_size))
        hbox_f1.addWidget(label_h)
        hbox_f1.addWidget(self.countdown_m)
        label_m = QLabel('分钟后')
        #label_m.setFont(QFont('宋体', all_font_size))
        hbox_f1.addWidget(label_m)
        hbox_f1.addStretch(10)

        hbox_f2 = QHBoxLayout()
        self.time_h = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,23)
        self.time_h.setValidator(qintv)
        self.time_h.setMaxLength(2)
        self.time_h.setAlignment(Qt.AlignCenter)
        self.time_h.setFont(QFont("Arial",18))
        self.time_h.setFixedSize(38,38)

        self.time_m = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,59)
        self.time_m.setValidator(qintv)
        self.time_m.setMaxLength(2)
        self.time_m.setAlignment(Qt.AlignCenter)
        self.time_m.setFont(QFont("Arial",18))
        self.time_m.setFixedSize(38,38)
        '''
        self.time_h = QSpinBox()
        self.time_h.setMinimum(0)
        self.time_h.setMaximum(23)
        self.time_m = QSpinBox()
        self.time_m.setMinimum(0)
        self.time_m.setMaximum(59)
        '''
        label_d = QLabel('到')
        #label_d.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(label_d)
        hbox_f2.addWidget(self.time_h)
        label_h = QLabel('点')
        #label_h.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(label_h)
        hbox_f2.addWidget(self.time_m)
        label_m = QLabel('分')
        #label_m.setFixedHeight(100)
        #label_m.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        #label_m.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(label_m)
        hbox_f2.addStretch(10)
        #hbox_f2.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        hbox_f3 = QHBoxLayout()
        self.button_confirm = QPushButton("开始")
        #self.button_confirm.setFont(QFont('宋体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_cancel = QPushButton("停止")
        #self.button_cancel.setFont(QFont('宋体', all_font_size))
        self.button_cancel.clicked.connect(self.cancelFocus)
        self.button_cancel.setDisabled(True)

        hbox_f3.addWidget(self.button_confirm)
        hbox_f3.addWidget(self.button_cancel)

        #label_method = QLabel('设置方式')
        #label_method.setFont(QFont('宋体', all_font_size))
        #label_method.setStyleSheet("color : grey")
        vbox_f.addLayout(hbox_f0)
        vbox_f.addWidget(QHLine())
        vbox_f.addWidget(self.checkA)
        vbox_f.addLayout(hbox_f1)
        vbox_f.addStretch(1)
        vbox_f.addWidget(self.checkB)
        vbox_f.addLayout(hbox_f2)
        vbox_f.addStretch(1)
        space_label = QLabel("")
        space_label.setFixedHeight(20)
        vbox_f.addWidget(space_label)
        vbox_f.addLayout(hbox_f3)

        self.centralwidget.setLayout(vbox_f)
        #self.setLayout(vbox_f)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.centralwidget)
        self.setLayout(self.layout_window)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        #self.setFixedSize(250*size_factor,200*size_factor)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        if event.button() == Qt.LeftButton:
            # 左键绑定拖拽
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            event.accept()
            self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件, 左键且绑定跟随, 移动窗体
        :param event:
        :return:
        """
        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        松开鼠标操作
        :param event:
        :return:
        """
        self.is_follow_mouse = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    # uncheck method
    def uncheck(self, state):
        # checking if state is checked
        if state == Qt.Checked:
            # if first check box is selected
            if self.sender() == self.checkA:
  
                # making other check box to uncheck
                self.checkB.setChecked(False)
  
            # if second check box is selected
            elif self.sender() == self.checkB:
  
                # making other check box to uncheck
                self.checkA.setChecked(False)

    def confirm(self):
        if self.focus_on and not self.focus_pause:
            self.button_confirm.setText('继续')
            self.focus_pause = True
            #记得考虑暂停后终止的情况
            self.pauseTimer_focus.emit(True)

        elif self.focus_on and self.focus_pause:
            self.button_confirm.setText('暂停')
            self.focus_pause = False
            #记得考虑暂停后终止的情况
            self.pauseTimer_focus.emit(False)

        else:
            if self.checkA.isChecked():
                self.pausable = True
                h = self.countdown_h.text()
                m = self.countdown_m.text()
                if h == '' and m=='':
                    return
                else:
                    try:
                        h = int(h)
                    except:
                        h=0
                    try: 
                        m = int(m)
                    except:
                        m=0
                    self.confirm_focus.emit('range', h, m)

            elif self.checkB.isChecked():
                h = self.time_h.text()
                m = self.time_m.text()
                if h == '' or m=='':
                    return
                else:
                    self.confirm_focus.emit('point', int(h), int(m))
            else:
                return

            self.focus_on = True
            if self.pausable:
                self.button_confirm.setText('暂停')
            else:
                self.button_confirm.setDisabled(True)
            self.button_cancel.setDisabled(False)

    def endFocus(self):
        self.focus_on = False
        self.pausable = False
        self.button_confirm.setText('开始')
        self.button_cancel.setDisabled(True)
        self.button_confirm.setDisabled(False)





##############################
#           提醒事项
##############################
class Remindme(QWidget):
    close_remind = pyqtSignal(name='close_remind')
    confirm_remind = pyqtSignal(str, int, int, str, name='confirm_remind')

    def __init__(self, parent=None):
        super(Remindme, self).__init__(parent)
        # Remindme time window
        vbox_r = QVBoxLayout()

        self.checkA = QCheckBox("一段时间后提醒", self)
        self.checkA.setFont(QFont('宋体', all_font_size))
        self.checkB = QCheckBox("定时提醒", self)
        self.checkB.setFont(QFont('宋体', all_font_size))
        self.checkC = QCheckBox("间隔重复", self)
        self.checkC.setFont(QFont('宋体', all_font_size))
        self.checkA.stateChanged.connect(self.uncheck)
        self.checkB.stateChanged.connect(self.uncheck)
        self.checkC.stateChanged.connect(self.uncheck)

        hbox_r1 = QHBoxLayout()
        self.countdown_h = QSpinBox()
        self.countdown_h.setMinimum(0)
        self.countdown_h.setMaximum(23)
        self.countdown_m = QSpinBox()
        self.countdown_m.setMinimum(0)
        self.countdown_m.setMaximum(59)
        self.countdown_m.setSingleStep(5)
        hbox_r1.addWidget(self.countdown_h)
        label_h = QLabel('小时')
        label_h.setFont(QFont('宋体', all_font_size))
        hbox_r1.addWidget(label_h)
        hbox_r1.addWidget(self.countdown_m)
        label_m = QLabel('分钟后')
        label_m.setFont(QFont('宋体', all_font_size))
        hbox_r1.addWidget(label_m)
        hbox_r1.addStretch(10)

        hbox_r2 = QHBoxLayout()
        self.time_h = QSpinBox()
        self.time_h.setMinimum(0)
        self.time_h.setMaximum(23)
        self.time_m = QSpinBox()
        self.time_m.setMinimum(0)
        self.time_m.setMaximum(59)
        label_d = QLabel('到')
        label_d.setFont(QFont('宋体', all_font_size))
        hbox_r2.addWidget(label_d)
        hbox_r2.addWidget(self.time_h)
        label_h = QLabel('点')
        label_h.setFont(QFont('宋体', all_font_size))
        hbox_r2.addWidget(label_h)
        hbox_r2.addWidget(self.time_m)
        label_m = QLabel('分')
        label_m.setFont(QFont('宋体', all_font_size))
        hbox_r2.addWidget(label_m)
        hbox_r2.addStretch(10)

        hbox_r5 = QHBoxLayout()
        self.check1 = QCheckBox("在", self) # xx 分时
        self.check1.setFont(QFont('宋体', all_font_size))
        self.check2 = QCheckBox("每", self)
        self.check2.setFont(QFont('宋体', all_font_size))
        self.check1.stateChanged.connect(self.uncheck)
        self.check2.stateChanged.connect(self.uncheck)
        self.every_min = QSpinBox()
        self.every_min.setMinimum(0)
        self.every_min.setMaximum(59)
        label_em = QLabel('分时')
        label_em.setFont(QFont('宋体', all_font_size))
        self.interval_min = QSpinBox()
        self.interval_min.setMinimum(1)
        label_im = QLabel('分钟')
        label_im.setFont(QFont('宋体', all_font_size))
        hbox_r5.addWidget(self.check1)
        hbox_r5.addWidget(self.every_min)
        hbox_r5.addWidget(label_em)
        hbox_r5.addWidget(self.check2)
        hbox_r5.addWidget(self.interval_min)
        hbox_r5.addWidget(label_im)
        hbox_r5.addStretch(10)

        hbox_r3 = QHBoxLayout()
        self.button_confirm = QPushButton("确定")
        self.button_confirm.setFont(QFont('宋体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_cancel = QPushButton("关闭")
        self.button_cancel.setFont(QFont('宋体', all_font_size))
        self.button_cancel.clicked.connect(self.close_remind)
        hbox_r3.addWidget(self.button_confirm)
        hbox_r3.addWidget(self.button_cancel)

        hbox_r4 = QHBoxLayout()
        self.e1 = QLineEdit()
        self.e1.setMaxLength(14)
        self.e1.setAlignment(Qt.AlignLeft)
        self.e1.setFont(QFont("宋体",all_font_size))
        hbox_r4.addWidget(self.e1)
        hbox_r4.addStretch(1)

        label_method = QLabel('提醒方式')
        label_method.setFont(QFont('宋体', all_font_size))
        label_method.setStyleSheet("color : grey")
        vbox_r.addWidget(label_method)
        vbox_r.addWidget(QHLine())
        vbox_r.addWidget(self.checkA)
        vbox_r.addLayout(hbox_r1)
        vbox_r.addStretch(1)
        vbox_r.addWidget(self.checkB)
        vbox_r.addLayout(hbox_r2)
        vbox_r.addStretch(1)
        vbox_r.addWidget(self.checkC)
        vbox_r.addLayout(hbox_r5)
        vbox_r.addStretch(2)

        label_r = QLabel('提醒我（限14个字以内）')
        label_r.setFont(QFont('宋体', all_font_size))
        label_r.setStyleSheet("color : grey")
        vbox_r.addWidget(label_r)
        vbox_r.addWidget(QHLine())
        vbox_r.addLayout(hbox_r4)
        vbox_r.addLayout(hbox_r3, Qt.AlignBottom | Qt.AlignHCenter)
        vbox_r.addStretch(1)


        vbox_r2 = QVBoxLayout()
        label_on = QLabel('提醒事项（宠物退出后会保留）')
        label_on.setFont(QFont('宋体', all_font_size))
        label_on.setStyleSheet("color : grey")
        vbox_r2.addWidget(label_on)
        vbox_r2.addWidget(QHLine())
        self.e2 = QTextEdit()
        #self.e2.setMaxLength(14)
        self.e2.setAlignment(Qt.AlignLeft)
        self.e2.setFont(QFont("宋体",all_font_size))
        self.e2.textChanged.connect(self.save_remindme)
        vbox_r2.addWidget(self.e2)

        hbox_all = QHBoxLayout()
        hbox_all.addLayout(vbox_r)
        #hbox_all.addStretch(0.5)
        hbox_all.addWidget(QVLine())
        #hbox_all.addStretch(0.5)
        hbox_all.addLayout(vbox_r2)

        self.setLayout(hbox_all)
        self.setFixedSize(450*size_factor,300*size_factor)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)

        if os.path.isfile('data/remindme.txt'):
            f = open('data/remindme.txt','r', encoding='UTF-8')
            texts = f.read()
            f.close()
            self.e2.setPlainText(texts)
        else:
            f = open('data/remindme.txt','w', encoding='UTF-8')
            f.write('')
            f.close()

    def initial_task(self):
        f = open('data/remindme.txt','r', encoding='UTF-8')
        texts = f.readlines()
        f.close()
        for line in texts:
            line = line.rstrip('\n')
            if line.startswith('#重复'):
                line = line.split(' ')
                if line[-1] == '-':
                    line += ['']

                if line[1] == '每到':
                    self.confirm_remind.emit('repeat_point', 0, int(line[2]), line[-1])

                elif line[2] == '每隔':
                    self.confirm_remind.emit('repeat_interval', 0, int(line[2]), line[-1])


    # uncheck method
    def uncheck(self, state):
        # checking if state is checked
        if state == Qt.Checked:
            # if first check box is selected
            if self.sender() == self.checkA:
  
                # making other check box to uncheck
                self.checkB.setChecked(False)
                self.checkC.setChecked(False)
  
            # if second check box is selected
            elif self.sender() == self.checkB:
  
                # making other check box to uncheck
                self.checkA.setChecked(False)
                self.checkC.setChecked(False)

            elif self.sender() == self.checkC:
  
                # making other check box to uncheck
                self.checkA.setChecked(False)
                self.checkB.setChecked(False)

            elif self.sender() == self.check1:
                self.check2.setChecked(False)

            elif self.sender() == self.check2:
                self.check1.setChecked(False)

    def confirm(self):
        if self.checkA.isChecked():
            hs = self.countdown_h.value()
            ms = self.countdown_m.value()
            timeset = datetime.now() + timedelta(hours=hs, minutes=ms)
            timeset = timeset.strftime("%m/%d %H:%M")
            remind_text = self.e1.text()
            current_text = self.e2.toPlainText()
            current_text += '%s - %s\n'%(timeset, remind_text)
            self.e2.setPlainText(current_text)
            self.confirm_remind.emit('range', self.countdown_h.value(), self.countdown_m.value(), remind_text)

        elif self.checkB.isChecked():
            hs = self.time_h.value()
            ms = self.time_m.value()
            now = datetime.now()
            time_torun = datetime(year=now.year, month=now.month, day=now.day,
                                  hour=hs, minute=ms, second=now.second)
            time_diff = time_torun - datetime.now()
            if time_diff <= timedelta(0):
                time_torun = time_torun + timedelta(days=1)
            timeset = time_torun.strftime("%m/%d %H:%M")
            remind_text = self.e1.text()
            current_text = self.e2.toPlainText()
            current_text += '%s - %s\n'%(timeset, remind_text)
            self.e2.setPlainText(current_text)
            self.confirm_remind.emit('point', self.time_h.value(), self.time_m.value(), remind_text)

        elif self.checkC.isChecked():
            remind_text = self.e1.text()
            current_text = self.e2.toPlainText()
            if self.check1.isChecked():
                current_text += '#重复 每到 %s 分时 - %s\n'%(int(self.every_min.value()), remind_text)
                self.confirm_remind.emit('repeat_point', 0, self.every_min.value(), remind_text)

            elif self.check2.isChecked():
                current_text += '#重复 每隔 %s 分钟 - %s\n'%(int(self.interval_min.value()), remind_text)
                self.confirm_remind.emit('repeat_interval', 0, self.interval_min.value(), remind_text)

            self.e2.setPlainText(current_text)

    def save_remindme(self):
        #print(self.e2.toPlainText()=='')
        f = open('data/remindme.txt','w', encoding='UTF-8')
        f.write(self.e2.toPlainText())
        f.close()





##############################
#          背包系统
##############################

ItemStyle = f"""
QLabel{{
    border : {int(2*size_factor)}px solid #EFEBDF;
    border-radius: {int(5*size_factor)}px;
    background-color: #EFEBDF
}}
"""

ItemClick = f"""
QLabel{{
    border : {int(2*size_factor)}px solid #B1C790;
    border-radius: {int(5*size_factor)}px;
    background-color: #EFEBDF
}}
"""
EmptyStyle = f"""
QLabel{{
    border : {int(2*size_factor)}px solid #EFEBDF;
    border-radius: {int(5*size_factor)}px;
    background-color: #EFEBDF
}}
"""

class Inventory_item(QLabel):
    clicked = pyqtSignal()
    Ii_selected = pyqtSignal(int, name="Ii_selected")
    Ii_removed = pyqtSignal(int, name="Ii_removed")

    '''特性
    
    - 固定大小的正方形
    - 主界面是物品UI
    - 右下角是物品个数
    - 鼠标点击时更改背景颜色
    - 鼠标停留时显示物品信息

    - 可更改个数
    - 可更改图片
    - 可更改背景

    '''
    def __init__(self, cell_index, item_config=None, item_num=0):
        '''item_config
        
        name: str
        img: Pixmap object
        number: int
        effect_HP: int
        effect_EM: int
        drop_rate: float
        description: str

        '''
        super(Inventory_item, self).__init__()
        self.cell_index = cell_index

        self.item_config = item_config
        self.item_name = None
        self.image = None
        self.item_num = item_num
        self.selected = False
        self.size_wh = int(56*size_factor)

        self.setFixedSize(self.size_wh,self.size_wh)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignCenter)
        #self.installEventFilter(self)
        #self.setPixmap(QPixmap.fromImage())
        self.font = QFont()
        self.font.setPointSize(self.size_wh/8)
        self.font.setBold(True)

        if item_config is not None:
            self.item_name = item_config['name']
            self.image = item_config['image']
            self.image = self.image.scaled(self.size_wh,self.size_wh)
            self.setPixmap(QPixmap.fromImage(self.image))
            self.setToolTip(item_config['hint'])

            self.setStyleSheet(ItemStyle) #"QLabel{border : 3px solid #4c9bf7; border-radius: 5px}")
        else:
            self.setStyleSheet(EmptyStyle) #"QLabel{border : 3px solid #6d6f6d; border-radius: 5px}")

    def mousePressEvent(self, ev):
        self.clicked.emit()

    def mouseReleaseEvent(self, event):
        if self.item_config is not None:
            if self.selected:
                self.Ii_selected.emit(self.cell_index)
                self.setStyleSheet(ItemStyle) #"QLabel{border : 3px solid #4c9bf7; border-radius: 5px}")
                self.selected = False
            else:
                self.setStyleSheet(ItemClick) #"QLabel{border : 3px solid #ee171d; border-radius: 5px}")
                self.Ii_selected.emit(self.cell_index)
                self.selected = True
        #pass # change background, enable Feed bottom

    def paintEvent(self, event):
        super(Inventory_item, self).paintEvent(event)
        if self.item_num > 0:
            text_printer = QPainter(self)
            text_printer.setFont(self.font)
            text_printer.drawText(QRect(0, 0, self.size_wh-3*size_factor, self.size_wh-3*size_factor), Qt.AlignBottom | Qt.AlignRight, str(self.item_num))



    def unselected(self):
        self.selected = False
        self.setStyleSheet(ItemStyle) #"QLabel{border : 3px solid #4c9bf7; border-radius: 5px}")

    def registItem(self, item_config, n_items):
        self.item_config = item_config
        self.item_num = n_items
        self.item_name = item_config['name']
        self.image = item_config['image']
        self.image = self.image.scaled(self.size_wh,self.size_wh)
        self.setPixmap(QPixmap.fromImage(self.image))
        self.setToolTip(item_config['hint'])
        self.setStyleSheet(ItemStyle) #"QLabel{border : 3px solid #4c9bf7; border-radius: 5px}")

    def addItem(self, add_n):
        self.item_num += add_n
        self.setPixmap(QPixmap.fromImage(self.image))

    def consumeItem(self):
        self.item_num += -1
        if self.item_num == 0:
            self.removeItem()
        else:
            self.setPixmap(QPixmap.fromImage(self.image))
    '''
    def changeNum(self):
        self.setPixmap(QPixmap.fromImage(self.image))
    '''

    def removeItem(self):
        # 告知Inventory item被移除
        self.Ii_removed.emit(self.cell_index)

        self.item_config = None
        self.item_name = None
        self.image = None
        self.item_num = 0
        self.selected = False

        self.clear()
        self.setToolTip('')
        self.setStyleSheet(EmptyStyle) #"QLabel{border : 3px solid #6d6f6d; border-radius: 5px}")
        

    def changeBackground(self):
        pass


ItemGroupStyle = f"""
QGroupBox {{
    border: {int(max(1,int(1*size_factor)))}px solid transparent;
    background-color: #F5F4EF;
    border-radius: {int(10*size_factor)}px
}}
"""

IvenTitle = f"""
QLabel {{
    border: 0;
    background-color: #F5F4EF;
    font-size: {int(15*size_factor)}px;
    font-family: "黑体";
    width: {int(10*size_factor)}px;
    height: {int(10*size_factor)}px
}}
"""

InvenStyle = f"""
QFrame{{
    background:#F5F4EF;
    border: {int(3*size_factor)}px solid #F5F4EF;
    border-radius: {int(10*size_factor)}px
}}

QScrollArea {{
    padding: {int(2*size_factor)}px;
    border: {int(3*size_factor)}px solid #9f7a6a;
    background-color: #F5F4EF;
    border-radius: {int(10*size_factor)}px
}}

QPushButton {{
    width: {int(60*size_factor)}px;
    background-color: #ffbdad;
    color: #000000;
    border-style: solid;
    padding: {int(7*size_factor)}px;
    font: {int(16*size_factor)}px;
    font-family: "黑体";
    border-width: {int(3*size_factor)}px;
    border-radius: {int(15*size_factor)}px;
    border-color: #B39C86;
}}
QPushButton:hover:!pressed {{
    background-color: #ffb19e;
}}
QPushButton:pressed {{
    background-color: #ffa48f;
}}
QPushButton:disabled {{
    background-color: #e0e1e0;
}}
QScrollBar:vertical
{{
    background-color: #F5F4EF;
    width: {int(15*size_factor)}px;
    margin: {int(5*size_factor)}px {int(max(1,int(1*size_factor)))}px {int(5*size_factor)}px {int(max(1,int(1*size_factor)))}px;
    border: {int(max(1,int(1*size_factor)))}px #F5F4EF;
    border-radius: {int(6*size_factor)}px;
}}

QScrollBar::handle:vertical
{{
    width: {int(15*size_factor)}px;
    background-color: #FFC8BB;         /* #f184ae; */
    min-height: {int(5*size_factor)}px;
    border-radius: {int(6*size_factor)}px;
}}
QScrollBar::add-line:vertical {{
height: 0px;
}}

QScrollBar::sub-line:vertical {{
height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
height: 0px;
}}
"""


class Inventory(QWidget):
    close_inventory = pyqtSignal(name='close_inventory')
    use_item_inven = pyqtSignal(str, name='use_item_inven')
    item_note = pyqtSignal(str, str, name='item_note')
    #confirm_inventory = pyqtSignal(str, int, int, str, name='confirm_inventory')

    def __init__(self, items_data, parent=None):
        super(Inventory, self).__init__(parent)

        self.is_follow_mouse = False
        
        self.items_data = items_data
        self.all_items = []
        self.all_probs = []
        #确定物品掉落概率
        for item in items_data.item_dict.keys():
            self.all_items.append(item)
            self.all_probs.append((items_data.item_dict[item]['drop_rate'])*int(items_data.item_dict[item]['fv_lock']<=settings.pet_data.fv_lvl))
        if sum(self.all_probs) != 0:
            self.all_probs = [i/sum(self.all_probs) for i in self.all_probs]

        #print(self.all_items)
        #print(self.all_probs)

        self.selected_cell = None

        self.centralwidget = QFrame()

        self.ItemGroupBox = QGroupBox() #"背包")
        self.ItemGroupBox.setStyleSheet(ItemGroupStyle)
        self.layout = QGridLayout()
        self.layout.setVerticalSpacing(9)
        #layout.setColumnStretch(1, 4)
        #layout.setColumnStretch(2, 4)


        #items_list = ['汉堡','薯条','可乐', None]
        self.inven_shape = (5,3)
        #self.items_list = {} #[None] * (self.inven_shape[0]*self.inven_shape[1])
        self.items_numb = {}
        self.cells_dict = {}
        self.empty_cell = []

        index_item = 0
        for item in settings.pet_data.items.keys():
            n_row = index_item // self.inven_shape[1]
            n_col = (index_item - (n_row-1)*self.inven_shape[1]) % self.inven_shape[1]

            if settings.pet_data.items[item] <= 0:
                continue

            self.items_numb[index_item] = int(settings.pet_data.items[item])
            self.cells_dict[index_item] = Inventory_item(index_item, items_data.item_dict[item], self.items_numb[index_item])
            self.cells_dict[index_item].Ii_selected.connect(self.change_selected)
            self.cells_dict[index_item].Ii_removed.connect(self.item_removed)
            self.layout.addWidget(self.cells_dict[index_item], n_row, n_col)
            index_item += 1

        if index_item < self.inven_shape[0]*self.inven_shape[1]:

            for j in range(index_item, (self.inven_shape[0]*self.inven_shape[1])):
                n_row = j // self.inven_shape[1]
                n_col = (j - (n_row-1)*self.inven_shape[1]) % self.inven_shape[1]

                self.items_numb[j] = 0
                self.cells_dict[j] = Inventory_item(j)
                self.cells_dict[j].Ii_selected.connect(self.change_selected)
                self.cells_dict[j].Ii_removed.connect(self.item_removed)
                self.layout.addWidget(self.cells_dict[j], n_row, n_col)

                self.empty_cell.append(j)



            '''
            self.item_dict[self.items_list[i]] = Inventory_item(items_data.item_dict[self.items_list[i]], self.items_numb[i])
            self.item_dict[self.items_list[i]].Ii_selected.connect(self.change_selected)
            self.item_dict[self.items_list[i]].Ii_removed.connect(self.item_removed)
            layout.addWidget(self.item_dict[self.items_list[i]],n_row,n_col)

            self.items_list[i] = item
            self.items_numb[i] = int(settings.pet_data.items[item])
            '''
        '''
        for i in range(len(self.items_list)):

            n_row = i // self.inven_shape[1]
            n_col = (i - (n_row-1)*self.inven_shape[1]) % self.inven_shape[1]

            if self.items_list[i] is None:
                self.item_dict['empty_%s'%i] = Inventory_item()
                layout.addWidget(self.item_dict['empty_%s'%i],n_row,n_col)
            else:
                self.item_dict[self.items_list[i]] = Inventory_item(items_data.item_dict[self.items_list[i]], self.items_numb[i])
                self.item_dict[self.items_list[i]].Ii_selected.connect(self.change_selected)
                self.item_dict[self.items_list[i]].Ii_removed.connect(self.item_removed)
                layout.addWidget(self.item_dict[self.items_list[i]],n_row,n_col)
        '''
            
        '''
        self.item1 = Inventory_item(items_data.item_dict['汉堡'], 2)
        self.item1.Ii_selected.connect(self.change_selected)
        self.item2 = Inventory_item(items_data.item_dict['薯条'], 1)
        self.item3 = Inventory_item(items_data.item_dict['可乐'], 5)
        self.item4 = Inventory_item() #items_data.item_dict['鸡翅'], 22)

        layout.addWidget(self.item1,0,0)
        layout.addWidget(self.item2,0,1)
        layout.addWidget(self.item3,1,0)
        layout.addWidget(self.item4,1,1)
        '''

        self.ItemGroupBox.setLayout(self.layout)

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidget(self.ItemGroupBox)

        hbox = QHBoxLayout()
        self.button_confirm = QPushButton("使用") #, objectName='InvenButton')
        #self.button_confirm.setFont(QFont('黑体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_confirm.setDisabled(True)
        #self.button_confirm.setStyleSheet(InventQSS)
        '''
        self.button_confirm.setStyleSheet("QPushButton {\
                                                background-color: #bcbdbc;\
                                                color: #000000;\
                                                border-style: outset;\
                                                padding: 3px;\
                                                font: bold 15px;\
                                                border-width: 2px;\
                                                border-radius: 10px;\
                                                border-color: #facccc;\
                                            }\
                                            QPushButton:pressed {\
                                                background-color: lightgreen;\
                                            }")
        '''
        self.button_cancel = QPushButton("关闭") #, objectName='InvenButton')
        #self.button_cancel.setStyleSheet(objectName='InvenButton')

        #self.button_cancel.setFont(QFont('黑体', all_font_size))
        self.button_cancel.clicked.connect(self.close_inventory)
        hbox.addStretch()
        hbox.addWidget(self.button_confirm)
        hbox.addStretch()
        hbox.addWidget(self.button_cancel)
        hbox.addStretch()

        hbox_0 = QHBoxLayout()
        title = QLabel("宠物背包")
        title.setStyleSheet(IvenTitle)
        icon = QLabel()
        icon.setStyleSheet(IvenTitle)
        inven_image = QImage()
        inven_image.load('res/icons/Inven_icon.png')
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(inven_image.scaled(20*size_factor,20*size_factor)))
        hbox_0.addWidget(icon)
        hbox_0.addWidget(title)
        hbox_0.addStretch()
        hbox_0.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        windowLayout = QVBoxLayout()
        #windowLayout.addWidget(QLabel(" "))
        windowLayout.addLayout(hbox_0)
        #windowLayout.addWidget(QLabel(" "))
        windowLayout.addWidget(self.scrollArea) #ItemGroupBox)
        windowLayout.addLayout(hbox)

        #radius = 10
        self.centralwidget.setLayout(windowLayout)
        self.centralwidget.setStyleSheet(InvenStyle)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.centralwidget)
        self.setLayout(self.layout_window)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        #self.setFixedSize(253,379)

        #self.setLayout(windowLayout)
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        #self.setFixedSize(235,379)
        #self.setStyleSheet(InvenStyle)
        '''
        radius = 10.0
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        mask = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)
        '''
        
    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        if event.button() == Qt.LeftButton:
            # 左键绑定拖拽
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            event.accept()
            self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件, 左键且绑定跟随, 移动窗体
        :param event:
        :return:
        """
        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        松开鼠标操作
        :param event:
        :return:
        """
        self.is_follow_mouse = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    def change_selected(self, selected_index):

        if self.selected_cell == selected_index:
            self.selected_cell = None
            self.changeButton()
        elif self.selected_cell is not None:
            self.cells_dict[self.selected_cell].unselected()
            self.selected_cell = selected_index
            #self.changeButton()
        else:
            self.selected_cell = selected_index
            self.changeButton()

    def item_removed(self, rm_index):
        self.items_numb[rm_index] = 0
        self.empty_cell.append(rm_index)
        self.empty_cell.sort()

    def changeButton(self):
        if self.selected_cell is None:
            self.button_confirm.setDisabled(True)
            '''
            self.button_confirm.setStyleSheet("QPushButton {\
                                                background-color: #bcbdbc;\
                                                color: #000000;\
                                                border-style: outset;\
                                                padding: 3px;\
                                                font: bold 15px;\
                                                border-width: 2px;\
                                                border-radius: 10px;\
                                                border-color: #facccc;\
                                            }\
                                            QPushButton:pressed {\
                                                background-color: lightgreen;\
                                            }")
            '''    
        else:
            self.button_confirm.setDisabled(False)
            '''
            self.button_confirm.setStyleSheet("QPushButton {\
                                                background-color: #EA4C89;\
                                                color: #000000;\
                                                border-style: outset;\
                                                padding: 3px;\
                                                font: bold 15px;\
                                                border-width: 2px;\
                                                border-radius: 10px;\
                                                border-color: #facccc;\
                                            }\
                                            QPushButton:pressed {\
                                                background-color: lightgreen;\
                                            }")
            '''

    def confirm(self):
        
        if self.selected_cell is None: #无选择
            return

        item_name_selected = self.cells_dict[self.selected_cell].item_name

        #数值已满 且物品均为正向效果
        #if (settings.pet_data.hp == 100 and self.items_data.item_dict[item_name_selected]['effect_HP'] >= 0)and\
        #   (settings.pet_data.fv == 100 and self.items_data.item_dict[item_name_selected]['effect_EM'] >= 0):
        #    return

        # 使用物品所消耗的数值不足 （当有负向效果时）
        if (settings.pet_data.hp + self.items_data.item_dict[item_name_selected]['effect_HP']) < 0: # or\
            #(settings.pet_data.em + self.items_data.item_dict[item_name_selected]['effect_EM']) < 0:
            return

        else: #成功使用物品
            self.items_numb[self.selected_cell] -= 1

            # change pet_data
            settings.pet_data.change_item(item_name_selected, item_change=-1)

            # signal to item label
            self.cells_dict[self.selected_cell].unselected()
            self.cells_dict[self.selected_cell].consumeItem()

            # signal to act feed animation
            self.use_item_inven.emit(item_name_selected)
            self.item_note.emit(item_name_selected, '[%s] 数量 -1'%item_name_selected)

            # change button
            self.selected_cell = None
            self.changeButton()

        return

    def add_items(self, n_items, item_names=[]):
        # 如果没有item_name，则随机一个物品
        if len(item_names) == 0:
            #print('check')
            item_names = random.choices(self.all_items, weights=self.all_probs, k=n_items)
        #print(n_items, item_names)
        # 物品添加列表
        items_toadd = {}
        for i in range(n_items):
            item_name = item_names[int(i%len(item_names))]
            if item_name in items_toadd.keys():
                items_toadd[item_name] += 1
            else:
                items_toadd[item_name] = 1

        # 依次添加物品
        for item in items_toadd.keys():
            self.add_item(item, items_toadd[item])


    def add_item(self, item_name, n_items):
        item_exist = False
        for i in list(set(self.cells_dict.keys())-set(self.empty_cell)):
            if self.cells_dict[i].item_name == item_name:
                item_index = i
                item_exist = True
                break
            else:
                continue

        if item_exist:
            self.items_numb[item_index] += n_items
            # signal to item label
            self.cells_dict[item_index].addItem(n_items)
        elif self.empty_cell:
            item_index = self.empty_cell[0]
            self.empty_cell = self.empty_cell[1:]

            self.cells_dict[item_index].registItem(self.items_data.item_dict[item_name], n_items)
        else:
            item_index = len(self.cells_dict.keys())

            n_row = item_index // self.inven_shape[1]
            n_col = (item_index - (n_row-1)*self.inven_shape[1]) % self.inven_shape[1]

            self.items_numb[item_index] = int(n_items)
            self.cells_dict[item_index] = Inventory_item(item_index, self.items_data.item_dict[item_name], n_items)
            self.cells_dict[item_index].Ii_selected.connect(self.change_selected)
            self.cells_dict[item_index].Ii_removed.connect(self.item_removed)
            self.layout.addWidget(self.cells_dict[item_index], n_row, n_col)

        self.item_note.emit(item_name, '[%s] 数量 +%s'%(item_name, n_items))
        # change pet_data
        settings.pet_data.change_item(item_name, item_change=n_items)

    def fvchange(self, fv_lvl):

        all_items = []
        all_probs = []
        #确定物品掉落概率
        for item in self.items_data.item_dict.keys():
            all_items.append(item)
            all_probs.append((self.items_data.item_dict[item]['drop_rate'])*int(self.items_data.item_dict[item]['fv_lock']<=fv_lvl))
        if sum(all_probs) != 0:
            all_probs = [i/sum(all_probs) for i in all_probs]

        self.all_items = all_items
        self.all_probs = all_probs
        #print(self.all_items)
        #print(self.all_probs)







##############################
#           通知栏
##############################

class QToaster(QFrame):
    closed_note = pyqtSignal(str, name='closed_note')

    def __init__(self, note_index,
                 message='', #parent
                 icon=QStyle.SP_MessageBoxInformation,
                 corner=Qt.BottomRightCorner,
                 height_margin=10,
                 closable=True,
                 timeout=5000,
                 parent=None):
        super(QToaster, self).__init__(parent)

        #def __init__(self, *args, **kwargs):
        #    super(QToaster, self).__init__(*args, **kwargs)
        self.note_index = note_index
        QHBoxLayout(self)

        self.setSizePolicy(QSizePolicy.Maximum, 
                           QSizePolicy.Maximum)

        self.setStyleSheet(f'''
            QToaster {{
                border: {int(max(1, int(1*size_factor)))}px solid black;
                border-radius: {int(4*size_factor)}px; 
                background: palette(window);
            }}
        ''')
        # alternatively:
        # self.setAutoFillBackground(True)
        # self.setFrameShape(self.Box)

        self.timer = QTimer(singleShot=True, timeout=self.hide)

        '''
        if self.parent():
            self.opacityEffect = QtWidgets.QGraphicsOpacityEffect(opacity=0)
            self.setGraphicsEffect(self.opacityEffect)
            self.opacityAni = QtCore.QPropertyAnimation(self.opacityEffect, b'opacity')
            # we have a parent, install an eventFilter so that when it's resized
            # the notification will be correctly moved to the right corner
            self.parent().installEventFilter(self)
        else:
            # there's no parent, use the window opacity property, assuming that
            # the window manager supports it; if it doesn't, this won'd do
            # anything (besides making the hiding a bit longer by half a second)
        '''
        self.opacityAni = QPropertyAnimation(self, b'windowOpacity')
        self.opacityAni.setStartValue(0.)
        self.opacityAni.setEndValue(1.)
        self.opacityAni.setDuration(100)
        self.opacityAni.finished.connect(self.checkClosed)

        self.corner = Qt.TopLeftCorner
        self.margin = 10*size_factor

        self.setupMessage(message, icon, corner, height_margin, closable, timeout)

    def _closeit(self):
        #self.closed_note.emit(self.note_index)
        self.close()

    def checkClosed(self):
        # if we have been fading out, we're closing the notification
        if self.opacityAni.direction() == self.opacityAni.Backward:
            self._closeit()

    def restore(self):
        # this is a "helper function", that can be called from mouseEnterEvent
        # and when the parent widget is resized. We will not close the
        # notification if the mouse is in or the parent is resized
        self.timer.stop()
        # also, stop the animation if it's fading out...
        self.opacityAni.stop()
        # ...and restore the opacity
        '''
        if self.parent():
            self.opacityEffect.setOpacity(1)
        else:
        '''
        self.setWindowOpacity(1)

    def hide(self):
        # start hiding
        self.opacityAni.setDirection(self.opacityAni.Backward)
        self.opacityAni.setDuration(500)
        self.opacityAni.start()

    '''
    def eventFilter(self, source, event):
        if source == self.parent() and event.type() == QtCore.QEvent.Resize:
            self.opacityAni.stop()
            parentRect = self.parent().rect()
            geo = self.geometry()
            if self.corner == QtCore.Qt.TopLeftCorner:
                geo.moveTopLeft(
                    parentRect.topLeft() + QtCore.QPoint(self.margin, self.margin))
            elif self.corner == QtCore.Qt.TopRightCorner:
                geo.moveTopRight(
                    parentRect.topRight() + QtCore.QPoint(-self.margin, self.margin))
            elif self.corner == QtCore.Qt.BottomRightCorner:
                geo.moveBottomRight(
                    parentRect.bottomRight() + QtCore.QPoint(-self.margin, -self.margin))
            else:
                geo.moveBottomLeft(
                    parentRect.bottomLeft() + QtCore.QPoint(self.margin, -self.margin))
            self.setGeometry(geo)
            self.restore()
            self.timer.start()
        return super(QToaster, self).eventFilter(source, event)
    '''

    def enterEvent(self, event):
        self.restore()

    def leaveEvent(self, event):
        self.timer.start()

    def closeEvent(self, event):
        # we don't need the notification anymore, delete it!
        self.closed_note.emit(self.note_index)
        self.deleteLater()

    '''
    def resizeEvent(self, event):
        super(QToaster, self).resizeEvent(event)
        # if you don't set a stylesheet, you don't need any of the following!
        if not self.parent():
            # there's no parent, so we need to update the mask
            path = QtGui.QPainterPath()
            path.addRoundedRect(QtCore.QRectF(self.rect()).translated(-.5, -.5), 4, 4)
            self.setMask(QtGui.QRegion(path.toFillPolygon(QtGui.QTransform()).toPolygon()))
        else:
            self.clearMask()
    '''

    #@staticmethod
    def setupMessage(self,
                    message='', #parent
                    icon=QStyle.SP_MessageBoxInformation, 
                    corner=Qt.BottomRightCorner,
                    height_margin=10,
                    closable=True, 
                    timeout=5000): #, desktop=False, parentWindow=True):

        

        #if not parent or desktop:
        #self = QToaster(None)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.BypassWindowManagerHint | Qt.SubWindow)
        # This is a dirty hack!
        # parentless objects are garbage collected, so the widget will be
        # deleted as soon as the function that calls it returns, but if an
        # object is referenced to *any* other object it will not, at least
        # for PyQt (I didn't test it to a deeper level)
        #self.__self = self

        currentScreen = QApplication.primaryScreen()
        '''
            if parent and parent.window().geometry().size().isValid():
                # the notification is to be shown on the desktop, but there is a
                # parent that is (theoretically) visible and mapped, we'll try to
                # use its geometry as a reference to guess which desktop shows
                # most of its area; if the parent is not a top level window, use
                # that as a reference
                reference = parent.window().geometry()
            else:
        '''
        # the parent has not been mapped yet, let's use the cursor as a
        # reference for the screen
        reference = QRect(QCursor.pos() - QPoint(1, 1), 
                          QSize(3, 3))
        maxArea = 0
        for screen in QApplication.screens():
            intersected = screen.geometry().intersected(reference)
            area = intersected.width() * intersected.height()
            if area > maxArea:
                maxArea = area
                currentScreen = screen
        parentRect = currentScreen.availableGeometry()
        '''
        else:
            self = QToaster(parent)
            parentRect = parent.rect()
        '''

        self.timer.setInterval(timeout)

        # use Qt standard icon pixmaps; see:
        # https://doc.qt.io/qt-5/qstyle.html#StandardPixmap-enum
        #if isinstance(icon, QStyle.StandardPixmap):
        labelIcon = QLabel()
        #size = self.style().pixelMetric(QStyle.PM_SmallIconSize)
        labelIcon.setFixedSize(24*size_factor,24*size_factor)
        labelIcon.setScaledContents(True)
        labelIcon.setPixmap(QPixmap.fromImage(icon)) #.scaled(24,24)))

        self.layout().addWidget(labelIcon)
        #icon = self.style().standardIcon(icon)
        #labelIcon.setPixmap(icon.pixmap(size))

        self.label = QLabel(message)
        font = QFont('黑体')
        #print(settings.font_factor)
        font.setPointSize(10)
        self.label.setFont(font) #QFont('黑体', int(10/screen_scale)))
        self.label.setWordWrap(True)
        self.layout().addWidget(self.label, Qt.AlignLeft) # | Qt.AlignVCenter)

        if closable:
            self.closeButton = QToolButton()
            self.layout().addWidget(self.closeButton)
            closeIcon = self.style().standardIcon(QStyle.SP_TitleBarCloseButton)
            self.closeButton.setIcon(closeIcon)
            iw = int(self.closeButton.iconSize().width() * size_factor)
            self.closeButton.setIconSize(QSize(iw,iw))
            self.closeButton.setAutoRaise(True)
            self.closeButton.clicked.connect(self._closeit)

        self.timer.start()

        # raise the widget and adjust its size to the minimum
        self.raise_()
        self.setFixedWidth(200*size_factor)
        self.adjustSize()
        self.setFixedHeight(self.height()*1.3)


        self.corner = corner
        self.height_margin = height_margin*size_factor

        geo = self.geometry()
        # now the widget should have the correct size hints, let's move it to the
        # right place
        if corner == Qt.TopLeftCorner:
            geo.moveTopLeft(
                parentRect.topLeft() + QPoint(self.margin, self.margin+self.height_margin))
        elif corner == Qt.TopRightCorner:
            geo.moveTopRight(
                parentRect.topRight() + QPoint(-self.margin, self.margin+self.height_margin))
        elif corner == Qt.BottomRightCorner:
            geo.moveBottomRight(
                parentRect.bottomRight() + QPoint(-self.margin, -(self.margin+self.height_margin)))
        else:
            geo.moveBottomLeft(
                parentRect.bottomLeft() + QPoint(self.margin, -(self.margin+self.height_margin)))

        self.setGeometry(geo)
        self.show()
        self.opacityAni.start()
        #return self.height()




























