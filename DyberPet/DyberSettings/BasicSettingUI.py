# coding:utf-8
#from .config import HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, HyperlinkCard,InfoBar,
                            ComboBoxSettingCard, ScrollArea, ExpandLayout, InfoBarPosition)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QWidget, QLabel, QApplication
#from qframelesswindow import FramelessWindow

from .custom_utils import Dyber_RangeSettingCard, Dyber_ComboBoxSettingCard
import DyberPet.settings as settings
import os
from sys import platform
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



class SettingInterface(ScrollArea):
    """ Setting interface """

    ontop_changed = Signal(name='ontop_changed')
    scale_changed = Signal(name='scale_changed')
    lang_changed = Signal(name='lang_changed')

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SettingInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        '''
        # music folders
        self.musicInThisPCGroup = SettingCardGroup(
            self.tr("Music on this PC"), self.scrollWidget)
        self.musicFolderCard = FolderListSettingCard(
            cfg.musicFolders,
            self.tr("Local music library"),
            directory=QStandardPaths.writableLocation(QStandardPaths.MusicLocation),
            parent=self.musicInThisPCGroup
        )
        self.downloadFolderCard = PushSettingCard(
            self.tr('Choose folder'),
            FIF.DOWNLOAD,
            self.tr("Download directory"),
            cfg.get(cfg.downloadFolder),
            self.musicInThisPCGroup
        )
        '''
        
        # Mode =========================================================================================
        self.ModeGroup = SettingCardGroup(self.tr('Mode'), self.scrollWidget)
        #self.personalGroup.titleLabel
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


        # Volumn parameters ============================================================================
        self.VolumnGroup = SettingCardGroup(self.tr('Volumn'), self.scrollWidget)
        self.VolumnCard = Dyber_RangeSettingCard(
            0, 10, 0.1,
            QIcon(os.path.join(basedir, 'res/icons/system/speaker.svg')),
            self.tr("Volumn"),
            self.tr("Volumn of notification and pet"),
            parent=self.VolumnGroup
        )
        self.VolumnCard.setValue(int(settings.volume*10))
        self.VolumnCard.slider.valueChanged.connect(self._VolumnChanged)

        # Personalization ==============================================================================
        self.PersonalGroup = SettingCardGroup(self.tr('Personalization'), self.scrollWidget)
        self.ScaleCard = Dyber_RangeSettingCard(
            0, 50, 0.1,
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

        # About ==============================================================================
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        self.aboutCard = HyperlinkCard(
            settings.PROJECT_URL,
            self.tr('Open GitHub Page'),
            QIcon(os.path.join(basedir, 'res/icons/system/home.svg')),
            self.tr('Project Website'),
            self.tr('Check update and learn more about the project on our GitHub page'),
            self.aboutGroup
        )
        self.helpCard = HyperlinkCard(
            settings.HELP_URL,
            self.tr('Open Issue Page'),
            FIF.HELP,
            self.tr('Help & Issue'),
            self.tr('Post your issue or question on our GitHub Issue, or contact us on BiliBili'),
            self.aboutGroup
        )
        self.devCard = HyperlinkCard(
            settings.DEVDOC_URL,
            self.tr('Open Developer Document'),
            QIcon(os.path.join(basedir, 'res/icons/system/design.svg')),
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

        self.InteractionGroup.addSettingCard(self.GravityCard)
        self.InteractionGroup.addSettingCard(self.DragCard)

        self.VolumnGroup.addSettingCard(self.VolumnCard)

        self.PersonalGroup.addSettingCard(self.ScaleCard)
        self.PersonalGroup.addSettingCard(self.DefaultPetCard)
        self.PersonalGroup.addSettingCard(self.languageCard)

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

    def _GravityChanged(self, value):
        settings.gravity = value*0.01
        settings.save_settings()

    def _DragChanged(self, value):
        settings.fixdragspeedx, settings.fixdragspeedy = value*0.01, value*0.01
        settings.save_settings()

    def _VolumnChanged(self, value):
        settings.volume = value*0.1
        settings.save_settings()

    def _ScaleChanged(self, value):
        settings.tunable_scale = value*0.1
        settings.save_settings()
        self.scale_changed.emit()

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

    '''
    def __onDeskLyricFontCardClicked(self):
        """ desktop lyric font button clicked slot """
        font, isOk = QFontDialog.getFont(
            cfg.desktopLyricFont, self.window(), self.tr("Choose font"))
        if isOk:
            cfg.desktopLyricFont = font

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return

        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)

    def __onThemeChanged(self, theme: Theme):
        """ theme changed slot """
        # change the theme of qfluentwidgets
        setTheme(theme)

        # chang the theme of setting interface
        self.__setQss()

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        cfg.themeChanged.connect(self.__onThemeChanged)

        # music in the pc
        self.musicFolderCard.folderChanged.connect(
            self.musicFoldersChanged)
        self.downloadFolderCard.clicked.connect(
            self.__onDownloadFolderCardClicked)

        # personalization
        self.enableAcrylicCard.checkedChanged.connect(
            self.acrylicEnableChanged)
        self.themeColorCard.colorChanged.connect(setThemeColor)

        # playing interface
        self.deskLyricFontCard.clicked.connect(self.__onDeskLyricFontCardClicked)

        # main panel
        self.minimizeToTrayCard.checkedChanged.connect(
            self.minimizeToTrayChanged)

        # about
        self.aboutCard.clicked.connect(self.checkUpdateSig)
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
    '''
