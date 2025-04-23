# coding:utf-8
from PySide6.QtCore import Qt, Signal, QObject, QEvent, QUrl, QRectF, QSize, QPoint, Property
from PySide6.QtGui import QDesktopServices, QIcon, QPainter, QColor
from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtWidgets import QRadioButton, QToolButton, QApplication, QWidget, QSizePolicy

from qframelesswindow import FramelessDialog

from qfluentwidgets import (TextWrap, FluentStyleSheet, PrimaryPushButton, #MaskDialogBase,
                            LineEdit, RoundMenu, MenuAnimationType, ToolButton)
from qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase

from typing import Union

from qfluentwidgets.common.animation import TranslateYAnimation
from qfluentwidgets.common.icon import FluentIconBase, drawIcon, isDarkTheme, Theme, toQIcon, Icon
from qfluentwidgets.common.icon import FluentIcon as FIF
from qfluentwidgets.common.font import setFont
from qfluentwidgets.common.style_sheet import FluentStyleSheet, themeColor, ThemeColor
from qfluentwidgets.common.overload import singledispatchmethod


class Ui_SaveNameDialog:
    """ Ui of message box """

    yesSignal = Signal()
    cancelSignal = Signal()

    def __init__(self, *args, **kwargs):
        pass

    def _setUpUi(self, title, content, parent):
        self.titleLabel = QLabel(title, parent)

        self.content = content
        self.nameLineEdit = LineEdit()
        self.nameLineEdit.setText(content)
        self.nameLineEdit.setClearButtonEnabled(True)

        self.buttonGroup = QFrame(parent)
        self.yesButton = PrimaryPushButton(self.tr('OK'), self.buttonGroup)
        self.cancelButton = QPushButton(self.tr('Cancel'), self.buttonGroup)

        self.vBoxLayout = QVBoxLayout(parent)
        self.textLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout(self.buttonGroup)

        self.__initWidget()

    def __initWidget(self):
        self.__setQss()
        self.__initLayout()

        # fixes https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/19
        self.yesButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)
        self.cancelButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        self.yesButton.setFocus()
        self.buttonGroup.setFixedHeight(81)

        #self._adjustText()

        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)

    '''
    def _adjustText(self):
        if self.isWindow():
            if self.parent():
                w = max(self.titleLabel.width(), self.parent().width())
                chars = max(min(w / 9, 140), 30)
            else:
                chars = 100
        else:
            w = max(self.titleLabel.width(), self.window().width())
            chars = max(min(w / 9, 100), 30)

        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])
    '''
    def __initLayout(self):
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.textLayout, 1)
        self.vBoxLayout.addWidget(self.buttonGroup, 0, Qt.AlignBottom)
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.textLayout.setSpacing(12)
        self.textLayout.setContentsMargins(24, 24, 24, 24)
        self.textLayout.addWidget(self.titleLabel, 0, Qt.AlignTop)
        self.textLayout.addWidget(self.nameLineEdit, 0, Qt.AlignTop)

        self.buttonLayout.setSpacing(12)
        self.buttonLayout.setContentsMargins(12, 12, 12, 12)
        self.buttonLayout.addWidget(self.yesButton, 1, Qt.AlignVCenter)
        self.buttonLayout.addWidget(self.cancelButton, 1, Qt.AlignVCenter)

    
    def __onCancelButtonClicked(self):
        self.reject()
        self.cancelSignal.emit()

    def __onYesButtonClicked(self):
        self.accept()
        self.yesSignal.emit(self.nameLineEdit.text())
    

    def __setQss(self):
        self.titleLabel.setObjectName("titleLabel")
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.buttonGroup.setObjectName('buttonGroup')
        self.cancelButton.setObjectName('cancelButton')

        FluentStyleSheet.DIALOG.apply(self)

        self.yesButton.adjustSize()
        self.cancelButton.adjustSize()


class HyperlinkButton(ToolButton):
    """ Hyperlink button """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._url = QUrl()
        FluentStyleSheet.BUTTON.apply(self)
        self.setCursor(Qt.PointingHandCursor)
        setFont(self)
        self.clicked.connect(self._onClicked)

    @__init__.register
    def _(self, url: str, parent: QWidget = None, icon: Union[QIcon, FluentIconBase, str] = None):
        self.__init__(parent)
        #self.setText(text)
        self.url.setUrl(url)
        self.setIcon(icon)

    def getUrl(self):
        return self._url

    def setUrl(self, url: Union[str, QUrl]):
        self._url = QUrl(url)

    def _onClicked(self):
        if self.getUrl().isValid():
            QDesktopServices.openUrl(self.getUrl())

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            icon = icon.icon(color=themeColor())
        elif not self.isEnabled():
            painter.setOpacity(0.786 if isDarkTheme() else 0.9)
            if isinstance(icon, FluentIconBase):
                icon = icon.icon(Theme.DARK)

        drawIcon(icon, painter, rect, state)

    url = Property(QUrl, getUrl, setUrl)