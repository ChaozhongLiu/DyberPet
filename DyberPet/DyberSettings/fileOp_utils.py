import hashlib
import os

from PySide6.QtCore import QStandardPaths
from zipfile import *
from hashlib import *
from sys import platform
from shutil import copyfile, rmtree, copytree

from DyberPet.settings import *


SAVEFILES = ['settings.json', 'pet_data.json', 'version', 'task_data.json']


def CopySave(source_folder, target_folder):
    for filename in SAVEFILES:
        srcFile = os.path.join(source_folder, filename)
        dstFile = os.path.join(target_folder, filename)
        copyfile(srcFile, dstFile)

    status_code = checkFolderMD5(source_folder, target_folder)
    return status_code



# 验证文件MD5函数，保存（无论是否需要打包导出）与读取（无论是否从外部包读取）均需要
def checkFileMD5(targetFile):
    with open(targetFile, 'rb') as checkFile:
        fileContent = checkFile.read()
    targetMD5 = hashlib.md5(fileContent).hexdigest()
    return targetMD5



def checkFolderMD5(source_folder, target_folder):
    """Check and compare MD5 in source folder and target folder, return status code"""

    """
    return status
    0: success
    1: file lost
    2: MD5 check failed
    """

    for filename in SAVEFILES:
        sourceFile = os.path.join(source_folder, filename)
        sourceMD5 = checkFileMD5(targetFile=sourceFile)

        targetFile = os.path.join(target_folder, filename)
        if os.path.isfile(targetFile): # 若文件存在
            targetMD5 = checkFileMD5(targetFile=targetFile) # 获取存档文件的MD5
            if sourceMD5 == targetMD5: # 如果两个MD5一致，则检查通过
                print('检查通过')
            else:
                print('检测到MD5不一致')
                return 2
        else:
            return 1

    return 0

    '''
    for root, ds, fs in os.walk(dataPath):
        for i in fs:
            print(i)
            fileStructureSource = os.path.join(root, i) # 带目录结构的/data文件
            print(fileStructureSource)
            fileStructureSourceSE = fileStructureSource.replace(dataPath, '')
            sourceFileMD5 = checkMD5().checkFileMD5(targetFile=fileStructureSource) # 计算原文件的MD5
            filePathDst = docPath + '/DyberPet/Saves/' + saveSlot + '/data/' + i #获取存档文件的对应位置
            filePathDst = filePathDst.replace('\\', '/')
            filePathDst = filePathDst.replace('//', '/')
            print(filePathDst)
            if os.path.isfile(filePathDst): # 若文件存在
                targetDataFileMD5 = checkMD5().checkFileMD5(targetFile=filePathDst) # 获取存档文件的MD5
                if sourceFileMD5 == targetDataFileMD5: # 如果两个MD5一致，则检查通过
                    print('检查通过')
                else:
                    print('检测到MD5不一致')
                    return 2
            else:
                return 1
            print()
            return 0
    '''

def DeleteQuickSave(directory_path, keep=True):
    if keep:
        try:
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)  # remove file or symlink
                elif os.path.isdir(file_path):
                    rmtree(file_path)  # remove directory
        except:
            return 0

    else:
        try:
            rmtree(directory_path)
        except:
            return 0

    return 1





