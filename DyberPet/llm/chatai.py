from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QApplication, 
    QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon,QPixmap,QImage
from qfluentwidgets import (
    LineEdit, SmoothScrollArea,
    isDarkTheme, setFont, BodyLabel, 
    CardWidget, FluentWindow,
    TransparentPushButton,
    FluentIcon, MessageBox ,
    PushButton
)

from DyberPet.DyberSettings.custom_utils import AvatarImage


import json
import os
import sys
import DyberPet.settings as settings
basedir = settings.BASEDIR


class ChatBubble(CardWidget):
    """Message Bubble"""

    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(420)
        self.setBorderRadius(8)
        
        # Global Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 8, 12, 8)
        self.layout.setSpacing(0)
        
        # Create a text label for the message
        label = BodyLabel(text)
        label.setWordWrap(True)
        setFont(label, 12)
        
        # Background and text color
        user_bg = "#0078D4"  # user message background color
        pet_bg = "#F5F5F5" if not isDarkTheme() else "#232323"  # pet message background color
        user_color = "white"  # user message text color
        pet_color = "#222" if not isDarkTheme() else "#eee"  # pet message text color
        
        # Stylesheet
        self.setStyleSheet(
            f"""
            background:{user_bg if is_user else pet_bg};
            color:{user_color if is_user else pet_color};
            border: none;
            """
        ) # box-shadow: none;
        label.setStyleSheet(f"color:{user_color if is_user else pet_color};")
        self.layout.addWidget(label)
        self.is_user = is_user


class ChatInterface(SmoothScrollArea):
    """ Chat Interface """

    message_sent = Signal(str, name='message_sent')
    
    def __init__(self, sizeHintdb: tuple[int, int], parent=None, pet_name=None):
        super().__init__(parent=parent)
        self.pet_name = pet_name
        self.thinking_bubble = None
        self.thinking_container = None
        
        # Initialize UI
        self.setObjectName("chatInterface")
        self.scrollWidget = QWidget()  # Create content widget for scroll area
        self.expandLayout = QVBoxLayout(self.scrollWidget)  # Main layout
        
        # Chat area
        self.chatContainer = QWidget()
        self.chatLayout = QVBoxLayout(self.chatContainer)
        self.chatLayout.setContentsMargins(24, 24, 24, 24)
        self.chatLayout.setSpacing(18)  # Spacing between messages
        self.chatLayout.setAlignment(Qt.AlignTop)  # Align to top
        self.chatLayout.addStretch(1)  # Add stretch to ensure messages start from the top
        
        # Add to main layout
        self.expandLayout.addWidget(self.chatContainer)
        
        # Initialize interface and style
        self.__initWidget()
        self.__setQss()
        
        # Load user avatar
        user_image = QImage()
        user_image.load(os.path.join(basedir, "data/head1.png"))
        if user_image.isNull():
            # If user avatar is not found, use default icon
            self.user_avatar = QPixmap(FluentIcon.GAME.path())
            print("user_avatar is None")
        else:
            self.user_avatar = QPixmap.fromImage(user_image)
        
        # Load pet avatar
        pet_image = QImage()
        # Try to load avatar from pet resource directory
        try:
            
            info_file = os.path.join(basedir, 'res/role', settings.petname, 'info', 'info.json')
            pfp_file = None
            if os.path.exists(info_file):
                
                info = json.load(open(info_file, 'r', encoding='UTF-8'))
                pfp_file = info.get('pfp', None)

            if pfp_file is None:
                # Use the first image of the default action
                print("pfp_file is None")
                actJson = json.load(open(os.path.join(basedir, 'res/role', settings.petname, 'act_conf.json'),
                                    'r', encoding='UTF-8'))
                pfp_file = f"{actJson['default']['images']}_0.png"
                pfp_file = os.path.join(basedir, 'res/role', settings.petname, 'action', pfp_file)
            else:
                pfp_file = os.path.join(basedir, 'res/role', settings.petname, 'info', pfp_file)
            
            pet_image.load(pfp_file)
        except  Exception as e:
            # If loading fails, use default icon
            print("pet_image is None",e)
            pet_image.load(os.path.join(os.path.dirname(__file__), "../../res/icons/pet_avatar.png"))
        
        if pet_image.isNull():
            # If pet avatar is not found, use default icon
            self.pet_avatar = QPixmap(FluentIcon.EMOJI_TAB_SYMBOLS.path())
        else:
            self.pet_avatar = QPixmap.fromImage(pet_image)
    
    def __initWidget(self):
        """Initialize interface settings
        
        Set scrollbar policy, viewport margins, and resizable property
        """
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide horizontal scrollbar
        self.setViewportMargins(0, 20, 0, 20)  # Set viewport margins
        self.setWidget(self.scrollWidget)  # Set content widget for scroll area
        self.setWidgetResizable(True)  # Allow content widget to resize
    
    def __setQss(self):
        """Set stylesheet
        
        Define QSS styles for the interface, including background, scrollbars, etc.
        """
        # Set style for scroll content widget
        self.scrollWidget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        
        # Set style for scroll area
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
        """Add message to chat area
        
        Args:
            text: Message text
            is_user: Whether it's a user message, True for user, False for pet
        """
        # Create bubble
        bubble = ChatBubble(text, is_user)
        
        # Create container to control layout of bubble and avatar
        bubbleContainer = QWidget()
        bubbleLayout = QHBoxLayout(bubbleContainer)
        bubbleLayout.setContentsMargins(0, 0, 0, 0)
        bubbleLayout.setSpacing(8)  # Spacing between avatar and bubble
        
        # Get avatar
        avatar_pixmap = self.user_avatar if is_user else self.pet_avatar
        
        # Convert QPixmap to QImage to use AvatarImage
        if isinstance(avatar_pixmap, QPixmap):
            avatar_image = avatar_pixmap.toImage()
        else:
            avatar_image = avatar_pixmap  # If already QImage
            
        # Create circular avatar
        avatarLabel = AvatarImage(avatar_image, edge_size=36, frameColor="#ffffff")
        
        # Set alignment based on message sender
        if is_user:
            bubbleLayout.addStretch()  # Add stretch to align avatar and bubble to the right
            bubbleLayout.addWidget(bubble)
            bubbleLayout.addWidget(avatarLabel)
        else:
            bubbleLayout.addWidget(avatarLabel)
            bubbleLayout.addWidget(bubble)
            bubbleLayout.addStretch()  # Add stretch to align avatar and bubble to the left
        
        # Insert into chat area
        self.chatLayout.insertWidget(self.chatLayout.count()-1, bubbleContainer)
        self.scroll_to_bottom()  # Scroll to bottom
        
    
    def scroll_to_bottom(self):
        """Scroll to bottom to show the latest message"""
        # Use QTimer to delay scroll operation to ensure layout is updated
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, lambda: self.verticalScrollBar().setValue(self.verticalScrollBar().maximum()))
    
    def clear(self):
        """Clear chat history"""
        # Use MessageBox to confirm clearing
        w = MessageBox(
            self.tr('确认清空'), # This string is for UI text, not a comment. Keeping as is.
            self.tr('确定要清空所有聊天记录吗？'), # This string is for UI text, not a comment. Keeping as is.
            self
        )
        if w.exec():
            while self.chatLayout.count() > 1:  # Keep the last stretch
                item = self.chatLayout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
    
    def send_message(self):
        """Send message
        
        Get input text, add to chat area, and emit signal to notify external components
        """
        message = self.chatInput.text().strip()
        if not message:
            return
        
        self.chatInput.clear()
        self.add_message(message, is_user=True)
        # Emit signal
        self.message_sent.emit(message)
        
        # Add "thinking" bubble
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
        Add pet response
        Remove "thinking" bubble, add pet response message
        """
        if self.thinking_bubble:
            self.thinking_container.deleteLater()
            self.thinking_bubble = None
            self.thinking_container = None

        self.add_message(response, is_user=False)

    def send_thinking_bubble(self):
        """Add "thinking" bubble"""
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
    """Chat dialog main window
    
    Inherits from qfluentwidgets' FluentWindow, providing a modern window frame
    FluentWindow includes title bar, navigation bar, etc., conforming to Fluent Design language
    """
    def __init__(self):
        super().__init__()
        pet_name = settings.petname
        self.setWindowTitle(f"与宠物对话") 
        self.setMinimumSize(850, 500)
        self.last_pos = None
        
        # Create main container
        self.mainWidget = QWidget()
        self.mainWidget.setObjectName("chatMainWidget")
        self.mainLayout = QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        
        # Create chat interface
        self.chatInterface = ChatInterface(sizeHintdb=(750, 450), parent=self, pet_name=pet_name)
        
        # Input area
        self.inputArea = QFrame()
        self.inputArea.setFrameShape(QFrame.NoFrame)
        self.inputArea.setStyleSheet("background:transparent;")
        self.inputLayout = QHBoxLayout(self.inputArea)
        self.inputLayout.setContentsMargins(24, 16, 24, 16)
        self.inputLayout.setSpacing(12)
        
        # Create input field
        self.chatInput = LineEdit()
        self.chatInput.setPlaceholderText("输入消息...")
        self.chatInput.setClearButtonEnabled(True)
        self.chatInput.setMinimumHeight(36)
        
        # Add clear chat history button
        self.clearBtn = TransparentPushButton(FluentIcon.DELETE, "")
        self.clearBtn.setToolTip("清空聊天记录") 
        self.clearBtn.clicked.connect(self.chatInterface.clear)
        
        self.sendBtn = PushButton(self.tr("发送")) 
        self.sendBtn.setFixedWidth(80)
        self.sendBtn.setMinimumHeight(36)
        self.sendBtn.clicked.connect(self.send_message)
        
        # Add widgets to input area layout
        self.inputLayout.addWidget(self.clearBtn)
        self.inputLayout.addWidget(self.chatInput)
        self.inputLayout.addWidget(self.sendBtn)
        
        # Add to main layout
        self.mainLayout.addWidget(self.chatInterface, 1)  # Chat area takes remaining space
        self.mainLayout.addWidget(self.inputArea, 0)      # Input area does not stretch
        
        # Initialize window
        self.initWindow()
        
        # Connect Enter key to send message
        self.chatInput.returnPressed.connect(self.send_message)
        
        self.message_sent = self.chatInterface.message_sent
    
    def initWindow(self):
        """Initialize window
        
        Set window icon, navigation bar, and sub-interfaces
        """
        screen_width = QApplication.primaryScreen().availableGeometry().width()
        self.navigationInterface.setExpandWidth(int(screen_width * 0.10))
        self.navigationInterface.setMinimumWidth(0)
        # Add main container as sub-interface
        self.addSubInterface(self.mainWidget, QIcon(), self.tr("与宠物对话")) 
        
        # Center window
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
    
    def add_response(self, response):
        """Add pet response
        
        Forward to chat interface
        
        Args:
            response: Response text
        """
        self.chatInterface.add_response(response)
    
    def clear_chat_history(self):
        """Clear chat history"""
        self.chatInterface.clear()
    
    def center_dialog(self):
        """Center the dialog window"""
        screen = QApplication.primaryScreen().geometry()
        dialog_geometry = self.geometry()
        center_point = screen.center()
        dialog_geometry.moveCenter(center_point)
        self.setGeometry(dialog_geometry)
    
    # Add sending message method
    def send_message(self):
        """Send message"""
        message = self.chatInput.text().strip()
        if not message:
            return
        
        # Clear input field
        self.chatInput.clear()
        self.chatInterface.add_message(message, is_user=True)
        # Emit signal
        self.message_sent.emit(message)
        # Add "thinking" bubble
        self.chatInterface.send_thinking_bubble()

    def handle_llm_error(self, error_message, error_details):
        """Handle LLM error
        Display error message in chat interface
        Args:
            error_message: Error message text
        """
        if settings.llm_config['debug_mode'] and error_details:
            self.chatInterface.add_response(f"{error_message}\n{error_details}")
        else:
            self.chatInterface.add_response(error_message)
    
    def reinitialize(self):
        """Reinitialize chat interface"""
        print("chatAI reinitialize unfinished!")
        return

    def open_dialog(self):
        """Open dialog
        
        If the window is not visible, show it
        If the window is visible, raise and activate it
        """
        if not self.isVisible():
            if self.last_pos:
                self.move(self.last_pos)
            else:
                self.center_dialog()
            self.show()
        self.raise_()  # Raise window to top
        self.activateWindow()  # Activate window
    
    def closeEvent(self, event):
        """Close event handler
        
        Save window position to restore next time it opens
        """
        self.last_pos = self.pos()
        event.accept()
        self.hide()
        event.ignore()
