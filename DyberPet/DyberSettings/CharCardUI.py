#coding:utf-8
#from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, HyperlinkCard,InfoBar,
#                            ComboBoxSettingCard, ScrollArea, ExpandLayout, FluentTranslator)
import os
import json
from datetime import datetime
from shutil import copytree

from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup, InfoBar, FlowLayout,
                            PushSettingCard, PushButton, RoundMenu, Action, MessageBox,
                            InfoBarPosition, HyperlinkButton, ToolButton, PushButton, setFont,
                            StateToolTip, TransparentPushButton)

from qfluentwidgets import FluentIcon as FIF

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QStandardPaths, QLocale, QPoint
from PyQt5.QtGui import QDesktopServices, QIcon, QFont
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QFileDialog

from .custom_utils import CharCard, CharCardGroup, CharLine
from DyberPet.conf import CheckCharFiles
import DyberPet.settings as settings

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


class CharInterface(ScrollArea):
    """ Character Management interface """
    change_pet = pyqtSignal(str, name='change_pet')

    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("CharInterface")
        self.newPetFolder = None
        self.thread = None
        self.sizeHintDyber = (sizeHintDyber[0]-100, sizeHintDyber[1])

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Characters Management"), self)
        # HyperLink to character collection (website not implemented yet)
        self.CharListLink = HyperlinkButton(
                                            settings.CHARCOLLECT_LINK, 
                                            self.tr('Collected Characters'), 
                                            self, FIF.LINK)
        # Button to add chars from local file
        self.addButton = PushButton(self.tr("Add Characters"), self, FIF.ADD)

        # Button to show instructions on how to manually add chars
        self.instructButton = TransparentPushButton(self.tr("Add Chars Manually"), self, FIF.QUESTION)
        

        self.__initCardLayout()

        self.__initWidget()

    def __initCardLayout(self):

        self.CharCardGroup = CharCardGroup(
            self.tr("Characters"), self.sizeHintDyber, self.scrollWidget)

        self.CharCardList = []
        self.CharLineList = []
        petlist = settings.pets.copy()
        petlist.sort()
        for i, character in enumerate(petlist):
            
            infoLine = CharLine(i, chrFolder=character, parent=self.CharCardGroup)
            self.CharCardGroup.addInfoCard(infoLine)
            self.CharLineList.append(infoLine)
            
            
            infoFile = os.path.join(basedir,"res/role", character, "info/info.json")
            if not os.path.exists(infoFile):
                self.CharCardList.append(None)
            else:
                card = CharCard(i, jsonPath=infoFile, petFolder=character) #, parent=self.CharCardGroup)
                self.CharCardList.append(card)



    def __initWidget(self):
        #self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidget(self.scrollWidget)
        #self.scrollWidget.resize(1000, 800)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(50, 20)
        self.addButton.move(55, 75)
        self.CharListLink.move(200, 75)
        self.instructButton.move(450,75)

        # add cards to group
        #self.TransferSaveGroup.addSettingCard(self.ExportSaveCard)
        #self.TransferSaveGroup.addSettingCard(self.ImportSaveCard)
        #self.TransferSaveGroup.addSettingCard(self.PushTestCard)

        
        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        #self.expandLayout.addWidget(self.TransferSaveGroup)
        self.expandLayout.addWidget(self.CharCardGroup)
        #self.expandLayout.addWidget(self.PushTestCard)


    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')

        theme = 'light' #if isDarkTheme() else 'light'
        with open(os.path.join(basedir, 'res/icons/system/qss', theme, 'setting_interface.qss'), encoding='utf-8') as f:
            self.setStyleSheet(f.read())

        setFont(self.settingLabel, 33, QFont.Bold)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        
        for i, charCard in enumerate(self.CharCardList):
            self.CharLineList[i].launchClicked.connect(self.__onLaunchClicked)

            if charCard:
                self.CharLineList[i].infoClicked.connect(self.__onInfoClicked)
        
                self.CharCardList[i].card.gotoClicked.connect(self.__onGotoClicked)
                self.CharCardList[i].card.deleteClicked.connect(self.__onDeleteClicked)

        self.addButton.clicked.connect(self.__onAddClicked)
        self.instructButton.clicked.connect(self.__onShowInstruction)

    def __onLaunchClicked(self, petname):
        # Confirm
        title = self.tr('Switch to ') + petname + "?"
        content = self.tr("Might take some time, just wait a moment <3")
        if not self.__showMessageBox(title, content):
            return

        self._launchStateTooltip()
        self.change_pet.emit(petname)

    def _launchStateTooltip(self):
        self.launchTooltip = StateToolTip(
            self.tr('Loading Character...'), self.tr('Please wait patiently'), self.window())
        self.launchTooltip.move(self.launchTooltip.getSuitablePos())
        self.launchTooltip.show()

    def _finishStateTooltip(self):
        if not self.launchTooltip:
            return
        else:
            self.launchTooltip.setContent(
                self.tr('Launched!') + ' 😆')
            self.launchTooltip.setState(True)
            self.launchTooltip = None

    def __onGotoClicked(self, folder):
        os.startfile(os.path.normpath(folder))

    def __onDeleteClicked(self, cardIndex, folder):
        # Judge if it is current pet

        # Move file to trash bin

        # Remove char from settings.pet

        # Update basicSetting change pet

        # Delete character List and Card
        print(cardIndex, folder)
        title = self.tr("Function incomplete")
        content = self.tr("The function has not been implemented yet.\nCurrently, you can Go To Folder, delete the whole folder, and restart App.\nSorry for the inconvenience.")
        #if not self.__showMessageBox(title, content):
        #    return
        yesText = self.tr("Go to Folder")
        if self.__showMessageBox(title, content, yesText):
            resFolder = os.path.join(basedir, 'res/role')
            os.startfile(os.path.normpath(resFolder))
        else:
            return


    def __onInfoClicked(self, cardIndex, pos):
        if self.CharCardList[cardIndex].isVisible():
            self.CharCardList[cardIndex].hide()
        else:
            self.CharCardList[cardIndex].move(pos)
            self.CharCardList[cardIndex].show()

    def __onAddClicked(self):
        # Confirm
        title = self.tr("Adding Character")
        content = self.tr("You are about to import a character from a local file. Please be aware that it is from third-party sources. We are not responsible for any potential harm or issues that may arise from using this character. Only proceed if you trust the source.")
        if not self.__showMessageBox(title, content):
            return

        # FileDialogue to select folder
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Please select the character folder"), 
            QStandardPaths.locate(QStandardPaths.DocumentsLocation, '', QStandardPaths.LocateDirectory))

        # If no file selected
        if not folder:
            return
        else:
            print(folder)
            #return

        # Check files integrity - not implemented yet
        statCode, errorList = CheckCharFiles(os.path.abspath(folder))
        if statCode:
            self._send_CharImportResult(statCode, errorList)
            return

        # Copy file to res/role
        petFolder = os.path.basename(folder)
        destinationFolder = os.path.join(basedir, 'res/role', petFolder)
        #status = 
        # Check if char with the same name exist
        if os.path.exists(destinationFolder):
            content = self.tr("There is already a character with the same name added.")
            self.__showSystemNote(content, 2)
            return 0
        self.newPetFolder = petFolder
        self._importChar(folder, destinationFolder)
        #if not status:
        #    return
        #return


    def _importChar(self, sourceFolder, destinationFolder):

        # Copy folders
        self.thread = FileCopyThread(sourceFolder, destinationFolder)
        self.thread.started.connect(self._startStateTooltip)
        self.thread.done.connect(self._stopStateTooltip)
        #self.thread.done.connect(self.__onAddClickedContinue)
        self.thread.start()

        '''
        try:
            copytree(sourceFolder, destinationFolder)
        except:
            content = self.tr("Copying folder failed with unknown reason.")
            self.__showSystemNote(content, 2)
            self._stopStateTooltip(False)
            return 0
        '''

        # stop processing note
        #self._stopStateTooltip(True)
        #return 1

    def __onAddClickedContinue(self):

        # Add pet in settings.pet
        petFolder = self.newPetFolder
        settings.pets.append(petFolder)
        settings.defaultAct[petFolder] = None

        # Add pet in basicSetting change pet tab - not implemented yet

        # Add character List and Card
        iCard = len(self.CharLineList)
        infoLine = CharLine(iCard, chrFolder=petFolder, parent=self.CharCardGroup)
        self.CharCardGroup.addInfoCard(infoLine)
        self.CharLineList.append(infoLine)
        
        infoFile = os.path.join(basedir,"res/role", petFolder, "info/info.json")
        if not os.path.exists(infoFile):
            self.CharCardList.append(None)
        else:
            card = CharCard(iCard, jsonPath=infoFile, petFolder=petFolder) #, parent=self.CharCardGroup)
            self.CharCardList.append(card)

        self.CharLineList[iCard].launchClicked.connect(self.__onLaunchClicked)
        if os.path.exists(infoFile):
            self.CharLineList[iCard].infoClicked.connect(self.__onInfoClicked)
    
            self.CharCardList[iCard].card.gotoClicked.connect(self.__onGotoClicked)
            self.CharCardList[iCard].card.deleteClicked.connect(self.__onDeleteClicked)

        content = self.tr("Adding character completed!")
        self.__showSystemNote(content, 0)

        self.newPetFolder = None


    def _startStateTooltip(self):
        self.stateTooltip = StateToolTip(
            self.tr('Copying Files'), self.tr('Please wait patiently'), self.window())
        self.stateTooltip.move(self.stateTooltip.getSuitablePos())
        self.stateTooltip.show()

    def _stopStateTooltip(self, success=True):
        if not self.stateTooltip:
            pass
        elif success:
            self.stateTooltip.setContent(
                self.tr('Copy complete!') + ' 😆')
            self.stateTooltip.setState(True)
            self.stateTooltip = None
            self.__onAddClickedContinue()
        else:
            self.stateTooltip.setState(True)
            self.stateTooltip = None
            content = self.tr("Copying folder failed with unknown reason.")
            self.__showSystemNote(content, 2)
            self.newPetFolder = None
        
        self._terminateThread()

    def _terminateThread(self):
        if self.thread:
            self.thread.quit()  # Terminate the thread
            self.thread.wait()  # Wait until it's fully terminated
            self.thread = None 



    def _send_CharImportResult(self, statCode, errorList):
        title = self.tr("Adding Failed")
        stat_notes = [self.tr("Success!"),
                      self.tr("pet_conf.json broken or not exist!"),
                      self.tr("act_conf.json broken or not exist"),
                      self.tr('The following actions are missing "images" attribute:'),
                      self.tr("The following image files missing:"),
                      self.tr("The following default actions missing in pet_conf.json:"),
                      self.tr("The following actions called by pet_conf.json are missing from act_conf.json:")]
        content = stat_notes[statCode]
        if errorList is not None:
            content += '\n' + ', '.join(errorList)

        self.__showMessageBox(title, content)
        return

    def __onShowInstruction(self):
        title = self.tr("Add Characters Manually")
        content = self.tr("1. Prepare the character folder containing all files;\n2. Copy the folder to App resource folder (you can click 'Go to Folder' button);\n3. Close App and open again;\n4. You will see the character show up here;\n5. Click 'Launch' to start;\n6. If App crushed, it means the character file is problematic, please contact the author for help.")
        yesText = self.tr("Go to Folder")
        if self.__showMessageBox(title, content, yesText):
            resFolder = os.path.join(basedir, 'res/role')
            os.startfile(os.path.normpath(resFolder))
        else:
            return
        

    def __showMessageBox(self, title, content, yesText='OK'):

        WarrningMessage = MessageBox(title, content, self)
        if yesText == 'OK':
            WarrningMessage.yesButton.setText(self.tr('OK'))
        else:
            WarrningMessage.yesButton.setText(yesText)
        WarrningMessage.cancelButton.setText(self.tr('Cancel'))
        if WarrningMessage.exec():
            return True
        else:
            #print('Cancel button is pressed')
            return False

    def __showSystemNote(self, content, type_code, duration=5000):
        """ show restart tooltip """
        notMethods = [InfoBar.success, InfoBar.warning, InfoBar.error]
        notMethods[type_code](
            '',
            content,
            duration=duration,
            position=InfoBarPosition.BOTTOM,
            parent=self.window()
        )






    
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


class FileCopyThread(QThread):
    started = pyqtSignal()
    done = pyqtSignal(bool)

    def __init__(self, source, destination):
        super(FileCopyThread, self).__init__()
        self.source = source
        self.destination = destination

    def run(self):
        # Assuming you want to copy a directory
        # You can change this to suit your needs
        self.started.emit()
        try:
            copytree(self.source, self.destination)
        except:
            self.done.emit(False)
            return

        # Emitting progress and done signals as an example
        self.done.emit(True)
