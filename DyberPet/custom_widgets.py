# coding:utf-8
import os
from PySide6.QtWidgets import (QWidget, QApplication, QSystemTrayIcon, QMenu, QHBoxLayout,
                               QFrame, QLabel, QSpacerItem, QSizePolicy, QVBoxLayout, 
                               QLayout, QProgressBar)
from PySide6.QtGui import (QIcon, QAction, QCursor, QImage, QPixmap, QColor,
                           QPainter, QBrush, QPen, QPainterPath, QFont, QFontMetrics)
from PySide6.QtCore import Qt, QPoint, Signal, QSize, QRectF


from qfluentwidgets import (StrongBodyLabel, TransparentToolButton, BodyLabel, PushButton, 
                            isDarkTheme, Slider, CaptionLabel, setFont, ToolTipFilter)
from qfluentwidgets import FluentIcon as FIF
from DyberPet.utils import text_wrap
import DyberPet.settings as settings

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
            new_pos = cursor_pos - QPoint(0, self.contextMenu().height()-20)
            self.contextMenu().popup(new_pos)

    def setMenu(self, menu):
        """ Set a new context menu for the tray """
        old_menu = self.contextMenu()
        if old_menu:
            old_menu.hide()
            old_menu.deleteLater()
            
        super().setContextMenu(menu)




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

##########################
#      Progress Bar
##########################

class RoundBarBase(QProgressBar):

    def __init__(self, fill_color, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Custom colors and sizes
        self.bar_color = QColor(fill_color)  # Fill color
        self.border_color = QColor(0, 0, 0)  # Border color
        self.border_width = 1                # Border width in pixels
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Full widget rect minus border width to avoid overlap
        full_rect = QRectF(self.border_width / 2.0, self.border_width / 2.0,
                           self.width() - self.border_width, self.height() - self.border_width)
        radius = (self.height() - self.border_width) / 2.0

        # Draw the background rounded rectangle
        painter.setBrush(QBrush(QColor(240, 240, 240)))  # Light gray background
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.drawRoundedRect(full_rect, radius, radius)

        # Create a clipping path for the filled progress that is inset by the border width
        clip_path = QPainterPath()
        inner_rect = full_rect.adjusted(self.border_width, self.border_width, -self.border_width, -self.border_width)
        clip_path.addRoundedRect(inner_rect, radius - self.border_width, radius - self.border_width)
        painter.setClipPath(clip_path)

        # Calculate progress rect and draw it within the clipping region
        progress_width = (self.width() - 2 * self.border_width) * self.value() / max(1,self.maximum())
        progress_rect = QRectF(self.border_width, self.border_width,
                               progress_width, self.height() - 2 * self.border_width)

        painter.setBrush(QBrush(self.bar_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(progress_rect)
        
        # Text drawing
        painter.setClipping(False)  # Disable clipping to draw text over entire bar
        text = self.format()  # Use the format string directly
        painter.setPen(QColor(0, 0, 0))  # Set text color
        font = QFont("Segoe UI", 9, QFont.Normal)
        painter.setFont(font)
        #painter.drawText(full_rect, Qt.AlignCenter, text)
        font_metrics = QFontMetrics(font)
        text_height = font_metrics.height()
        # Draw text in the calculated position
        painter.drawText(full_rect.adjusted(0, -font_metrics.descent()//2, 0, 0), Qt.AlignCenter, text)

    def setBarColor(self, color):
        self.bar_color = QColor(color)
        self.update()  # Request repaint


#########################
#      Menu Slider
#########################

class MenuSlider(QWidget):
    def __init__(self, vmin, vmax, sstep, title, parent=None):
        """
        Parameters
        ----------

        """
        super().__init__(parent)
        self.slider = Slider(Qt.Horizontal, self)
        self.slider.setMinimumWidth(120)
        self.sstep = sstep
        self.slider.setSingleStep(1)
        self.slider.setRange(vmin, vmax)
        self.slider.setValue(vmin*sstep)

        self.valueLabel = CaptionLabel()
        self.valueLabel.setNum(vmin)
        setFont(self.valueLabel, 14, QFont.Normal)

        self.titleLabel = CaptionLabel(title)
        setFont(self.titleLabel, 14, QFont.Normal)

        self.hBoxLayout = QHBoxLayout()
        self.hBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignRight)
        
        self.hBoxLayout2 = QHBoxLayout()
        self.hBoxLayout2.setContentsMargins(0,5,30,5)
        self.hBoxLayout2.addWidget(self.slider, 0, Qt.AlignLeft)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0,5,0,5)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        self.vBoxLayout.addLayout(self.hBoxLayout2)
        

        self.valueLabel.setObjectName('valueLabel')
        self.slider.valueChanged.connect(self.__onValueChanged)

        self.adjustSize()
    
    def __onValueChanged(self, value: int):
        """ slider value changed slot """
        self.setValue(value)
    
    def setValue(self, value):
        self.valueLabel.setNum(value*self.sstep)
        self.valueLabel.adjustSize()
        self.slider.setValue(value)


#########################
#      Level Badge
#########################

def _get_q_img(img_file) -> QPixmap:
    #image = QImage()
    image = QPixmap()
    image.load(img_file)
    return image

badge_width = 200
badge_height = 25

class LevelBadge(QWidget):
    def __init__(self, level: int, size:int=16, parent=None):
        super().__init__(parent)
        self.level = level
        self.size = size
        self.icons = {
            "icon_1": _get_q_img(os.path.join(basedir, "res/icons/star.svg")),
            "icon_2": _get_q_img(os.path.join(basedir, "res/icons/moon.svg")),
            "icon_3": _get_q_img(os.path.join(basedir, "res/icons/sun.svg")),
            "icon_4": _get_q_img(os.path.join(basedir, "res/icons/crown.svg")),
        }

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(1)  # Adjust spacing between icons
        self.setLayout(self.layout)

        self.update_badge()
        self.setFixedSize(badge_width, badge_height)
        self.installEventFilter(ToolTipFilter(self, showDelay=500))
        self.setToolTip(f'Lv. {self.level}')

    def calculate_icons(self, level):
        """Calculate the number of each type of icon needed for the given level."""
        icons_needed = []
        for value, name in zip([64, 16, 4, 1], ["icon_4", "icon_3", "icon_2", "icon_1"]):
            count = level // value
            icons_needed.append((name, count))
            level %= value
        return icons_needed

    def update_badge(self):
        """Update the badge icons based on the current level."""
        # Clear the layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.spacerItem():
                self.layout.removeItem(item)

        # Calculate icons and add them to the layout
        icons_needed = self.calculate_icons(self.level)
        for icon_name, count in icons_needed:
            for _ in range(count):
                label = QLabel()
                label.setFixedSize(self.size, self.size)
                label.setScaledContents(True)
                label.setAlignment(Qt.AlignCenter)
                label.setPixmap(self.icons[icon_name])  # Adjust size as needed
                self.layout.addWidget(label, Qt.AlignLeft | Qt.AlignVCenter)
        self.layout.addStretch(1)

    def set_level(self, level: int):
        """Update the badge to reflect a new level."""
        self.level = level
        self.update_badge()
        self.setToolTip(f'Lv. {self.level}')



