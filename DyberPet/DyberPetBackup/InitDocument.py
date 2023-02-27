'''
by: Marcus
created on: 2023-02-27 10:09 A.M.
last modified: 2023-02-27 10:42 A.M.
function: Setup document folder
功能：创建文档目录
'''
import os.path

from PyQt5.QtCore import QStandardPaths
from os import *

docDir = (QStandardPaths.locate(QStandardPaths.DocumentsLocation, '', QStandardPaths.LocateDirectory))
dyberPetTarget = docDir + '/DyberPet/'
dyberPetTarget = dyberPetTarget.replace('//', '/')
dyberPetTarget = dyberPetTarget.replace('\\', '/')
savesDir = dyberPetTarget + '/Saves/'
savesDir = savesDir.replace('//', '/')
savesDir = savesDir.replace('\\', '/')
saveSlot1Dir = savesDir + '/0/'
saveSlot1Dir = saveSlot1Dir.replace('//', '/')
saveSlot1Dir = saveSlot1Dir.replace('\\', '/')
saveSlot2Dir = savesDir + '/1/'
saveSlot2Dir = saveSlot2Dir.replace('//', '/')
saveSlot2Dir = saveSlot2Dir.replace('\\', '/')
saveSlot3Dir = savesDir + '/2/'
saveSlot3Dir = saveSlot3Dir.replace('//', '/')
saveSlot3Dir = saveSlot3Dir.replace('\\', '/')
autoSaveDir = savesDir + '/3/'
autoSaveDir = autoSaveDir.replace('//', '/')
autoSaveDir = autoSaveDir.replace('\\', '/')
saveSlot1DataDir = saveSlot1Dir + '/data/'
saveSlot1DataDir.replace('//', '/')
saveSlot1DataDir.replace('\\', '/')
saveSlot2DataDir = saveSlot2Dir + '/data/'
saveSlot2DataDir.replace('//', '/')
saveSlot2DataDir.replace('\\', '/')
saveSlot3DataDir = saveSlot3Dir + '/data/'
saveSlot3DataDir.replace('//', '/')
saveSlot3DataDir.replace('\\', '/')

class createSaveDocument():
    def configSavePath(self, targetFolder):
        if not os.path.exists(targetFolder):
            print('Checking ' + targetFolder + ' ..........Folder does not exist')
            os.makedirs(targetFolder)
            print('Successfully created ' + targetFolder)
        else:
            print('Checking ' + targetFolder + ' ..........Folder exist')

    def createSavePath(self):
        print('Document folder location: ' + docDir)
        createSaveDocument().configSavePath(targetFolder=dyberPetTarget)
        createSaveDocument().configSavePath(targetFolder=savesDir)
        createSaveDocument().configSavePath(targetFolder=saveSlot1Dir)
        createSaveDocument().configSavePath(targetFolder=saveSlot2Dir)
        createSaveDocument().configSavePath(targetFolder=saveSlot3Dir)
        createSaveDocument().configSavePath(targetFolder=saveSlot2Dir)
        createSaveDocument().configSavePath(targetFolder=autoSaveDir)
        createSaveDocument().configSavePath(targetFolder=saveSlot1DataDir)
        createSaveDocument().configSavePath(targetFolder=saveSlot2DataDir)
        createSaveDocument().configSavePath(targetFolder=saveSlot3DataDir)
        print('Your Folders are all ready.')