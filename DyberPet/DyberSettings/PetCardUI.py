#coding:utf-8
import os
import json
from datetime import datetime
from shutil import copytree
import subprocess

from qfluentwidgets import (ScrollArea, ExpandLayout, InfoBar,
                            PushButton, MessageBox,
                            InfoBarPosition, HyperlinkButton, PushButton, setFont,
                            StateToolTip, TransparentPushButton)

from qfluentwidgets import FluentIcon as FIF

from PySide6.QtCore import Qt, QThread, Signal, QUrl, QStandardPaths, QLocale, QPoint
from PySide6.QtGui import QDesktopServices, QIcon, QFont
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QFileDialog

from .custom_utils import CharCard, CharCardGroup, CharLine
from DyberPet.conf import CheckCharFiles
import DyberPet.settings as settings
from DyberPet.utils import get_file_time

from sys import platform

basedir = settings.BASEDIR
module_path = os.path.join(basedir, 'DyberPet/DyberSettings/')


class PetInterface(ScrollArea):
    """ SubPet Management interface """

    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("PetInterface")
        self.newPetFolder = None
        self.thread = None
        self.stateTooltip = None
        self.launchTooltip = None
        self.sizeHintDyber = (sizeHintDyber[0]-100, sizeHintDyber[1])

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Mini-Pet Management"), self)
        # HyperLink to pet collection (website not implemented yet)
        self.CharListLink = HyperlinkButton(
                                            settings.PETCOLLECT_LINK, 
                                            self.tr('Collected Mini-Pets'), 
                                            self, FIF.LINK)
        # Button to add chars from local file
        self.addButton = PushButton(self.tr("Add Mini-Pets"), self, FIF.ADD)

        # Button to show instructions on how to manually add chars
        self.instructButton = TransparentPushButton(self.tr("Add Manually"), self, FIF.QUESTION)
        

        self.__initCardLayout()

        self.__initWidget()

    def __initCardLayout(self):

        self.PetCardGroup = CharCardGroup(
            self.tr("Mini-Pets"), self.sizeHintDyber, self.scrollWidget)

        self.PetCardList = []
        self.PetLineList = []
        petlist = get_child_folder(os.path.join(basedir,'res/pet'), relative=False)
        fileTimes = [get_file_time(pet) for pet in petlist]
        paired_list = zip(fileTimes, petlist)
        sorted_pairs = sorted(paired_list)
        sorted_petlist = [os.path.basename(element) for _, element in sorted_pairs]

        for i, pet in enumerate(sorted_petlist):
            
            infoLine = CharLine(i, chrFolder=pet, parentDir='pet', parent=self.PetCardGroup)
            self.PetCardGroup.addInfoCard(infoLine)
            self.PetLineList.append(infoLine)
            
            
            infoFile = os.path.join(basedir,"res/pet", pet, "info/info.json")
            if not os.path.exists(infoFile):
                self.PetCardList.append(None)
            else:
                card = CharCard(i, jsonPath=infoFile, petFolder=pet, parentDir='pet')
                self.PetCardList.append(card)



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
        
        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        #self.expandLayout.addWidget(self.TransferSaveGroup)
        self.expandLayout.addWidget(self.PetCardGroup)
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
        
        for i, charCard in enumerate(self.PetCardList):

            if charCard:
                self.PetLineList[i].infoClicked.connect(self.__onInfoClicked)
        
                self.PetCardList[i].card.gotoClicked.connect(self.__onGotoClicked)
                self.PetCardList[i].card.deleteClicked.connect(self.__onDeleteClicked)

        self.addButton.clicked.connect(self.__onAddClicked)
        self.instructButton.clicked.connect(self.__onShowInstruction)

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
        content = self.tr("""The function has not been implemented yet.
Currently, you can Go To Folder, delete the pet's folder, and restart App.
Sorry for the inconvenience.""")
        #if not self.__showMessageBox(title, content):
        #    return
        yesText = self.tr("Go to Folder")
        if self.__showMessageBox(title, content, yesText):
            resFolder = os.path.join(basedir, 'res/pet')

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
        if self.PetCardList[cardIndex].isVisible():
            self.PetCardList[cardIndex].hide()
        else:
            self.PetCardList[cardIndex].move(pos)
            self.PetCardList[cardIndex].show()

    def __onAddClicked(self):
        # Confirm
        title = self.tr("Adding Mini-Pet")
        content = self.tr("You are about to import a Mini-Pet from a local file. Please be aware that it is from third-party sources. We are not responsible for any potential harm or issues that may arise from using this mini-pet. Only proceed if you trust the source.")
        if not self.__showMessageBox(title, content):
            return

        # FileDialogue to select folder
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Please select the pet folder"), 
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
            return

        # Copy file to res/pet
        petFolder = os.path.basename(folder)
        destinationFolder = os.path.join(basedir, 'res/pet', petFolder)
        #status = 
        # Check if char with the same name exist
        if os.path.exists(destinationFolder):
            content = self.tr("There is already a Mini-Pet with the same name added.")
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


    def __onAddClickedContinue(self):

        # Add pet in settings.pet
        petFolder = self.newPetFolder

        # Add character List and Card
        iCard = len(self.PetLineList)
        infoLine = CharLine(iCard, chrFolder=petFolder, parentDir='pet', parent=self.PetCardGroup)
        self.PetCardGroup.addInfoCard(infoLine)
        self.PetLineList.append(infoLine)
        
        infoFile = os.path.join(basedir,"res/pet", petFolder, "info/info.json")
        if not os.path.exists(infoFile):
            self.PetCardList.append(None)
        else:
            card = CharCard(iCard, jsonPath=infoFile, parentDir='pet', petFolder=petFolder)
            self.PetCardList.append(card)

        if os.path.exists(infoFile):
            self.PetLineList[iCard].infoClicked.connect(self.__onInfoClicked)
            self.PetCardList[iCard].card.gotoClicked.connect(self.__onGotoClicked)
            self.PetCardList[iCard].card.deleteClicked.connect(self.__onDeleteClicked)

        content = self.tr("Adding Mini-Pet completed! You need to restart the App to have the Mini-Pet enabled.")
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
    

    def __onShowInstruction(self):
        title = self.tr("Add Mini-Pet Manually")
        content = self.tr("""1. Prepare/download the Mini-Pet folder containing all files
2. Copy the folder to App resource folder (you can click 'Go to Folder' button);
3. Close App and open again;
4. You will see the Mini-Pet show up here;
5. If App crushed when calling the Mini-Pet, it means the source file is problematic, please contact the author for help.""")
        yesText = self.tr("Go to Folder")
        if self.__showMessageBox(title, content, yesText):
            resFolder = os.path.join(basedir, 'res/pet')

            if platform == 'win32':
                os.startfile(os.path.normpath(resFolder))
            elif platform == "darwin":
                subprocess.call(["open", os.path.normpath(resFolder)])
            else:
                # For Linux - not tested
                subprocess.call(["xdg-open", os.path.normpath(resFolder)])
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





def get_child_folder(parentFolder, relative=False):
    all_files_and_dirs = os.listdir(parentFolder)
    if relative:
        all_dirs = [os.path.basename(d) for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]
    else:
        all_dirs = [os.path.join(parentFolder,d) for d in all_files_and_dirs if os.path.isdir(os.path.join(parentFolder, d))]

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
