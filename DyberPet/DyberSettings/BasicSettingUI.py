# coding:utf-8
import os
import json
import urllib.request
from sys import platform

from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, HyperlinkCard,InfoBar,
                            ComboBoxSettingCard, ScrollArea, ExpandLayout, InfoBarPosition,
                            setThemeColor, LineEdit, PushButton)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QHBoxLayout
#from qframelesswindow import FramelessWindow

from .custom_utils import Dyber_RangeSettingCard, Dyber_ComboBoxSettingCard, CustomColorSettingCard
import DyberPet.settings as settings

basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/DyberSettings/')
'''
if platform == 'win32':
    basedir = ''
    module_path = 'DyberPet/DyberSettings/'
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-2])

    module_path = os.path.join(basedir, 'DyberPet/DyberSettings/')
'''


class SettingInterface(ScrollArea):
    """ Setting interface """

    ontop_changed = Signal(name='ontop_changed')
    scale_changed = Signal(name='scale_changed')
    lang_changed = Signal(name='lang_changed')
    llm_change_model = Signal(name='llm_change_model')
    llm_change_debug = Signal(name='llm_change_debug')
    llm_change_api_key = Signal(name='llm_change_api_key')

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SettingInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)
        
        # Mode =========================================================================================
        self.ModeGroup = SettingCardGroup(self.tr('Mode'), self.scrollWidget)
        # Always on top
        self.AlwaysOnTopCard = SwitchSettingCard(
            FIF.PIN,
            self.tr("Always-On-Top"),
            self.tr("Pet will be displayed on top of the other Apps"),
            parent=self.ModeGroup #DisplayModeGroup
        )
        if settings.on_top_hint:
            self.AlwaysOnTopCard.setChecked(True)
        else:
            self.AlwaysOnTopCard.setChecked(False)
        self.AlwaysOnTopCard.switchButton.checkedChanged.connect(self._AlwaysOnTopChanged)

        # Allow drop
        self.AllowDropCard = SwitchSettingCard(
            QIcon(os.path.join(basedir, 'res/icons/system/falldown.svg')),
            self.tr("Allow Drop"),
            self.tr("When mouse released, pet falls to the ground (on) / stays at the site (off)"),
            parent=self.ModeGroup #DisplayModeGroup
        )
        if settings.set_fall:
            self.AllowDropCard.setChecked(True)
        else:
            self.AllowDropCard.setChecked(False)
        self.AllowDropCard.switchButton.checkedChanged.connect(self._AllowDropChanged)

        # Auto-Lock
        self.AutoLockCard = SwitchSettingCard(
            QIcon(os.path.join(basedir, 'res/icons/system/lock.svg')),
            self.tr("Auto-Lock"),
            self.tr("When screen is locked, HP and FV will be locked too (currently only works in Windows)"),
            parent=self.ModeGroup #DisplayModeGroup
        )
        if settings.auto_lock:
            self.AutoLockCard.setChecked(True)
        else:
            self.AutoLockCard.setChecked(False)
        self.AutoLockCard.switchButton.checkedChanged.connect(self._AutoLockChanged)
        if platform != 'win32':
            self.AutoLockCard.switchButton.indicator.setEnabled(False)


        # Interaction parameters =======================================================================
        self.InteractionGroup = SettingCardGroup(self.tr('Interaction'), self.scrollWidget)
        self.GravityCard = Dyber_RangeSettingCard(
            1, 200, 0.01,
            QIcon(os.path.join(basedir, 'res/icons/system/gravity.svg')),
            self.tr("Gravity"),
            self.tr("Pet falling down acceleration"),
            parent=self.InteractionGroup
        )

        self.GravityCard.setValue(int(settings.gravity*100))
        self.GravityCard.slider.valueChanged.connect(self._GravityChanged)

        self.DragCard = Dyber_RangeSettingCard(
            0, 200, 0.01,
            QIcon(os.path.join(basedir, 'res/icons/system/mousedrag.svg')),
            self.tr("Drag Speed"),
            self.tr("Mouse speed factor"),
            parent=self.InteractionGroup
        )
        self.DragCard.setValue(int(settings.fixdragspeedx*100))
        self.DragCard.slider.valueChanged.connect(self._DragChanged)


        # Notification parameters ======================================================================
        self.VolumnGroup = SettingCardGroup(self.tr('Notification'), self.scrollWidget)
        self.VolumnCard = Dyber_RangeSettingCard(
            0, 10, 0.1,
            QIcon(os.path.join(basedir, 'res/icons/system/speaker.svg')),
            self.tr("Volumn"),
            self.tr("Volumn of notification and pet"),
            parent=self.VolumnGroup
        )
        self.VolumnCard.setValue(int(settings.volume*10))
        self.VolumnCard.slider.valueChanged.connect(self._VolumnChanged)

        self.AllowToasterCard = SwitchSettingCard(
            QIcon(os.path.join(basedir, 'res/icons/system/popup.svg')),
            self.tr("Pop-up Toaster"),
            self.tr("When turned on, notification will pop-up at the bottom right corner"),
            parent=self.VolumnGroup
        )
        if settings.toaster_on:
            self.AllowToasterCard.setChecked(True)
        else:
            self.AllowToasterCard.setChecked(False)
        self.AllowToasterCard.switchButton.checkedChanged.connect(self._AllowToasterChanged)

        self.AllowBubbleCard = SwitchSettingCard(
            QIcon(os.path.join(basedir, 'res/icons/system/bubble.svg')),
            self.tr("Dialogue Bubble"),
            self.tr("When turned on, various kinds of bubbles will pop-up above the pet"),
            parent=self.VolumnGroup
        )
        if settings.bubble_on:
            self.AllowBubbleCard.setChecked(True)
        else:
            self.AllowBubbleCard.setChecked(False)
        self.AllowBubbleCard.switchButton.checkedChanged.connect(self._AllowBubbleChanged)

        # Personalization ==============================================================================
        self.PersonalGroup = SettingCardGroup(self.tr('Personalization'), self.scrollWidget)
        self.ScaleCard = Dyber_RangeSettingCard(
            1, 50, 0.1,
            QIcon(os.path.join(basedir, 'res/icons/system/resize.svg')),
            self.tr("Pet Scale"),
            self.tr("Adjust size of the pet"),
            parent=self.PersonalGroup
        )
        self.ScaleCard.setValue(int(settings.tunable_scale*10))
        self.ScaleCard.slider.valueChanged.connect(self._ScaleChanged)

        pet_list = settings.pets
        self.DefaultPetCard = Dyber_ComboBoxSettingCard(
            pet_list,
            pet_list,
            QIcon(os.path.join(basedir, 'res/icons/system/homestar.svg')),
            self.tr('Default Pet'),
            self.tr('Pet to show everytime App starts'),
            parent=self.PersonalGroup
        )
        self.DefaultPetCard.comboBox.currentTextChanged.connect(self._DefaultPetChanged)

        lang_choices = list(settings.lang_dict.keys())
        lang_now = lang_choices[list(settings.lang_dict.values()).index(settings.language_code)]
        lang_choices.remove(lang_now)
        lang_choices = [lang_now] + lang_choices
        self.languageCard = Dyber_ComboBoxSettingCard(
            lang_choices,
            lang_choices,
            FIF.LANGUAGE,
            self.tr('Language/语言'),
            self.tr('Set your preferred language for UI'),
            parent=self.PersonalGroup
        )
        self.languageCard.comboBox.currentTextChanged.connect(self._LanguageChanged)

        self.themeColorCard = CustomColorSettingCard(
            FIF.PALETTE,
            self.tr('Theme color'),
            self.tr('Change the theme color of you application'),
            self.PersonalGroup
        )
        self.themeColorCard.colorChanged.connect(self.colorChanged)

        # LLM Settings =================================================================================
        self.LLMGroup = SettingCardGroup(self.tr('LLM Settings'), self.scrollWidget)
        self.LLMEnableCard = SwitchSettingCard(
            QIcon(os.path.join(basedir, 'res/icons/system/chat.svg')),
            self.tr("Enable LLM"),
            self.tr("Enable LLM for pet interaction"),
            parent=self.LLMGroup
        )
        self.LLMEnableCard.setChecked(settings.llm_config.get('enabled', False))
        self.LLMEnableCard.switchButton.checkedChanged.connect(self._LLMEnableChanged)
        
        # 添加模型类型选择
        model_types = sorted(list(settings.LLM_NAMES.values()))
        self.LLMTypeCard = Dyber_ComboBoxSettingCard(
            model_types,
            model_types,
            QIcon(os.path.join(basedir, 'res/icons/system/ai.svg')),
            self.tr('Model Type'),
            self.tr('Select the type of LLM to use'),
            parent=self.LLMGroup
        )
        # 设置当前选中的模型类型
        model_key = settings.llm_config.get('model_type', 'Qwen')
        self.LLMTypeCard.comboBox.setCurrentText(settings.LLM_NAMES[model_key])
        self.LLMTypeCard.comboBox.currentTextChanged.connect(self._LLMTypeChanged)
        
        # 添加API Key设置
        self.LLMApiKeyCard = SwitchSettingCard(
            QIcon(os.path.join(basedir, 'res/icons/system/key.svg')),
            self.tr("API Key"),
            self.tr("API key for remote LLM services"),
            parent=self.LLMGroup
        )
        self.LLMApiKeyCard.hBoxLayout.removeWidget(self.LLMApiKeyCard.switchButton)
        self.LLMApiKeyCard.switchButton.deleteLater()
        self.LLMApiKeyEdit = LineEdit(self.LLMApiKeyCard)
        self.LLMApiKeyEdit.setText(settings.llm_config.get('api_key', ''))
        self.LLMApiKeyEdit.setClearButtonEnabled(True)
        self.LLMApiKeyEdit.setEchoMode(LineEdit.Password)  # 密码模式显示
        self.LLMApiKeyEdit.setPlaceholderText(self.tr("Enter your API key here"))
        self.LLMApiKeyCard.hBoxLayout.addStretch(1)
        self.LLMApiKeyCard.hBoxLayout.addWidget(self.LLMApiKeyEdit)
        self.LLMApiKeyCard.hBoxLayout.setContentsMargins(16, 0, 15, 0)
        self.LLMApiKeyEdit.editingFinished.connect(self._LLMApiKeyChanged)
        
        # 添加调试模式开关
        self.LLMDebugCard = SwitchSettingCard(
            QIcon(os.path.join(basedir, 'res/icons/system/debug.svg')),
            self.tr("Debug Mode"),
            self.tr("Show detailed LLM request and response logs"),
            parent=self.LLMGroup
        )
        self.LLMDebugCard.setChecked(settings.llm_config.get('debug_mode', False))
        self.LLMDebugCard.switchButton.checkedChanged.connect(self._LLMDebugChanged)

        # About ==============================================================================
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        update_needed, update_text = self._checkUpdate()
        settings.UPDATE_NEEDED = update_needed
        self.aboutCard = HyperlinkCard(
            settings.RELEASE_URL,
            self.tr('Release Website'),
            QIcon(os.path.join(basedir, 'res/icons/system/update.svg')),
            self.tr('Check Updates'),
            update_text, #self.tr('Check update and learn more about the project on our GitHub page'),
            self.aboutGroup
        )
        self.helpCard = HyperlinkCard(
            settings.HELP_URL,
            self.tr('Issue Page'),
            FIF.HELP,
            self.tr('Help & Issue'),
            self.tr('Post your issue or question on our GitHub Issue, or contact us on BiliBili'),
            self.aboutGroup
        )
        self.devCard = HyperlinkCard(
            settings.DEVDOC_URL,
            self.tr('Developer Document'),
            QIcon(os.path.join(basedir, 'res/icons/system/document.svg')),
            self.tr('Re-development'),
            self.tr('If you want to develop your own pet/item/actions... Check here'),
            self.aboutGroup
        )


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
        #self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(50, 20)

        # add cards to group
        self.ModeGroup.addSettingCard(self.AlwaysOnTopCard)
        self.ModeGroup.addSettingCard(self.AllowDropCard)
        self.ModeGroup.addSettingCard(self.AutoLockCard)

        self.InteractionGroup.addSettingCard(self.GravityCard)
        self.InteractionGroup.addSettingCard(self.DragCard)

        self.VolumnGroup.addSettingCard(self.VolumnCard)
        self.VolumnGroup.addSettingCard(self.AllowToasterCard)
        self.VolumnGroup.addSettingCard(self.AllowBubbleCard)

        self.PersonalGroup.addSettingCard(self.ScaleCard)
        self.PersonalGroup.addSettingCard(self.DefaultPetCard)
        self.PersonalGroup.addSettingCard(self.languageCard)
        self.PersonalGroup.addSettingCard(self.themeColorCard)

        self.LLMGroup.addSettingCard(self.LLMEnableCard)
        self.LLMGroup.addSettingCard(self.LLMTypeCard)
        #self.LLMGroup.addSettingCard(self.LLMApiUrlCard)
        self.LLMGroup.addSettingCard(self.LLMApiKeyCard)
        self.LLMGroup.addSettingCard(self.LLMDebugCard)

        self.aboutGroup.addSettingCard(self.aboutCard)
        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.devCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)

        self.expandLayout.addWidget(self.ModeGroup)
        self.expandLayout.addWidget(self.InteractionGroup)
        self.expandLayout.addWidget(self.VolumnGroup)
        self.expandLayout.addWidget(self.PersonalGroup)
        self.expandLayout.addWidget(self.LLMGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')

        theme = 'light' #if isDarkTheme() else 'light'
        with open(os.path.join(basedir, 'res/icons/system/qss/', theme, 'setting_interface.qss'), encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def _AlwaysOnTopChanged(self, isChecked):
        if isChecked:
            settings.on_top_hint = True
            settings.save_settings()
            self.ontop_changed.emit()
        else:
            settings.on_top_hint = False
            settings.save_settings()
            self.ontop_changed.emit()

    def _AllowDropChanged(self, isChecked):
        if isChecked:
            settings.set_fall = True
        else:
            settings.set_fall = False
        settings.save_settings()

    def _AutoLockChanged(self, isChecked):
        if isChecked:
            settings.auto_lock = True
        else:
            settings.auto_lock = False
        settings.save_settings()

    def _GravityChanged(self, value):
        settings.gravity = value*0.01
        settings.save_settings()

    def _DragChanged(self, value):
        settings.fixdragspeedx, settings.fixdragspeedy = value*0.01, value*0.01
        settings.save_settings()

    def _VolumnChanged(self, value):
        settings.volume = round(value*0.1, 3)
        settings.save_settings()

    def _LLMEnableChanged(self, isChecked):
        settings.llm_config['enabled'] = isChecked
        settings.save_settings()

    def _LLMApiUrlChanged(self, text):
        settings.llm_config['api_url'] = text
        settings.save_settings()

    def _ScaleChanged(self, value):
        settings.tunable_scale = value*0.1
        settings.scale_dict[settings.petname] = settings.tunable_scale
        settings.save_settings()
        self.scale_changed.emit()

    def _update_scale(self):
        self.ScaleCard.setValue(int(settings.tunable_scale*10))

    def _DefaultPetChanged(self, value):
        settings.default_pet = value
        settings.save_settings()

    def _LanguageChanged(self, value):
        settings.language_code = settings.lang_dict[value]
        settings.save_settings()
        settings.change_translator(settings.lang_dict[value])
        #self.retranslateUi()
        self.__showRestartTooltip()
        self.lang_changed.emit()
    
    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.warning(
            '',
            self.tr('Configuration takes effect after restart\n此设置在重启后生效'),
            duration=3000,
            position=InfoBarPosition.BOTTOM,
            parent=self.window()
        )

    def colorChanged(self, color_str):
        setThemeColor(color_str)
        settings.themeColor = color_str
        settings.save_settings()

    def _checkUpdate(self):
        local_version = settings.VERSION
        success, github_version = self.get_latest_version()
        if success:
            update_needed = self.compare_versions(local_version, github_version)
            if update_needed:
                return True, local_version + "  " + self.tr("New version available")
            else:
                return False, local_version + "  " + self.tr("Already the latest")
        else:
            return False, self.tr("Failed to check updates. Please check the website.")
        
    def _AllowToasterChanged(self, isChecked):
        if isChecked:
            settings.toaster_on = True
        else:
            settings.toaster_on = False
        settings.save_settings()

    def _AllowBubbleChanged(self, isChecked):
        if isChecked:
            settings.bubble_on = True
        else:
            settings.bubble_on = False
        settings.save_settings()

    def get_latest_version(self):
        url = settings.RELEASE_API
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                return True, data['tag_name']
        except Exception as e:
            return False, None

    def compare_versions(self, local_version, github_version):
        # Remove 'v' prefix from version strings
        local_version = local_version.lstrip('v')
        github_version = github_version.lstrip('v')

        # Split version strings into their components
        local_parts = local_version.split('.')
        github_parts = github_version.split('.')

        # Convert version components to integers
        local_numbers = [int(part) for part in local_parts]
        github_numbers = [int(part) for part in github_parts]

        # Compare each component
        for local, github in zip(local_numbers, github_numbers):
            if local < github:
                return True  # User should update
            elif local > github:
                return False  # Local version is ahead

        # If all components are equal, check for additional components
        if len(local_numbers) < len(github_numbers):
            return True  # User should update
        else:
            return False  # Local version is up to date or ahead

    """
    def _LLMSourceChanged(self, index):
        use_local = (index == 0)
        settings.llm_config['use_local'] = use_local
        settings.save_settings()
        
        # 如果有LLM客户端实例，切换模型源
        if hasattr(settings, 'llm_client'):
            settings.llm_client.switch_model_source(use_local)
        
        self._updateLLMUIState()

    def _LLMLocalUrlChanged(self, text):
        settings.llm_config['api_url'] = text
        settings.save_settings()

    def _LLMRemoteUrlChanged(self, text):
        settings.llm_config['remote_api_url'] = text
        settings.save_settings()
    """

    def _LLMApiKeyChanged(self):
        text = self.LLMApiKeyEdit.text().strip()
        settings.llm_config['api_key'] = text
        settings.save_settings()
        self.llm_change_api_key.emit()

    def _LLMDebugChanged(self, isChecked):
        settings.llm_config['debug_mode'] = isChecked
        settings.save_settings()
        self.llm_change_debug.emit()

    def _LLMTypeChanged(self, model_type):
        model_key = get_key_by_value(settings.LLM_NAMES, model_type)
        settings.llm_config['model_type'] = model_key
        settings.save_settings()
        self.llm_change_model.emit()


    """
    def _updateLLMUIState(self):
        # 根据当前选择的模型类型更新UI状态
        api_type = settings.llm_config.get('api_type', 'local')
        
        # 本地模型只需要API URL
        if api_type == 'local':
            self.LLMApiUrlCard.setEnabled(True)
            self.LLMApiKeyCard.setEnabled(False)
            self.LLMApiUrlEdit.setPlaceholderText("http://localhost:8000/v1/chat/completions")
        
        # 远程API需要URL和Key
        elif api_type == 'remote':
            self.LLMApiUrlCard.setEnabled(True)
            self.LLMApiKeyCard.setEnabled(True)
            self.LLMApiUrlEdit.setPlaceholderText("https://api.openai.com/v1/chat/completions")
        
        # 通义千问只需要Key
        elif api_type == 'dashscope':
            self.LLMApiUrlCard.setEnabled(False)
            self.LLMApiKeyCard.setEnabled(True)
            self.LLMApiKeyEdit.setPlaceholderText("输入通义千问API密钥")
            
        # 更新UI控件值以反映当前配置
        self.LLMApiUrlEdit.setText(settings.llm_config.get('api_url', ''))
        self.LLMApiKeyEdit.setText(settings.llm_config.get('api_key', ''))
    """


def get_key_by_value(d, target_value):
    for key, value in d.items():
        if value == target_value:
            return key
    raise ValueError(f"Value '{target_value}' not found in dictionary.")

