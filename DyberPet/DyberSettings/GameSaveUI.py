#coding:utf-8
#from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, HyperlinkCard,InfoBar,
#                            ComboBoxSettingCard, ScrollArea, ExpandLayout, FluentTranslator)
import os
import json
from datetime import datetime

from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup, InfoBar, FlowLayout,
                            PushSettingCard, PushButton, RoundMenu, Action, MessageBox,
                            InfoBarPosition, TransparentToolButton)

from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths, QLocale, QSize
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QFileDialog, QSizePolicy, QHBoxLayout, QSpacerItem

from .custom_utils import DyberToolBottonCard, QuickSaveCard, SaveCardGroup, LineEditDialog
from .fileOp_utils import CopySave, DeleteQuickSave
import DyberPet.settings as settings
basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/DyberSettings/')

from sys import platform


class SaveInterface(ScrollArea):
    """ Gaem Save interface """
    freeze_pet = Signal(name='freeze_pet')
    refresh_pet = Signal(name='refresh_pet')

    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SaveInterface")
        self.sizeHintDyber = (sizeHintDyber[0]-100, sizeHintDyber[1])

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # panel title
        self.headerWidget = QWidget(self)
        self.headerWidget.setFixedWidth(sizeHintDyber[0]-165)
        self.panelLabel = QLabel(self.tr("Game Save"), self.headerWidget)
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
        spacerItem2 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.headerLayout.addItem(spacerItem2)

        
        # Save transfer ================================================================================
        self.TransferSaveGroup = SettingCardGroup(
            self.tr("Save Transfer"), self.scrollWidget)
        
        ExportDir = '/DyberPet/Exports'
        docPath = (QStandardPaths.locate(QStandardPaths.DocumentsLocation, '', QStandardPaths.LocateDirectory))
        ExportDir = os.path.normpath(docPath + ExportDir)
        if not os.path.exists(ExportDir):
            os.makedirs(ExportDir)

        self.ExportSaveCard = PushSettingCard(
            self.tr('Choose folder'),
            QIcon(os.path.join(basedir, 'res/icons/system/download.svg')),
            self.tr("Export to"),
            ExportDir,
            self.TransferSaveGroup
        )

        self.ImportSaveCard = DyberToolBottonCard(
            self.tr('Import for'),
            QIcon(os.path.join(basedir, 'res/icons/system/upload.svg')),
            self.tr("Import from"),
            menu_text = [self.tr('All pets')] + settings.pets,
            content=self.tr("Please choose the pet, then choose the save folder"),
            parent=self.TransferSaveGroup
        )
        self.ImportSaveCard.ToolButton.setToolTip(self.tr("Select pet, then select folder"))

        SaveDir = '/DyberPet/Saves'
        self.quickSaveDir = os.path.join(docPath + SaveDir)
        if not os.path.exists(self.quickSaveDir):
            os.makedirs(self.quickSaveDir)

        self.__initQuickSaveLayout()       
        self.__initWidget()


    def __initQuickSaveLayout(self):

        self.QuickSaveGroup = SaveCardGroup(
            self.tr("Quick Save"), self.sizeHintDyber, self.scrollWidget)

        self.saveCardList = []
        for iCard in range(6):
            folder = os.path.join(self.quickSaveDir, str(iCard))
            folder = os.path.normpath(folder)
            if os.path.exists(folder):
                allSaves = get_child_folder(folder, relative=True)
                if len(allSaves) > 0:
                    jsonPath = [iSave for iSave in allSaves if iSave.startswith(str(len(allSaves)-1))][0]
                    jsonPath = os.path.join(folder, jsonPath)
                    card = QuickSaveCard(iCard, jsonPath=jsonPath, parent=self.QuickSaveGroup)
                else:
                    card = QuickSaveCard(iCard, parent=self.QuickSaveGroup)
            else:
                card = QuickSaveCard(iCard, parent=self.QuickSaveGroup)

            self.QuickSaveGroup.addSaveCard(card)
            self.saveCardList.append(card)


    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 75, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.headerWidget.move(50, 20)

        # add cards to group
        self.TransferSaveGroup.addSettingCard(self.ExportSaveCard)
        self.TransferSaveGroup.addSettingCard(self.ImportSaveCard)
        
        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.TransferSaveGroup)
        self.expandLayout.addWidget(self.QuickSaveGroup)


    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.panelLabel.setObjectName('settingLabel')

        theme = 'light' #if isDarkTheme() else 'light'
        with open(os.path.join(basedir, 'res/icons/system/qss/', theme, 'setting_interface.qss'), encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        self.panelHelp.clicked.connect(self._showInstruction)
        self.ExportSaveCard.clicked.connect(
            self.__onExportSaveCardClicked)
        self.ImportSaveCard.optionSelcted.connect(
            self.__onImportSaveCardClicked)

        for i in range(len(self.saveCardList)):
            self.saveCardList[i].saveClicked.connect(self.__onCardSaveClicked)
            self.saveCardList[i].loadinClicked.connect(self.__onCardLoadinClicked)
            self.saveCardList[i].rewriteClicked.connect(self.__onCardSaveClicked)
            self.saveCardList[i].deleteClicked.connect(self.__onCardDeleteClicked)
            self.saveCardList[i].backtraceClicked.connect(self.__onCardBackClicked)


    def __onExportSaveCardClicked(self):
        """ export folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose Export folder"), 
            self.ExportSaveCard.contentLabel.text())
        if not folder:
            return

        # get folder name YYYY-MM-DD-HH-MM-SS
        save_folder = get_foler_name()
        # get final folder name and create
        save_folder = os.path.join(folder, save_folder)
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        # copy file and check MD5
        source_folder = os.path.join(basedir, 'data')
        status_code = CopySave(source_folder, save_folder)
        # Notification
        status_mssg = [self.tr('Export Succeed!'),
                       self.tr('Export Failed! Please try again.'),
                       self.tr('Export Failed! Please try again.')]
        status_meth = [0, 2, 2]
        self.__showSystemNote(status_mssg[status_code], status_meth[status_code])
        self.ExportSaveCard.setContent(folder)

    def __onImportSaveCardClicked(self, petname):
        """ import folder card clicked slot """

        # Confirm
        title = self.tr('Are you sure you want to import another save?')
        content = self.tr("""• Make sure you have exported the current save, in case an error happened\n• Currently, only save will be imported, note and settings won't be influenced\n• Only selected character save will be modified""")
        if not self.__showMessageBox(title, content):
            return

        # Get the save folder name
        ExportDir = '/DyberPet/Exports'
        docPath = (QStandardPaths.locate(QStandardPaths.DocumentsLocation, '', QStandardPaths.LocateDirectory))
        ExportDir = os.path.normpath(docPath + ExportDir)
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose Save Folder to Import"), 
            ExportDir) #self.ImportSaveCard.contentLabel.text())

        # If no file selected
        if not folder:
            return

        # Load in data
        self._loadin_petData(folder, petname)

        self.ImportSaveCard.setContent(folder)

    def _loadin_petData(self, folder, petname):

        # check if pet_data.json is there
        if not os.path.exists(os.path.join(folder, 'pet_data.json')):
            self.__showSystemNote(self.tr('File: pet_data.json not found in selected folder!'),
                                  type_code=2)
            return

        # check the integrity of files (making sure it can be used)
        save_dict = json.load(open(os.path.join(folder, 'pet_data.json'), 'r', encoding='UTF-8'))
        if petname == self.tr("All pets"):
            petname = 'all'
        CheckStatus = settings.pet_data.check_save_integrity(save_dict, petname)
        if not CheckStatus:
            self.__showSystemNote(self.tr('File: pet_data.json is not in compatible format!'),
                                  type_code=2)
            return

        # freeze current pet data
        settings.pet_data.frozen()

        # try transfer data to settings.pet_data and save
        save_dict = json.load(open(os.path.join(folder, 'pet_data.json'), 'r', encoding='UTF-8'))
        TransferStatus = settings.pet_data.transfer_save(save_dict, petname)

        if TransferStatus:
            self.__showSystemNote(self.tr('Save imported successfully!'),
                                  type_code=0)
        else:
            self.__showSystemNote(self.tr('Failed to import save!'),
                                  type_code=2)

        self.refresh_pet.emit()


    def __onCardSaveClicked(self, cardIndex):
        """ Creat Quick Save """

        # Enter Folder Name
        title = self.tr('Name of the Save')
        if self.saveCardList[cardIndex].jsonPath is None:
            self.saveName = get_foler_name(filename=False)
        else:
            oldTitle = self.saveCardList[cardIndex].cardTitle
            if is_default_time_format(oldTitle):
                self.saveName = get_foler_name(filename=False)
            else:
                self.saveName = oldTitle
        w = LineEditDialog(title, self.saveName, self)
        w.yesButton.setText(self.tr('OK'))
        w.cancelButton.setText(self.tr('Cancel'))
        #w.yesSignal.connect(self.__setSaveName)
        if w.exec():
            self.saveName = w.nameLineEdit.text()
            #pass
        else:
            return

        # Get final folder name and create
        parentFolder = os.path.join(self.quickSaveDir, str(cardIndex))
        if not os.path.exists(parentFolder):
            os.makedirs(parentFolder)

        #all_files_and_dirs = os.listdir(parentFolder)
        #oldSaves = [d for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]
        oldSaves = get_child_folder(parentFolder)
        finalFolder = os.path.join(parentFolder, f'{str(len(oldSaves))}')
        os.makedirs(finalFolder)

        # Record info file
        infoFile = open(os.path.join(finalFolder, 'info.txt'), 'w', encoding='UTF-8')
        infoFile.write(f"{settings.petname}\n{self.saveName}")
        infoFile.close()

        # Transfer Save Files
        source_folder = os.path.join(basedir, 'data')
        status_code = CopySave(source_folder, finalFolder)
        # Notification
        status_mssg = [self.tr('Save Succeed!'),
                       self.tr('Save Failed! Please try again.'),
                       self.tr('Save Failed! Please try again.')]
        status_meth = [0, 2, 2]

        # Change Save Card UI
        try:
            self.saveCardList[cardIndex]._registerSave(finalFolder)
        except:
            self.__showSystemNote(self.tr('Updating Save card failed!'), 2)

        self.__showSystemNote(status_mssg[status_code], status_meth[status_code])


    def __setSaveName(self, saveName):
        self.saveName = saveName


    def __onCardLoadinClicked(self, cardIndex):

        # Confirm
        title = self.tr('Load in the save?')
        content = self.tr("""Pet save data will be overwritten.""")
        if not self.__showMessageBox(title, content):
            return

        folder = os.path.join(self.quickSaveDir, str(cardIndex))
        folder = os.path.normpath(folder)
        if os.path.exists(folder):
            allSaves = get_child_folder(folder, relative=True)
            if len(allSaves) > 0:
                jsonPath = [iSave for iSave in allSaves if iSave.startswith(str(len(allSaves)-1))][0]
                jsonPath = os.path.join(folder, jsonPath)
            else:
                self.__showSystemNote(self.tr('Error: Save folder in bad format!'), 2)
                return
        else:
            self.__showSystemNote(self.tr('Error: Save folder in bad format!'), 2)
            return

        info = open(os.path.join(jsonPath,'info.txt'),'r', encoding='UTF-8').readlines()
        info = [i.strip() for i in info]
        petname = info[0]

        self._loadin_petData(jsonPath, petname)


    def __onCardDeleteClicked(self, cardIndex):
        
        # Confirm
        title = self.tr('Are you sure you want to delete the save?')
        content = self.tr("""All history saves in this slot will be deleted, use carefully""")
        if not self.__showMessageBox(title, content):
            return

        # Delete all saves
        folder = os.path.join(self.quickSaveDir, str(cardIndex))
        folder = os.path.normpath(folder)
        status = DeleteQuickSave(folder)
        if status:
            self.__showSystemNote(self.tr('Deletion Succeed!'), 0)
        else:
            self.__showSystemNote(self.tr('Error: Deletion Failed!'), 2)
            return

        # Change quick save card UI
        try:
            self.saveCardList[cardIndex]._deleteSave()
        except:
            self.__showSystemNote(self.tr('Updating Save card failed!'), 2)


    def __onCardBackClicked(self, cardIndex):

        # Confirm
        title = self.tr('Are you sure you want to backtrace the save slot?')
        content = self.tr("""It will delete the current save, and backtrace to the last one in this slot.""")
        if not self.__showMessageBox(title, content):
            return

        # Delete current save
        folder = os.path.join(self.quickSaveDir, str(cardIndex))
        folder = os.path.normpath(folder)
        if os.path.exists(folder):
            allSaves = get_child_folder(folder, relative=True)
            if len(allSaves) > 0:
                jsonPath = [iSave for iSave in allSaves if iSave.startswith(str(len(allSaves)-1))][0]
                jsonPath = os.path.join(folder, jsonPath)
            else:
                self.__showSystemNote(self.tr('Error: Save folder in bad format!'), 2)
                return
        else:
            self.__showSystemNote(self.tr('Error: Save folder in bad format!'), 2)
            return

        status = DeleteQuickSave(jsonPath, keep=False)
        if status:
            self.__showSystemNote(self.tr("Save backtraced successfully!"), 0)
        else:
            self.__showSystemNote(self.tr('Error: Deleting current save Failed!'), 2)
            return

        # Change Save Card UI
        folder = os.path.join(self.quickSaveDir, str(cardIndex))
        folder = os.path.normpath(folder)
        if os.path.exists(folder):
            allSaves = get_child_folder(folder, relative=True)
            if len(allSaves) > 0: # Trace back to the last save
                jsonPath = [iSave for iSave in allSaves if iSave.startswith(str(len(allSaves)-1))][0]
                jsonPath = os.path.join(folder, jsonPath)
                try:
                    self.saveCardList[cardIndex]._registerSave(jsonPath)
                except:
                    self.__showSystemNote(self.tr('Updating Save card failed!'), 2)
                    return
            else: # Card becomes empty
                try:
                    self.saveCardList[cardIndex]._deleteSave()
                except:
                    self.__showSystemNote(self.tr('Updating Save card failed!'), 2)
                

    def __showMessageBox(self, title, content):

        WarrningMessage = MessageBox(title, content, self)
        WarrningMessage.yesButton.setText(self.tr('OK'))
        WarrningMessage.cancelButton.setText(self.tr('Cancel'))
        if WarrningMessage.exec():
            return True
        else:
            #print('Cancel button is pressed')
            return False

    def __showSystemNote(self, content, type_code):
        """ show restart tooltip """
        notMethods = [InfoBar.success, InfoBar.warning, InfoBar.error]
        notMethods[type_code](
            '',
            content,
            duration=3000,
            position=InfoBarPosition.BOTTOM,
            parent=self.window()
        )

    def _showInstruction(self):
        title = self.tr("Game Save Guide")
        content = self.tr("""Game Save Panel is the place you can Save and Load data.

From top to bottom, there are 3 functions:
⏺ Export Data
    - You can make a copy of the data to selected path
    - It contains character, settings, and task-related data

⏺ Import Data
    - You can import character data from the selected folder
    - Choose import for all character or only one specific character
    - Currently, only status and items data can be imported
    - If you want to import other data like customized action, settings, you need to manually copy the files to the App data folder

⏺ Quick Save
    - Quick save frees you from selecting folders, and has more functions
    - It has 6 Slots, and their are 4 operations
    - Load In: Load in the Slot data for this character (! cannot undo, so be careful)
    - Rewrite: Save current character's data in this slot
    - Backtrace: Go back to the previous save data in this slot. Usefull when you accidentally over-write the save. But it also means you will lose the current save
    - Delete: Empty ALL save data in this slot (current one, and all previous ones)""")
        self.__showMessageBox(title, content)
        return

    
def get_foler_name(filename=True):

    # Get the current time
    current_time = datetime.now()

    # Format the current time into the desired string format
    if filename:
        formatted_time = current_time.strftime('%Y-%m-%d-%H-%M-%S')
    else:
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

    return formatted_time


def get_child_folder(parentFolder, relative=False):
    all_files_and_dirs = os.listdir(parentFolder)
    if relative:
        all_dirs = [os.path.basename(d) for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]
    else:
        all_dirs = [d for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]

    return all_dirs



def is_default_time_format(s):
    try:
        datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False


