'''
    by: Marcus
    created: 2023-02-19 17:16 P.M.
    last modified: 2023-02-19 18:19 P.M.

    description in Chinese: 此版本的呆啵宠物将会把数据储存到用户文档下的/DyberPet/，此class允许定位需要的资源或数据文件，并返回该文件的绝对路径
    description in English: This version of DyberPet will store data in /DyberPet/ under the user documentation, which allows locating the required resource or data file and returning the absolute path to the file.
'''

from PyQt5.QtCore import QObject, QStandardPaths

class getFile(QObject):

    def locateresources(self, str):
        filename = str
        transformedpath = '/DyberPet/res/' + filename
        targetfile = QStandardPaths.locate(QStandardPaths.DocumentsLocation, transformedpath)
        return targetfile

    def locatedata(self, str):
        filename = str
        transformedpath = '/DyberPet/data/' + filename
        targetfile = QStandardPaths.locate(QStandardPaths.DocumentsLocation, transformedpath)
        return targetfile
    def locateresourcesfolder(self, str):
        foldername = str
        transformedpath = '/DyberPet/res/' + foldername
        targetfolder = QStandardPaths.locate(QStandardPaths.DocumentsLocation, transformedpath, QStandardPaths.LocateDirectory)
        return targetfolder
    def locatedatafolder(self, str):
        foldername = str
        transformedpath = '/DyberPet/data/' + foldername
        targetfolder = QStandardPaths.locate(QStandardPaths.DocumentsLocation, transformedpath, QStandardPaths.LocateDirectory)
        return targetfolder