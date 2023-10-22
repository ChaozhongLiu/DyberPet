#coding:utf-8
import os
import json
from datetime import datetime
from shutil import copytree

from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup, InfoBar, FlowLayout,
                            PushSettingCard, PushButton, RoundMenu, Action, MessageBox,
                            InfoBarPosition, HyperlinkButton, ToolButton, PushButton, setFont,
                            StateToolTip, TransparentPushButton)

from qfluentwidgets import FluentIcon as FIF

from PySide6.QtCore import Qt, QThread, Signal, QUrl, QStandardPaths, QLocale, QPoint
from PySide6.QtGui import QDesktopServices, QIcon, QFont
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QFileDialog

from .custom_utils import CharCard, CharCardGroup, ItemLine, ItemCard
from DyberPet.conf import checkItemMOD
import DyberPet.settings as settings
from DyberPet.utils import get_file_time

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


class ItemInterface(ScrollArea):
    """ Item Mode Management Interface """

    def __init__(self, sizeHintDyber, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ItemInterface")
        self.newItemFolder = None
        self.thread = None
        self.stateTooltip = None

        self.sizeHintDyber = (sizeHintDyber[0]-100, sizeHintDyber[1])

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Item MOD"), self)
        # HyperLink to character collection (website not implemented yet)
        self.ItemListLink = HyperlinkButton(
                                            settings.ITEMCOLLECT_LINK, 
                                            self.tr('Collected Item MOD'), 
                                            self, FIF.LINK)
        # Button to add chars from local file
        self.addButton = PushButton(self.tr("Add Items"), self, FIF.ADD)

        # Button to show instructions on how to manually add chars
        self.instructButton = TransparentPushButton(self.tr("Add Items Manually"), self, FIF.QUESTION)
        

        self.__initCardLayout()

        self.__initWidget()

    def __initCardLayout(self):

        self.ItemCardGroup = CharCardGroup(
            self.tr("Items"), self.sizeHintDyber, self.scrollWidget)

        self.ItemLineList = []
        self.ItemCardList = []
        
        itemMods = get_child_folder(os.path.join(basedir,'res/items'), relative=False)
        modTimes = [get_file_time(mod) for mod in itemMods]
        modNameDict = {modTimes[i]:itemMods[i] for i in range(len(modTimes))}
        modTimes.sort()

        #for i, itemFolder in enumerate(itemMods):
        for i, modTime in enumerate(modTimes):
            itemFolder = modNameDict[modTime]

            if not os.path.exists(os.path.join(itemFolder, 'items_config.json')):
                continue
            
            infoLine = ItemLine(i, itemFolder=itemFolder, parent=self.ItemCardGroup)
            self.ItemCardGroup.addInfoCard(infoLine)
            self.ItemLineList.append(infoLine)
            
            
            infoFile = os.path.join(itemFolder, "info.json")
            if not os.path.exists(infoFile):
                self.ItemCardList.append(None)
            else:
                # Check items
                stat, errorList = checkItemMOD(itemFolder)
                if not stat:
                    card = ItemCard(i, itemFolder=itemFolder) #, parent=self.CharCardGroup)
                    self.ItemCardList.append(card)
                else:
                    self.ItemCardList.append(None)


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
        self.ItemListLink.move(200, 75)
        self.instructButton.move(450,75)
        
        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        #self.expandLayout.addWidget(self.TransferSaveGroup)
        self.expandLayout.addWidget(self.ItemCardGroup)
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
        
        for i, itemCard in enumerate(self.ItemCardList):
            self.ItemLineList[i].deleteClicked.connect(self.__onDeleteClicked)

            if itemCard:
                self.ItemLineList[i].infoClicked.connect(self.__onInfoClicked)
        
                #self.CharCardList[i].card.gotoClicked.connect(self.__onGotoClicked)
                #self.CharCardList[i].card.deleteClicked.connect(self.__onDeleteClicked)

        self.addButton.clicked.connect(self.__onAddClicked)
        self.instructButton.clicked.connect(self.__onShowInstruction)

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
            self.__onGotoClicked(folder)
            #resFolder = os.path.join(basedir, 'res/role')
            #os.startfile(os.path.normpath(resFolder))
        else:
            return

    def __onInfoClicked(self, cardIndex, pos):
        if self.ItemCardList[cardIndex].isVisible():
            self.ItemCardList[cardIndex].hide()
        else:
            self.ItemCardList[cardIndex].move(pos)
            self.ItemCardList[cardIndex].show()


    def __onAddClicked(self):
        # Confirm
        title = self.tr("Adding Item MOD")
        content = self.tr("You are about to import a item MOD from a local file. Please be aware that it is from third-party sources. We are not responsible for any potential harm or issues that may arise from using this MOD. Only proceed if you trust the source.")
        if not self.__showMessageBox(title, content):
            return

        # FileDialogue to select folder
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Please select the MOD folder"), 
            QStandardPaths.locate(QStandardPaths.DocumentsLocation, '', QStandardPaths.LocateDirectory))

        # If no file selected
        if not folder:
            return
        else:
            print(folder)
            #return

        # Check files integrity
        statCode, errorList = checkItemMOD(os.path.abspath(folder))
        if statCode:
            self._send_itemImportResult(statCode, errorList)
            return

        # Copy file to res/role
        itemFolder = os.path.basename(folder)
        destinationFolder = os.path.join(basedir, 'res/items', itemFolder)
        #status = 
        # Check if char with the same name exist
        if os.path.exists(destinationFolder):
            content = self.tr("There is already a MOD with the same folder name.")
            self.__showSystemNote(content, 2)
            return 0
        self.newItemFolder = itemFolder
        self._importItem(folder, destinationFolder)
        #if not status:
        #    return
        #return


    def _importItem(self, sourceFolder, destinationFolder):

        # Copy folders
        self.thread = FileCopyThread(sourceFolder, destinationFolder)
        self.thread.started.connect(self._startStateTooltip)
        self.thread.done.connect(self._stopStateTooltip)
        #self.thread.done.connect(self.__onAddClickedContinue)
        self.thread.start()


    def __onAddClickedContinue(self):

        # Add items to item system - not implemented yet
        itemFolder = self.newItemFolder

        # Add character List and Card
        iCard = len(self.ItemLineList)
        infoLine = ItemLine(iCard, itemFolder=itemFolder, parent=self.ItemCardGroup)
        self.ItemCardGroup.addInfoCard(infoLine)
        self.ItemLineList.append(infoLine)
        
        infoFile = os.path.join(itemFolder, "info.json")
        if not os.path.exists(infoFile):
            self.ItemCardList.append(None)
        else:
            card = ItemCard(iCard, itemFolder=itemFolder) #, parent=self.CharCardGroup)
            self.itemCardList.append(card)

        self.ItemLineList[iCard].deleteClicked.connect(self.__onDeleteClicked)
        if os.path.exists(infoFile):
            self.ItemLineList[iCard].infoClicked.connect(self.__onInfoClicked)

        content = self.tr("Adding item MOD completed! Please restart App to apply MOD.")
        self.__showSystemNote(content, 0)

        self.newItemFolder = None


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
            self.newItemFolder = None
        
        self._terminateThread()

    def _terminateThread(self):
        if self.thread:
            self.thread.quit()  # Terminate the thread
            self.thread.wait()  # Wait until it's fully terminated
            self.thread = None 



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
        title = self.tr("Add Item MOD Manually")
        content = self.tr("1. Prepare the MOD folder containing all files;\n2. Copy the folder to App resource folder (you can click 'Go to Folder' button);\n3. Close App and open again;\n4. You will see the MOD show up here;\n *If the MOD not shown or App crushed, it means the MOD file has unexpected error, please contact the author for help.")
        yesText = self.tr("Go to Folder")
        if self.__showMessageBox(title, content, yesText):
            resFolder = os.path.join(basedir, 'res/items')
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
