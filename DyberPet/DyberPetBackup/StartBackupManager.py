import sys
import ctypes
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSlot, QEvent
from PyQt5.QtGui import QCursor, QColor
from DyberPet.DyberPetBackup.BackupManager import *
from DyberPet.DyberPetBackup.QuickBackup import *

try:
    size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
except:
    size_factor = 1.5
    all_font_size = 14 #int(10/screen_scale)

class BackupManager(QMainWindow, Ui_backupManagerFrame):
    windowMovement = 'N'
    saveMode = 'write'

    def __init__(self, parent=None):
        super(BackupManager, self).__init__(parent)
        self.setupUi(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.pos().y() < 100:
                if event.pos().y() > 12:
                    self.windowMovement = 'Y'
                    self.mouse_drag_pos = event.globalPos() - self.pos()
                    self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        if Qt.LeftButton:
            if self.windowMovement == 'Y':
                self.move(event.globalPos() - self.mouse_drag_pos)
                self.setCursor(QCursor(Qt.SizeAllCursor))

    def mouseReleaseEvent(self, event):
        self.windowMovement = 'N'
        self.setCursor(QCursor(Qt.ArrowCursor))

    def on_setSaveModeRead_clicked(self):
        self.saveMode = 'read'
        self.setSaveModeRead.setChecked(1)
        self.setSaveModeWrite.setChecked(0)

    def on_setSaveModeWrite_clicked(self):
        self.saveMode = 'write'
        print(self.saveMode)
        self.setSaveModeRead.setChecked(0)
        self.setSaveModeWrite.setChecked(1)

    def on_closeApp_clicked(self):
        QApplication.exit()

    def on_saveSlot1_clicked(self):
        print(self.saveMode)
        if self.saveMode == 'read':
            readData().quickRead(targetSlot=1)
            self.saveSlot1.setText('存档1 - 加载执行完成')
        elif self.saveMode == 'write':
            saveResult = saveData().quickSave(targetSlot=1)
            print(saveResult)
            if saveResult == 1:
                self.saveSlot1.setText('保存错误：检测到文件丢失')
            elif saveResult == 2:
                self.saveSlot1.setText('保存错误：检测到文件损坏')
            elif saveResult == 0:
                self.saveSlot1.setText('存档1 - 保存成功')
            else:
                self.saveSlot1.setText('保存错误：未定义的状态')

    def on_saveSlot2_clicked(self):
        print(self.saveMode)
        if self.saveMode == 'read':
            readData().quickRead(targetSlot=2)
            self.saveSlot2.setText('存档2 - 加载执行完成')
        elif self.saveMode == 'write':
            saveResult = saveData().quickSave(targetSlot=2)
            print(saveResult)
            if saveResult == 1:
                self.saveSlot2.setText('保存错误：检测到文件丢失')
            elif saveResult == 2:
                self.saveSlot2.setText('保存错误：检测到文件损坏')
            elif saveResult == 0:
                self.saveSlot2.setText('存档2 - 保存成功')
            else:
                self.saveSlot2.setText('保存错误：未定义的状态')

    def on_saveSlot3_clicked(self):
        print(self.saveMode)
        if self.saveMode == 'read':
            readData().quickRead(targetSlot=3)
            self.saveSlot3.setText('存档3 - 加载执行完成')
        elif self.saveMode == 'write':
            saveResult = saveData().quickSave(targetSlot=3)
            print(saveResult)
            if saveResult == 1:
                self.saveSlot3.setText('保存错误：检测到文件丢失')
            elif saveResult == 2:
                self.saveSlot3.setText('保存错误：检测到文件损坏')
            elif saveResult == 0:
                self.saveSlot3.setText('存档3 - 保存成功')
            else:
                self.saveSlot3.setText('保存错误：未定义的状态')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    Form = BackupManager()
    if sys.platform == 'win32':
        Form.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
    else:
        Form.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
    Form.setAttribute(QtCore.Qt.WA_TranslucentBackground)
    cardShadow = QtWidgets.QGraphicsDropShadowEffect(Form)
    cardShadow.setColor(QColor(189,167,165))
    cardShadow.setOffset(0,0)
    cardShadow.setBlurRadius(20)
    Form.setGraphicsEffect(cardShadow)
    Form.show()
    sys.exit(app.exec_())