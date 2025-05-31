from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QApplication, 
    QWidget, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QEasingCurve
from PySide6.QtGui import QIcon,QPixmap,QImage
from qfluentwidgets import (
    PrimaryPushButton, LineEdit, SmoothScrollArea,
    isDarkTheme, setFont, BodyLabel, 
    CardWidget, FluentWindow, InfoBar,
    InfoBarPosition, TransparentPushButton,
    FluentIcon, TextEdit, MessageBox ,
    PushButton  # 添加 PushButton 组件
)

from DyberPet.DyberSettings.custom_utils import AvatarImage


import json
import os
import sys
# 如果需要在实际项目中使用，取消以下注释
import DyberPet.settings as settings
basedir = settings.BASEDIR


class ChatBubble(CardWidget):
    """聊天气泡组件
    
    使用 qfluentwidgets 的 CardWidget 作为基类，实现聊天气泡效果
    CardWidget 提供了圆角、阴影等现代化 UI 效果
    """
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(420)  # 设置最大宽度，避免气泡过宽
        self.setBorderRadius(8)   # 设置圆角半径
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 8, 12, 8)
        self.layout.setSpacing(0)
        
        # 创建文本标签
        label = BodyLabel(text)  # BodyLabel 是 qfluentwidgets 提供的文本标签组件
        label.setWordWrap(True)  # 启用自动换行
        setFont(label, 12)       # 设置字体大小
        
        # 根据主题设置颜色
        user_bg = "#0078D4"  # 用户消息背景色（微软蓝）
        pet_bg = "#F5F5F5" if not isDarkTheme() else "#232323"  # 宠物消息背景色
        user_color = "white"  # 用户消息文本色
        pet_color = "#222" if not isDarkTheme() else "#eee"  # 宠物消息文本色
        
        # 应用样式
        self.setStyleSheet(
            f"""
            background:{user_bg if is_user else pet_bg};
            color:{user_color if is_user else pet_color};
            border: none;
            box-shadow: none;
            """
        )
        label.setStyleSheet(f"color:{user_color if is_user else pet_color};")
        self.layout.addWidget(label)
        self.is_user = is_user
        
        self.is_user = is_user


class ChatInterface(SmoothScrollArea):
    """聊天界面
    
    继承自 qfluentwidgets 的 SmoothScrollArea，提供平滑滚动效果
    实现聊天消息的显示、发送和接收功能
    """
    # 定义信号，用于在发送消息时通知外部
    message_sent = Signal(str, name='message_sent')
    
    def __init__(self, sizeHintdb: tuple[int, int], parent=None, pet_name="宠物"):
        super().__init__(parent=parent)
        self.pet_name = pet_name
        self.thinking_bubble = None
        self.thinking_container = None
        
        # 初始化 UI
        self.setObjectName("chatInterface")
        self.scrollWidget = QWidget()  # 创建滚动区域的内容控件
        self.expandLayout = QVBoxLayout(self.scrollWidget)  # 主布局
        
        # 聊天区域
        self.chatContainer = QWidget()
        self.chatLayout = QVBoxLayout(self.chatContainer)
        self.chatLayout.setContentsMargins(24, 24, 24, 24)
        self.chatLayout.setSpacing(18)  # 消息之间的间距
        self.chatLayout.setAlignment(Qt.AlignTop)  # 顶部对齐
        self.chatLayout.addStretch(1)  # 添加弹性空间，使消息始终从顶部开始显示
        
        # 添加到主布局
        self.expandLayout.addWidget(self.chatContainer)
        
        # 初始化界面和样式
        self.__initWidget()
        self.__setQss()
        
        # 加载用户头像
        user_image = QImage()
        user_image.load(os.path.join(basedir, "data/head1.png"))
        if user_image.isNull():
            # 如果找不到用户头像，使用默认图标
            self.user_avatar = QPixmap(FluentIcon.GAME.path())
            print("user_avatar is None")
        else:
            self.user_avatar = QPixmap.fromImage(user_image)
        
        # 加载宠物头像
        pet_image = QImage()
        # 尝试从宠物资源目录加载头像
        try:
            
            info_file = os.path.join(basedir, 'res/role', settings.petname, 'info', 'info.json')
            pfp_file = None
            if os.path.exists(info_file):
                
                info = json.load(open(info_file, 'r', encoding='UTF-8'))
                pfp_file = info.get('pfp', None)

            if pfp_file is None:
                # 使用默认动作的第一张图片
                print("pfp_file is None")
                actJson = json.load(open(os.path.join(basedir, 'res/role', settings.petname, 'act_conf.json'),
                                    'r', encoding='UTF-8'))
                pfp_file = f"{actJson['default']['images']}_0.png"
                pfp_file = os.path.join(basedir, 'res/role', settings.petname, 'action', pfp_file)
            else:
                pfp_file = os.path.join(basedir, 'res/role', settings.petname, 'info', pfp_file)
            
            pet_image.load(pfp_file)
        except  Exception as e:
            # 如果加载失败，使用默认图标
            print("pet_image is None",e)
            pet_image.load(os.path.join(os.path.dirname(__file__), "../../res/icons/pet_avatar.png"))
        
        if pet_image.isNull():
            # 如果找不到宠物头像，使用默认图标
            self.pet_avatar = QPixmap(FluentIcon.EMOJI_TAB_SYMBOLS.path())
        else:
            self.pet_avatar = QPixmap.fromImage(pet_image)
    
    def __initWidget(self):
        """初始化界面设置
        
        设置滚动条策略、视口边距和可调整大小属性
        """
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 隐藏水平滚动条
        self.setViewportMargins(0, 20, 0, 20)  # 设置视口边距
        self.setWidget(self.scrollWidget)  # 设置滚动区域的内容控件
        self.setWidgetResizable(True)  # 允许内容控件调整大小
    
    def __setQss(self):
        """设置样式表
        
        定义界面的 QSS 样式，包括背景、滚动条等
        """
        # 设置滚动内容控件的样式
        self.scrollWidget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        
        # 设置滚动区域的样式
        self.setStyleSheet("""
            ChatInterface {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #E0E0E0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #B0B0B0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
    
    def add_message(self, text, is_user=True):
        """添加消息到聊天区域
        
        Args:
            text: 消息文本
            is_user: 是否为用户消息，True 为用户，False 为宠物
        """
        # 创建气泡
        bubble = ChatBubble(text, is_user)
        
        # 创建容器，用于控制气泡和头像的布局
        bubbleContainer = QWidget()
        bubbleLayout = QHBoxLayout(bubbleContainer)
        bubbleLayout.setContentsMargins(0, 0, 0, 0)
        bubbleLayout.setSpacing(8)  # 头像和气泡之间的间距
        
        # 获取头像
        avatar_pixmap = self.user_avatar if is_user else self.pet_avatar
        
        # 将QPixmap转换为QImage以便使用AvatarImage
        if isinstance(avatar_pixmap, QPixmap):
            avatar_image = avatar_pixmap.toImage()
        else:
            avatar_image = avatar_pixmap  # 如果已经是QImage
            
        # 创建圆形头像
        avatarLabel = AvatarImage(avatar_image, edge_size=36, frameColor="#ffffff")
        
        # 根据消息发送者设置对齐方式
        if is_user:
            bubbleLayout.addStretch()  # 添加弹性空间，使头像和气泡右对齐
            bubbleLayout.addWidget(bubble)
            bubbleLayout.addWidget(avatarLabel)
        else:
            bubbleLayout.addWidget(avatarLabel)
            bubbleLayout.addWidget(bubble)
            bubbleLayout.addStretch()  # 添加弹性空间，使头像和气泡左对齐
        
        # 插入到聊天区域
        self.chatLayout.insertWidget(self.chatLayout.count()-1, bubbleContainer)
        self.scroll_to_bottom()  # 滚动到底部
        
    
    def scroll_to_bottom(self):
        """滚动到底部，显示最新消息"""
        # self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
            # 使用 QTimer 延迟执行滚动操作，确保布局已更新
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, lambda: self.verticalScrollBar().setValue(self.verticalScrollBar().maximum()))
    
    def clear(self):
        """清空聊天记录"""
        # 使用 MessageBox 确认是否清空
        w = MessageBox(
            self.tr('确认清空'), 
            self.tr('确定要清空所有聊天记录吗？'), 
            self
        )
        if w.exec():
            while self.chatLayout.count() > 1:  # 保留最后的 stretch
                item = self.chatLayout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
    
    def send_message(self):
        """发送消息
        
        获取输入框文本，添加到聊天区域，并发出信号通知外部
        """
        message = self.chatInput.text().strip()
        if not message:
            return
        
        self.chatInput.clear()
        self.add_message(message, is_user=True)
        # 发出信号
        self.message_sent.emit(message)
        
        # 添加"正在思考"气泡
        thinkingContainer = QWidget()
        thinkingLayout = QHBoxLayout(thinkingContainer)
        thinkingLayout.setContentsMargins(0, 0, 0, 0)
        self.thinking_bubble = ChatBubble(self.tr("正在思考..."), is_user=False)
        thinkingLayout.addWidget(self.thinking_bubble)
        thinkingLayout.addStretch()
        
        self.chatLayout.insertWidget(self.chatLayout.count()-1, thinkingContainer)
        self.thinking_container = thinkingContainer
        self.scroll_to_bottom()
    
    def add_response(self, response):
        """
        添加宠物回复
        移除"正在思考"气泡，添加宠物回复消息
        """
        if self.thinking_bubble:
            self.thinking_container.deleteLater()
            self.thinking_bubble = None
            self.thinking_container = None

        self.add_message(response, is_user=False)

    def send_thinking_bubble(self):
        """添加"正在思考"气泡"""
        if self.thinking_bubble:
            self.thinking_container.deleteLater()
            self.thinking_bubble = None
            self.thinking_container = None
        thinkingContainer = QWidget()
        thinkingLayout = QHBoxLayout(thinkingContainer)
        thinkingLayout.setContentsMargins(0, 0, 0, 0)
        self.thinking_bubble = ChatBubble("正在思考...", is_user=False)
        thinkingLayout.addWidget(self.thinking_bubble)
        thinkingLayout.addStretch()
        self.chatLayout.insertWidget(self.chatLayout.count()-1, thinkingContainer)
        self.thinking_container = thinkingContainer
        self.scroll_to_bottom()

class ChatDialog(FluentWindow):
    """聊天对话框主窗口
    
    继承自 qfluentwidgets 的 FluentWindow，提供现代化的窗口框架
    FluentWindow 包含标题栏、导航栏等，符合 Fluent Design 设计语言
    """
    def __init__(self,pet_name="宠物"):
        super().__init__()
        self.setWindowTitle(f"与{pet_name}对话")
        self.setMinimumSize(850, 500)
        self.last_pos = None
        
        # 创建主容器
        self.mainWidget = QWidget()
        self.mainWidget.setObjectName("chatMainWidget")  # 添加这一行，设置对象名称
        self.mainLayout = QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        
        # 创建聊天界面
        self.chatInterface = ChatInterface(sizeHintdb=(750, 450), parent=self, pet_name=pet_name)
        
        # 输入区域
        self.inputArea = QFrame()
        self.inputArea.setFrameShape(QFrame.NoFrame)
        self.inputArea.setStyleSheet("background:transparent;")
        self.inputLayout = QHBoxLayout(self.inputArea)
        self.inputLayout.setContentsMargins(24, 16, 24, 16)
        self.inputLayout.setSpacing(12)
        
        # 创建输入框
        self.chatInput = LineEdit()
        self.chatInput.setPlaceholderText("输入消息...")
        self.chatInput.setClearButtonEnabled(True)  # 启用清除按钮
        self.chatInput.setMinimumHeight(36)
        
        # 添加清空聊天记录按钮
        self.clearBtn = TransparentPushButton(FluentIcon.DELETE, "")
        self.clearBtn.setToolTip("清空聊天记录")
        self.clearBtn.clicked.connect(self.chatInterface.clear)
        
        self.sendBtn = PushButton(self.tr("发送"))
        self.sendBtn.setFixedWidth(80)
        self.sendBtn.setMinimumHeight(36)
        self.sendBtn.clicked.connect(self.send_message)
        
        # 添加控件到输入区域布局
        self.inputLayout.addWidget(self.clearBtn)
        self.inputLayout.addWidget(self.chatInput)
        self.inputLayout.addWidget(self.sendBtn)
        
        # 添加到主布局
        self.mainLayout.addWidget(self.chatInterface, 1)  # 聊天区域占据剩余空间
        self.mainLayout.addWidget(self.inputArea, 0)      # 输入区域不拉伸
        
        # 初始化窗口
        self.initWindow()
        
        # 连接回车键发送消息
        self.chatInput.returnPressed.connect(self.send_message)
        
        self.message_sent = self.chatInterface.message_sent
    
    def initWindow(self):
        """初始化窗口
        
        设置窗口图标、导航栏和子界面
        """
        screen_width = QApplication.primaryScreen().availableGeometry().width()
        self.navigationInterface.setExpandWidth(int(screen_width * 0.10))
        self.navigationInterface.setMinimumWidth(0)
        # 添加主容器为子界面
        self.addSubInterface(self.mainWidget, QIcon(), self.tr("与宠物对话"))
        
        # 居中显示窗口
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
    
    def add_response(self, response):
        """添加宠物回复
        
        转发到聊天界面
        
        Args:
            response: 回复文本
        """
        self.chatInterface.add_response(response)
    
    def clear_chat_history(self):
        """清空聊天记录"""
        self.chatInterface.clear()
    
    def center_dialog(self):
        """居中显示窗口"""
        screen = QApplication.primaryScreen().geometry()
        dialog_geometry = self.geometry()
        center_point = screen.center()
        dialog_geometry.moveCenter(center_point)
        self.setGeometry(dialog_geometry)
    
    # 添加发送消息方法
    def send_message(self):
        """发送消息"""
        message = self.chatInput.text().strip()
        if not message:
            return
        
        # 清空输入框
        self.chatInput.clear()
        self.chatInterface.add_message(message, is_user=True)
        # 发出信号
        self.message_sent.emit(message)
        # 添加"正在思考"气泡
        self.chatInterface.send_thinking_bubble()

    def open_dialog(self):
        """打开对话框
        
        如果窗口未显示，则显示窗口
        如果窗口已显示，则提升窗口并激活
        """
        if not self.isVisible():
            if self.last_pos:
                self.move(self.last_pos)
            else:
                self.center_dialog()
            self.show()
        self.raise_()  # 提升窗口到顶层
        self.activateWindow()  # 激活窗口
    
    def closeEvent(self, event):
        """关闭事件处理
        
        保存窗口位置，以便下次打开时恢复
        """
        self.last_pos = self.pos()
        event.accept()
        self.hide()
        event.ignore()
