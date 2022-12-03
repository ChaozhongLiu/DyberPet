import os
import sys
import time
import math
import random
import inspect
import types
from datetime import datetime, timedelta

from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QEvent
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontDatabase
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from typing import List
import ctypes
screen_scale = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
all_font_size = int(10/screen_scale)

class Tomato(QWidget):
    close_tomato = pyqtSignal(name='close_tomato')
    confirm_tomato = pyqtSignal(int, name='confirm_tomato')

    def __init__(self, parent=None):
        super(Tomato, self).__init__(parent)
        # tomato clock window

        vbox_t = QVBoxLayout()

        hbox_t1 = QHBoxLayout()
        self.n_tomato = QSpinBox()
        self.n_tomato.setMinimum(1)
        n_tomato_label = QLabel("请选择要进行番茄钟的个数:")
        QFontDatabase.addApplicationFont('res/font/MFNaiSi_Noncommercial-Regular.otf')
        n_tomato_label.setFont(QFont('宋体', all_font_size))
        hbox_t1.addWidget(n_tomato_label)
        hbox_t1.addWidget(self.n_tomato)

        hbox_t = QHBoxLayout()
        self.button_confirm = QPushButton("确定")
        self.button_confirm.setFont(QFont('宋体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_cancel = QPushButton("取消")
        self.button_cancel.setFont(QFont('宋体', all_font_size))
        self.button_cancel.clicked.connect(self.close_tomato)
        hbox_t.addWidget(self.button_confirm)
        hbox_t.addWidget(self.button_cancel)

        vbox_t.addLayout(hbox_t1)
        vbox_t.addLayout(hbox_t)
        self.setLayout(vbox_t)
        self.setFixedSize(250,100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)


    def confirm(self):
        self.confirm_tomato.emit(self.n_tomato.value())




class Focus(QWidget):
    close_focus = pyqtSignal(name='close_focus')
    confirm_focus = pyqtSignal(str,int,int, name='confirm_focus')

    def __init__(self, parent=None):
        super(Focus, self).__init__(parent)
        # Focus time window

        vbox_f = QVBoxLayout()
        self.checkA = QCheckBox("持续一段时间", self)
        self.checkA.setFont(QFont('宋体', all_font_size))
        self.checkB = QCheckBox("定时结束", self)
        self.checkB.setFont(QFont('宋体', all_font_size))
        self.checkA.stateChanged.connect(self.uncheck)
        self.checkB.stateChanged.connect(self.uncheck)

        hbox_f1 = QHBoxLayout()
        self.countdown_h = QSpinBox()
        self.countdown_h.setMinimum(0)
        self.countdown_h.setMaximum(23)
        self.countdown_m = QSpinBox()
        self.countdown_m.setMinimum(0)
        self.countdown_m.setMaximum(59)
        self.countdown_m.setSingleStep(5)
        hbox_f1.addWidget(self.countdown_h)
        label_h = QLabel('小时')
        label_h.setFont(QFont('宋体', all_font_size))
        hbox_f1.addWidget(label_h)
        hbox_f1.addWidget(self.countdown_m)
        label_m = QLabel('分钟后')
        label_m.setFont(QFont('宋体', all_font_size))
        hbox_f1.addWidget(label_m)
        hbox_f1.addStretch(10)

        hbox_f2 = QHBoxLayout()
        self.time_h = QSpinBox()
        self.time_h.setMinimum(0)
        self.time_h.setMaximum(23)
        self.time_m = QSpinBox()
        self.time_m.setMinimum(0)
        self.time_m.setMaximum(59)
        label_d = QLabel('到')
        label_d.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(label_d)
        hbox_f2.addWidget(self.time_h)
        label_h = QLabel('点')
        label_h.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(label_h)
        hbox_f2.addWidget(self.time_m)
        label_m = QLabel('分')
        label_m.setFont(QFont('宋体', all_font_size))
        hbox_f2.addWidget(label_m)
        hbox_f2.addStretch(10)

        hbox_f3 = QHBoxLayout()
        self.button_confirm = QPushButton("确定")
        self.button_confirm.setFont(QFont('宋体', all_font_size))
        self.button_confirm.clicked.connect(self.confirm)
        self.button_cancel = QPushButton("取消")
        self.button_cancel.setFont(QFont('宋体', all_font_size))
        self.button_cancel.clicked.connect(self.close_focus)
        hbox_f3.addWidget(self.button_confirm)
        hbox_f3.addWidget(self.button_cancel)

        label_method = QLabel('设置方式')
        label_method.setFont(QFont('宋体', all_font_size))
        label_method.setStyleSheet("color : grey")
        vbox_f.addWidget(label_method)
        vbox_f.addWidget(QHLine())
        vbox_f.addWidget(self.checkA)
        vbox_f.addLayout(hbox_f1)
        vbox_f.addStretch(1)
        vbox_f.addWidget(self.checkB)
        vbox_f.addLayout(hbox_f2)
        vbox_f.addStretch(1)
        vbox_f.addLayout(hbox_f3)

        self.setLayout(vbox_f)
        self.setFixedSize(250,200)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)

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
        if self.checkA.isChecked():
            self.confirm_focus.emit('range', self.countdown_h.value(), self.countdown_m.value())
        elif self.checkB.isChecked():
            self.confirm_focus.emit('point', self.time_h.value(), self.time_m.value())
        else:
            pass




class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)



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
        self.setFixedSize(450,300)
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
