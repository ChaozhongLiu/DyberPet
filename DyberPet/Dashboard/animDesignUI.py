# coding:utf-8
import os
import sys
import math
import json
import glob
import uuid
import datetime
from collections import defaultdict
from typing import Union, List

from PySide6 import QtGui
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QObject, QEvent, QModelIndex, QRectF, QRect, QTime
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QProgressBar, QFrame, QStyleOptionViewItem,
                             QSizePolicy, QStackedWidget, QLayout, QSpacerItem)
from PySide6.QtGui import (QPixmap, QImage, QImageReader, QPainter, QBrush, QPen, QColor, QIcon,
                        QFont, QPainterPath, QCursor, QAction, QFontMetrics, QPalette)

from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import PushButton
from qfluentwidgets import (TransparentToolButton, PillPushButton,
                            BodyLabel, setFont, setTheme, Theme, isDarkTheme,
                             FlowLayout, IconWidget, getFont, LineEdit, MessageBox,
                            PushButton, SpinBox, StrongBodyLabel, ComboBox, ProgressBar)

import DyberPet.settings as settings
#from DyberPet.utils import MaskPhrase, TimeConverter
from .dashboard_widgets import HorizontalSeparator
from DyberPet.conf import EmptyAct

from sys import platform
basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/Dashboard/')



class ActDesignWindow(QWidget):

    createNewAnim =Signal(str, dict, name='createNewAnim')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActDesignWindow")
        self.is_follow_mouse = False

        self.all_design_conf = {}
        self.tags_dict = {}
        self.current_tagid = 'initAct'
        self.current_template_conf = {}
        self.design_name_valid = False
        self.design_status = 0

        self.__initWidget()
        self.__connectSignalToSlot()

    def __initWidget(self):

        # The Round Frame
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.frame = QFrame()
        self.frame.setStyleSheet(f'''
            QFrame {{
                border: 1px solid black;
                border-radius: 4px; 
                background: rgb(255, 255, 255);
            }}
            QLabel{{
                border: 0px
            }}
        ''')

        # Title Header ------------------------------------------------------------------------------------------------------------
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.setContentsMargins(0,0,0,0)
        # icon
        self.windowIcon = IconWidget(self)
        self.windowIcon.setMinimumSize(QSize(20, 20))
        self.windowIcon.setMaximumSize(QSize(20, 20))
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(os.path.join(basedir,'res/icons/Dashboard/filmmaker.svg')), QIcon.Normal, QIcon.Off)
        self.windowIcon.setIcon(icon1)
        # title
        self.title = StrongBodyLabel(self)
        self.title.setText(self.tr("Animation Design"))
        self.title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft) 
        # close button
        self.button_close = TransparentToolButton(FIF.CLOSE, self)
        self.button_close.setFixedSize(25,25)
        self.button_close.setIconSize(QSize(15,15))
        
        # layout
        self.horizontalLayout_1.addWidget(self.windowIcon)
        spacerItem1 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem1)
        self.horizontalLayout_1.addWidget(self.title)
        spacerItem2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem2)
        self.horizontalLayout_1.addWidget(self.button_close, 0, Qt.AlignRight)
        self.verticalLayout.addLayout(self.horizontalLayout_1)
        spacerItem3 = QSpacerItem(20, 15, QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem3)

        # Action Editting Panel -------------------------------------------------------------------------------------------------
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_2.setContentsMargins(10,0,10,0)

        # Left Side -------------------------------------------------
        self.verticalLayout_1 = QVBoxLayout()
        self.verticalLayout_1.setContentsMargins(0,0,0,0)
        # image frame
        self.imgFrame = QFrame()
        self.imgFrame.setFixedSize(200,200)
        self.imgFrame.setStyleSheet(f'''
            QFrame {{
                border: 1px solid black;
                border-radius: 0px; 
                background: rgb(255, 255, 255);
            }}
            QLabel{{
                border: 0px
            }}
        ''')
        self.imgLayout = QHBoxLayout()
        self.imgLayout.setContentsMargins(5,5,5,5)
        self.image = QLabel()
        self.image.setScaledContents(True)
        self.image.setAlignment(Qt.AlignCenter) #Qt.AlignBottom | Qt.AlignHCenter)
        self.imgLayout.addStretch()
        self.imgLayout.addWidget(self.image, Qt.AlignCenter)
        self.imgLayout.addStretch()
        self.imgFrame.setLayout(self.imgLayout)
        # Progress bar
        self.animProgress = ProgressBar(self)
        self.animProgress.setFixedWidth(200)
        self.animProgress.setRange(0,100)
        self.animProgress.setValue(1)

        self.verticalLayout_1.addWidget(self.imgFrame)
        self.verticalLayout_1.addWidget(self.animProgress)

        # Right Side operation panel ---------------------------------
        self.verticalLayout_2 = QVBoxLayout()
        # ComboBox to select action
        self.actComboBox = ComboBox(self)
        self.actComboBox.setPlaceholderText(self.tr("Select an action"))
        items = [k for k,v in settings.act_data.allAct_params[settings.petname].items() if v['act_type']!='customized' and v['unlocked'] and not v['special_act']]
        self.actComboBox.addItems(items)
        self.actComboBox.setCurrentIndex(-1)

        # SpinBox for start frame index
        hbox_1 = QHBoxLayout()
        spinbox_label_1 = BodyLabel(self.tr("Start:"))
        spinbox_label_1.setFixedWidth(45)
        self.start_SpinBox = SpinBox(self)
        self.start_SpinBox.setRange(1, 1)
        hbox_1.addWidget(spinbox_label_1)
        hbox_1.addWidget(self.start_SpinBox)

        # SpinBox for end frame index
        hbox_2 = QHBoxLayout()
        spinbox_label_2 = BodyLabel(self.tr("End:"))
        spinbox_label_2.setFixedWidth(45)
        self.end_SpinBox = SpinBox(self)
        self.end_SpinBox.setRange(1, 1)
        hbox_2.addWidget(spinbox_label_2)
        hbox_2.addWidget(self.end_SpinBox)

        # SpinBox for repeat number
        hbox_3 = QHBoxLayout()
        spinbox_label_3 = BodyLabel(self.tr("Repeat:"))
        spinbox_label_3.setFixedWidth(45)
        self.rep_SpinBox = SpinBox(self)
        self.rep_SpinBox.setRange(1, 100)
        hbox_3.addWidget(spinbox_label_3)
        hbox_3.addWidget(self.rep_SpinBox)

        # Buttons
        hbox_4 = QHBoxLayout()
        self.saveBtn = PushButton(FIF.ADD, self.tr("Add"))
        self.saveBtn.setEnabled(False)
        self.deleteBtn = PushButton(FIF.DELETE, self.tr("Delete"))
        self.deleteBtn.setEnabled(False)
        hbox_4.addWidget(self.saveBtn)
        hbox_4.addWidget(self.deleteBtn)
        self.verticalLayout_2.addStretch()
        self.verticalLayout_2.addWidget(self.actComboBox)
        self.verticalLayout_2.addStretch()
        self.verticalLayout_2.addLayout(hbox_1)
        self.verticalLayout_2.addStretch()
        self.verticalLayout_2.addLayout(hbox_2)
        self.verticalLayout_2.addStretch()
        self.verticalLayout_2.addLayout(hbox_3)
        self.verticalLayout_2.addStretch()
        self.verticalLayout_2.addLayout(hbox_4)
        self.verticalLayout_2.addStretch()

        spacerItem4 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.horizontalLayout_2.addLayout(self.verticalLayout_1)
        spacerItem5 = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem5)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        spacerItem6 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem6)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        spacerItem7 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem7)

        self.verticalLayout.addWidget(HorizontalSeparator(QColor(0,0,0,125), 1))
        spacerItem10 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem10)

        # Control Panel -------------------------------------------------------------------------------------------------
        # Action component layout
        self.actCompLayout = FlowLayout()
        self.actCompLayout.setSpacing(5)
        self.actCompLayout.setContentsMargins(10, 0, 10, 10)
        self.init_actBtn = PillPushButton(self.tr("Add New"))
        self.init_actBtn.setChecked(True)
        self.actCompLayout.addWidget(self.init_actBtn)

        '''
        self.actCompLayout.addWidget(self._generateSeparator())
        
        for i in range(7):
            toy_actBtn = PillPushButton(items[i])
            self.actCompLayout.addWidget(toy_actBtn)
            self.actCompLayout.addWidget(self._generateSeparator())
        
        for i in range(4):
            toy_actBtn = PillPushButton(items[i])
            self.actCompLayout.addWidget(toy_actBtn)
            self.actCompLayout.addWidget(StrongBodyLabel("-"))
        '''

        self.verticalLayout.addLayout(self.actCompLayout)
        spacerItem8 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem8)

        self.verticalLayout.addWidget(HorizontalSeparator(QColor(0,0,0,125), 1))
        spacerItem11 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem11)

        # Final Operation panel
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_3.setContentsMargins(10,0,10,0)
        self.nameEdit = LineEdit()
        self.nameEdit.setClearButtonEnabled(True)
        self.nameEdit.setPlaceholderText(self.tr("New Action Name"))
        self.nameEdit.setFixedWidth(200)

        self.nameHint = IconWidget(self)
        self.nameHint.setMinimumSize(QSize(20, 20))
        self.nameHint.setMaximumSize(QSize(20, 20))
        self.notValid_icon = QIcon()
        self.notValid_icon.addPixmap(QPixmap(os.path.join(basedir,'res/icons/Dashboard/not_available.svg')), QIcon.Normal, QIcon.Off)
        self.isValid_icon = QIcon()
        self.isValid_icon.addPixmap(QPixmap(os.path.join(basedir,'res/icons/Dashboard/available.svg')), QIcon.Normal, QIcon.Off)
        self.nameHint.setIcon(self.notValid_icon)
        self.HPLabel = BodyLabel(self.tr("HP Level:"))

        spacerItem12 = QSpacerItem(30, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem12)
        self.horizontalLayout_3.addWidget(self.nameEdit)
        spacerItem15= QSpacerItem(5, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem15)
        self.horizontalLayout_3.addWidget(self.nameHint)
        spacerItem13= QSpacerItem(10, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem13)
        self.horizontalLayout_3.addWidget(self.HPLabel)
        spacerItem14= QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem14)

        self.verticalLayout.addLayout(self.horizontalLayout_3)
        spacerItem9 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem9)

        # Decision Button
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_4.setContentsMargins(10,0,10,0)
        self.confirmBtn = PushButton(self.tr("Create"))
        self.confirmBtn.setFixedWidth(165)
        self.cancelBtn = PushButton(self.tr("Cancel"))
        self.cancelBtn.setFixedWidth(165)

        spacerItem15 = QSpacerItem(30, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem15)
        self.horizontalLayout_4.addWidget(self.confirmBtn)
        spacerItem16 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem16)
        self.horizontalLayout_4.addWidget(self.cancelBtn)
        spacerItem17 = QSpacerItem(30, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem17)

        self.verticalLayout.addLayout(self.horizontalLayout_4)
 
        spacerItem20 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem20)

        self.frame.setLayout(self.verticalLayout)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.frame, Qt.AlignCenter)
        self.setLayout(self.layout_window)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        if settings.platform == 'win32':
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)

        self.frame.setFixedSize(480, 550)

    def _generateSeparator(self):
        cnct_icon = TransparentToolButton(FIF.CHEVRON_RIGHT)
        cnct_icon.setEnabled(False)
        cnct_icon.setFixedWidth(10)
        return cnct_icon

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
        self.hide()

    def __connectSignalToSlot(self):
        self.button_close.clicked.connect(self._closeit)
        self.actComboBox.currentTextChanged.connect(self._updateEditPanel)

        self.start_SpinBox.valueChanged.connect(self._startValueChanged)
        self.end_SpinBox.valueChanged.connect(self._endValueChanged)
        self.rep_SpinBox.valueChanged.connect(self._repValueChanged)

        self.saveBtn.clicked.connect(self._saveClicked)
        self.deleteBtn.clicked.connect(self._deleteClicked)

        self.init_actBtn.clicked.connect(self._initActClicked)

        self.nameEdit.textChanged.connect(self._checkNameAvail)
        self.confirmBtn.clicked.connect(self._confirmClicked)
        self.cancelBtn.clicked.connect(self._closeit)

    def __showMessageBox(self, title, content):

        WarrningMessage = MessageBox(title, content, self)
        WarrningMessage.yesButton.setText(self.tr('Confirm'))
        WarrningMessage.cancelButton.setText(self.tr('Cancel'))
        if WarrningMessage.exec():
            return True
        else:
            #print('Cancel button is pressed')
            return False
        
    def updateCombo(self):
        # Switch to 'Add New' Tag
        self.init_actBtn.setChecked(True)
        self._initActClicked()

        # Check all predefined animation
        anim_configs = settings.act_data.allAct_params[settings.petname]
        anim_list = [i.text for i in self.actComboBox.items]
        for anim_name, anim_conf in anim_configs.items():
            if anim_conf['act_type'] != 'customized':
                if anim_conf['unlocked'] and not anim_conf['special_act'] and anim_name not in anim_list:
                    self.actComboBox.addItem(anim_name)
                elif not anim_conf['unlocked'] and anim_name in anim_list:
                    anim_combo_idx = self.actComboBox.findText(anim_name)
                    self.actComboBox.removeItem(anim_combo_idx)
                    # check if a tag was created with this animation
                    invalid_tag_ids = [tag_id for tag_id, tag_conf in self.all_design_conf.items() if tag_conf['name']==anim_name]
                    for tag_id in invalid_tag_ids:
                        self._deleteTag(tag_id)


    def _updateEditPanel(self, anim_name):
        if self.actComboBox.currentIndex() == -1:
            self.empty_EditPanel()
            self._empty_actConf()
        else:
            # get current animation config
            self.current_template_conf = self._get_anim_config(anim_name)
            self._EditPanel_animChanged()
        
        if self.current_tagid != 'initAct':
            # existing tag has been edited
            self._update_tag_conf()
            self._update_tag_name()
            self._update_HP_lvl()
            self.switch_Btn_state("Reload_Design")


    def _startValueChanged(self):
        if not self.current_template_conf:
            return
        
        startVal = self.start_SpinBox.value()
        self._set_img(startVal-1)
        self.end_SpinBox.blockSignals(True)
        self.end_SpinBox.setRange(startVal, self.end_SpinBox.maximum())
        self.end_SpinBox.blockSignals(False)
        self.animProgress.setValue(startVal)

        if self.current_tagid != 'initAct':
            # existing tag has been edited
            self._update_tag_conf()
    

    def _endValueChanged(self):
        if not self.current_template_conf:
            return
        
        endVal = self.end_SpinBox.value()
        self._set_img(endVal-1)
        self.start_SpinBox.blockSignals(True)
        self.start_SpinBox.setRange(self.start_SpinBox.minimum(), endVal)
        self.start_SpinBox.blockSignals(False)
        self.animProgress.setValue(endVal)

        if self.current_tagid != 'initAct':
            # existing tag has been edited
            self._update_tag_conf()


    def _repValueChanged(self):
        if not self.current_template_conf:
            return
        if self.current_tagid != 'initAct':
            # existing tag has been edited
            self._update_tag_conf()

    def _saveClicked(self):
        if self.current_tagid == 'initAct':
            # New design saved
            # Get design config
            current_design_conf = {"name": self.actComboBox.currentText(),
                                "comboIndex": self.actComboBox.currentIndex(),
                                "start": self.start_SpinBox.value()-1,
                                "end": self.end_SpinBox.value()-1,
                                "repeat": self.rep_SpinBox.value()}
            
            # save in self.all_design_conf
            tag_id = str(uuid.uuid4())
            self.all_design_conf[tag_id] = current_design_conf

            # create new Tag
            self._create_design_Tag(tag_id)

            # refresh Edit Panel and check the "Add New" Tag
            self.empty_EditPanel()
            self._empty_actConf()

            # check design HP level
            self._update_HP_lvl()
        
        else:
            # Existing tag got updated
            print("This should not happen")

    def _deleteTag(self, tag_id):
        # remove design config
        del self.all_design_conf[tag_id]
        # remove tag from tag_dict and layout
        design_tag = self.tags_dict.pop(tag_id)
        for i, item in enumerate(self.actCompLayout._items):
            if item.widget() is design_tag:
                tag_layout_idx = i
                break
        if tag_layout_idx > 1:
            separator = self.actCompLayout.takeAt(tag_layout_idx-1)
            separator.deleteLater()
        elif tag_layout_idx == 1 and len(self.tags_dict) > 0:
            separator = self.actCompLayout.takeAt(tag_layout_idx+1)
            separator.deleteLater()

        self.actCompLayout.removeWidget(design_tag)
        design_tag.deleteLater()
        self._update_HP_lvl()


    def _deleteClicked(self):
        if self.current_tagid == 'initAct':
            print("This should not happen")
        else:
            # Ask to confirm
            title = self.tr("Delete?")
            content = self.tr("""Do you want to delete this single design?
You won't be able to recover after confirming.""")
            if not self.__showMessageBox(title, content):
                return

            # remove design config
            del self.all_design_conf[self.current_tagid]
            # remove tag from tag_dict and layout
            design_tag = self.tags_dict.pop(self.current_tagid)
            for i, item in enumerate(self.actCompLayout._items):
                if item.widget() is design_tag:
                    tag_layout_idx = i
                    break
            if tag_layout_idx > 1:
                separator = self.actCompLayout.takeAt(tag_layout_idx-1)
                separator.deleteLater()
            elif tag_layout_idx == 1 and len(self.tags_dict) > 0:
                separator = self.actCompLayout.takeAt(tag_layout_idx+1)
                separator.deleteLater()

            self.actCompLayout.removeWidget(design_tag)
            design_tag.deleteLater()

            # refresh Edit Panel and check the "Add New" Tag
            self.init_actBtn.setChecked(True)
            self.empty_EditPanel()
            self._empty_actConf()
            self._update_HP_lvl()


    def _initActClicked(self):
        if self.init_actBtn.isChecked():
            # set all others as not checked
            self._uncheck_other_tags()
            self.empty_EditPanel()
        else:
            self.froze_EditPanel()

        self._empty_actConf()


    def _actTagClicked(self, tag_id):
        if not self.tags_dict[tag_id].isChecked():
            # no tag is checked
            self.froze_EditPanel()
            self._empty_actConf()
        else:
            # set all others as not checked
            self._uncheck_other_tags(tag_id)

            # set up configs
            self._saved_actConf(tag_id)

            # set up Edit Panel
            self._EditPanel_tagSelected()


    def _checkNameAvail(self):
        design_name = self.nameEdit.text()
        if not design_name or design_name in settings.act_data.allAct_params[settings.petname].keys():
            self.design_name_valid = False
        else:
            self.design_name_valid = True
        
        self._setNameCheck(self.design_name_valid)

    def _setNameCheck(self, name_valid: bool):
        if name_valid:
            self.nameHint.setIcon(self.isValid_icon)
        else:
            self.nameHint.setIcon(self.notValid_icon)


    def _confirmClicked(self):
        # Check design config
        if not self.all_design_conf:
            title = self.tr("Empty Design")
            content = self.tr("""You need to add at least one animation to create new design.""")
            self.__showMessageBox(title, content)
            return

        # Check design name
        if not self.design_name_valid:
            title = self.tr("Name Not Valid")
            content = self.tr("""The new name cannot be empty or the same as existing ones.""")
            self.__showMessageBox(title, content)
            return

        # Ask the user to confirm create
        title = self.tr("Confirm to create")
        content = self.tr("""After confirmation, designed animation will be added to list""")
        if not self.__showMessageBox(title, content):
            return

        # Convert design config into actData format
        formated_config = self._format_config_to_actData()

        # send to animation panel
        self.createNewAnim.emit(self.nameEdit.text(), formated_config)

        # clean design name and set as not valid
        self.nameEdit.setText("")
        self._checkNameAvail()

    def _empty_actConf(self):
        self.current_template_conf = {}
        self.current_tagid = 'initAct'
    
    def _saved_actConf(self, tag_id):
        anim_name = self.all_design_conf[tag_id]['name']
        if anim_name != self.current_template_conf.get('name', 'NoAnimation'):
            self.current_template_conf = self._get_anim_config(anim_name)
        self.current_tagid = tag_id

    def _update_tag_conf(self):
        new_design_conf = {"name": self.actComboBox.currentText(),
                           "comboIndex": self.actComboBox.currentIndex(),
                           "start": self.start_SpinBox.value()-1,
                           "end": self.end_SpinBox.value()-1,
                           "repeat": self.rep_SpinBox.value()}
        self.all_design_conf[self.current_tagid] = new_design_conf

    def _update_tag_name(self):
        anim_name = self.all_design_conf[self.current_tagid]['name']
        self.tags_dict[self.current_tagid].setText(anim_name)

    '''
    def _init_designConf(self, anim_name):
        self.current_design_conf = {"name": anim_name,
                                    "comboIndex": self.actComboBox.currentIndex(),
                                    "start": 1,
                                    "end": 1,
                                    "repeat": 1}
    '''

    def _uncheck_other_tags(self, tag_id='initAct'):
        for uid, design_tag in self.tags_dict.items():
            if uid != tag_id:
                design_tag.setChecked(False)
        if tag_id != 'initAct':
            self.init_actBtn.setChecked(False)

    def empty_EditPanel(self):
        self.actComboBox.blockSignals(True)
        self.actComboBox.setCurrentIndex(-1)
        self.actComboBox.blockSignals(False)
        self.actComboBox.setEnabled(True)

        self.start_SpinBox.blockSignals(True)
        self.start_SpinBox.setRange(1, 1)
        self.start_SpinBox.blockSignals(False)
        self.start_SpinBox.setEnabled(True)

        self.end_SpinBox.blockSignals(True)
        self.end_SpinBox.setRange(1, 1)
        self.end_SpinBox.blockSignals(False)
        self.end_SpinBox.setEnabled(True)

        self.rep_SpinBox.blockSignals(True)
        self.rep_SpinBox.setValue(1)
        self.rep_SpinBox.blockSignals(False)
        self.rep_SpinBox.setEnabled(True)

        self.image.setPixmap(QPixmap())
        self.switch_Btn_state("Init_New")
        self.animProgress.setValue(1)

    def froze_EditPanel(self):
        self.actComboBox.blockSignals(True)
        self.actComboBox.setCurrentIndex(-1)
        self.actComboBox.blockSignals(False)
        self.actComboBox.setEnabled(False)

        self.start_SpinBox.blockSignals(True)
        self.start_SpinBox.setRange(1, 1)
        self.start_SpinBox.blockSignals(False)
        self.start_SpinBox.setEnabled(False)

        self.end_SpinBox.blockSignals(True)
        self.end_SpinBox.setRange(1, 1)
        self.end_SpinBox.blockSignals(False)
        self.end_SpinBox.setEnabled(False)

        self.rep_SpinBox.blockSignals(True)
        self.rep_SpinBox.setValue(1)
        self.rep_SpinBox.blockSignals(False)
        self.rep_SpinBox.setEnabled(False)

        self.image.setPixmap(QPixmap())
        self.switch_Btn_state("Init_New")
        self.animProgress.setValue(1)


    def _EditPanel_animChanged(self):
        # set up image
        self._set_img(0)

        num_imgs = max(self.current_template_conf['acts_num_images'],
                       self.current_template_conf['accs_num_images'])

        # init progress bar
        self.animProgress.setRange(0,num_imgs)
        self.animProgress.setValue(1)

        # ini spinboxsc
        self.start_SpinBox.blockSignals(True)
        self.start_SpinBox.setRange(1, num_imgs)
        self.start_SpinBox.setValue(1)
        self.start_SpinBox.blockSignals(False)
        self.start_SpinBox.setEnabled(True)
        self.end_SpinBox.blockSignals(True)
        self.end_SpinBox.setRange(1, num_imgs)
        self.end_SpinBox.setValue(1)
        self.end_SpinBox.blockSignals(False)
        self.end_SpinBox.setEnabled(True)
        self.rep_SpinBox.blockSignals(True)
        self.rep_SpinBox.setValue(1)
        self.rep_SpinBox.blockSignals(False)
        self.rep_SpinBox.setEnabled(True)

        # change buttons state
        self.switch_Btn_state("Init_Anim")

    def _EditPanel_tagSelected(self):
        design_conf = self.all_design_conf[self.current_tagid]
        start_img_index = design_conf['start']+1
        end_img_index = design_conf['end']+1
        rep_num = design_conf['repeat']
        anim_combo_index = design_conf['comboIndex']
        num_imgs = max(self.current_template_conf['acts_num_images'],
                       self.current_template_conf['accs_num_images'])
        
        self._set_img(start_img_index-1)

        # init progress bar
        self.animProgress.setRange(0,num_imgs)
        self.animProgress.setValue(start_img_index)

        # comboBox
        self.actComboBox.blockSignals(True)
        self.actComboBox.setCurrentIndex(anim_combo_index)
        self.actComboBox.blockSignals(False)
        self.actComboBox.setEnabled(True)

        # ini spinboxsc
        self.start_SpinBox.blockSignals(True)
        self.start_SpinBox.setRange(1, end_img_index)
        self.start_SpinBox.setValue(start_img_index)
        self.start_SpinBox.blockSignals(False)
        self.start_SpinBox.setEnabled(True)
        self.end_SpinBox.blockSignals(True)
        self.end_SpinBox.setRange(start_img_index, num_imgs)
        self.end_SpinBox.setValue(end_img_index)
        self.end_SpinBox.blockSignals(False)
        self.end_SpinBox.setEnabled(True)
        self.rep_SpinBox.blockSignals(True)
        self.rep_SpinBox.setValue(rep_num)
        self.rep_SpinBox.blockSignals(False)
        self.rep_SpinBox.setEnabled(True)

        # change buttons state
        self.switch_Btn_state("Reload_Design")
        

    def switch_Btn_state(self, state):
        if state == "Init_New":
            # When "Add New" Tag clicked or no Tag selected
            self.saveBtn.setEnabled(False)
            self.deleteBtn.setEnabled(False)
        elif state == "Init_Anim":
            # When user selected a new animation to edit
            self.saveBtn.setEnabled(True)
            self.deleteBtn.setEnabled(False)
        elif state == "Reload_Design":
            # When user selected a new animation to edit
            self.saveBtn.setEnabled(False)
            self.deleteBtn.setEnabled(True)

    def _create_design_Tag(self, tag_id):
        # create tag
        design_tag = PillPushButton(self.all_design_conf[tag_id]['name'])
        design_tag.setChecked(False)
        design_tag.tag_index = tag_id #self.all_design_conf[tag_id]['comboIndex']
        
        # add into tag_dict
        self.tags_dict[tag_id] = design_tag

        # connect signal to slot
        design_tag.clicked.connect(lambda checked=False,tag=design_tag.tag_index: self._actTagClicked(tag))

        # add to UI
        if len(self.tags_dict) > 1:
            self.actCompLayout.addWidget(self._generateSeparator())
        self.actCompLayout.addWidget(design_tag)
        

    def _get_anim_config(self, anim_name):
        anim_type = settings.act_data.allAct_params[settings.petname][anim_name]['act_type']
        if anim_type == 'random_act':
            act_index = settings.pet_conf.act_name.index(anim_name)
            acts = settings.pet_conf.random_act[act_index]
            acts_index_range, acts_num_images, acts_time = get_Acts_info(acts)
            accs = []
            accs_index_range, accs_num_images, accs_time = [0], 0, 0
            anchor = [0,0]
        
        elif anim_type == 'accessory_act':
            acts = settings.pet_conf.accessory_act[anim_name]['act_list']
            acts_index_range, acts_num_images, acts_time = get_Acts_info(acts)
            accs = settings.pet_conf.accessory_act[anim_name]['acc_list']
            accs_index_range, accs_num_images, accs_time = get_Acts_info(accs)
            anchor = settings.pet_conf.accessory_act[anim_name]['anchor']

        # Fill in duration gap (between act and acc) with EmptyAct
        #time_diff = acts_time - accs_time
        imgn_diff = acts_num_images - accs_num_images
        refresh_t = acts[0].frame_refresh # this assum in one animation, all acts have the same refresh unit time
        if imgn_diff > 0:
            #num_emptyAct = int(time_diff//10)
            accs.append(EmptyAct(imgn_diff, refresh_t))
            accs_index_range.append(accs_index_range[-1]+imgn_diff)
            accs_num_images += imgn_diff

        elif imgn_diff < 0:
            #num_emptyAct = int(-time_diff//10)
            acts.append(EmptyAct(-imgn_diff, refresh_t))
            acts_index_range.append(acts_index_range[-1]-imgn_diff)
            acts_num_images += -imgn_diff
        
        assert acts_index_range[-1] == accs_index_range[-1]
        assert acts_num_images == accs_num_images

        return {"name": anim_name,
                "acts": acts,
                "acts_index_range": acts_index_range,
                "acts_num_images": acts_num_images,
                "accs": accs,
                "accs_index_range": accs_index_range,
                "accs_num_images": accs_num_images,
                "anchor": anchor}
    
    def _set_img(self, img_index):
        # Get act and acc image
        act_img, acc_img = self._get_index_img(img_index)
        anchor = self.current_template_conf['anchor']
        # Draw the two image together
        combined_width, combined_height = calc_qpixmap_size(act_img, acc_img, anchor)
        if not act_img:
            combined_pixmap = acc_img
        elif not acc_img:
            combined_pixmap = act_img
        else:
            combined_pixmap = QPixmap(combined_width, combined_height)
            combined_pixmap.fill(Qt.transparent)
            #calculatre draw position
            act_bottom_mid_x = act_img.width() // 2
            act_bottom_mid_y = act_img.height()
            acc_top_left_x = act_bottom_mid_x + anchor[0]
            acc_top_left_y = act_bottom_mid_y + anchor[1]
            offset_x = min(0, acc_top_left_x)
            offset_y = min(0, acc_top_left_y)

            painter = QPainter(combined_pixmap)
            painter.drawPixmap(0-offset_x, 0-offset_y, act_img)
            
            painter.drawPixmap(acc_top_left_x-offset_x, acc_top_left_y-offset_y, acc_img)
            painter.end()

        # Resize image label
        pixmap_w, pixmap_h = combined_pixmap.width(), combined_pixmap.height()
        #print(pixmap_w, pixmap_h)
        self.resize_image_label(pixmap_w, pixmap_h)
        self.image.setPixmap(combined_pixmap)


    def _get_index_img(self, img_index):
        # Main action
        act_index = sum( img_index >= idx for idx in self.current_template_conf['acts_index_range'] ) - 1
        if img_index >= self.current_template_conf['acts_index_range'][-1]:
            act_img = QPixmap()
        else:
            act_img_index = img_index - self.current_template_conf['acts_index_range'][act_index]
            act = self.current_template_conf['acts'][act_index]
            act_img = (act.images * act.act_num)[act_img_index]

        # Accessory
        acc_index = sum( img_index >= idx for idx in self.current_template_conf['accs_index_range'] ) - 1
        if img_index >= self.current_template_conf['accs_index_range'][-1]:
            acc_img = QPixmap()
        else:
            acc_img_index = img_index - self.current_template_conf['accs_index_range'][acc_index]
            acc = self.current_template_conf['accs'][acc_index]
            acc_img = (acc.images * acc.act_num)[acc_img_index]

        return act_img, acc_img
    
    def resize_image_label(self, img_w, img_h):
        frame_edge = 180
        if img_w <= frame_edge and img_h <= frame_edge:
            self.image.setFixedSize(img_w, img_h)
        else:
            scale_factor = max(img_w/frame_edge, img_h/frame_edge)
            self.image.setFixedSize(int(img_w/scale_factor), int(img_h/scale_factor))
        #print(self.image.width(), self.image.height())

    def _update_HP_lvl(self):
        anim_list = [v['name'] for _,v in self.all_design_conf.items()]
        anim_configs = settings.act_data.allAct_params[settings.petname]
        anim_HP_status = [ anim_configs[anim_name]['status_type'][0] for anim_name in anim_list ]
        if anim_HP_status:
            self.design_status = max(anim_HP_status)
            self.HPLabel.setText(self.tr("HP Level:") + f" {settings.TIER_NAMES[self.design_status]}")
        else:
            self.HPLabel.setText(self.tr("HP Level:"))

    def _format_config_to_actData(self):
        act_list = []
        acc_list = []
        anchor_list = []
        for _, design_conf in self.all_design_conf.items():
            anim_name = design_conf['name']
            anim_conf = self._get_anim_config(anim_name)
            design_start = design_conf['start']
            design_end = design_conf['end']
            design_rep = design_conf['repeat']
            acts, accs, anchors = self._format_design_acts(anim_conf, design_start, 
                                                           design_end, design_rep)
            for i in range(design_rep):
                act_list += acts
                acc_list += accs
                anchor_list += anchors

        act_list, acc_list, anchor_list = self._clean_design_conf(act_list, acc_list, anchor_list)

        self._update_HP_lvl()
        anim_list = [v['name'] for _,v in self.all_design_conf.items()]
        anim_configs = settings.act_data.allAct_params[settings.petname]
        anim_FV_status = [ anim_configs[anim_name]['status_type'][1] for anim_name in anim_list ]
        design_FV_status = max(anim_FV_status)

        return {"act_type":"customized",
                "special_act": False,
                "unlocked": True,
                "in_playlist": False,
                "act_prob": 1.0,
                "status_type": [self.design_status, design_FV_status],
                "act_list": act_list,
                "acc_list": acc_list,
                "anchor_list": anchor_list}
            
    def _format_design_acts(self, anim_conf, design_start, design_end, design_rep):
        # acts
        acts = []
        start_act_index = sum( design_start >= idx for idx in anim_conf['acts_index_range'] ) - 1
        end_act_index = sum( design_end >= idx for idx in anim_conf['acts_index_range'] ) - 1
        overall_img_index = design_start
        for i in range(start_act_index, end_act_index+1):
            act_min_idx = anim_conf['acts_index_range'][i]
            act_max_idx = anim_conf['acts_index_range'][i+1] - 1
            img_start = overall_img_index - act_min_idx
            img_end = min(design_end, act_max_idx) - act_min_idx
            act = anim_conf['acts'][i]

            if act.act_name:
                acts.append([act.act_name, img_start, img_end, 1])
            else:
                acts.append([None, act.frame_refresh*1000, img_end-img_start+1])
            
            overall_img_index = act_max_idx+1

        # accs and anchors
        accs, anchors = [], []
        anchor = anim_conf['anchor']
        start_acc_index = sum( design_start >= idx for idx in anim_conf['accs_index_range'] ) - 1
        end_acc_index = sum( design_end >= idx for idx in anim_conf['accs_index_range'] ) - 1
        overall_img_index = design_start
        for i in range(start_acc_index, end_acc_index+1):
            acc_min_idx = anim_conf['accs_index_range'][i]
            acc_max_idx = anim_conf['accs_index_range'][i+1] - 1
            img_start = overall_img_index - acc_min_idx
            img_end = min(design_end, acc_max_idx) - acc_min_idx
            acc = anim_conf['accs'][i]

            if acc.act_name:
                accs.append([acc.act_name, img_start, img_end, 1])
                anchors.append(anchor)
            else:
                accs.append([None, acc.frame_refresh*1000, img_end-img_start+1])
                anchors.append([0,0])
            
            overall_img_index = acc_max_idx+1
        
        return acts, accs, anchors
    
    def _clean_design_conf(self, act_list, acc_list, anchor_list):
        new_acc_list = []
        new_anchor_list = []
        for i in range(len(acc_list)-1, -1, -1):
            if acc_list[i][0]:
                new_acc_list = acc_list[:i+1]
                new_anchor_list = anchor_list[:i+1]
                break

        new_act_list = [i if i[0] else i[1:] for i in act_list]
        new_acc_list = [i if i[0] else i[1:] for i in new_acc_list]

        return new_act_list, new_acc_list, new_anchor_list



'''
{'fe8e40c0-346b-4a56-b4c8-68d34d83183b': {'name': '站立', 'comboIndex': 0, 'start': 13, 'end': 50, 'repeat': 2}, 
 'b8ff996d-7543-4968-a8a9-d2329433451e': {'name': 'Q技能', 'comboIndex': 8, 'start': 16, 'end': 146, 'repeat': 1}}
{'act_type': 'customized', 'special_act': False, 'unlocked': True, 'in_playlist': False, 'act_prob': 1.0, 'status_type': [2, 2], 
 'act_list': [['left', 13, 50, 1], ['left', 13, 50, 1], ['qskill', 16, 36, 1], [None, 60.0, 110]], 
 'acc_list': [[None, 60.0, 38], [None, 60.0, 38], ['palace_2', 7, 99, 1], ['palace_2', 0, 37, 1]], 
 'anchor_list': [[0, 0], [0, 0], [-445.0, -501.0], [-445.0, -501.0]]}


{'fe8e40c0-346b-4a56-b4c8-68d34d83183b': {'name': '站立', 'comboIndex': 0, 'start': 13, 'end': 50, 'repeat': 2}, 'b8ff996d-7543-4968-a8a9-d2329433451e': {'name': 'Q技能', 'comboIndex': 8, 'start': 40, 'end': 146, 'repeat': 1}}
{'act_type': 'customized', 'special_act': False, 'unlocked': True, 'in_playlist': False, 'act_prob': 1.0, 'status_type': [2, 2], 
 'act_list': [['left', 13, 50, 1], ['left', 13, 50, 1], [None, 60.0, 107]], 
 'acc_list': [[None, 60.0, 38], [None, 60.0, 38], ['palace_2', 31, 99, 1], ['palace_2', 0, 37, 1]], 
 'anchor_list': [[0, 0], [0, 0], [-445.0, -501.0], [-445.0, -501.0]]}     

{'bc3f6d4a-f94b-4afa-8ae7-eceac37e8ee5': {'name': '挥手', 'comboIndex': 2, 'start': 0, 'end': 28, 'repeat': 2}, 
'eaa2686d-9f9c-4ab9-ba31-803096c93e64': {'name': 'Q技能', 'comboIndex': 8, 'start': 0, 'end': 210, 'repeat': 1}, 
'f602be46-70f6-4469-84e5-7a44ec49caba': {'name': '挥手', 'comboIndex': 2, 'start': 0, 'end': 28, 'repeat': 2}}
{'act_type': 'customized', 'special_act': False, 'unlocked': True, 'in_playlist': False, 'act_prob': 1.0, 'status_type': [2, 2], ]
'act_list': [['wavehand', 0, 28, 1], ['wavehand', 0, 28, 1], ['qskill', 0, 36, 1], [60.0, 174], ['wavehand', 0, 28, 1], ['wavehand', 0, 28, 1]], 
'acc_list': [[60.0, 29], [60.0, 29], ['palace_1', 0, 8, 1]], 
'anchor_list': [[0, 0], [0, 0], [-445.0, -501.0]]}

[]
[0, 50]
[0, 50, 120, 400]


[3, 125, 5]
[0, 0, 1]
[75, 350, 2]
[75, 450, 2]
'''


def get_Acts_info(acts):
    act_nums = [ len(act.images)*act.act_num for act in acts]
    acts_index_range = [sum(act_nums[:i]) for i in range(len(act_nums)+1)]
    num_images = acts_index_range[-1]
    # action duration in ms
    act_time = sum([ len(act.images)*act.act_num*act.frame_refresh*1000 for act in acts])

    return acts_index_range, num_images, act_time


def calc_qpixmap_size(pixmap1, pixmap2, anchor):
    anchor_x, anchor_y = anchor[0], anchor[1]
    # Calculate extreme coordinates based on anchor points
    width_leftmost = min(0, pixmap1.width() // 2 + anchor_x)
    width_rightmost = max(pixmap1.width(), pixmap1.width() // 2 + anchor_x + pixmap2.width())
    
    height_topmost = min(0, pixmap1.height() + anchor_y)
    height_bottommost = max(pixmap1.height(), pixmap1.height() + anchor_y + pixmap2.height())
    
    # Determine the dimensions of the combined pixmap
    combined_width = width_rightmost - width_leftmost
    combined_height = height_bottommost - height_topmost
    
    return combined_width, combined_height
