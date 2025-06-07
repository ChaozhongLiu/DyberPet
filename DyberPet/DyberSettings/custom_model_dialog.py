# coding:utf-8
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PySide6.QtGui import QIcon

from qfluentwidgets import (
    LineEdit, PushButton, ComboBox, MessageBox, 
    FluentIcon as FIF, setTheme, Theme
)

import DyberPet.settings as settings

basedir = os.path.dirname(os.path.dirname(__file__))


class CustomModelDialog(QDialog):
    """自定义模型配置对话框"""
    
    model_saved = Signal(str, dict)  # 模型名称, 模型配置
    
    def __init__(self, parent=None, model_name=None, model_config=None):
        super().__init__(parent)
        self.model_name = model_name
        self.model_config = model_config or {}
        self.is_edit_mode = model_name is not None
        
        self.setWindowTitle("编辑模型配置" if self.is_edit_mode else "添加自定义模型")
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon(os.path.join(basedir, 'res/icons/system/ai.svg')))
        
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 模型名称
        name_layout = QHBoxLayout()
        name_label = QLabel("模型名称:")
        name_label.setFixedWidth(80)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("输入模型名称，如：GPT-4")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # API类型
        type_layout = QHBoxLayout()
        type_label = QLabel("API类型:")
        type_label.setFixedWidth(80)
        self.type_combo = ComboBox()
        self.type_combo.addItems(["remote", "dashscope", "local"])
        self.type_combo.setCurrentText("remote")
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # API URL
        self.url_layout = QHBoxLayout()
        self.url_label = QLabel("API URL:")
        self.url_label.setFixedWidth(80)
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText("https://api.openai.com/v1/chat/completions")
        self.url_layout.addWidget(self.url_label)
        self.url_layout.addWidget(self.url_edit)
        layout.addLayout(self.url_layout)
        
        # API Key
        key_layout = QHBoxLayout()
        key_label = QLabel("API Key:")
        key_label.setFixedWidth(80)
        self.key_edit = LineEdit()
        self.key_edit.setEchoMode(LineEdit.Password)
        self.key_edit.setPlaceholderText("输入API密钥")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)
        
        # 模型标识符
        model_layout = QHBoxLayout()
        model_label = QLabel("模型ID:")
        model_label.setFixedWidth(80)
        self.model_edit = LineEdit()
        self.model_edit.setPlaceholderText("gpt-4, qwen-plus等")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_edit)
        layout.addLayout(model_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = PushButton("保存" if self.is_edit_mode else "添加")
        self.save_btn.clicked.connect(self._save_model)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)
        
        # 初始化UI状态
        self._on_type_changed("remote")
        
    def _on_type_changed(self, api_type):
        """API类型改变时的处理"""
        if api_type == "dashscope":
            # 通义千问不需要URL
            self.url_label.setVisible(False)
            self.url_edit.setVisible(False)
            self.key_edit.setPlaceholderText("输入通义千问API密钥")
            self.model_edit.setPlaceholderText("qwen-plus, qwen-max等")
        elif api_type == "local":
            # 本地模型需要URL，不需要Key
            self.url_label.setVisible(True)
            self.url_edit.setVisible(True)
            self.url_edit.setPlaceholderText("http://localhost:8000/v1/chat/completions")
            self.key_edit.setPlaceholderText("本地模型通常不需要密钥")
            self.model_edit.setPlaceholderText("local-model")
        else:
            # 远程API需要URL和Key
            self.url_label.setVisible(True)
            self.url_edit.setVisible(True)
            self.url_edit.setPlaceholderText("https://api.openai.com/v1/chat/completions")
            self.key_edit.setPlaceholderText("输入API密钥")
            self.model_edit.setPlaceholderText("gpt-4, claude-3等")
    
    def _load_data(self):
        """加载现有数据（编辑模式）"""
        if self.is_edit_mode and self.model_config:
            self.name_edit.setText(self.model_name)
            self.name_edit.setEnabled(False)  # 编辑模式下不允许修改名称
            
            api_type = self.model_config.get('api_type', 'remote')
            self.type_combo.setCurrentText(api_type)
            
            self.url_edit.setText(self.model_config.get('api_url', ''))
            self.key_edit.setText(self.model_config.get('api_key', ''))
            self.model_edit.setText(self.model_config.get('model_id', ''))
    
    def _save_model(self):
        """保存模型配置"""
        name = self.name_edit.text().strip()
        api_type = self.type_combo.currentText()
        api_url = self.url_edit.text().strip()
        api_key = self.key_edit.text().strip()
        model_id = self.model_edit.text().strip()
        
        # 验证输入
        if not name:
            MessageBox("错误", "请输入模型名称", self).exec()
            return
            
        if not model_id:
            MessageBox("错误", "请输入模型ID", self).exec()
            return
            
        if api_type in ["remote", "local"] and not api_url:
            MessageBox("错误", "请输入API URL", self).exec()
            return
            
        if api_type in ["remote", "dashscope"] and not api_key:
            MessageBox("错误", "请输入API密钥", self).exec()
            return
        
        # 检查名称是否已存在（新增模式）
        if not self.is_edit_mode:
            custom_models = settings.llm_config.get('custom_models', {})
            if name in custom_models:
                MessageBox("错误", "模型名称已存在，请使用其他名称", self).exec()
                return
        
        # 构建配置
        config = {
            'api_type': api_type,
            'model_id': model_id
        }
        
        if api_type in ["remote", "local"]:
            config['api_url'] = api_url
        if api_type in ["remote", "dashscope"]:
            config['api_key'] = api_key
            
        # 发送信号并关闭对话框
        self.model_saved.emit(name, config)
        self.accept()
