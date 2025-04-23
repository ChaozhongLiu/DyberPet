#coding:utf-8
import os
import json
from datetime import datetime
from shutil import copytree
import subprocess

from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup, InfoBar, FlowLayout,
                            PushSettingCard, PushButton, RoundMenu, Action, MessageBox,
                            InfoBarPosition, HyperlinkButton, ToolButton, PushButton, setFont,
                            StateToolTip, TransparentPushButton, TransparentToolButton)

from qfluentwidgets import FluentIcon as FIF

from PySide6.QtCore import Qt, QThread, Signal, QUrl, QStandardPaths, QSize
from PySide6.QtGui import QDesktopServices, QIcon, QFont
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QFileDialog, QSizePolicy, QHBoxLayout, QSpacerItem

from .custom_utils import CharCard, CharCardGroup, CharLine
from DyberPet.conf import CheckCharFiles
import DyberPet.settings as settings

from sys import platform

basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/DyberSettings/')


class CharInterface(ScrollArea):
    """ Character Management interface """
    change_pet = Signal(str, name='change_pet')

    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("CharInterface")
        self.newPetFolder = None
        self.thread = None
        self.stateTooltip = None
        self.launchTooltip = None
        self.sizeHintDyber = (sizeHintDyber[0]-100, sizeHintDyber[1])

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # Title label
        self.panelLabel = QLabel(self.tr("Characters Management"), self)
        self.panelLabel.setSizePolicy(QSizePolicy.Maximum, self.panelLabel.sizePolicy().verticalPolicy())
        self.panelLabel.adjustSize()
        self.panelHelp = TransparentToolButton(QIcon(os.path.join(basedir, 'res/icons/question.svg')))
        self.panelHelp.setFixedSize(25,25)
        self.panelHelp.setIconSize(QSize(25,25))

        self.titleWidget = QWidget(self)
        self.titleWidget.setFixedWidth(sizeHintDyber[0]-165)
        self.titleLayout = QHBoxLayout(self.titleWidget)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLayout.setSpacing(0)

        self.titleLayout.addWidget(self.panelLabel, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem1 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.titleLayout.addItem(spacerItem1)
        self.titleLayout.addWidget(self.panelHelp, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem2 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.titleLayout.addItem(spacerItem2)

        # HyperLink to character collection (website not implemented yet)
        self.CharListLink = HyperlinkButton(
                                            settings.CHARCOLLECT_LINK, 
                                            self.tr('Collected Characters'), 
                                            self, FIF.LINK)
        self.CharListLink.setSizePolicy(QSizePolicy.Maximum, self.CharListLink.sizePolicy().verticalPolicy())
        
        # Button to add chars from local file
        self.addButton = PushButton(self.tr("Add Characters"), self, FIF.ADD)
        self.addButton.setSizePolicy(QSizePolicy.Maximum, self.addButton.sizePolicy().verticalPolicy())

        # Button to show instructions on how to manually add chars
        #self.instructButton = TransparentPushButton(self.tr("Add Chars Manually"), self, FIF.QUESTION)
        #self.instructButton.setSizePolicy(QSizePolicy.Maximum, self.instructButton.sizePolicy().verticalPolicy())

        self.headerWidget = QWidget(self)
        self.headerWidget.setFixedWidth(sizeHintDyber[0]-165)
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(0)

        self.headerLayout.addWidget(self.addButton, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem1 = QSpacerItem(15, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.headerLayout.addItem(spacerItem1)
        self.headerLayout.addWidget(self.CharListLink, Qt.AlignLeft | Qt.AlignVCenter)
        #spacerItem2 = QSpacerItem(15, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        #self.headerLayout.addItem(spacerItem2)
        #self.headerLayout.addWidget(self.instructButton, Qt.AlignLeft | Qt.AlignVCenter)
        spacerItem3 = QSpacerItem(15, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.headerLayout.addItem(spacerItem3)
        

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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.titleWidget.move(50, 20)
        self.headerWidget.move(55, 75)
 
        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.CharCardGroup)


    def __setQss(self):
        """ set style sheet """
        self.scrollWidget.setObjectName('scrollWidget')
        self.panelLabel.setObjectName('settingLabel')

        theme = 'light' #if isDarkTheme() else 'light'
        with open(os.path.join(basedir, 'res/icons/system/qss', theme, 'setting_interface.qss'), encoding='utf-8') as f:
            self.setStyleSheet(f.read())

        #setFont(self.panelLabel, 33, QFont.Bold)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        
        for i, charCard in enumerate(self.CharCardList):
            self.CharLineList[i].launchClicked.connect(self.__onLaunchClicked)

            if charCard:
                self.CharLineList[i].infoClicked.connect(self.__onInfoClicked)
        
                self.CharCardList[i].card.gotoClicked.connect(self.__onGotoClicked)
                self.CharCardList[i].card.deleteClicked.connect(self.__onDeleteClicked)

        self.addButton.clicked.connect(self.__onAddClicked)
        self.panelHelp.clicked.connect(self.__onShowInstruction)

    def __onLaunchClicked(self, petname):
        # Ignore if it's current char
        if settings.petname == petname:
            return
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
        if platform == 'win32':
            os.startfile(os.path.normpath(folder))
        elif platform == "darwin":
            subprocess.call(["open", os.path.normpath(folder)])
        else:
            # For Linux - not tested
            subprocess.call(["xdg-open", os.path.normpath(folder)])

    def __onDeleteClicked(self, cardIndex, folder):
        # Judge if it is current pet

        # Move file to trash bin

        # Remove char from settings.pet

        # Update basicSetting change pet

        # Delete character List and Card
        title = self.tr("Function incomplete")
        content = self.tr("The function has not been implemented yet.\nCurrently, you can Go To Folder, delete the whole folder, and restart App.\nSorry for the inconvenience.")
        #if not self.__showMessageBox(title, content):
        #    return
        yesText = self.tr("Go to Folder")
        if self.__showMessageBox(title, content, yesText):
            resFolder = os.path.join(basedir, 'res/role')

            if platform == 'win32':
                os.startfile(os.path.normpath(resFolder))
            elif platform == "darwin":
                subprocess.call(["open", os.path.normpath(resFolder)])
            else:
                # For Linux - not tested
                subprocess.call(["xdg-open", os.path.normpath(resFolder)])
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

        # Check files integrity
        statCode, errorList = CheckCharFiles(os.path.abspath(folder))
        if 0 < statCode < 7:
            self._send_CharImportResult(statCode, errorList)
            return
        elif statCode >=7:
            statCode -= 6
            self._send_itemImportResult(statCode, errorList)
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
        self.thread.start()

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
            card = CharCard(iCard, jsonPath=infoFile, petFolder=petFolder)
            self.CharCardList.append(card)

        self.CharLineList[iCard].launchClicked.connect(self.__onLaunchClicked)
        if os.path.exists(infoFile):
            self.CharLineList[iCard].infoClicked.connect(self.__onInfoClicked)
    
            self.CharCardList[iCard].card.gotoClicked.connect(self.__onGotoClicked)
            self.CharCardList[iCard].card.deleteClicked.connect(self.__onDeleteClicked)

        content = self.tr("Adding character completed! It's recommended to restart the App to have all features enabled.")
        self.__showSystemNote(content, 0)

        self.newPetFolder = None


    def _startStateTooltip(self):
        if self.stateTooltip:
            return
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
    
    def _send_itemImportResult(self, statCode, errorList):
        title = self.tr("Adding Failed")
        stat_notes = [self.tr("Success!"),
                      self.tr("items_config.json broken or not exist."),
                      self.tr("'image' key missing:"),
                      self.tr('The following items are missing image files:'),
                      self.tr("In the following items, 'pet_limit' is not a list:")]
        content = stat_notes[statCode]
        if errorList is not None:
            content += '\n' + ', '.join(errorList)

        self.__showMessageBox(title, content)
        return

    def __onShowInstruction(self):
        title = self.tr("Character Management Guide")
        content_1 = self.tr("""This panel shows all the characters you have so far.
You can switch to a char, or check the character information.

By clicking Add Characters, you can import a new one from the selected folder.
To find new characters, you can check our official collection by clicking the hyperlink button.

For most of time, App can import the character for you automatically. But in any case you want to add it manually:""")
        content_2 = self.tr("1. Prepare the character folder containing all files;\n2. Copy the folder to App resource folder (you can click 'Go to Folder' button);\n3. Close App and open again;\n4. You will see the character show up here;\n5. Click 'Launch' to start;\n6. If App crushed, it means the character file is problematic, please contact the author for help.")
        content = f"{content_1}\n{content_2}"
        if not self.__showMessageBox(title, content, cancelText=self.tr("Go to Folder")):
            resFolder = os.path.join(basedir, 'res/role')

            if platform == 'win32':
                os.startfile(os.path.normpath(resFolder))
            elif platform == "darwin":
                subprocess.call(["open", os.path.normpath(resFolder)])
            else:
                # For Linux - not tested
                subprocess.call(["xdg-open", os.path.normpath(resFolder)])
        else:
            return
        

    def __showMessageBox(self, title, content, yesText='OK', cancelText=None):

        WarrningMessage = MessageBox(title, content, self)
        if yesText == 'OK':
            WarrningMessage.yesButton.setText(self.tr('OK'))
        else:
            WarrningMessage.yesButton.setText(yesText)
        if cancelText:
            WarrningMessage.cancelButton.setText(cancelText)
        else:
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





def get_child_folder(parentFolder, relative=False):
    all_files_and_dirs = os.listdir(parentFolder)
    if relative:
        all_dirs = [os.path.basename(d) for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]
    else:
        all_dirs = [d for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]

    return all_dirs


class FileCopyThread(QThread):
    started = Signal()
    done = Signal(bool)

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
