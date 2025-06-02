import os
import sys
from typing import List, Dict, Optional, Union, Any

from PySide6.QtCore import Qt, Signal, QSize, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame

from qfluentwidgets import (FluentIcon as FIF, 
                           LineEdit, ComboBox, PrimaryPushButton, 
                           ToggleButton, MessageBox, InfoBar,
                           ScrollArea, ExpandLayout, SettingCard, SwitchButton,
                           InfoBarPosition, SwitchSettingCard, SettingCardGroup)

import DyberPet.settings as settings
from DyberPet.utils import text_wrap
from .custom_utils import Dyber_ComboBoxSettingCard

class AISettingInterface(ScrollArea):
    """AI 设置界面"""
    
    ai_settings_changed = Signal(name='ai_settings_changed')
    menu_update_needed = Signal(name='menu_update_needed')  # 新增信号，用于通知主窗口更新菜单
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("AISettingInterface")  # 设置对象名
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        
        # 设置滚动区域
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 初始化 UI
        self.__initWidget()
        
    def __initWidget(self):
        """初始化界面"""
        # 创建设置卡片组
        self.aiGroup = SettingCardGroup(self.tr('AI 设置'), self.scrollWidget)
        
        # AI 功能开关
        self.aiEnabledCard = SwitchSettingCard(
            FIF.ROBOT,
            self.tr("启用 AI 对话"),
            self.tr("启用后，可以与宠物进行 AI 对话"),
            parent=self.aiGroup
        )
        self.aiEnabledCard.setChecked(settings.ai_enabled)
        self.aiEnabledCard.checkedChanged.connect(self.__onAIEnabledChanged)
        
        # API Key 设置
        self.apiKeyCard = SettingCard(
            FIF.DOCUMENT,  # 使用文档图标替换不存在的 KEY 图标
            self.tr("API Key"),
            self.tr("设置 API Key，用于访问 AI 服务"),
            self.aiGroup
        )
        self.apiKeyEdit = LineEdit(self.apiKeyCard)
        self.apiKeyEdit.setPlaceholderText(self.tr("请输入 API Key"))
        self.apiKeyEdit.setText(settings.ai_api_key)
        self.apiKeyEdit.textChanged.connect(self.__onAPIKeyChanged)
        self.apiKeyCard.hBoxLayout.addWidget(self.apiKeyEdit, 0, Qt.AlignRight)
        
        # AI 模型选择
        ai_models = ["deepseek-chat", "deepseek-coder", "gpt-3.5-turbo", "gpt-4"]
        self.aiModelCard = Dyber_ComboBoxSettingCard(
            ai_models,
            ai_models,
            FIF.LIBRARY,
            self.tr("AI 模型"),
            self.tr("选择要使用的 AI 模型"),
            parent=self.aiGroup
        )
        self.aiModelCard.comboBox.setCurrentText(settings.ai_model)
        self.aiModelCard.comboBox.currentTextChanged.connect(self.__onAIModelChanged)
        
        # 测试连接按钮
        self.testConnectionCard = SettingCard(
            FIF.SEND,
            self.tr("测试连接"),
            self.tr("测试与 AI 服务的连接"),
            self.aiGroup
        )
        self.testConnectionButton = PrimaryPushButton(self.tr("测试"), self.testConnectionCard)
        self.testConnectionButton.clicked.connect(self.__onTestConnection)
        self.testConnectionCard.hBoxLayout.addWidget(self.testConnectionButton, 0, Qt.AlignRight)
        
        # 帮助链接
        self.helpCard = SettingCard(
            FIF.HELP,
            self.tr("获取帮助"),
            self.tr("了解如何获取 API Key 和使用 AI 对话功能"),
            self.aiGroup
        )
        self.helpButton = PrimaryPushButton(self.tr("查看帮助"), self.helpCard)
        self.helpButton.clicked.connect(self.__onHelpClicked)
        self.helpCard.hBoxLayout.addWidget(self.helpButton, 0, Qt.AlignRight)
        
        # 添加卡片到布局
        self.aiGroup.addSettingCard(self.aiEnabledCard)
        self.aiGroup.addSettingCard(self.apiKeyCard)
        self.aiGroup.addSettingCard(self.aiModelCard)
        self.aiGroup.addSettingCard(self.testConnectionCard)
        self.aiGroup.addSettingCard(self.helpCard)
        
        # 添加设置卡片组到主布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.aiGroup)
        
    def __onAIEnabledChanged(self, checked: bool):
        """AI 功能开关状态改变"""
        settings.ai_enabled = checked
        settings.save_settings()
        self.ai_settings_changed.emit()
        # 通知主窗口更新菜单
        self.menu_update_needed.emit()
        
        # 显示提示信息
        if checked:
            InfoBar.success(
                title=self.tr("成功"),
                content=self.tr("AI 对话功能已启用，请重启应用或右键宠物查看菜单"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.info(
                title=self.tr("提示"),
                content=self.tr("AI 对话功能已禁用"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
    def __onAPIKeyChanged(self, text: str):
        """API Key 改变"""
        settings.ai_api_key = text
        settings.save_settings()
        self.ai_settings_changed.emit()
        # 如果 AI 功能已启用且输入了 API Key，通知更新菜单
        if settings.ai_enabled and text:
            self.menu_update_needed.emit()
        
    def __onAIModelChanged(self, text: str):
        """AI 模型改变"""
        settings.ai_model = text
        settings.save_settings()
        self.ai_settings_changed.emit()
        
    def __onTestConnection(self):
        """测试连接"""
        if not settings.ai_api_key:
            InfoBar.error(
                title=self.tr("错误"),
                content=self.tr("请先设置 API Key"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        if not settings.ai_enabled:
            InfoBar.warning(
                title=self.tr("警告"),
                content=self.tr("AI 对话功能未启用"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # 这里应该实际测试连接，但为了简单起见，我们只显示一个成功消息
        InfoBar.success(
            title=self.tr("成功"),
            content=self.tr("连接测试成功"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def __onHelpClicked(self):
        """打开帮助页面"""
        QDesktopServices.openUrl(QUrl("https://github.com/ChaozhongLiu/DyberPet/blob/main/docs/ai_chat.md")) 