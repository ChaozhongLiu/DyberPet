# coding:utf-8
import os
import json
import random

from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, HyperlinkCard, InfoBar,
                            ComboBoxSettingCard, ScrollArea, ExpandLayout, InfoBarPosition,
                            PushButton, TransparentToolButton, MessageBox)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale, QSize, QPoint
from PySide6.QtGui import QDesktopServices, QIcon, QImage
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QHBoxLayout, QSpacerItem, QSizePolicy

from .dashboard_widgets import AnimationGroup
from .animDesignUI import ActDesignWindow

import DyberPet.settings as settings
import os
from sys import platform
basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/Dashboard/')



class animationInterface(ScrollArea):
    """ Character animations management interface """
    loadNewAct = Signal(str, name='loadNewAct')
    deletewAct = Signal(str, name='deletewAct')

    def __init__(self, sizeHintdb: tuple[int, int], parent=None):
        super().__init__(parent=parent)
        self.current_pet = settings.petname

        # UI Design --------------------------------------------------------------------
        self.setObjectName("animationInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # Header
        self.headerWidget = QWidget(self)
        self.headerWidget.setFixedWidth(sizeHintdb[0]-165)
        self.panelLabel = QLabel(self.tr("Animation"), self.headerWidget)
        self.panelLabel.setSizePolicy(QSizePolicy.Maximum, self.panelLabel.sizePolicy().verticalPolicy())
        self.panelLabel.adjustSize()
        self.panelHelp = TransparentToolButton(QIcon(os.path.join(basedir, 'res/icons/question.svg')), self.headerWidget)
        self.panelHelp.setFixedSize(25,25)
        self.panelHelp.setIconSize(QSize(25,25))

        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(0)

        self.headerLayout.addWidget(self.panelLabel, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem1 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.headerLayout.addItem(spacerItem1)
        self.headerLayout.addWidget(self.panelHelp, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.headerLayout.addItem(spacerItem2)

        # Action Panel
        self.animatPanel = AnimationGroup(sizeHintdb, self.scrollWidget)

        # Action Design Window
        self.designWindow = ActDesignWindow()

        self.__initWidget()

    def __initWidget(self):
        #self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 75, 0, 20)
        self.setWidget(self.scrollWidget)
        #self.scrollWidget.resize(1000, 800)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.headerWidget.move(60, 20)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(70, 10, 70, 0)

        self.expandLayout.addWidget(self.animatPanel)


    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.panelLabel.setObjectName('panelLabel')

        theme = 'light' #if isDarkTheme() else 'light'
        with open(os.path.join(basedir, 'res/icons/Dashboard/qss/', theme, 'status_interface.qss'), encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        self.panelHelp.clicked.connect(self._showInstruction)
        self.animatPanel.addNew.connect(self._showDesignWindow)
        self.animatPanel.deleteAct.connect(self._deleteAct)
        self.designWindow.createNewAnim.connect(self.addNewAct)
    
    def _showDesignWindow(self):
        # Pop-up animation design UI
        pos = self.mapToGlobal(QPoint(self.width()//2, 50))
        self.designWindow.move(pos)
        self.designWindow.show()


    def addNewAct(self, new_name, new_config):
        # Get result
        '''
        new_name = "自定义组合动作"
        new_config = {"act_type":"customized",
                      "special_act":False,
                      "unlocked":True,
                      "in_playlist":False,
                      "act_prob":1.0,
                      "status_type":[2,2],
                      "act_list":[
                          ["wavehand",0,28,2],
                          ["qskill",0,36,1],
                          [60,25],
                          ["wavehand",0,28,2]
                          ],
                      "acc_list":[
                          [60,58],
                          ["palace_1",0,8,1],
                          ["palace_2",0,0,50],
                          ["palace_3",0,1,1]
                          ],
                      "anchor_list":[
                          [0,0],
                          [-445,-501],
                          [-445,-501],
                          [-445,-501]
                          ]
                     }
        '''

        # Update settings.act_data
        settings.act_data.allAct_params[settings.petname][new_name] = new_config
        settings.act_data.save_data()

        # Create customized act in self.pet_conf
        self.loadNewAct.emit(new_name)

        # Update Animation Panel UI
        self.animatPanel._addCard(new_name, new_config, 1)

        return
    
    def _deleteAct(self, act_name):
        # Popup dialogue to confirm
        title = self.tr("Delete?")
        content = self.tr("""Do you want to delete this customized animation?
You won't be able to recover after confirming.""")
        if not self.__showMessageBox(title, content):
            return

        # Delete animation from act_data
        settings.act_data.allAct_params[settings.petname].pop(act_name)
        settings.act_data.save_data()

        # Delete animation from self.pet_conf and animation selection menu
        self.deletewAct.emit(act_name)

        # Delete it from animation panel UI
        self.animatPanel._deleteCard(act_name, 1)
        
    def __showMessageBox(self, title, content):

        WarrningMessage = MessageBox(title, content, self)
        WarrningMessage.yesButton.setText(self.tr('Confirm'))
        WarrningMessage.cancelButton.setText(self.tr('Cancel'))
        if WarrningMessage.exec():
            return True
        else:
            return False
        
    def updateDesignUI(self):
        if self.current_pet == settings.petname:
            # Character refreshed or status changed
            self.designWindow.updateCombo()
            
        else:
            # Character changed
            self.current_pet = settings.petname
            self.designWindow.close()  # Close the widget
            self.designWindow.deleteLater()
            self.designWindow = ActDesignWindow()
            self.designWindow.createNewAnim.connect(self.addNewAct)

    def _showInstruction(self):
        title = self.tr("Animation Panel Guide")
        content = self.tr("""In Animation Panel, you can 
⏺ select an action to play
⏺ decide the random playlist by selecting the checkbox
⏺ create customized animation by clicking 'Add New Animation'

📌About the random playlist:
The character will randomly do some action when not being interacted with
At different hunger level, the behavior will be different
If only one action is selected from the list, it will only play the one selected

📌About the customized animation:
Click 'Add New Animation' and the design window will pop up
Select an animation, define your new start, end, and repetition
Click 'Add' to save the single design!
You can repeat this to add more animation in your design
Once done, give the design a name, and click 'Create' to complete""")
        self.__showMessageBox(title, content)
        return

            

