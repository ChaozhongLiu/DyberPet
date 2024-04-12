# coding:utf-8
import os
from PySide6.QtWidgets import (QWidget, QApplication, QSystemTrayIcon, QMenu, QHBoxLayout,
                               QFrame, QLabel, QSpacerItem, QSizePolicy, QVBoxLayout, QLayout)
from PySide6.QtGui import QIcon, QAction, QCursor, QImage, QPixmap, QColor
from PySide6.QtCore import Qt, QPoint, Signal, QSize

from qfluentwidgets import (StrongBodyLabel, TransparentToolButton, BodyLabel, PushButton)
from qfluentwidgets import FluentIcon as FIF
from DyberPet.utils import text_wrap
import DyberPet.settings as settings
from DyberPet.Dashboard.dashboard_widgets import HorizontalSeparator
basedir = settings.BASEDIR


class SystemTray(QSystemTrayIcon):
    def __init__(self, menu, parent=None):
        super(SystemTray, self).__init__(parent)

        # Set an icon for the tray
        self.setIcon(QIcon('path_to_your_icon.png'))

        # Set the provided menu for the tray
        self.setMenu(menu)

        # Connect the activated signal to our custom slot
        self.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Context:
            # Get the current position of the cursor
            cursor_pos = QCursor.pos() #QApplication.primaryScreen().cursor().pos() #QApplication.desktop().cursor().pos()

            # Adjust the position. Here, we're moving it 100 pixels upward.
            new_pos = cursor_pos - QPoint(0, 200)
            self.contextMenu().popup(new_pos)

    def setMenu(self, menu):
        """ Set a new context menu for the tray """
        old_menu = self.contextMenu()
        if old_menu:
            old_menu.hide()
            old_menu.deleteLater()
            
        super().setContextMenu(menu)



class DPDialogue(QWidget):
    closed_acc = Signal(str, name='closed_acc')

    def __init__(self, acc_index,
                 message={},
                 pos_x=0,
                 pos_y=0,
                 parent=None):
        super(DPDialogue, self).__init__(parent)

        self.is_follow_mouse = False
        self.acc_index = acc_index
        self.message = message
        self.pos_x = pos_x
        self.pos_y = pos_y

        self.setSizePolicy(QSizePolicy.Minimum, 
                           QSizePolicy.Minimum)

        self.__initWidget()

    def __initWidget(self):

        # The Round Dialogue Frame
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

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(10, 5, 10, 15)

        # Title Header
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.setContentsMargins(0,0,0,0)

        icon = QLabel()
        image = QPixmap()
        image.load(os.path.join(basedir,'res/icons/Dialogue_icon.png'))
        icon.setFixedSize(int(25), int(25))
        icon.setScaledContents(True)
        icon.setPixmap(image)
        
        self.title = StrongBodyLabel(self)
        self.title.setText(self.message.get('title',''))
        self.title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft) 

        self.button_close = TransparentToolButton(FIF.CLOSE, self)
        self.button_close.setFixedSize(25,25)
        self.button_close.setIconSize(QSize(15,15))
        self.button_close.clicked.connect(self._closeit)
        
        self.horizontalLayout_1.addWidget(icon)
        spacerItem1 = QSpacerItem(5, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem1)
        self.horizontalLayout_1.addWidget(self.title)
        spacerItem2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_1.addItem(spacerItem2)
        self.horizontalLayout_1.addWidget(self.button_close, 0, Qt.AlignRight)

        self.verticalLayout.addLayout(self.horizontalLayout_1)
        spacerItem3 = QSpacerItem(20, 15, QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem3)


        # Dialogue Context
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_2.setContentsMargins(10,0,10,0)
        self.text_now = self.message['start']
        self.label = BodyLabel(self.message[self.message['start']])
        self.label.setWordWrap(True)
        self.label.setFixedWidth(250)
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_2.addStretch()
        self.horizontalLayout_2.addWidget(self.label, Qt.AlignCenter)
        self.horizontalLayout_2.addStretch()

        self.verticalLayout.addLayout(self.horizontalLayout_2, Qt.AlignCenter)
        spacerItem4 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem4)

        self.verticalLayout.addWidget(HorizontalSeparator(QColor(20,20,20,125), 1))
        spacerItem5 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem5)


        # Dialogue Options
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_3.setContentsMargins(10,0,10,0)
        self.OptionLayout = QVBoxLayout()
        self.OptionLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.OptionLayout.setContentsMargins(0,0,0,0)
        self.OptionLayout.setSpacing(10)
        self.OptionGenerator(self.message['start'])
        self.horizontalLayout_3.addStretch()
        self.horizontalLayout_3.addLayout(self.OptionLayout, Qt.AlignCenter)
        self.horizontalLayout_3.addStretch()
        self.verticalLayout.addLayout(self.horizontalLayout_3, Qt.AlignCenter)

        self.frame.setLayout(self.verticalLayout)
        self.frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.frame, Qt.AlignCenter) #, Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(self.layout_window)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        if settings.platform == 'win32':
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)

        self.frame.adjustSize()
        self.adjustSize()

        self.move(self.pos_x-self.width()//2, self.pos_y-self.height())
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
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)

        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()

    def OptionGenerator(self, text_key=None, prev_text=None, reverse=False):
        for item in [self.OptionLayout.itemAt(i) for i in range(self.OptionLayout.count())]:
            widget = item.widget()
            self.OptionLayout.removeWidget(widget)
            widget.deleteLater()
        
        self.opts_dict = {}
        option_index = 0

        if prev_text is not None and not reverse:
            if text_key is not None:
                self.message['relationship']['option_prev_%s'%text_key] = [prev_text]
                if 'option_prev_%s'%text_key not in self.message['relationship'].get(text_key, []):
                    self.message['option_prev_%s'%text_key] = self.tr('Back')
                    self.message['relationship'][text_key] = self.message['relationship'].get(text_key, []) + ['option_prev_%s'%text_key]
            else:
                self.message['relationship']['option_prev_end'] = [prev_text]
                self.opts_dict[option_index] = DialogueButtom(self.tr('Back'), 'option_prev_end') ##################
                self.opts_dict[option_index].clicked.connect(self.confirm)
                self.OptionLayout.addWidget(self.opts_dict[option_index], Qt.AlignCenter)
                option_index += 1

        if text_key is not None:
            for option in self.message.get('relationship', {}).get(text_key, []):
                self.opts_dict[option_index] = DialogueButtom(self.message[option], option) ##################
                self.opts_dict[option_index].clicked.connect(self.confirm)
                self.OptionLayout.addWidget(self.opts_dict[option_index], Qt.AlignCenter)
                option_index += 1

        if option_index == 0:
            pass


    def confirm(self):
        opt_key = self.sender().msg_key
        new_key = self.message['relationship'].get(opt_key,[])
        if new_key == []:
            self.label.setText('')
            self.label.adjustSize()
            self.OptionGenerator(prev_text=self.text_now, reverse=self.sender().msg==self.tr('Back'))
            self.text_now = ''
        else:
            new_key = new_key[0]
            self.label.setText(self.message[new_key])
            self.label.adjustSize()
            self.OptionGenerator(new_key, self.text_now, reverse=self.sender().msg==self.tr('Back'))
            self.text_now = new_key

        self.frame.adjustSize()
        self.adjustSize()
        

class DialogueButtom(PushButton):
    def __init__(self, msg, msg_key):

        super().__init__()
        self.msg = msg
        self.msg_key = msg_key
        self.setText(text_wrap(msg,15))
        self.setFixedWidth(250)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.adjustSize()