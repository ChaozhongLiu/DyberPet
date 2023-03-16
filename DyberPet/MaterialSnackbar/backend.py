import sys
import ctypes
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSlot, QEvent, pyqtSignal
from PyQt5.QtGui import QCursor, QColor
from DyberPet.MaterialSnackbar.snackBar import *

overrideHDPI = True

try:
    size_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
except:
    size_factor = 1
    all_font_size = 14 #int(10/screen_scale)

if overrideHDPI == False:
    size_factor = 1

class snackBar(QWidget, Ui_snackBar):
    def __init__(self, parent=None):
        super(snackBar, self).__init__(parent)
        self.setupUi(self)

        # 设置窗体属性
        if sys.platform == 'win32':
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)

        self.setAttribute(Qt.WA_TranslucentBackground)

        # 配置对HDPI的支持
        self.setMaximumWidth(int(400 * size_factor))
        self.setMinimumWidth(int(400 * size_factor))
        self.snackBarContainer.setStyleSheet("#snackBarContainer{ background: rgb(53, 47, 47); border: " + str(int(1 * size_factor)) + "px solid rgb(53,47,47); border-radius: " + str(int(5 * size_factor)) + "px; }")
        self.snackBarContainer.setContentsMargins(int(12 * size_factor), int(12 * size_factor), int(12 * size_factor), int(12 * size_factor))
        self.supportingText.setStyleSheet("#supportingText{ color: #f5f0f0; font-size: " + str(int(14 * size_factor)) + "px; }")
        self.action1.setStyleSheet("#action1{ background: transparent; color: #ffdad9; font-size: " + str(int(14 * size_factor)) + "px; }")
        self.action2.setStyleSheet( "#action2{ background: transparent; color: #ffdad9; font-size: " + str(int(14 * size_factor)) + "px; }")
        self.closeSnackBar.setFixedWidth(int(16 * size_factor))
        self.closeSnackBar.setFixedHeight(int(16 * size_factor))

        # 设置窗口阴影
        cardShadowSE = QtWidgets.QGraphicsDropShadowEffect(self.snackBarContainer)
        cardShadowSE.setColor(QColor(53, 47, 47))
        cardShadowSE.setOffset(0, 0)
        cardShadowSE.setBlurRadius(20)
        self.snackBarContainer.setGraphicsEffect(cardShadowSE)

        # 设置窗体位置
        self.move(QApplication.desktop().availableGeometry().width() - int(400 * size_factor), QApplication.desktop().availableGeometry().height() - self.height() - int(12 * size_factor))

    def on_action1_clicked(self):
        self.hide()
        snackBarValue().snackbar_return(message=1)

    def on_action2_clicked(self):
        self.hide()
        snackBarValue().snackbar_return(message=2)

    def on_closeSnackBar_clicked(self):
        self.hide()
        snackBarValue().snackbar_return(message=3)

    def snackbar_configWindow(self, supportingText, action1, action1Content, action2, action2Content, closeSnackBarBtn, snackBarID):
        # 修改supporting text
        self.supportingText.setText(str(supportingText))

        # 配置Action
        if action1 == "Enabled":
            self.action1.setText(action1Content)
        else:
            self.action1.setVisible(0)

        if action2 == "Enabled":
            self.action2.setText(action2Content)
        else:
            self.action2.setVisible(0)

        # 配置关闭
        if action1 != "Enabled":
            if action2 != "Enabled":
                self.closeSnackBar.setVisible(1)
            else:
                snackBarValue().snackbar_return(message=4)
        else:
            if closeSnackBarBtn == "Enabled":
                self.closeSnackBar.setVisible(1)
            else:
                self.closeSnackBar.setVisible(0)


class snackBarValue():
    snackbar_snackBarID = pyqtSignal([int])
    snackbar_snackBarReturn = pyqtSignal([str])
    def snackbar_return(self, message):
        self.snackbar_snackBarID.emit(str)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    Form = snackBar()
    if sys.platform == 'win32':
        Form.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
    else:
        Form.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
    Form.setAttribute(QtCore.Qt.WA_TranslucentBackground)
    cardShadow = QtWidgets.QGraphicsDropShadowEffect(Form)
    cardShadow.setColor(QColor(189, 167, 165))
    cardShadow.setOffset(0, 0)
    cardShadow.setBlurRadius(20)
    Form.setGraphicsEffect(cardShadow)
    Form.show()
    sys.exit(app.exec_())