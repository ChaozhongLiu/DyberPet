import os
import sys
import time
import math
import json
import types
import random
import ctypes
import inspect
import textwrap as tr
from typing import List
from datetime import datetime, timedelta

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QRectF
from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QEvent, QRect, QSize, QPropertyAnimation
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontDatabase, QColor, QPainterPath, QRegion, QIntValidator, QDoubleValidator

try:
    size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
except:
    size_factor = 1
all_font_size = 10 #int(10/screen_scale)

import DyberPet.settings as settings
from DyberPet.DyberPetData.file import getFile

##############################
#          General
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
    image: url(':/resources/icons/check_icon.png')
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

##############################
#          Settings
##############################
sliderStyle = f"""
QSlider::groove:horizontal {{
border: {int(max(1,int(1*size_factor)))}px solid #bbb;
background: white;
height: {int(7*size_factor)}px;
border-radius: {int(3*size_factor)}px;
}}

QSlider::sub-page:horizontal {{
background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,
    stop: 0 #8fccff, stop: 1 #bbdbf7);
background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
    stop: 0 #bbdbf7, stop: 1 #66baff);
border: {int(max(1,int(1*size_factor)))}px solid #777;
height: {int(7*size_factor)}px;
border-radius: {int(3*size_factor)}px;
}}

QSlider::add-page:horizontal {{
background: #fff;
border: {int(max(1,int(1*size_factor)))}px solid #777;
height: {int(7*size_factor)}px;
border-radius: {int(3*size_factor)}px;
}}

QSlider::handle:horizontal {{
background: qlineargradient(x1: 0, y1: 1, x2: 1, y2: 0,stop: 0 #f3d5f7, stop: 0.5 #fbf6e7,stop: 1 #e6fcf5);
border: {int(max(1,int(1*size_factor)))}px solid #777;
width: {int(12*size_factor)}px;
margin-top: -{int(2*size_factor)}px;
margin-bottom: -{int(2*size_factor)}px;
border-radius: {int(4*size_factor)}px;
}}

QSlider::handle:horizontal:hover {{
background: qlineargradient(x1: 0, y1: 1, x2: 1, y2: 0,stop: 0 #f3d5f7, stop: 0.5 #f6eac6,stop: 1 #c4f8e7);
border: {int(max(1,int(1*size_factor)))}px solid #444;
border-radius: {int(4*size_factor)}px;
}}

QSlider::sub-page:horizontal:disabled {{
background: #bbb;
border-color: #999;
}}

QSlider::add-page:horizontal:disabled {{
background: #eee;
border-color: #999;
}}

QSlider::handle:horizontal:disabled {{
background: #eee;
border: {int(max(1,int(1*size_factor)))}px solid #aaa;
border-radius: {int(4*size_factor)}px;
}}
"""
ComboBoxStyle = f"""
QComboBox {{
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: {int(4*size_factor)}px;
    padding-left: {int(10*size_factor)}px;
    font-family: "黑体";
    font-size: 16px;
}}

QComboBox::drop-down {{
    border: 0px;
}}

QComboBox::down-arrow {{
    image: url(:/resources/icons/arrow-204-32.ico);
    width: {int(12*size_factor)}px;
    height: {int(12*size_factor)}px;
    margin-right: 15px;
}}

QComboBox::on {{
    border: 3px solid #c2dbfe
}}

QComboBox QAbstractItemView {{
    font-size: 12px;
    border: 1px solid rgba(0,0,0,25);
    padding: {int(5*size_factor)}px;
    padding-left: {int(10*size_factor)}px;
    background-color: #fff;
    outline: 0px;
}}

"""


SettingStyle = f"""
QFrame {{
    background:#F5F4EF;
    border: {int(3*size_factor)}px solid #F5F4EF;
    border-radius: {int(10*size_factor)}px;
}}

QLabel {{
    font-size: {int(16*size_factor)}px;
    font-family: "黑体";
}}

{sliderStyle}

QCheckBox {{
    padding: {int(2*size_factor)}px;
    font-size: {int(16*size_factor)}px;
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
    image: url(:/resources/icons/check_icon.png)
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

{pushbuttonStyle}
"""

class SettingUI(QWidget):
    close_setting = pyqtSignal(name='close_setting')
    scale_changed = pyqtSignal(name='scale_changed')
    ontop_changed = pyqtSignal(name='ontop_changed')

    def __init__(self, parent=None):
        super(SettingUI, self).__init__(parent)
        self.is_follow_mouse = False

        # SettingUI window
        self.centralwidget = QFrame()
        self.centralwidget.setStyleSheet(SettingStyle)
        vbox_s = QVBoxLayout()

        hbox_t0 = QHBoxLayout()
        self.title = QLabel("设置")
        self.title.setStyleSheet(TomatoTitle)
        icon = QLabel()
        #icon.setStyleSheet(TomatoTitle)
        image = QImage()
        image.load(getFile().locateresources(str='icons/Setting_icon.png'))
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(image)) #.scaled(20,20)))
        icon.setFixedSize(int(25*size_factor), int(25*size_factor))
        hbox_t0.addWidget(icon, Qt.AlignBottom | Qt.AlignLeft)
        hbox_t0.addWidget(self.title, Qt.AlignVCenter | Qt.AlignLeft)
        hbox_t0.addStretch(1)

        # 缩放
        self.button_close = QPushButton()
        self.button_close.setStyleSheet(TomatoClose)
        self.button_close.setFixedSize(int(20*size_factor), int(20*size_factor))
        self.button_close.setIcon(QIcon(getFile().locateresources(str='icons/close_icon.png')))
        self.button_close.setIconSize(QSize(int(20*size_factor),int(20*size_factor)))
        self.button_close.clicked.connect(self.close_setting)
        hbox_t0.addWidget(self.button_close, Qt.AlignTop | Qt.AlignRight)

        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setMinimum(1)
        self.slider_scale.setMaximum(500)
        self.slider_scale.setValue(settings.tunable_scale*100)
        self.slider_scale.setTickInterval(5)
        self.slider_scale.setTickPosition(QSlider.TicksAbove)
        self.scale_label = QLabel("宠物缩放: ") # %s"%(self.slider_scale.value()/100))

        self.scale_text = QLineEdit()
        qfltv = QDoubleValidator()
        qfltv.setRange(0,5,2)
        qfltv.setNotation(QDoubleValidator.StandardNotation)
        #qfltv.setDecimals(2)
        self.scale_text.setValidator(qfltv)
        self.scale_text.setMaxLength(4)
        self.scale_text.setAlignment(Qt.AlignCenter)
        self.scale_text.setFont(QFont("Arial",12))
        self.scale_text.setFixedSize(int(3*15*size_factor), int(20*size_factor))
        self.scale_text.setText(str(settings.tunable_scale))
        self.scale_text.textChanged.connect(self.scale_text_update)

        hbox_s1 = QHBoxLayout()
        hbox_s1.addWidget(self.scale_label)
        hbox_s1.addWidget(self.scale_text) #, Qt.AlignVCenter | Qt.AlignRight)

        self.slider_scale.valueChanged.connect(self.valuechange_scale)
        vbox_s1 = QVBoxLayout()
        vbox_s1.addLayout(hbox_s1)
        vbox_s1.addWidget(self.slider_scale)


        # 重力
        self.slider_gravity = QSlider(Qt.Horizontal)
        self.slider_gravity.setMinimum(1)
        self.slider_gravity.setMaximum(20)
        self.slider_gravity.setValue(settings.gravity*10)
        self.slider_gravity.setTickInterval(1)
        self.slider_gravity.setTickPosition(QSlider.TicksAbove)
        self.slider_gravity.valueChanged.connect(self.valuechange_gravity)

        self.gravity_label = QLabel("重力加速度: ") #%s"%(self.slider_gravity.value()/10))
        self.gravity_text = QLineEdit()
        qfltv = QDoubleValidator()
        qfltv.setRange(0,10,2)
        qfltv.setNotation(QDoubleValidator.StandardNotation)
        #qfltv.setDecimals(2)
        self.gravity_text.setValidator(qfltv)
        self.gravity_text.setMaxLength(4)
        self.gravity_text.setAlignment(Qt.AlignCenter)
        self.gravity_text.setFont(QFont("Arial",12))
        self.gravity_text.setFixedSize(int(3*15*size_factor), int(20*size_factor))
        self.gravity_text.setText(str(settings.gravity))
        self.gravity_text.textChanged.connect(self.gravity_text_update)
        hbox_s2 = QHBoxLayout()
        hbox_s2.addWidget(self.gravity_label)
        hbox_s2.addWidget(self.gravity_text)

        vbox_s2 = QVBoxLayout()
        vbox_s2.addLayout(hbox_s2)
        vbox_s2.addWidget(self.slider_gravity)

        self.slider_mouse = QSlider(Qt.Horizontal)
        self.slider_mouse.setMinimum(1)
        self.slider_mouse.setMaximum(20)
        self.slider_mouse.setValue(settings.fixdragspeedx*10)
        self.slider_mouse.setTickInterval(1)
        self.slider_mouse.setTickPosition(QSlider.TicksAbove)
        self.slider_mouse.valueChanged.connect(self.valuechange_mouse)

        self.mouse_label = QLabel("鼠标拖拽速度: ") #%s"%(self.slider_mouse.value()/10))
        self.mouse_text = QLineEdit()
        qfltv = QDoubleValidator()
        qfltv.setRange(0,5,2)
        qfltv.setNotation(QDoubleValidator.StandardNotation)
        #qfltv.setDecimals(2)
        self.mouse_text.setValidator(qfltv)
        self.mouse_text.setMaxLength(4)
        self.mouse_text.setAlignment(Qt.AlignCenter)
        self.mouse_text.setFont(QFont("Arial",12))
        self.mouse_text.setFixedSize(int(3*15*size_factor), int(20*size_factor))
        self.mouse_text.setText(str(settings.fixdragspeedx))
        self.mouse_text.textChanged.connect(self.mouse_text_update)
        hbox_s3 = QHBoxLayout()
        hbox_s3.addWidget(self.mouse_label)
        hbox_s3.addWidget(self.mouse_text)

        vbox_s3 = QVBoxLayout()
        vbox_s3.addLayout(hbox_s3)
        vbox_s3.addWidget(self.slider_mouse)

        self.slider_volume = QSlider(Qt.Horizontal)
        self.slider_volume.setMinimum(0)
        self.slider_volume.setMaximum(10)
        self.slider_volume.setValue(settings.volume*10)
        self.slider_volume.setTickInterval(1)
        self.slider_volume.setTickPosition(QSlider.TicksAbove)
        self.volume_label = QLabel("音量: %s"%(self.slider_volume.value()/10))
        self.slider_volume.valueChanged.connect(self.valuechange_volume)
        vbox_s4 = QVBoxLayout()
        vbox_s4.addWidget(self.volume_label)
        vbox_s4.addWidget(self.slider_volume)

        self.checkA = QCheckBox("置顶宠物", self)
        if settings.on_top_hint:
            self.checkA.setChecked(True)
        self.checkA.stateChanged.connect(self.checks_update)
        vbox_s5 = QVBoxLayout()
        vbox_s5.addWidget(self.checkA)


        self.firstpet_label = QLabel("默认启动角色")
        self.first_pet = QComboBox()
        self.first_pet.setStyleSheet(ComboBoxStyle)
        pet_list = json.load(open(getFile().locateresources(str='role/pets.json'), 'r', encoding='UTF-8'))
        self.first_pet.addItems(pet_list)
        self.first_pet.currentTextChanged.connect(self.change_firstpet)
        vbox_s6 = QVBoxLayout()
        vbox_s6.addWidget(self.firstpet_label)
        vbox_s6.addWidget(self.first_pet)

        vbox_s.addLayout(hbox_t0)
        vbox_s.addWidget(QHLine())
        vbox_s.addLayout(vbox_s5)
        vbox_s.addLayout(vbox_s1)
        vbox_s.addLayout(vbox_s2)
        vbox_s.addLayout(vbox_s3)
        vbox_s.addLayout(vbox_s4)
        vbox_s.addLayout(vbox_s6)
        
        self.centralwidget.setLayout(vbox_s)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.centralwidget)
        self.setLayout(self.layout_window)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)

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

    def valuechange_scale(self):
        #print(self.slider_scale.value())
        if settings.tunable_scale >=5 and self.slider_scale.value()==500:
            self.scale_changed.emit()
        else:
            settings.tunable_scale = self.slider_scale.value()/100
            settings.save_settings()
            #self.scale_label.setText("宠物缩放: %s"%(self.slider_scale.value()/100))
            self.scale_text.setText(str(settings.tunable_scale))
            self.scale_changed.emit()

    def scale_text_update(self):
        try:
            scale = float(self.scale_text.text())
        except:
            return
        if scale == 0:
            return
        elif scale == settings.tunable_scale:
            return

        settings.tunable_scale = scale
        settings.save_settings()
        self.slider_scale.setValue(min(5,scale)*100)


    def valuechange_gravity(self):
        if settings.gravity >=2 and self.slider_gravity.value()==20:
            return
        else:
            settings.gravity = self.slider_gravity.value()/10
            settings.save_settings()
            #self.gravity_label.setText("重力加速度: %s"%(self.slider_gravity.value()/10))
            self.gravity_text.setText(str(settings.gravity))
        #self.gravity_changed.emit()

    def gravity_text_update(self):
        try:
            g = float(self.gravity_text.text())
        except:
            return
        if g == 0:
            return
        elif g == settings.gravity:
            return

        settings.gravity = g
        settings.save_settings()
        self.slider_gravity.setValue(min(2,g)*10)


    def valuechange_mouse(self):
        if settings.fixdragspeedx >=2 and self.slider_mouse.value()==20:
            return
        else:
            settings.fixdragspeedx, settings.fixdragspeedy = self.slider_mouse.value()/10, self.slider_mouse.value()/10
            #self.mouse_label.setText("鼠标拖拽速度: %s"%(self.slider_mouse.value()/10))
            settings.save_settings()
            self.mouse_text.setText(str(settings.fixdragspeedx))

        #print(self.slider_mouse.value(), settings.fixdragspeedx)

    def mouse_text_update(self):
        try:
            mouse = float(self.mouse_text.text())
        except:
            return
        if mouse == 0:
            return
        elif mouse == settings.fixdragspeedx:
            return

        settings.fixdragspeedx, settings.fixdragspeedy = mouse, mouse
        settings.save_settings()
        self.slider_mouse.setValue(min(2,mouse)*10)


    def valuechange_volume(self):
        settings.volume = self.slider_volume.value()/10
        self.volume_label.setText("音量: %s"%(self.slider_volume.value()/10))
        settings.save_settings()

    def checks_update(self, state):
        # checking if state is checked
        if state == Qt.Checked:
            # if first check box is selected
            if self.sender() == self.checkA:
                settings.on_top_hint = True
                settings.save_settings()
                self.ontop_changed.emit()
            else:
                return
        elif state == Qt.Unchecked:
            if self.sender() == self.checkA:
                settings.on_top_hint = False
                settings.save_settings()
                self.ontop_changed.emit()
            else:
                return
        else:
            return

    def change_firstpet(self, pet_name):
        pet_list = json.load(open(getFile().locateresources(str='role/pets.json'), 'r', encoding='UTF-8'))
        pet_list.remove(pet_name)
        pet_list = [pet_name] + pet_list
        with open(getFile().locateresources(str='role/pets.json'), 'w', encoding='utf-8') as f:
            json.dump(pet_list, f, ensure_ascii=False, indent=4)




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
    font-size: {int(16*size_factor)}px;
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
        self.title = QLabel("番茄钟")
        self.title.setStyleSheet(TomatoTitle)
        icon = QLabel()
        #icon.setStyleSheet(TomatoTitle)
        image = QImage()
        image.load(getFile().locateresources(str='icons/Tomato_icon.png'))
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(image)) #.scaled(20,20)))
        icon.setFixedSize(int(25*size_factor), int(25*size_factor))
        hbox_t0.addWidget(icon, Qt.AlignBottom | Qt.AlignLeft)
        hbox_t0.addWidget(self.title, Qt.AlignVCenter | Qt.AlignLeft)
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
        self.button_close.setFixedSize(int(20*size_factor), int(20*size_factor))
        self.button_close.setIcon(QIcon(getFile().locateresources(str='icons/close_icon.png')))
        self.button_close.setIconSize(QSize(int(20*size_factor), int(20*size_factor)))
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
        self.n_tomato.setFixedSize(int(38*size_factor), int(38*size_factor))


        self.n_tomato_label1 = QLabel("开始")
        self.n_tomato_label1.setFixedSize(int(100*size_factor), int(76*size_factor))
        self.n_tomato_label1.setAlignment(Qt.AlignCenter)
        self.n_tomato_label2 = QLabel("个循环")
        #n_tomato_label2.setFixedSize(110,80)
        #QFontDatabase.addApplicationFont(getFile().locateresources(str='font/MFNaiSi_Noncommercial-Regular.otf'))
        #n_tomato_label.setFont(QFont('宋体', all_font_size))
        hbox_t1.addStretch()
        hbox_t1.addWidget(self.n_tomato_label1, Qt.AlignVCenter | Qt.AlignRight)
        hbox_t1.addWidget(self.n_tomato, Qt.AlignCenter)
        hbox_t1.addWidget(self.n_tomato_label2, Qt.AlignVCenter | Qt.AlignLeft)

        hbox_t = QHBoxLayout()
        self.button_confirm = QPushButton("确定")
        self.button_confirm.setFixedSize(int(80*size_factor), int(40*size_factor))
        #self.button_confirm.setFont(QFont('宋体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_cancel = QPushButton("停止")
        self.button_cancel.setFixedSize(int(80*size_factor), int(40*size_factor))
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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
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
        self.button_cancel.setDisabled(True)
        self.cancelTm.emit()



##############################
#           专注事项
##############################

FocusStyle = f"""
QFrame {{
    background:#F5F4EF;
    border: {int(3*size_factor)}px solid #F5F4EF;
    border-radius: {int(10*size_factor)}px;
}}
QLabel {{
    font-size: {int(16*size_factor)}px;
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
        self.centralwidget = QFrame()
        self.centralwidget.setStyleSheet(FocusStyle)

        # 标题栏
        hbox_f0 = QHBoxLayout()
        self.title = QLabel("专注时间")
        self.title.setStyleSheet(TomatoTitle)
        icon = QLabel()
        #icon.setStyleSheet(TomatoTitle)
        image = QImage()
        image.load(getFile().locateresources(str='icons/Timer_icon.png'))
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(image)) #.scaled(20,20)))
        icon.setFixedSize(int(25*size_factor), int(25*size_factor))
        hbox_f0.addWidget(icon, Qt.AlignBottom | Qt.AlignLeft)
        hbox_f0.addWidget(self.title, Qt.AlignVCenter | Qt.AlignLeft)
        hbox_f0.addStretch(1)
        self.button_close = QPushButton()
        self.button_close.setStyleSheet(TomatoClose)
        self.button_close.setFixedSize(int(20*size_factor), int(20*size_factor))
        self.button_close.setIcon(QIcon(getFile().locateresources(str='icons/close_icon.png')))
        self.button_close.setIconSize(QSize(int(20*size_factor), int(20*size_factor)))
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
        self.countdown_h.setFixedSize(int(38*size_factor), int(38*size_factor))

        self.countdown_m = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,59)
        self.countdown_m.setValidator(qintv)
        self.countdown_m.setMaxLength(2)
        self.countdown_m.setAlignment(Qt.AlignCenter)
        self.countdown_m.setFont(QFont("Arial",18))
        self.countdown_m.setFixedSize(int(38*size_factor), int(38*size_factor))
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
        self.label_h = QLabel('小时')
        #label_h.setFont(QFont('宋体', all_font_size))
        hbox_f1.addWidget(self.label_h)
        hbox_f1.addWidget(self.countdown_m)
        self.label_m = QLabel('分钟后')
        #label_m.setFont(QFont('宋体', all_font_size))
        hbox_f1.addWidget(self.label_m)
        hbox_f1.addStretch(10)

        hbox_f2 = QHBoxLayout()
        self.time_h = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,23)
        self.time_h.setValidator(qintv)
        self.time_h.setMaxLength(2)
        self.time_h.setAlignment(Qt.AlignCenter)
        self.time_h.setFont(QFont("Arial",18))
        self.time_h.setFixedSize(int(38*size_factor), int(38*size_factor))

        self.time_m = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,59)
        self.time_m.setValidator(qintv)
        self.time_m.setMaxLength(2)
        self.time_m.setAlignment(Qt.AlignCenter)
        self.time_m.setFont(QFont("Arial",18))
        self.time_m.setFixedSize(int(38*size_factor), int(38*size_factor))
        '''
        self.time_h = QSpinBox()
        self.time_h.setMinimum(0)
        self.time_h.setMaximum(23)
        self.time_m = QSpinBox()
        self.time_m.setMinimum(0)
        self.time_m.setMaximum(59)
        '''
        self.label_d = QLabel('到')
        #label_d.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(self.label_d)
        hbox_f2.addWidget(self.time_h)
        self.label_h2 = QLabel('点')
        #label_h.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(self.label_h2)
        hbox_f2.addWidget(self.time_m)
        self.label_m2 = QLabel('分')
        #label_m.setFixedHeight(100)
        #label_m.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        #label_m.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(self.label_m2)
        hbox_f2.addStretch(10)
        #hbox_f2.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        hbox_f3 = QHBoxLayout()
        self.button_confirm = QPushButton("开始")
        #self.button_confirm.setFont(QFont('宋体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_cancel = QPushButton("停止")
        #self.button_cancel.setFont(QFont('宋体', all_font_size))
        self.button_cancel.clicked.connect(self.cancelFocus_func)
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
        space_label.setFixedHeight(int(20*size_factor))
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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)

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
                    if h==0 and m==0:
                        return
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

    def cancelFocus_func(self):
        self.button_cancel.setDisabled(True)
        self.cancelFocus.emit()

    def endFocus(self):
        self.focus_on = False
        self.pausable = False
        self.button_confirm.setText('开始')
        self.button_cancel.setDisabled(True)
        self.button_confirm.setDisabled(False)





##############################
#           提醒事项
##############################
RemindStyle = f"""
QFrame {{
    background:#F5F4EF;
    border: {int(3*size_factor)}px solid #F5F4EF;
    border-radius: {int(10*size_factor)}px;
}}

QLabel {{
    font-size: {int(15*size_factor)}px;
    font-family: "黑体";
}}

QTextEdit, QListView {{
    border: {int(2*size_factor)}px solid #9f7a6a;
    background-color: white;
    background-attachment: scroll;
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

{pushbuttonStyle}

{checkStyle}
"""

class Remindme(QWidget):
    close_remind = pyqtSignal(name='close_remind')
    confirm_remind = pyqtSignal(str, int, int, str, name='confirm_remind')

    def __init__(self, parent=None):
        super(Remindme, self).__init__(parent)
        # Remindme time window
        self.is_follow_mouse = False
        self.centralwidget = QFrame()
        self.centralwidget.setStyleSheet(RemindStyle)

        vbox_r = QVBoxLayout()

        self.checkA = QCheckBox("一段时间后提醒", self)
        #self.checkA.setFont(QFont('宋体', all_font_size))
        self.checkB = QCheckBox("定时提醒", self)
        #self.checkB.setFont(QFont('宋体', all_font_size))
        self.checkC = QCheckBox("间隔重复", self)
        #self.checkC.setFont(QFont('宋体', all_font_size))
        self.checkA.stateChanged.connect(self.uncheck)
        self.checkB.stateChanged.connect(self.uncheck)
        self.checkC.stateChanged.connect(self.uncheck)

        # 标题栏
        hbox_r0 = QHBoxLayout()
        self.title = QLabel("提醒事项")
        self.title.setStyleSheet(TomatoTitle)
        icon = QLabel()
        #icon.setStyleSheet(TomatoTitle)
        image = QImage()
        image.load(getFile().locateresources(str='icons/remind_icon.png'))
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(image)) #.scaled(20,20)))
        icon.setFixedSize(int(25*size_factor), int(25*size_factor))
        hbox_r0.addWidget(icon, Qt.AlignBottom | Qt.AlignLeft)
        hbox_r0.addWidget(self.title, Qt.AlignVCenter | Qt.AlignLeft)
        hbox_r0.addStretch(1)

        hbox_r1 = QHBoxLayout()
        self.countdown_h = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,23)
        self.countdown_h.setValidator(qintv)
        self.countdown_h.setMaxLength(2)
        self.countdown_h.setAlignment(Qt.AlignCenter)
        self.countdown_h.setFont(QFont("Arial",18))
        self.countdown_h.setFixedSize(int(38*size_factor), int(38*size_factor))

        self.countdown_m = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,59)
        self.countdown_m.setValidator(qintv)
        self.countdown_m.setMaxLength(2)
        self.countdown_m.setAlignment(Qt.AlignCenter)
        self.countdown_m.setFont(QFont("Arial",18))
        self.countdown_m.setFixedSize(int(38*size_factor), int(38*size_factor))

        hbox_r1.addWidget(self.countdown_h)
        self.label_h = QLabel('小时')
        #label_h.setFont(QFont('宋体', all_font_size))
        hbox_r1.addWidget(self.label_h)
        hbox_r1.addWidget(self.countdown_m)
        self.label_m = QLabel('分钟后')
        #label_m.setFont(QFont('宋体', all_font_size))
        hbox_r1.addWidget(self.label_m)
        hbox_r1.addStretch(10)

        hbox_r2 = QHBoxLayout()
        self.time_h = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,23)
        self.time_h.setValidator(qintv)
        self.time_h.setMaxLength(2)
        self.time_h.setAlignment(Qt.AlignCenter)
        self.time_h.setFont(QFont("Arial",18))
        self.time_h.setFixedSize(int(38*size_factor), int(38*size_factor))

        self.time_m = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,59)
        self.time_m.setValidator(qintv)
        self.time_m.setMaxLength(2)
        self.time_m.setAlignment(Qt.AlignCenter)
        self.time_m.setFont(QFont("Arial",18))
        self.time_m.setFixedSize(int(38*size_factor), int(38*size_factor))

        self.label_d = QLabel('到')
        #label_d.setFont(QFont('宋体', all_font_size))
        hbox_r2.addWidget(self.label_d)
        hbox_r2.addWidget(self.time_h)
        self.label_h2 = QLabel('点')
        #label_h.setFont(QFont('宋体', all_font_size))
        hbox_r2.addWidget(self.label_h2)
        hbox_r2.addWidget(self.time_m)
        self.label_m2 = QLabel('分')
        #label_m.setFont(QFont('宋体', all_font_size))
        hbox_r2.addWidget(self.label_m2)
        hbox_r2.addStretch(10)

        hbox_r5 = QHBoxLayout()
        self.check1 = QCheckBox("在", self) # xx 分时
        #self.check1.setFont(QFont('宋体', all_font_size))
        self.check2 = QCheckBox("每", self)
        #self.check2.setFont(QFont('宋体', all_font_size))
        self.check1.stateChanged.connect(self.uncheck)
        self.check2.stateChanged.connect(self.uncheck)

        self.every_min = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(0,59)
        self.every_min.setValidator(qintv)
        self.every_min.setMaxLength(2)
        self.every_min.setAlignment(Qt.AlignCenter)
        self.every_min.setFont(QFont("Arial",18))
        self.every_min.setFixedSize(int(38*size_factor), int(38*size_factor))

        self.label_em = QLabel('分时')
        #label_em.setFont(QFont('宋体', all_font_size))

        self.interval_min = QLineEdit()
        qintv = QIntValidator()
        qintv.setRange(1,999)
        self.interval_min.setValidator(qintv)
        self.interval_min.setMaxLength(3)
        self.interval_min.setAlignment(Qt.AlignCenter)
        self.interval_min.setFont(QFont("Arial",18))
        self.interval_min.setFixedSize(int(57*size_factor), int(38*size_factor))

        self.label_im = QLabel('分钟')
        #label_im.setFont(QFont('宋体', all_font_size))
        hbox_r5.addWidget(self.check1)
        hbox_r5.addWidget(self.every_min)
        hbox_r5.addWidget(self.label_em)
        hbox_r5.addWidget(self.check2)
        hbox_r5.addWidget(self.interval_min)
        hbox_r5.addWidget(self.label_im)
        hbox_r5.addStretch(10)

        #hbox_r3 = QHBoxLayout()
        self.button_confirm = QPushButton("确定")
        #self.button_confirm.setFont(QFont('宋体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        #self.button_cancel = QPushButton("关闭")
        #self.button_cancel.setFont(QFont('宋体', all_font_size))
        #self.button_cancel.clicked.connect(self.close_remind)
        #hbox_r3.addWidget(self.button_confirm)
        #hbox_r3.addWidget(self.button_cancel)

        hbox_r4 = QHBoxLayout()
        self.e1 = QLineEdit()
        self.e1.setFixedSize(int(250*size_factor), int(38*size_factor))
        #self.e1.setMaxLength(14)
        self.e1.setAlignment(Qt.AlignLeft)
        self.e1.setFont(QFont("宋体",12))
        hbox_r4.addWidget(self.e1)
        hbox_r4.addWidget(self.button_confirm)
        hbox_r4.addStretch(1)

        #label_method = QLabel('提醒方式')
        #label_method.setFont(QFont('宋体', all_font_size))
        #label_method.setStyleSheet("color : grey")
        vbox_r.addLayout(hbox_r0)
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

        self.label_r = QLabel('提醒我：')
        #label_r.setFont(QFont('宋体', all_font_size))
        #label_r.setStyleSheet("color : grey")
        vbox_r.addWidget(self.label_r)
        #vbox_r.addWidget(QHLine())
        vbox_r.addLayout(hbox_r4)
        #vbox_r.addLayout(hbox_r3, Qt.AlignBottom | Qt.AlignHCenter)
        vbox_r.addStretch(1)


        vbox_r2 = QVBoxLayout()

        hbox_r6 = QHBoxLayout()

        icon = QLabel()
        #icon.setStyleSheet(TomatoTitle)
        image = QImage()
        image.load(getFile().locateresources(str='icons/note_icon.png'))
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(image)) #.scaled(20,20)))
        icon.setFixedSize(int(25*size_factor), int(25*size_factor))
        hbox_r6.addWidget(icon, Qt.AlignBottom | Qt.AlignLeft)

        self.label_on = QLabel('备忘录')
        self.label_on.setToolTip('备忘录自动保存，\n下次打开时自动载入内容和提醒事项')
        self.label_on.setStyleSheet(TomatoTitle)
        self.label_on.setFixedHeight(int(25*size_factor))
        #label_on.setFont(QFont('宋体', all_font_size))
        #label_on.setStyleSheet("color : grey")

        self.button_close = QPushButton()
        self.button_close.setStyleSheet(TomatoClose)
        self.button_close.setFixedSize(int(20*size_factor), int(20*size_factor))
        self.button_close.setIcon(QIcon(getFile().locateresources(str='icons/close_icon.png')))
        self.button_close.setIconSize(QSize(int(20*size_factor), int(20*size_factor)))
        self.button_close.clicked.connect(self.close_remind)

        hbox_r6.addWidget(self.label_on)
        hbox_r6.addWidget(self.button_close, Qt.AlignTop | Qt.AlignRight)

        vbox_r2.addLayout(hbox_r6)
        vbox_r2.addWidget(QHLine())
        self.e2 = QTextEdit()
        #self.e2.setMaxLength(14)
        self.e2.setAlignment(Qt.AlignLeft)
        self.e2.setFont(QFont("宋体",12))
        self.e2.textChanged.connect(self.save_remindme)
        vbox_r2.addWidget(self.e2)

        hbox_all = QHBoxLayout()
        hbox_all.addLayout(vbox_r)
        #hbox_all.addStretch(0.5)
        #hbox_all.addWidget(QVLine())
        #hbox_all.addStretch(0.5)
        hbox_all.addLayout(vbox_r2)

        self.centralwidget.setLayout(hbox_all)
        vbox_window = QVBoxLayout()
        vbox_window.addWidget(self.centralwidget)
        self.setLayout(vbox_window)
        #self.setFixedSize(450*size_factor,300*size_factor)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)

        if os.path.isfile(getFile().locatedata(str='remindme.txt')):
            f = open(getFile().locatedata(str='remindme.txt'), 'r', encoding='UTF-8')
            texts = f.read()
            f.close()
            texts = texts.lstrip('\n')
            self.e2.setPlainText(texts)
        else:
            f = open(getFile().locatedata(str='remindme.txt'), 'w', encoding='UTF-8')
            f.write('')
            f.close()

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

    def initial_task(self):
        f = open(getFile().locatedata(str='remindme.txt'), 'r', encoding='UTF-8')
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
            #hs = self.countdown_h.value()
            #ms = self.countdown_m.value()
            hs = self.countdown_h.text()
            ms = self.countdown_m.text()
            if hs == '' and ms=='':
                return
            else:
                try:
                    hs = int(hs)
                except:
                    hs=0
                try: 
                    ms = int(ms)
                except:
                    ms=0

            timeset = datetime.now() + timedelta(hours=hs, minutes=ms)
            timeset = timeset.strftime("%m/%d %H:%M")
            remind_text = self.e1.text()
            current_text = self.e2.toPlainText()
            current_text += '%s - %s\n'%(timeset, remind_text)
            self.e2.setPlainText(current_text)
            self.confirm_remind.emit('range', hs, ms, remind_text)

        elif self.checkB.isChecked():
            #hs = self.time_h.value()
            #ms = self.time_m.value()
            hs = self.time_h.text()
            ms = self.time_m.text()
            if hs == '' or ms=='':
                return

            else:
                hs = int(hs)
                ms = int(ms)
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
                self.confirm_remind.emit('point', hs, ms, remind_text)

        elif self.checkC.isChecked():
            remind_text = self.e1.text()
            current_text = self.e2.toPlainText()
            if self.check1.isChecked() and self.every_min.text() != '':
                current_text += '#重复 每到 %s 分时 - %s\n'%(int(self.every_min.text()), remind_text)
                self.confirm_remind.emit('repeat_point', 0, int(self.every_min.text()), remind_text)

            elif self.check2.isChecked() and self.interval_min.text() != '':
                current_text += '#重复 每隔 %s 分钟 - %s\n'%(int(self.interval_min.text()), remind_text)
                self.confirm_remind.emit('repeat_interval', 0, int(self.interval_min.text()), remind_text)

            self.e2.setPlainText(current_text)

    def save_remindme(self):
        #print(self.e2.toPlainText()=='')
        f = open(getFile().locatedata(str='remindme.txt'), 'w', encoding='UTF-8')
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

CollectStyle = f"""
QLabel{{
    border : {int(2*size_factor)}px solid #e1eaf4;
    border-radius: {int(5*size_factor)}px;
    background-color: #e1eaf4
}}
"""

ItemClick = f"""
QLabel{{
    border : {int(2*size_factor)}px solid #B1C790;
    border-radius: {int(5*size_factor)}px;
    background-color: #EFEBDF
}}
"""

CollectClick = f"""
QLabel{{
    border : {int(2*size_factor)}px solid #B1C790;
    border-radius: {int(5*size_factor)}px;
    background-color: #e1eaf4
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
    Ii_selected = pyqtSignal(int, bool, name="Ii_selected")
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
        self.item_name = 'None'
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
        self.clct_inuse = False

        if item_config is not None:
            self.item_name = item_config['name']
            self.image = item_config['image']
            self.image = self.image.scaled(self.size_wh,self.size_wh)
            self.setPixmap(QPixmap.fromImage(self.image))
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
        if self.item_num > 0:
            text_printer = QPainter(self)
            text_printer.setFont(self.font)
            text_printer.drawText(QRect(0, 0, int(self.size_wh-3*size_factor), int(self.size_wh-3*size_factor)), Qt.AlignBottom | Qt.AlignRight, str(self.item_num))



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
        self.image = self.image.scaled(self.size_wh,self.size_wh)
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
    '''
    def changeNum(self):
        self.setPixmap(QPixmap.fromImage(self.image))
    '''

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
    item_anim = pyqtSignal(str, name='item_anim')
    #confirm_inventory = pyqtSignal(str, int, int, str, name='confirm_inventory')

    def __init__(self, items_data, parent=None):
        super(Inventory, self).__init__(parent)

        self.is_follow_mouse = False
        
        self.items_data = items_data
        self.calculate_droprate()
        '''
        self.all_items = []
        self.all_probs = []
        #确定物品掉落概率
        for item in items_data.item_dict.keys():
            self.all_items.append(item)
            self.all_probs.append((items_data.item_dict[item]['drop_rate'])*int(items_data.item_dict[item]['fv_lock']<=settings.pet_data.fv_lvl))
        if sum(self.all_probs) != 0:
            self.all_probs = [i/sum(self.all_probs) for i in self.all_probs]
        '''
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
            if items_data.item_dict[item]['item_type'] != 'collection':
                continue
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

        for item in settings.pet_data.items.keys():
            if items_data.item_dict[item]['item_type'] in ['collection', 'dialogue']:
                continue
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

        for item in settings.pet_data.items.keys():
            if items_data.item_dict[item]['item_type'] != 'dialogue':
                continue
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
        self.title = QLabel("宠物背包")
        self.title.setStyleSheet(IvenTitle)
        icon = QLabel()
        icon.setStyleSheet(IvenTitle)
        inven_image = QImage()
        inven_image.load(getFile().locateresources(str='icons/Inven_icon.png'))
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(inven_image.scaled(int(20*size_factor), int(20*size_factor))))
        hbox_0.addWidget(icon)
        hbox_0.addWidget(self.title)
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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
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

    def change_selected(self, selected_index, clct_inuse):

        if self.selected_cell == selected_index:
            self.selected_cell = None
            self.changeButton(clct_inuse)
        elif self.selected_cell is not None:
            self.cells_dict[self.selected_cell].unselected()
            self.selected_cell = selected_index
            self.changeButton(clct_inuse)
        else:
            self.selected_cell = selected_index
            self.changeButton(clct_inuse)

    def item_removed(self, rm_index):
        self.items_numb[rm_index] = 0
        self.empty_cell.append(rm_index)
        self.empty_cell.sort()

    def changeButton(self, clct_inuse=False):
        if self.selected_cell is None:
            self.button_confirm.setText('使用')
            self.button_confirm.setDisabled(True)
    
        else:
            if clct_inuse:
                self.button_confirm.setText('收回')
            else:
                self.button_confirm.setText('使用')
            self.button_confirm.setDisabled(False)

    def acc_withdrawed(self, item_name):
        cell_index = [i for i in self.cells_dict.keys() if self.cells_dict[i].item_name==item_name]
        cell_index = cell_index[0]
        self.cells_dict[cell_index].consumeItem()


    def confirm(self):
        
        if self.selected_cell is None: #无选择
            return

        item_name_selected = self.cells_dict[self.selected_cell].item_name

        #数值已满 且物品均为正向效果
        #if (settings.pet_data.hp == 100 and self.items_data.item_dict[item_name_selected]['effect_HP'] >= 0)and\
        #   (settings.pet_data.fv == 100 and self.items_data.item_dict[item_name_selected]['effect_EM'] >= 0):
        #    return

        # 判断是否为个别宠物的专属物品
        if len(self.items_data.item_dict[item_name_selected]['pet_limit']) != 0:
            pet_list = self.items_data.item_dict[item_name_selected]['pet_limit']
            if settings.petname not in pet_list:
                self.item_note.emit('system', '[%s] 仅能在切换至 [%s] 后使用哦'%(item_name_selected, '、'.join(pet_list)))
                return

        # 使用物品所消耗的数值不足 （当有负向效果时）
        if (settings.pet_data.hp + self.items_data.item_dict[item_name_selected]['effect_HP']) < 0: # or\
            #(settings.pet_data.em + self.items_data.item_dict[item_name_selected]['effect_EM']) < 0:
            return

        elif self.items_data.item_dict[item_name_selected]['item_type'] == 'consumable': #成功使用物品
            self.items_numb[self.selected_cell] -= 1

            # change pet_data
            settings.pet_data.change_item(item_name_selected, item_change=-1)

            # signal to item label
            self.cells_dict[self.selected_cell].unselected()
            self.cells_dict[self.selected_cell].consumeItem()

            # signal to act feed animation
            self.use_item_inven.emit(item_name_selected)
            self.item_note.emit(item_name_selected, '[%s] -1'%item_name_selected)

            # change button
            self.selected_cell = None
            self.changeButton()

        elif self.items_data.item_dict[item_name_selected]['item_type'] == 'collection':
            #print('collection used')
            self.cells_dict[self.selected_cell].unselected()
            self.cells_dict[self.selected_cell].consumeItem()
            if self.cells_dict[self.selected_cell].clct_inuse:
                self.use_item_inven.emit(item_name_selected)
            else:
                #print('收回')
                self.use_item_inven.emit(item_name_selected)
            self.selected_cell = None
            self.changeButton()

        elif self.items_data.item_dict[item_name_selected]['item_type'] == 'dialogue':
            #print('collection used')
            self.cells_dict[self.selected_cell].unselected()
            #self.cells_dict[self.selected_cell].consumeItem()
            self.use_item_inven.emit(item_name_selected)
            self.selected_cell = None
            self.changeButton()

        return

    def add_items(self, n_items, item_names=[]):
        # 没有可掉落物品 返回
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

        self.item_note.emit(item_name, '[%s] +%s'%(item_name, n_items))
        self.item_anim.emit(item_name)
        # change pet_data
        settings.pet_data.change_item(item_name, item_change=n_items)

    def fvchange(self, fv_lvl):

        if fv_lvl in self.items_data.reward_dict:
            for item_i in self.items_data.reward_dict[fv_lvl]:
                self.add_item(item_i, 1)

        self.calculate_droprate()

    def calculate_droprate(self):

        all_items = []
        all_probs = []
        #确定物品掉落概率
        for item in self.items_data.item_dict.keys():
            all_items.append(item)
            #排除已经获得的收藏品
            if self.items_data.item_dict[item]['item_type'] == 'collection' and settings.pet_data.items.get(item, 0)>0:
                all_probs.append(0)
            else:
                all_probs.append((self.items_data.item_dict[item]['drop_rate'])*int(self.items_data.item_dict[item]['fv_lock']<=settings.pet_data.fv_lvl))
        
        if sum(all_probs) != 0:
            all_probs = [i/sum(all_probs) for i in all_probs]

        self.all_items = all_items
        self.all_probs = all_probs







##############################
#           通知栏
##############################

class QToaster(QFrame):
    closed_note = pyqtSignal(str, str, name='closed_note')

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
        #QHBoxLayout(self)

        self.setSizePolicy(QSizePolicy.Maximum, 
                           QSizePolicy.Maximum)
        
        #self.setStyleSheet(f'''
        #    QToaster {{
        #        border: {int(max(1, int(1*size_factor)))}px solid black;
        #        border-radius: {int(4*size_factor)}px; 
        #        background: palette(window);
        #    }}
        #''')
        
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

        #self.corner = Qt.TopLeftCorner
        self.margin = int(10*size_factor)

        self.close_type = 'faded'

        self.setupMessage(message, icon, corner, height_margin, closable, timeout)

    def _closeit(self, close_type='button'):
        if not close_type:
            close_type = 'button'
        self.close_type = close_type
        #self.closed_note.emit(self.note_index)
        self.close()

    def checkClosed(self):
        # if we have been fading out, we're closing the notification
        if self.opacityAni.direction() == self.opacityAni.Backward:
            self._closeit('faded')

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
        self.closed_note.emit(self.note_index, self.close_type)
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
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.BypassWindowManagerHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
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
        labelIcon.setFixedSize(int(24*size_factor), int(24*size_factor))
        labelIcon.setScaledContents(True)
        labelIcon.setPixmap(QPixmap.fromImage(icon)) #.scaled(24,24)))

        frame = QFrame()
        frame.setStyleSheet(f'''
            QFrame {{
                border: {int(max(1, int(1*size_factor)))}px solid black;
                border-radius: {int(4*size_factor)}px; 
                background: palette(window);
            }}
            QLabel{{
                border: 0px
            }}
        ''')
        hbox = QHBoxLayout()
        hbox.setContentsMargins(10*size_factor,10*size_factor,10*size_factor,10*size_factor)
        hbox.setSpacing(0)

        #self.layout()
        hbox1 = QHBoxLayout()
        hbox1.setContentsMargins(0,0,10*size_factor,0)
        hbox1.addWidget(labelIcon)
        hbox.addLayout(hbox1)
        #icon = self.style().standardIcon(icon)
        #labelIcon.setPixmap(icon.pixmap(size))

        self.label = QLabel(message)
        font = QFont('黑体')
        #print(settings.font_factor)
        font.setPointSize(10)
        self.label.setFont(font) #QFont('黑体', int(10/screen_scale)))
        self.label.setWordWrap(True)
        #self.layout()
        hbox2 = QHBoxLayout()
        hbox2.setContentsMargins(0,0,5*size_factor,0)
        hbox2.addWidget(self.label, Qt.AlignLeft)
        hbox.addLayout(hbox2)
        #hbox.addWidget(self.label, Qt.AlignLeft) # | Qt.AlignVCenter)

        if closable:
            self.closeButton = QToolButton()
            #self.layout().
            hbox.addWidget(self.closeButton)
            closeIcon = self.style().standardIcon(QStyle.SP_TitleBarCloseButton)
            self.closeButton.setIcon(closeIcon)
            iw = int(self.closeButton.iconSize().width() * size_factor)
            self.closeButton.setIconSize(QSize(iw,iw))
            self.closeButton.setAutoRaise(True)
            self.closeButton.clicked.connect(self._closeit)

        frame.setLayout(hbox)
        wholebox = QHBoxLayout()
        wholebox.setContentsMargins(0,0,0,0)
        wholebox.addWidget(frame)
        self.setLayout(wholebox)

        self.timer.start()

        # raise the widget and adjust its size to the minimum
        self.raise_()
        self.setFixedWidth(int(200*size_factor))
        self.adjustSize()
        self.setFixedHeight(self.height()*1.3)


        #self.corner = corner
        self.height_margin = int(height_margin*size_factor)

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





###################
#  对话框
###################
OptionbuttonStyle = f"""
QPushButton {{
    background-color: #ffbdad;
    color: #000000;
    border-style: solid;
    padding: {int(7*size_factor)}px;
    font: {int(16*size_factor)}px;
    font-family: "黑体";
    text-align: left;
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


DialogueClose = f"""
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

DialogueTitle = f"""
QLabel {{
    border: 0;
    background-color: #F5F4EF;
    font-size: {int(15*size_factor)}px;
    font-family: "黑体";
    width: {int(10*size_factor)}px;
    height: {int(20*size_factor)}px
}}
"""
OptionGroupStyle = f"""
QGroupBox {{
    border: {int(max(1,int(1*size_factor)))}px solid transparent;
    background-color: #F5F4EF;
    border-radius: {int(10*size_factor)}px
}}
"""

DialogueClose = f"""
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

DialogueStyle = f"""
QLabel {{
    font-size: {int(16*size_factor)}px;
    font-family: "黑体";
    border: 0px
}}

QFrame{{
    background:#F5F4EF;
    border: {int(3*size_factor)}px solid #F5F4EF;
    border-radius: {int(10*size_factor)}px
}}

QScrollArea {{
    padding: {int(2*size_factor)}px;
    border: {int(3*size_factor)}px solid #F5F4EF;
    background-color: #F5F4EF;
    border-radius: {int(10*size_factor)}px
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

OptionScrollStyle = f"""
QScrollArea {{
    padding: {int(2*size_factor)}px;
    border: {int(3*size_factor)}px solid #9f7a6a;
    background-color: #F5F4EF;
    border-radius: {int(10*size_factor)}px
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


class DPDialogue(QWidget):
    closed_acc = pyqtSignal(str, name='closed_acc')

    def __init__(self, acc_index,
                 message={},
                 pos_x=0,
                 pos_y=0,
                 closable=True,
                 timeout=5000,
                 parent=None):
        super(DPDialogue, self).__init__(parent)

        self.is_follow_mouse = False

        self.acc_index = acc_index
        self.message = message

        self.setSizePolicy(QSizePolicy.Minimum, 
                           QSizePolicy.Minimum)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.BypassWindowManagerHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)


        # 界面设计
        frame = QFrame()
        frame.setStyleSheet(f'''
            QFrame {{
                border: {int(max(1, int(1*settings.size_factor)))}px solid black;
                border-radius: {int(4*settings.size_factor)}px; 
                background: palette(window);
            }}
            QLabel{{
                border: 0px
            }}
        ''')

        # 标题栏
        hbox_0 = QHBoxLayout()
        self.title = QLabel(message.get('title',''))
        self.title.setStyleSheet(DialogueTitle)
        icon = QLabel()
        image = QImage()
        image.load(getFile().locateresources(str='icons/Dialogue_icon.png'))
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap.fromImage(image)) #.scaled(20,20)))
        icon.setFixedSize(int(25*size_factor), int(25*size_factor))
        hbox_0.addWidget(icon, Qt.AlignBottom | Qt.AlignLeft)
        hbox_0.addWidget(self.title, Qt.AlignVCenter | Qt.AlignLeft)
        hbox_0.addStretch(1)
        self.button_close = QPushButton()
        self.button_close.setStyleSheet(DialogueClose)
        self.button_close.setFixedSize(int(20*size_factor), int(20*size_factor))
        self.button_close.setIcon(QIcon(getFile().locateresources(str='icons/close_icon.png')))
        self.button_close.setIconSize(QSize(int(20*size_factor), int(20*size_factor)))
        self.button_close.clicked.connect(self._closeit)
        hbox_0.addWidget(self.button_close, Qt.AlignTop | Qt.AlignRight)

        # 对话文本
        hbox_1 = QHBoxLayout()
        hbox_1.setContentsMargins(5,5,5,5)
        self.text_now = message['start']
        self.label = QLabel(message[message['start']])
        self.label.setFixedWidth(int(250*size_factor))
        self.label.setMinimumSize(int(250*size_factor),int(20*size_factor))
        font = QFont('黑体')
        #print(settings.font_factor)
        font.setPointSize(10)
        self.label.setFont(font) #QFont('黑体', int(10/screen_scale)))
        self.label.setWordWrap(True)
        #self.layout()

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidget(self.label)
        self.scrollArea.setMinimumHeight(int(100*size_factor))
        hbox_1.addWidget(self.scrollArea, Qt.AlignHCenter | Qt.AlignTop)


        # 选项
        self.n_col = 1
        self.OptionGroupBox = QGroupBox()
        self.OptionGroupBox.setStyleSheet(OptionGroupStyle)
        self.OptionLayout = QGridLayout()
        self.OptionLayout.setVerticalSpacing(9)
        self.OptionGenerator(message['start'])

        # Layout
        self.windowLayout = QVBoxLayout()
        self.windowLayout.addLayout(hbox_0, Qt.AlignHCenter | Qt.AlignTop)
        self.windowLayout.addLayout(hbox_1, Qt.AlignHCenter | Qt.AlignTop)
        if self.opts_dict != {}:
            #self.windowLayout.addWidget(QHLine())
            self.scrollArea2 = QScrollArea(self)
            self.scrollArea2.setFrameShape(QFrame.NoFrame)
            self.scrollArea2.setWidgetResizable(True)
            self.scrollArea2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.scrollArea2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scrollArea2.setWidget(self.OptionGroupBox)
            self.scrollArea2.setMinimumHeight(int(200*size_factor))
            self.scrollArea2.setMinimumHeight(int(200*size_factor))
            self.scrollArea2.setStyleSheet(OptionScrollStyle)
            #hbox_1.addWidget(self.scrollArea, Qt.AlignHCenter | Qt.AlignTop)
            self.windowLayout.addWidget(self.scrollArea2) #ItemGroupBox)

        self.centralwidget = QFrame()
        self.centralwidget.setLayout(self.windowLayout)
        self.centralwidget.setStyleSheet(DialogueStyle)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.centralwidget, Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(self.layout_window)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)

        self.setFixedWidth(int(350*size_factor))
        #self.adjustSize()
        #self.setFixedHeight(self.height()*1.1)

        self.move(pos_x-self.width()//2, pos_y-self.height())
        self.show()

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

    def _closeit(self):
        self.close()

    def closeEvent(self, event):
        # we don't need the notification anymore, delete it!
        self.closed_acc.emit(self.acc_index)
        self.deleteLater()

    def ontop_update(self):
        if settings.on_top_hint:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()

    def OptionGenerator(self, text_key=None, prev_text=None, reverse=False):
        for item in [self.OptionLayout.itemAt(i) for i in range(self.OptionLayout.count())]:
            #item.deleteLater()
            widget = item.widget()
            widget.deleteLater()
        
        self.opts_dict = {}
        option_index = 0

        # 添加上一步
        if prev_text is not None and not reverse:
            if text_key is not None:
                self.message['relationship']['option_prev_%s'%text_key] = [prev_text]
                if 'option_prev_%s'%text_key not in self.message['relationship'].get(text_key, []):
                    self.message['option_prev_%s'%text_key] = "上一步"
                    self.message['relationship'][text_key] = self.message['relationship'].get(text_key, []) + ['option_prev_%s'%text_key]
            else:
                self.message['relationship']['option_prev_end'] = [prev_text]
                n_row = option_index // self.n_col
                n_col = (option_index - (n_row-1)*self.n_col) % self.n_col

                self.opts_dict[option_index] = DialogueButtom("上一步", 'option_prev_end') ##################
                self.opts_dict[option_index].clicked.connect(self.confirm)
                self.OptionLayout.addWidget(self.opts_dict[option_index], n_row, n_col)
                option_index += 1


        if text_key is not None:
            for option in self.message.get('relationship', {}).get(text_key, []):
                n_row = option_index // self.n_col
                n_col = (option_index - (n_row-1)*self.n_col) % self.n_col

                self.opts_dict[option_index] = DialogueButtom(self.message[option], option) ##################
                self.opts_dict[option_index].clicked.connect(self.confirm)

                self.OptionLayout.addWidget(self.opts_dict[option_index], n_row, n_col)
                option_index += 1


        self.OptionGroupBox.setLayout(self.OptionLayout)

        if option_index == 0:
            pass
            '''
            try:
                item = self.windowLayout.itemAt(self.windowLayout.count()-1)
                widget = item.widget()
                widget.deleteLater()
            except:
                pass
            '''


    def confirm(self):
        opt_key = self.sender().msg_key
        new_key = self.message['relationship'].get(opt_key,[])
        if new_key == []:
            self.label.setText('')
            self.OptionGenerator(prev_text=self.text_now, reverse=self.sender().msg=="上一步")
            self.text_now = ''
        else:
            new_key = new_key[0]
            self.label.setText(self.message[new_key])
            self.OptionGenerator(new_key, self.text_now, reverse=self.sender().msg=="上一步")
            self.text_now = new_key

        self.adjustSize()
        

class DialogueButtom(QPushButton):
    def __init__(self, msg, msg_key):

        super(DialogueButtom, self).__init__()
        self.msg = msg
        self.msg_key = msg_key
        n_sp_symbol = math.ceil((msg.count('，') + msg.count('。') + msg.count('（') + msg.count('）')) / math.ceil(len(msg)/15))
        #print(n_sp_symbol)
        self.setText(text_wrap(msg,15-n_sp_symbol))

        self.setStyleSheet(OptionbuttonStyle)
        #self.adjustSize()
        self.setFixedWidth(int(250*settings.size_factor))
        self.adjustSize()


def text_wrap(texts, width):
    text_list = tr.wrap(texts, width=width)
    texts_wrapped = '\n'.join(text_list)

    return texts_wrapped























