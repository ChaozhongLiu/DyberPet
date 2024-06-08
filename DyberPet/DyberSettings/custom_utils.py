# coding:utf-8
import os
import sys
import math
import json
import glob

from typing import Union, List
from pathlib import Path

from PySide6 import QtGui
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QObject, QEvent, QModelIndex, QRectF
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, 
                               QVBoxLayout, QProgressBar, QFrame, QStyleOptionViewItem,
                               QButtonGroup)
from PySide6.QtGui import (QPixmap, QImage, QImageReader, QPainter, QBrush, QPen, QColor, QIcon,
                        QFont, QPainterPath, QCursor, QAction)

from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCard, Slider, FluentIconBase, SimpleCardWidget, PushButton #, ComboBox
from qfluentwidgets import (RoundMenu, FluentIcon, Action, AvatarWidget, BodyLabel, ToolButton,
                            HyperlinkButton, CaptionLabel, setFont, setTheme, Theme, isDarkTheme,
                            FluentStyleSheet, FlowLayout, IconWidget, getFont,
                            TransparentDropDownToolButton, DropDownPushButton, TransparentToolButton,
                            SingleDirectionScrollArea, PrimaryPushButton, LineEdit, MessageBoxBase,
                            SubtitleLabel, FlipImageDelegate, HorizontalPipsPager, HorizontalFlipView,
                            TextWrap, InfoBadge, PushButton, ScrollArea, ImageLabel, ToolTipFilter,
                            ExpandGroupSettingCard, RadioButton, ColorDialog)
#from qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase

from .custom_base import Ui_SaveNameDialog
from .custom_base import HyperlinkButton as DyperlinkButton
from .custom_combobox import ComboBox

import DyberPet.settings as settings
from DyberPet.conf import load_ItemMod
from DyberPet.utils import text_wrap

from sys import platform
basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/DyberSettings/')



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




#===========================================================
#    Customized range setting card
#===========================================================

class Dyber_RangeSettingCard(SettingCard):
    """ Setting card with a slider """

    #valueChanged = Signal(int)

    def __init__(self, vmin, vmax, sstep, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        #self.configItem = configItem
        self.slider = Slider(Qt.Horizontal, self)
        self.valueLabel = QLabel(self)
        self.slider.setMinimumWidth(250)

        self.sstep = sstep

        '''
        self.slider.setSingleStep(1)
        self.slider.setRange(*configItem.range)
        self.slider.setValue(configItem.value)
        '''
        self.slider.setSingleStep(1)
        self.slider.setRange(vmin, vmax)
        self.slider.setValue(vmin*sstep)
        self.valueLabel.setNum(vmin)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(6)
        self.hBoxLayout.addWidget(self.slider, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.valueLabel.setObjectName('valueLabel')
        #configItem.valueChanged.connect(self.setValue)
        self.slider.valueChanged.connect(self.__onValueChanged)
    
    def __onValueChanged(self, value: int):
        """ slider value changed slot """
        self.setValue(value)
        #self.valueChanged.emit(value)
    
    def setValue(self, value):
        #qconfig.set(self.configItem, value)
        self.valueLabel.setNum(value*self.sstep)
        self.valueLabel.adjustSize()
        self.slider.setValue(value)
    



#===========================================================
#    Customized ComboBox setting card
#===========================================================

class Dyber_ComboBoxSettingCard(SettingCard):
    """ Setting card with a combo box """
    optionChanged = Signal(str, name="optionChanged")

    def __init__(self, options, texts, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """
        Parameters
        ----------
        configItem: OptionsConfigItem
            configuration item operated by the card

        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        texts: List[str]
            the text of items

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.optionToText = {o: t for o, t in zip(options, texts)}
        for text, option in zip(texts, options):
            self.comboBox.addItem(text, userData=option)

        self.comboBox.setCurrentText(self.optionToText[options[0]])
        #self.comboBox.currentIndexChanged.connect(self.setValue)
        #self.comboBox.currentTextChanged.connect(self.setValue)
        #configItem.valueChanged.connect(self.setValue)
    '''
    def _onCurrentIndexChanged(self, index: int):

        qconfig.set(self.configItem, self.comboBox.itemData(index))
    '''

    def setValue(self, value):
        print("check")
        if value not in self.optionToText:
            print("check")
            return

        self.optionChanged.emit(self.optionToText[value])
        self.comboBox.setCurrentText(self.optionToText[value])
        #qconfig.set(self.configItem, value)
    



#===========================================================
#    Customized ToolBotton setting card (Save Import Card)
#===========================================================

class DyberToolBottonCard(SettingCard):
    """ Setting card with a push button """

    optionSelcted = Signal(str, name="optionSelcted")

    def __init__(self, text, icon: Union[str, QIcon, FluentIconBase], title, menu_icons=None, menu_text=None, content=None, parent=None):
        """
        Parameters
        ----------
        text: str
            the text of push button

        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        menu_icons: List
            Menu icon list

        menu_text: List
            Menu text list

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        #self.button = QPushButton(text, self)
        self.menu = RoundMenu() #parent=self)
        self.menu.addActions([_build_act(menu_text[i], self.menu, self._optionSelected) for i in range(len(menu_text))])

        self.ToolButton = DropDownPushButton(text, self, QIcon(os.path.join(basedir, 'res/icons/system/character.svg')))
        self.ToolButton.setMenu(self.menu)
        self.ToolButton.setIconSize(QSize(20, 20))
        #self.ToolButton.setFixedSize(60,30)

        self.hBoxLayout.addWidget(self.ToolButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        #self.button.clicked.connect(self._bclicked)
        #self.button.setObjectName('primaryButton')
    '''
    def _bclicked(self):
        pos = self.button.mapToGlobal(QPoint(self.button.width()+5, -100))
        self.clickedPos.emit(pos)
    '''

    def _optionSelected(self, optionText):
        self.optionSelcted.emit(optionText)




#===========================================================
#    Customized Color Picker
#===========================================================

class CustomColorSettingCard(ExpandGroupSettingCard):
    """ Custom color setting card """

    colorChanged = Signal(str, name='colorChanged')

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None, enableAlpha=False):
        """
        Parameters
        ----------

        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of setting card

        content: str
            the content of setting card

        parent: QWidget
            parent window

        enableAlpha: bool
            whether to enable the alpha channel
        """
        super().__init__(icon, title, content, parent=parent)
        self.enableAlpha = enableAlpha
        self.defaultColor = settings.DEFAULT_THEME_COL
        if settings.themeColor:
            self.customColor = settings.themeColor
        else:
            self.customColor = settings.DEFAULT_THEME_COL

        self.choiceLabel = QLabel(self)

        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.defaultRadioButton = RadioButton(
            self.tr('Default color'), self.radioWidget)
        self.customRadioButton = RadioButton(
            self.tr('Custom color'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self)

        self.customColorWidget = QWidget(self.view)
        self.customColorLayout = QHBoxLayout(self.customColorWidget)
        self.customLabel = QLabel(
            self.tr('Custom color'), self.customColorWidget)
        self.chooseColorButton = QPushButton(
            self.tr('Choose color'), self.customColorWidget)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()

        if self.defaultColor != self.customColor:
            self.customRadioButton.setChecked(True)
            self.chooseColorButton.setEnabled(True)
        else:
            self.defaultRadioButton.setChecked(True)
            self.chooseColorButton.setEnabled(False)

        self.choiceLabel.setText(self.buttonGroup.checkedButton().text())
        self.choiceLabel.adjustSize()

        self.chooseColorButton.setObjectName('chooseColorButton')

        self.buttonGroup.buttonClicked.connect(self.__onRadioButtonClicked)
        self.chooseColorButton.clicked.connect(self.__showColorDialog)

    def __initLayout(self):
        self.addWidget(self.choiceLabel)

        self.radioLayout.setSpacing(19)
        self.radioLayout.setAlignment(Qt.AlignTop)
        self.radioLayout.setContentsMargins(48, 18, 0, 18)
        self.buttonGroup.addButton(self.customRadioButton)
        self.buttonGroup.addButton(self.defaultRadioButton)
        self.radioLayout.addWidget(self.customRadioButton)
        self.radioLayout.addWidget(self.defaultRadioButton)
        self.radioLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.customColorLayout.setContentsMargins(48, 18, 44, 18)
        self.customColorLayout.addWidget(self.customLabel, 0, Qt.AlignLeft)
        self.customColorLayout.addWidget(self.chooseColorButton, 0, Qt.AlignRight)
        self.customColorLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radioWidget)
        self.addGroupWidget(self.customColorWidget)

    def __onRadioButtonClicked(self, button: RadioButton):
        """ radio button clicked slot """
        if button.text() == self.choiceLabel.text():
            return

        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()

        if button is self.defaultRadioButton:
            self.chooseColorButton.setDisabled(True)
            if self.defaultColor != self.customColor:
                self.colorChanged.emit(self.defaultColor)
        else:
            self.chooseColorButton.setDisabled(False)
            if self.defaultColor != self.customColor:
                self.colorChanged.emit(self.customColor)

    def __showColorDialog(self):
        """ show color dialog """
        w = ColorDialog(
            self.customColor, self.tr('Choose color'), self.window(), self.enableAlpha)
        w.colorChanged.connect(self.__onCustomColorChanged)
        w.exec()

    def __onCustomColorChanged(self, color):
        """ custom color changed slot """
        color = color.name()
        self.customColor = color
        self.colorChanged.emit(color)




#===========================================================
#    Quick Save Card and related widgets
#===========================================================

SACECARD_W, SACECARD_H = 270, 150

class QuickSaveCard(SimpleCardWidget):
    """ Quick Save card """

    saveClicked = Signal(int, name='saveClicked')
    loadinClicked = Signal(int, name='loadinClicked')
    rewriteClicked = Signal(int, name='rewriteClicked')
    deleteClicked = Signal(int, name='deleteClicked')
    backtraceClicked = Signal(int, name='backtraceClicked')

    def __init__(self, cardIndex: int, jsonPath=None, parent=None):
        self.cardIndex = cardIndex
        self.jsonPath = jsonPath
        super().__init__(parent)
        self.setBorderRadius(10)
        self.setObjectName("QuickSaveCard")

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.setContentsMargins(5, 5, 5, 5)

        self.setFixedSize(SACECARD_W, SACECARD_H)

        if jsonPath is None:
            self.__init_EmptyCard()
        else:
            self.__init_SaveCard()


    def _normalBackgroundColor(self):
        if self.jsonPath is None:
            return QColor(255, 255, 255, 13 if isDarkTheme() else 170)
        else:
            return QColor(235, 242, 255, 13 if isDarkTheme() else 170)

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

    def __init_EmptyCard(self):

        self.saveButton = TransparentToolButton(os.path.join(basedir, 'res/icons/system/add_circle.svg'), self)
        self.saveButton.setIconSize(QSize(50, 50))
        self.saveButton.resize(75, 75)
        self.saveButton.clicked.connect(self._saveClicked)

        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.saveButton, 0, Qt.AlignCenter)
        self.vBoxLayout.addStretch(1)

    def __init_SaveCard(self):

        # Load in info
        info = open(os.path.join(self.jsonPath,'info.txt'),'r', encoding='UTF-8').readlines()
        info = [i.strip() for i in info]
        petname = info[0]

        # Title
        self.cardTitle = info[1] #os.path.normpath(self.jsonPath).split(os.sep)[-1]
        #self.cardTitle = self.cardTitle.split('_', maxsplit=1)[1]
        self.titleLabel = CaptionLabel(self.cardTitle, self)
        setFont(self.titleLabel, 13, QFont.Normal)
        self.titleLabel.adjustSize()

        # Pet Name
        self.nameLabel = CaptionLabel(petname, self)
        setFont(self.nameLabel, 14, QFont.DemiBold)
        self.nameLabel.adjustSize()
        self.nameLabel.setFixedSize(130, self.nameLabel.height())


        #pfp
        image = QImage()
        infoJson = os.path.join(basedir,'res/role',petname,'info/info.json')
        if os.path.exists(infoJson):
            infoJson = json.load(open(infoJson, 'r', encoding='UTF-8'))
            pfp_file = infoJson.get('pfp', None)
            if pfp_file is None:
                pfp_file = os.path.join(basedir,'res/icons/unknown.svg')
            else:
                pfp_file = os.path.join(basedir, 'res/role', petname, 'info', pfp_file)
        else:
            pfp_file = os.path.join(basedir,'res/icons/unknown.svg')
        #image.load(os.path.join(basedir, 'res/icons/system/nxd.png'))
        image.load(pfp_file)
        '''
        pixmap = AvatarImage(image)
        self.pfpLabel = QLabel(self)
        self.pfpLabel.setPixmap(pixmap)
        
        pfpImg = AvatarImage(image)
        self.pfpLabel = QLabel(self)
        self.pfpLabel.setPixmap(QPixmap.fromImage(pfpImg))
        '''
        self.pfpLabel = AvatarImage(image)



        # HP, FV
        '''
        self.hpbar = simpleStatusBar(ranges=(0,100), value=77, 
                                      text='', color='#FAC486',
                                      icon=os.path.join(basedir, 'res/icons/HP_icon.png'))
        self.fvbar = simpleStatusBar(ranges=(0,120), value=99,
                                      text='lv2: ', color='#F69290',
                                      icon=os.path.join(basedir, 'res/icons/FV_icon.png'))
        '''
        saveData = json.load(open(os.path.join(self.jsonPath,'pet_data.json'), 'r', encoding='UTF-8'))
        saveData = saveData[petname]
        hp = saveData.get('HP', 'null')
        if hp != 'null': 
            hp = math.ceil(hp / settings.HP_INTERVAL)
        hp_tier = saveData.get('HP_tier', 'null')
        fv = saveData.get('FV', 'null')
        fv_lvl = saveData.get('FV_lvl', 'null')
        hpText1 = f"{settings.TIER_NAMES[hp_tier]}"
        hpText2 = f"{hp}/100"
        fvText1 = f"Lv{fv_lvl}"
        fvText2 = f"{fv}/{settings.LVL_BAR[fv_lvl]}"
        self.hpbar = simpleStatus(text1=hpText1, text2=hpText2,
                                  icon=os.path.join(basedir, 'res/icons/HP_icon.png'))

        self.fvbar = simpleStatus(text1=fvText1, text2=fvText2,
                                  icon=os.path.join(basedir, 'res/icons/FV_icon.png'))


        # Menu
        self.menu = RoundMenu() #parent=self)
        self.menu.addAction(_build_act(icon=QIcon(os.path.join(basedir, 'res/icons/system/upload.svg')),
                                       name=self.tr('Load In'),
                                       act_func=self._loadinClicked,
                                       parent=self.menu))
        self.menu.addAction(_build_act(icon=QIcon(os.path.join(basedir, 'res/icons/system/rewrite.svg')), 
                                       name=self.tr('Rewrite'),
                                       act_func=self._rewriteClicked,
                                       parent=self.menu))
        self.menu.addAction(_build_act(icon=FIF.DELETE, 
                                       name=self.tr('Delete'),
                                       act_func=self._deleteClicked,
                                       parent=self.menu))
        self.menu.addAction(_build_act(icon=FIF.CANCEL, 
                                       name=self.tr('Backtrace'),
                                       act_func=self._backtraceClicked,
                                       parent=self.menu))


        self.ToolButton = TransparentDropDownToolButton(os.path.join(basedir, 'res/icons/system/menu.svg'), self)
        self.ToolButton.setMenu(self.menu)
        self.ToolButton.setFixedSize(60,30)

        # Assemble menu bar
        hBoxLayout = QHBoxLayout()
        hBoxLayout.setContentsMargins(10, 0, 0, 0)
        hBoxLayout.addWidget(self.titleLabel, Qt.AlignLeft | Qt.AlignVCenter)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(self.ToolButton, Qt.AlignRight | Qt.AlignVCenter)

        # Assemble status body
        vBoxLayout_status = QVBoxLayout()
        #vBoxLayout_status.setContentsMargins(0, 0, 0, 0)
        vBoxLayout_status.setSpacing(3)
        vBoxLayout_status.addStretch(1)
        vBoxLayout_status.addWidget(
            self.nameLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        vBoxLayout_status.addWidget(HorizontalSeparator(QColor(20,20,20,125)))
        #vBoxLayout_status.addStretch(1)
        vBoxLayout_status.addWidget(self.hpbar, 1, Qt.AlignLeft | Qt.AlignVCenter)
        vBoxLayout_status.addWidget(self.fvbar, 1, Qt.AlignLeft | Qt.AlignVCenter)
        vBoxLayout_status.addStretch(1)

        # Assemble main body
        hBoxLayout2 = QHBoxLayout()
        hBoxLayout2.setSpacing(5)
        hBoxLayout2.setContentsMargins(15, 5, 15, 5)
        hBoxLayout2.addStretch(1)
        hBoxLayout2.addWidget(self.pfpLabel, Qt.AlignCenter)
        hBoxLayout2.addStretch(1)
        hBoxLayout2.addLayout(vBoxLayout_status, Qt.AlignCenter)
        hBoxLayout2.addStretch(1)

        # Assemble card
        self.vBoxLayout.setSpacing(1)
        self.vBoxLayout.addLayout(hBoxLayout, Qt.AlignTop | Qt.AlignHCenter)
        self.vBoxLayout.addWidget(HorizontalSeparator(QColor("#000000")))
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addLayout(hBoxLayout2) #, 0, Qt.AlignCenter)
        self.vBoxLayout.addStretch(1)

    def _registerSave(self, jsonPath):
        self._clear_layout(self.vBoxLayout)
        self.jsonPath = jsonPath
        self.__init_SaveCard()
        self._updateBackgroundColor()

    def _deleteSave(self):
        self._clear_layout(self.vBoxLayout)
        self.jsonPath = None
        self.cardTitle = None
        self.__init_EmptyCard()
        self._updateBackgroundColor()
        
    def _saveClicked(self):
        self.saveClicked.emit(self.cardIndex)

    def _loadinClicked(self, actionName):
        self.loadinClicked.emit(self.cardIndex)

    def _rewriteClicked(self, actionName):
        self.rewriteClicked.emit(self.cardIndex)

    def _deleteClicked(self, actionName):
        self.deleteClicked.emit(self.cardIndex)

    def _backtraceClicked(self, actionName):
        print("Backtrace")
        self.backtraceClicked.emit(self.cardIndex)


class simpleStatus(QWidget):

    def __init__(self, text1, text2, icon=None):

        super(simpleStatus, self).__init__()

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(2, 0, 2, 0)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setSpacing(5)

        self.icon = IconWidget(QIcon(icon), self)
        self.icon.setFixedSize(15,15)

        self.statusLabel1 = CaptionLabel(text1, self)
        setFont(self.statusLabel1, 12, QFont.DemiBold)
        self.statusLabel1.setFixedSize(55,15)

        self.statusLabel2 = CaptionLabel(text2, self)
        setFont(self.statusLabel2, 12, QFont.DemiBold)
        #self.statusLabel2.setFixedSize(36,15)

        #self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(
            self.icon, 0, Qt.AlignLeft | Qt.AlignVCenter)
        #self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.statusLabel1, 1, Qt.AlignLeft | Qt.AlignVCenter)
        #self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.statusLabel2, 1, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(1)

        self.setFixedWidth(150)


class simpleStatusBar(QWidget):

    def __init__(self, ranges, value, text, icon=None, color='#FAC486'):

        super(simpleStatusBar, self).__init__()

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setSpacing(5)

        self.icon = IconWidget(QIcon(icon), self)
        self.icon.setFixedSize(15,15)

        self.statusBar = QProgressBar(self)
        self.statusBar.setMinimum(ranges[0])
        self.statusBar.setMaximum(ranges[1])
        self.statusBar.setFormat(f'{text}{value}/{ranges[1]}')
        self.statusBar.setValue(value)
        self.statusBar.setAlignment(Qt.AlignCenter)

        stylesheet = f'''QProgressBar {{
                                        font-family: "Times";
                                        border: 2px solid #08060f;
                                        border-radius: 7px;
                                      }}
                        QProgressBar::chunk {{
                                        background-color: {color};
                                        border-radius: 5px;}}'''
        self.statusBar.setStyleSheet(stylesheet)
        self.statusBar.setFixedSize(125,20)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(
            self.icon, 0, Qt.AlignCenter)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.statusBar, 1, Qt.AlignCenter)
        self.hBoxLayout.addStretch(1)



class LineEditDialog(MessageBoxBase):
    """ Custom message box """

    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        #self.setAttribute(Qt.WA_DeleteOnClose)
        self.titleLabel = SubtitleLabel(title, self)
        self.nameLineEdit = LineEdit(self)
        self.nameLineEdit.setText(content)
        self.nameLineEdit.setClearButtonEnabled(True)

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameLineEdit)

        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(False)
        self.nameLineEdit.textChanged.connect(self._validateName)

    def _validateName(self, text):
        if text:
            self.yesButton.setEnabled(True)
        else:
            self.yesButton.setEnabled(False)

'''
class LineEditDialog(MaskDialogBase, Ui_SaveNameDialog):
    """ Message box """

    yesSignal = Signal(str)
    cancelSignal = Signal()

    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent=parent)
        self._setUpUi(title, content, self.widget)
        #self.setAttribute(Qt.WA_DeleteOnClose)

        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))
        self._hBoxLayout.removeWidget(self.widget)
        self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignCenter)

        self.buttonGroup.setMinimumWidth(280)
        self.widget.setFixedSize(
            max(self.nameLineEdit.width(), self.titleLabel.width()) + 48,
            self.nameLineEdit.y() + self.nameLineEdit.height() + 105
        )
        self.nameLineEdit.textChanged.connect(self._validateUrl)

    def eventFilter(self, obj, e: QEvent):
        if obj is self.window():
            if e.type() == QEvent.Resize:
                self._adjustText()

        return super().eventFilter(obj, e)

    def _validateUrl(self, text):
        if text:
            self.yesButton.setEnabled(True)
        else:
            self.yesButton.setEnabled(False)

'''

#===========================================================
#    Save Card Group
#===========================================================

class SaveCardGroup(QWidget):
    """ Setting card group """

    def __init__(self, title: str, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.sizeHintDyber = sizeHintDyber
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = FlowLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)

        self.cardLayout.setSpacing(6)
        self.cardLayout.setContentsMargins(15, 0, 15, 15)
        self.cardLayout.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.cardLayout, 1)

        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        setFont(self.titleLabel, 20)
        self.titleLabel.adjustSize()

    def addSaveCard(self, card: QWidget):
        """ add setting card to group """
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()
        #print(self.width(), self.height())

    def addSaveCards(self, cards: List[QWidget]):
        """ add setting cards to group """
        for card in cards:
            self.addSaveCard(card)
    
    def adjustSize(self):
        width = self.sizeHintDyber[0] - 50
        n = self.cardLayout.count()
        ncol = width // (SACECARD_W+12) #math.ceil(SACECARD_WH*n / width)
        nrow = math.ceil(n / ncol)
        h = (SACECARD_H+12)*nrow + 46
        #h = self.cardLayout.heightForWidth(self.width()) #+ 6
        return self.resize(self.width(), h)
    


#===========================================================
#    Character Card Utilities
#===========================================================

class CustomFlipItemDelegate(FlipImageDelegate):
    """ Custom flip item delegate, keep image ratio """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # Get the bounding rect
        boundingRect = option.rect

        # draw image
        image = index.data(Qt.UserRole)  # type: QImage
        if image is None:
            return painter.restore()

        # The image should have already been scaled in the setItemImage function.
        # Calculate the x and y position to center the image within the boundingRect
        x = boundingRect.x() + (boundingRect.width() - image.width()) / 2
        y = boundingRect.y() + (boundingRect.height() - image.height()) / 2
        rect = QRectF(x, y, image.width(), image.height())

        # clipped path
        path = QPainterPath()
        path.addRoundedRect(rect, self.borderRadius, self.borderRadius)

        painter.setClipPath(path)
        painter.drawImage(rect, image)
        painter.restore()


class CustomHorizontalFlipView(HorizontalFlipView):
    """ Customized HorizontalFlipView, keep image ratio """

    def setItemImage(self, index: int, image: Union[QImage, QPixmap, str], targetSize: QSize = None):
        """ set the image of specified item """
        if not 0 <= index < self.count():
            return

        item = self.item(index)

        # convert image to QImage
        if isinstance(image, str):
            image = QImage(image)
        elif isinstance(image, QPixmap):
            image = image.toImage()

        # Scale the image while keeping its aspect ratio
        scaledImage = image.scaled(self._itemSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # If the scaled image is larger than the original, revert back to the original image
        if scaledImage.width() > image.width() or scaledImage.height() > image.height():
            scaledImage = image

        item.setData(Qt.UserRole, scaledImage)
        item.setSizeHint(self.itemSize)


INFOCARD_W, INFOCARD_H = 300, 410
INFOLINE_W, INFOLINE_H = 500, 75

class CharCardGroup(QWidget):
    """ Setting card group """

    def __init__(self, title: str, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.sizeHintDyber = sizeHintDyber
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = FlowLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)

        self.cardLayout.setSpacing(6)
        self.cardLayout.setContentsMargins(15, 0, 15, 15)
        self.cardLayout.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.cardLayout, 1)

        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        setFont(self.titleLabel, 20)
        self.titleLabel.adjustSize()
        self.adjustSize()

    def addInfoCard(self, card: QWidget):
        """ add setting card to group """
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()
        #print(self.width(), self.height())

    def addInfoCards(self, cards: List[QWidget]):
        """ add setting cards to group """
        for card in cards:
            self.addInfoCard(card)
    
    def adjustSize(self):
        width = self.sizeHintDyber[0] - 50
        n = self.cardLayout.count()
        ncol = width // (INFOLINE_W+18) #math.ceil(SACECARD_WH*n / width)
        nrow = math.ceil(n / ncol)
        h = (INFOLINE_H+18)*nrow + 46
        #h = self.cardLayout.heightForWidth(self.width()) #+ 6
        return self.resize(self.width(), h)


class CharLine(SimpleCardWidget):
    """ Character Info Card """
    launchClicked = Signal(str, name="launchClicked")
    infoClicked = Signal(int, QPoint, name="infoClicked")

    def __init__(self, cardIndex: int, chrFolder=None, parentDir='role', parent=None):
        self.cardIndex = cardIndex
        self.chrFolder = chrFolder
        self.parentDir = parentDir
        super().__init__(parent)
        self.setBorderRadius(5)
        self.setObjectName("CharLine")

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setContentsMargins(15, 5, 5, 5)

        self.setFixedSize(INFOLINE_W, INFOLINE_H)

        self.__init_InfoList()
        #self._adjustText()

    def __init_InfoList(self):
        infoFile = os.path.join(basedir, f"res/{self.parentDir}", self.chrFolder, "info/info.json")
        if not os.path.exists(infoFile):
            self.chrName = self.chrFolder
            pfpPath = os.path.join(basedir,'res/icons/unknown.svg')
        else:
            infoConfig = json.load(open(infoFile, 'r', encoding='UTF-8'))
            self.chrName = infoConfig.get("petName", self.chrFolder)
            pfpPath = infoConfig.get("pfp", None)
            if pfpPath:
                pfpPath = os.path.join(basedir, f'res/{self.parentDir}', self.chrFolder, 'info', pfpPath)
            else:
                pfpPath = os.path.join(basedir, 'res/icons/unknown.svg')

        # Character pfp
        image = QImage()
        image.load(pfpPath)
        self.pfp = AvatarImage(image)

        # Character name
        self.chrLabel = CaptionLabel(self.chrName)
        setFont(self.chrLabel, 15, QFont.DemiBold)
        self.chrLabel.adjustSize()

        # Lauch character button
        if self.parentDir == 'role':
            self.launchButton = PushButton(text=self.tr("Launch"), parent=self,
                                        icon=FluentIcon.PLAY)
            self.launchButton.clicked.connect(self._launchClicked)
        # More info
        self.infoButton = TransparentToolButton(FluentIcon.INFO)
        self.infoButton.clicked.connect(lambda: self._infoClicked(
                                                self.infoButton.mapToGlobal(QPoint(self.infoButton.width()-10, 0)))
                                       )
                                                    

        self.hBoxLayout.addWidget(self.pfp, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(0.2)
        self.hBoxLayout.addWidget(self.chrLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(1)
        if self.parentDir == 'role':
            self.hBoxLayout.addWidget(self.launchButton, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.infoButton, 0, Qt.AlignRight | Qt.AlignVCenter)

    def _launchClicked(self):
        self.launchClicked.emit(self.chrFolder)

    def _infoClicked(self, pos):
        self.infoClicked.emit(self.cardIndex, pos)


class CharCard(QWidget):

    def __init__(self, cardIndex: int, jsonPath=None, petFolder=None, parentDir='role', parent=None):
        super(CharCard, self).__init__(parent)

        self.setObjectName("CharCard")
        self.is_follow_mouse = False
        self.parentDir = parentDir

        self.centralwidget = QFrame(objectName='infoFrame')
        self.centralwidget.setStyleSheet("""#infoFrame {
                                                    background:rgba(255, 255, 255, 255);
                                                    border: 3px solid rgba(255, 255, 255, 255);
                                                    border-radius: 10px;
                                                }
                                         """)
        vbox_s = QVBoxLayout()
        vbox_s.setContentsMargins(0, 0, 0, 0)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(5, 0, 0, 0)
        if self.parentDir == 'role':
            self.title = CaptionLabel(self.tr("Character Info"))
        elif self.parentDir == 'pet':
            self.title = CaptionLabel(self.tr("Mini-Pet Info"))
        setFont(self.title, 14, QFont.DemiBold)
        self.title.adjustSize()
        self.closeButton = TransparentToolButton(FIF.CLOSE)
        self.closeButton.clicked.connect(self._close)
        hbox.addWidget(self.title, Qt.AlignLeft | Qt.AlignVCenter)
        hbox.addStretch(1)
        hbox.addWidget(self.closeButton, Qt.AlignRight | Qt.AlignVCenter)

        self.card = CharCardWidget(cardIndex, jsonPath=jsonPath, petFolder=petFolder, 
                                   parentDir = self.parentDir, parent=self)
        vbox_s.addLayout(hbox)
        vbox_s.addWidget(self.card)
        
        self.centralwidget.setLayout(vbox_s)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.centralwidget)
        self.setLayout(self.layout_window)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        if settings.platform == 'win32':
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow) # | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint) # | Qt.NoDropShadowWindowHint)

    def _close(self):
        self.hide()

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




class CharCardWidget(SimpleCardWidget):
    """ Character Info Card """
    gotoClicked = Signal(str, name="gotoClicked")
    deleteClicked = Signal(int, str, name="deleteClicked")

    def __init__(self, cardIndex: int, jsonPath=None, petFolder=None, parentDir='role', parent=None):
        self.cardIndex = cardIndex
        self.jsonPath = jsonPath
        self.petFolder = petFolder
        self.parentDir = parentDir
        super().__init__(parent)
        self.setBorderRadius(5)
        self.setObjectName("CharCardWidget")

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.setContentsMargins(5, 5, 5, 5)

        self.setFixedSize(INFOCARD_W+10, INFOCARD_H)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.__init_InfoCard()

        self._adjustText()


    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)


    def _updateBackgroundColor(self):
        color = self._normalBackgroundColor()
        #self.backgroundColorAni.stop()
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

    def __init_InfoCard(self):

        # Load in json
        self.folderPath = os.path.join(basedir,f'res/{self.parentDir}',self.petFolder)
        self.folderPath = os.path.normpath(self.folderPath)
        infoConfig = json.load(open(self.jsonPath, 'r', encoding='UTF-8'))

        # Images Display
        self.flipView = CustomHorizontalFlipView(self)
        self.pager = HorizontalPipsPager(self)
        # adjust view size
        self.flipView.setItemSize(QSize(300, 169))
        self.flipView.setFixedSize(QSize(300, 169))
        self.flipView.setItemDelegate(CustomFlipItemDelegate(self.flipView))
        # add images
        images = infoConfig.get("coverImages",[])
        if images:
            images = [os.path.join(basedir, f'res/{self.parentDir}',self.petFolder,'info',i) for i in images]
            self.flipView.addImages(images)
            self.pager.setPageNumber(self.flipView.count())
        self.pager.currentIndexChanged.connect(self.flipView.setCurrentIndex)
        self.flipView.currentIndexChanged.connect(self.pager.setCurrentIndex)

        # Layout for the other widgets
        self.vBoxLayout2 = QVBoxLayout()
        self.vBoxLayout2.setAlignment(Qt.AlignCenter)
        self.vBoxLayout2.setContentsMargins(8, 0, 8, 5)
        self.vBoxLayout2.setSpacing(10)

        # Title bar
        self.hBoxLayoutTitle = QHBoxLayout()
        self.hBoxLayoutTitle.setContentsMargins(0, 0, 0, 0)

        self.petName = infoConfig.get("petName", self.tr("Unnamed"))
        self.titleLabel = CaptionLabel(self.petName)
        setFont(self.titleLabel, 14, QFont.DemiBold)
        self.titleLabel.adjustSize()
        self.menuButton = TransparentToolButton(os.path.join(basedir,'res/icons/system/more.svg'))
        self.menuButton.setFixedSize(40,25)
        self.menuButton.setIconSize(QSize(25,25))
        self.hBoxLayoutTitle.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.hBoxLayoutTitle.addWidget(self.menuButton, 0, Qt.AlignRight)

        # Set up menu
        self.menu = RoundMenu() #parent=self)
        #self.menu.addActions()
        '''
        self.menu.addAction(_build_act(name = self.tr('Launch character'),
                                       parent = self.menu,
                                       icon = FluentIcon.PLAY,
                                       act_func = self.__onMenuClicked))
        '''
        self.menu.addAction(_build_act(name = self.tr('Go to folder'),
                                       parent = self.menu,
                                       icon = FluentIcon.FOLDER,
                                       act_func = self.__onMenuClicked))
        #Action(FluentIcon.FOLDER, self.tr('Go to folder')))
        self.menu.addAction(_build_act(name = self.tr('Delete'),
                                       parent = self.menu,
                                       icon = FluentIcon.DELETE,
                                       act_func = self.__onMenuClicked))
        #self.menu.addAction(Action(FluentIcon.DELETE, self.tr('Delete')))
        self.menuButton.clicked.connect(lambda: self.__showMenu(
            self.menuButton.mapToGlobal(QPoint(self.menuButton.width()-10, 0))))


        # Tags
        self.hBoxLayoutTags = QHBoxLayout()
        self.hBoxLayoutTags.setContentsMargins(0, 0, 0, 0)
        tags = infoConfig.get("tages", {})
        for text, color in tags.items():
            stylesheet="InfoBadge {padding: 2px 6px 2px 6px; color: black;}"
            tagWidget = InfoBadge.custom(text, color, color)
            tagWidget.setStyleSheet(stylesheet)
            self.hBoxLayoutTags.addWidget(tagWidget, 0, Qt.AlignLeft)
        self.hBoxLayoutTags.addStretch(1)


        # Description
        self.content = infoConfig.get("intro", self.tr("No description."))
        self.contentLabel = CaptionLabel(self.content)
        setFont(self.contentLabel, 13) #, QFont.DemiBold)
        self.contentLabel.adjustSize()

        self.vBoxLayout2.addLayout(self.hBoxLayoutTitle, Qt.AlignLeft)
        self.vBoxLayout2.addLayout(self.hBoxLayoutTags, Qt.AlignLeft)
        self.vBoxLayout2.addWidget(self.contentLabel, 0, Qt.AlignLeft)
        self.vBoxLayout2.addStretch(1)
        

        # Author Info
        authorInfo = infoConfig.get("author", {})
        self.hBoxLayoutAuthor = QHBoxLayout()
        self.hBoxLayoutAuthor.setContentsMargins(8, 0, 8, 0)

        pfpPath = authorInfo.get("pfp", None)
        if pfpPath:
            pfpPath = os.path.join(basedir, f'res/{self.parentDir}', self.petFolder, 'info', pfpPath)
        else:
            pfpPath = os.path.join(basedir, 'res/icons/unknown.svg')
        image = QImage()
        image.load(pfpPath)
        self.authorPfp = AvatarImage(image, edge_size=35, frameColor=authorInfo.get("frameColor","#4f91ff"))

        # Author Info ToolTip
        tooltip_info = authorInfo.get("infos", None)
        if tooltip_info:
            self.authorPfp.installEventFilter(ToolTipFilter(self.authorPfp, showDelay=500))
            self.authorPfp.setToolTip(text_wrap(tooltip_info, 30))

        self.authorName = authorInfo.get("name",self.tr("Unknown author"))
        self.authorLabel = CaptionLabel(self.authorName)
        setFont(self.authorLabel, 15, QFont.DemiBold)
        self.authorLabel.adjustSize()

        self.hBoxLayoutAuthor.addWidget(self.authorPfp, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayoutAuthor.addStretch(0.2)
        self.hBoxLayoutAuthor.addWidget(self.authorLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayoutAuthor.addStretch(1)

        #Links
        links = authorInfo.get("links", {})
        for link, userid in links.items():
            if link in settings.LINK_PERMIT.keys():
                iconPath = glob.glob(os.path.join(basedir, 'res/icons', link+".*"))[0]
                linkButton = DyperlinkButton(
                                url=settings.LINK_PERMIT[link]+userid,
                                icon=QIcon(iconPath)) #os.path.join(basedir, 'res/icons', link+'.svg')))
                linkButton.setFixedSize(25,25)
                linkButton.setIconSize(QSize(18,18))
                linkButton.setToolTip(link)
                self.hBoxLayoutAuthor.addWidget(linkButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.vBoxLayout.addWidget(self.flipView, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.pager, 0, Qt.AlignCenter)

        self.vBoxLayout.addLayout(self.vBoxLayout2, Qt.AlignCenter)
        self.vBoxLayout.addWidget(HorizontalSeparator(QColor("#000000")))
        self.vBoxLayout.addLayout(self.hBoxLayoutAuthor, Qt.AlignCenter)
        self.vBoxLayout.addStretch(1)
        #self.vBoxLayout.addWidget(self.saveButton, 0, Qt.AlignCenter)
        #self.vBoxLayout.addStretch(1)

    def _adjustText(self):
        w = 320 if not self.parent() else (self.parent().width() - 50)
        w = self.width() - 26

        # adjust title
        chars = w / 7 #max(min(w / 6, 120), 30)
        self.titleLabel.setText(TextWrap.wrap(self.petName, chars, False)[0])

        # adjust content
        chars = w / 6.5 #max(min(w / 6, 120), 30)
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])
        self.contentLabel.adjustSize()
        self.contentLabel.setFixedSize(self.contentLabel.width(), 76)

    def __showMenu(self, pos):
        self.menu.popup(pos)

    def __onMenuClicked(self, menuName):

        if menuName == self.tr("Go to folder"):
            self.gotoClicked.emit(self.folderPath)
        elif menuName == self.tr("Delete"):
            self.deleteClicked.emit(self.cardIndex, self.folderPath)




#===========================================================
#    Item Mod UI
#===========================================================


class ItemLine(SimpleCardWidget):
    """ Character Info Card """
    deleteClicked = Signal(int, str, name="deleteClicked")
    infoClicked = Signal(int, QPoint, name="infoClicked")

    def __init__(self, cardIndex: int, itemFolder=None, parent=None):
        self.cardIndex = cardIndex
        self.itemFolder = itemFolder
        super().__init__(parent)
        self.setBorderRadius(5)
        self.setObjectName("ItemLine")

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.setContentsMargins(15, 5, 5, 5)

        self.setFixedSize(INFOLINE_W, INFOLINE_H)

        self.__init_InfoList()
        #self._adjustText()

    def __init_InfoList(self):
        extensions = ["*.jpg", "*.jpeg", "*.png"]
        infoFile = os.path.join(self.itemFolder, "info.json")
        if not os.path.exists(infoFile):
            self.modName = os.path.basename(self.itemFolder)

            # Use a generator expression to get the first image file
            image_file = next((file for ext in extensions for file in glob.iglob(os.path.join(self.itemFolder, ext))), None)
            if image_file:
                pfpPath = os.path.normpath(image_file)
            else:
                pfpPath = os.path.join(basedir,'res/icons/unknown.svg')

        else:
            infoConfig = json.load(open(infoFile, 'r', encoding='UTF-8'))
            self.modName = infoConfig.get("modName", os.path.basename(self.itemFolder))
            pfpPath = infoConfig.get("pfp", None)
            if pfpPath:
                pfpPath = os.path.join(self.itemFolder, pfpPath)
            else:
                image_file = next((file for ext in extensions for file in glob.iglob(os.path.join(self.itemFolder, ext))), None)
                if image_file:
                    pfpPath = os.path.normpath(image_file)
                else:
                    pfpPath = os.path.join(basedir,'res/icons/unknown.svg')

        # MOD pfp
        image = QImage()
        image.load(pfpPath)
        '''
        pixmap = AvatarImage(image, edge_size=50, frameColor="#ffffff")
        self.pfp = QLabel()
        self.pfp.setPixmap(pixmap)
        
        pfpImg = AvatarImage(image, edge_size=50, frameColor="#ffffff")
        self.pfp = QLabel(self)
        self.pfp.setPixmap(QPixmap.fromImage(pfpImg))
        '''
        self.pfp = AvatarImage(image, edge_size=50) #, frameColor="#ffffff")

        # MOD name
        self.modLabel = CaptionLabel(self.modName)
        setFont(self.modLabel, 15, QFont.DemiBold)
        self.modLabel.adjustSize()

        # Delete MOD button
        self.deleteButton = PushButton(text=self.tr("Delete"), parent=self,
                                       icon=FluentIcon.DELETE)
        self.deleteButton.clicked.connect(self._deleteClicked)
        # More info
        self.infoButton = TransparentToolButton(FluentIcon.INFO)
        self.infoButton.clicked.connect(lambda: self._infoClicked(
                                                self.infoButton.mapToGlobal(QPoint(self.infoButton.width()-10, 0)))
                                       )
                                                    

        self.hBoxLayout.addWidget(self.pfp, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(0.2)
        self.hBoxLayout.addWidget(self.modLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.deleteButton, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.infoButton, 0, Qt.AlignRight | Qt.AlignVCenter)

    def _deleteClicked(self):
        self.deleteClicked.emit(self.cardIndex, self.itemFolder)

    def _infoClicked(self, pos):
        self.infoClicked.emit(self.cardIndex, pos)


class ItemCard(QWidget):

    def __init__(self, cardIndex: int, itemFolder=None, parent=None):
        super(ItemCard, self).__init__(parent)

        self.setObjectName("ItemCard")
        self.is_follow_mouse = False

        self.centralwidget = QFrame(objectName='infoFrame')
        self.centralwidget.setStyleSheet("""#infoFrame {
                                                    background:rgba(255, 255, 255, 255);
                                                    border: 3px solid rgba(255, 255, 255, 255);
                                                    border-radius: 10px;
                                                }
                                         """)
        vbox_s = QVBoxLayout()
        vbox_s.setContentsMargins(0, 0, 0, 0)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(5, 0, 0, 0)

        self.title = CaptionLabel(self.tr("Item MOD Info"))
        setFont(self.title, 14, QFont.DemiBold)
        self.title.adjustSize()
        self.closeButton = TransparentToolButton(FIF.CLOSE)
        self.closeButton.clicked.connect(self._close)
        hbox.addWidget(self.title, Qt.AlignLeft | Qt.AlignVCenter)
        hbox.addStretch(1)
        hbox.addWidget(self.closeButton, Qt.AlignRight | Qt.AlignVCenter)

        self.card = ItemCardWidget(cardIndex, itemFolder=itemFolder, parent=self)
        vbox_s.addLayout(hbox)
        vbox_s.addWidget(self.card)
        
        self.centralwidget.setLayout(vbox_s)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.centralwidget)
        self.setLayout(self.layout_window)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        if settings.platform == 'win32':
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow) # | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint) # | Qt.NoDropShadowWindowHint)

    def _close(self):
        self.hide()

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




class ItemCardWidget(SimpleCardWidget):
    """ Item MOD Info Card """
    #gotoClicked = Signal(str, name="gotoClicked")
    #deleteClicked = Signal(int, str, name="deleteClicked")

    def __init__(self, cardIndex: int, itemFolder=None, parent=None):
        self.cardIndex = cardIndex
        self.itemFolder = itemFolder
        super().__init__(parent)
        self.setBorderRadius(5)
        self.setObjectName("ItemCardWidget")

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.setContentsMargins(5, 5, 5, 5)

        self.setFixedSize(INFOCARD_W+10, INFOCARD_H)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.__init_InfoCard()

        self._adjustText()

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _updateBackgroundColor(self):
        color = self._normalBackgroundColor()
        #self.backgroundColorAni.stop()
        self.backgroundColorAni.setEndValue(color)
        self.backgroundColorAni.start()

    def __init_InfoCard(self):

        # Load in json
        infoJsonPath = os.path.join(self.itemFolder, 'info.json')
        infoConfig = json.load(open(infoJsonPath, 'r', encoding='UTF-8'))

        # Items Display
        itemJsonPath = os.path.join(self.itemFolder, 'items_config.json')
        items_dict = load_ItemMod(itemJsonPath, HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)

        # Order item by fv_lock
        fv_locks = [v['fv_lock'] for _,v in items_dict.items()]
        itemNames = [k for k,_ in items_dict.items()]
        sorted_pairs = sorted(zip(fv_locks, itemNames))
        itemNames = [item[1] for item in sorted_pairs]

        self.scrollView = ScrollArea()        
        self.scrollView.setStyleSheet("""ScrollArea{
                                                    background-color: rgb(252, 252, 252);
                                                    border: black;
                                                }""")
                                                

        itemDisplay = ItemGroup(300, 36, self)
        itemDisplay.setFixedWidth(300)
        for item in itemNames:
            itemIcon = loadItemIcon(items_dict[item], 36)
            itemDisplay.addItemCard(itemIcon)

        self.scrollView.setFixedSize(300, 169)
        self.scrollView.setWidget(itemDisplay)
        self.scrollView.horizontalScrollBar().setValue(0)

        # Layout for the other widgets
        self.vBoxLayout2 = QVBoxLayout()
        self.vBoxLayout2.setAlignment(Qt.AlignCenter)
        self.vBoxLayout2.setContentsMargins(8, 0, 8, 5)
        self.vBoxLayout2.setSpacing(10)

        # Title bar
        self.hBoxLayoutTitle = QHBoxLayout()
        self.hBoxLayoutTitle.setContentsMargins(0, 0, 0, 0)

        self.modName = infoConfig.get("modName", self.tr("Unnamed"))
        self.titleLabel = CaptionLabel(self.modName)
        setFont(self.titleLabel, 14, QFont.DemiBold)
        self.titleLabel.adjustSize()
        '''
        self.menuButton = TransparentToolButton(os.path.join(basedir,'res/icons/system/more.svg'))
        self.menuButton.setFixedSize(40,25)
        self.menuButton.setIconSize(QSize(25,25))
        '''
        self.hBoxLayoutTitle.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        #self.hBoxLayoutTitle.addWidget(self.menuButton, 0, Qt.AlignRight)

        # Set up menu
        '''
        self.menu = RoundMenu() #parent=self)
        #self.menu.addActions()
        self.menu.addAction(_build_act(name = self.tr('Go to folder'),
                                       parent = self.menu,
                                       icon = FluentIcon.FOLDER,
                                       act_func = self.__onMenuClicked))
        #Action(FluentIcon.FOLDER, self.tr('Go to folder')))
        self.menu.addAction(_build_act(name = self.tr('Delete'),
                                       parent = self.menu,
                                       icon = FluentIcon.DELETE,
                                       act_func = self.__onMenuClicked))
        #self.menu.addAction(Action(FluentIcon.DELETE, self.tr('Delete')))
        self.menuButton.clicked.connect(lambda: self.__showMenu(
            self.menuButton.mapToGlobal(QPoint(self.menuButton.width()-10, 0))))
        '''


        # Tags
        self.hBoxLayoutTags = QHBoxLayout()
        self.hBoxLayoutTags.setContentsMargins(0, 0, 0, 0)
        tags = infoConfig.get("tages", {})
        for text, color in tags.items():
            stylesheet="InfoBadge {padding: 2px 6px 2px 6px; color: black;}"
            tagWidget = InfoBadge.custom(text, color, color)
            tagWidget.setStyleSheet(stylesheet)
            self.hBoxLayoutTags.addWidget(tagWidget, 0, Qt.AlignLeft)
        self.hBoxLayoutTags.addStretch(1)


        # Description
        self.content = infoConfig.get("intro", self.tr("No description."))
        self.contentLabel = CaptionLabel(self.content)
        setFont(self.contentLabel, 13) #, QFont.DemiBold)
        self.contentLabel.adjustSize()

        self.vBoxLayout2.addLayout(self.hBoxLayoutTitle, Qt.AlignLeft)
        self.vBoxLayout2.addLayout(self.hBoxLayoutTags, Qt.AlignLeft)
        self.vBoxLayout2.addWidget(self.contentLabel, 0, Qt.AlignLeft)
        self.vBoxLayout2.addStretch(1)
        

        # Author Info
        authorInfo = infoConfig.get("author", {})
        self.hBoxLayoutAuthor = QHBoxLayout()
        self.hBoxLayoutAuthor.setContentsMargins(8, 0, 8, 0)

        pfpPath = authorInfo.get("pfp", None)
        if pfpPath:
            pfpPath = os.path.join(self.itemFolder, pfpPath)
        else:
            pfpPath = os.path.join(basedir, 'res/icons/unknown.svg')
        image = QImage()
        image.load(pfpPath)

        self.authorPfp = AvatarImage(image, edge_size=35, frameColor=authorInfo.get("frameColor","#4f91ff"))
        
        # Author Info ToolTip
        tooltip_info = authorInfo.get("infos", None)
        if tooltip_info:
            self.authorPfp.installEventFilter(ToolTipFilter(self.authorPfp, showDelay=500))
            self.authorPfp.setToolTip(text_wrap(tooltip_info, 30))

        self.authorName = authorInfo.get("name",self.tr("Unknown author"))
        self.authorLabel = CaptionLabel(self.authorName)
        setFont(self.authorLabel, 15, QFont.DemiBold)
        self.authorLabel.adjustSize()

        self.hBoxLayoutAuthor.addWidget(self.authorPfp, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayoutAuthor.addStretch(0.2)
        self.hBoxLayoutAuthor.addWidget(self.authorLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayoutAuthor.addStretch(1)

        #Links
        links = authorInfo.get("links", {})
        for link, userid in links.items():
            if link in settings.LINK_PERMIT.keys():
                iconPath = glob.glob(os.path.join(basedir, 'res/icons', link+".*"))[0]
                linkButton = DyperlinkButton(
                                url=settings.LINK_PERMIT[link]+userid,
                                icon=QIcon(iconPath)) #os.path.join(basedir, 'res/icons', link+'.svg')))
                linkButton.setFixedSize(25,25)
                linkButton.setIconSize(QSize(18,18))
                linkButton.setToolTip(link)
                self.hBoxLayoutAuthor.addWidget(linkButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.vBoxLayout.addWidget(self.scrollView, 0, Qt.AlignCenter)
        #self.vBoxLayout.addWidget(self.pager, 0, Qt.AlignCenter)

        self.vBoxLayout.addLayout(self.vBoxLayout2, Qt.AlignCenter)
        self.vBoxLayout.addWidget(HorizontalSeparator(QColor("#000000")))
        self.vBoxLayout.addLayout(self.hBoxLayoutAuthor, Qt.AlignCenter)
        self.vBoxLayout.addStretch(1)
        #self.vBoxLayout.addWidget(self.saveButton, 0, Qt.AlignCenter)
        #self.vBoxLayout.addStretch(1)

    def _adjustText(self):
        w = 320 if not self.parent() else (self.parent().width() - 50)
        w = self.width() - 26

        # adjust title
        chars = w / 7 #max(min(w / 6, 120), 30)
        self.titleLabel.setText(TextWrap.wrap(self.modName, chars, False)[0])

        # adjust content
        chars = w / 6.5 #max(min(w / 6, 120), 30)
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])
        self.contentLabel.adjustSize()
        #self.contentLabel.setFixedSize(self.contentLabel.width(), 76)

        self.setFixedSize(INFOCARD_W+10, 10+169+self.titleLabel.height()+self.contentLabel.height()+6+16+90)
    '''
    def __showMenu(self, pos):
        self.menu.popup(pos)

    def __onMenuClicked(self, menuName):

        if menuName == self.tr("Go to folder"):
            self.gotoClicked.emit(self.folderPath)
        elif menuName == self.tr("Delete"):
            self.deleteClicked.emit(self.cardIndex, self.folderPath)
    '''



class ItemGroup(QWidget):
    """ Item display group """

    def __init__(self, sizeWidth, imageSize, parent=None):
        super().__init__(parent=parent)
        self.sizeWidth = sizeWidth
        self.imageSize = imageSize
        #self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = FlowLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)

        self.cardLayout.setSpacing(6)
        self.cardLayout.setContentsMargins(15, 0, 15, 15)
        self.cardLayout.setAlignment(Qt.AlignVCenter)

        #self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.cardLayout, 1)

        #FluentStyleSheet.SETTING_CARD_GROUP.apply(self)

        self.setStyleSheet("""background-color: transparent""")
        #setFont(self.titleLabel, 20)
        #self.titleLabel.adjustSize()

    def addItemCard(self, card: QWidget):
        """ add setting card to group """
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()
        #print(self.width(), self.height())

    def addItemCards(self, cards: List[QWidget]):
        """ add setting cards to group """
        for card in cards:
            self.addItemCard(card)
    
    def adjustSize(self):
        width = self.sizeWidth - 30
        n = self.cardLayout.count()
        ncol = width // (self.imageSize+6) #math.ceil(SACECARD_WH*n / width)
        nrow = math.ceil(n / ncol)
        h = (self.imageSize+6)*nrow + 15+6+12*2
        #h = self.cardLayout.heightForWidth(self.width()) #+ 6
        return self.resize(self.width(), h)


def loadItemIcon(item_config, imgSize):

    image = item_config['image']
    '''
    if image.width() > image.height():
        image = image.scaledToWidth(imgSize, mode=Qt.SmoothTransformation)
    else:
        image = image.scaledToHeight(imgSize, mode=Qt.SmoothTransformation)
    '''

    label = ImageLabel(image)
    label.setScaledContents(True)
    label.setFixedSize(imgSize, imgSize) #image.width(), image.height()) #
    label.installEventFilter(ToolTipFilter(label, showDelay=500))
    label.setToolTip(item_config['hint'])

    return label



#===========================================================
#    Common Utilities
#===========================================================


def _build_act(name: str, parent: QObject, act_func, icon=None) -> QAction:
    """
    构建改变菜单动作
    :param pet_name: 菜单动作名称
    :param parent 父级菜单
    :param act_func: 菜单动作函数
    :return:
    """
    if icon is None:
        act = Action(name, parent)
    else:
        act  = Action(icon, name, parent)
    act.triggered.connect(lambda: act_func(name))
    return act



class AvatarLabel(QLabel):

    def __init__(self, edge_size, frameColor):
        super().__init__()
        self.edge_size = edge_size
        self.frameColor = frameColor
        self.setScaledContents(True)
        self.setFixedSize(edge_size, edge_size)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Draw frame ring
        ring_thickness = 2  # adjust this for the ring thickness
        pen = QPen(QColor(self.frameColor), ring_thickness)
        pen.setCapStyle(Qt.SquareCap)
        painter.setPen(pen)
        painter.drawEllipse(1, 1, self.edge_size-2, self.edge_size-2)
        painter.end()
        

def AvatarImage(image, edge_size=65, frameColor=QColor(255, 255, 255, 0)): #"#ffffff"):
    # Calculate the shorter edge
    label = AvatarLabel(edge_size, frameColor)

    # Create a transparent QImage with the same size
    mask = QImage(image.size(), QImage.Format_ARGB32)
    mask.fill(Qt.transparent)
    # Create a QPainter object to draw the circular mask
    painter = QPainter(mask)
    painter.setBrush(QBrush(Qt.white))
    painter.setPen(QPen(Qt.black))
    circle_r = min(image.width(), image.height())
    margin = max(1, math.ceil(2*(circle_r/edge_size)))
    painter.drawEllipse(margin, margin, circle_r-2*margin, circle_r-2*margin)
    painter.end()
    # Apply the mask to the image
    image.setAlphaChannel(mask)
    image = image.copy(0, 0, circle_r, circle_r)

    label.setPixmap(QPixmap.fromImage(image))

    return label


