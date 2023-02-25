'''
by: Marcus
created on: 2023-02-24 09:50 A.M.
last modified: 2023-02-24 09:50 A.M.
function: Quick backup /data folder
功能：快速备份/data文件夹
'''

import hashlib
import os

from PyQt5.QtCore import QStandardPaths
from zipfile import *
from hashlib import *
from sys import platform
from shutil import copyfile, rmtree, copytree

# 定义了变量dataPath，指向程序所使用的data文件夹
if platform == 'win32':
    basedir = ''
else:
    #from pathlib import Path
    basedir = os.path.dirname(__file__) #Path(os.path.dirname(__file__))
    #basedir = basedir.parent
    basedir = basedir.replace('\\','/')
    basedir = '/'.join(basedir.split('/')[:-1])

dataPath = os.path.join(basedir, 'data')
print(dataPath)

# 验证文件MD5函数，保存（无论是否需要打包导出）与读取（无论是否从外部包读取）均需要
class checkMD5():
    def checkFileMD5(self, targetFile):
        with open(targetFile, 'rb') as checkFile:
            fileContent = checkFile.read()
        targetMD5 = hashlib.md5(fileContent).hexdigest()
        return targetMD5

class saveData():
    # 快速保存：仅将data备份到特定位置，不将data打包为压缩包，不验证MIME类型，验证备份文件是否存在，验证文件MD5
    def quickSave(self, targetSlot):
        # 清空保存槽位（覆写）
        saveSlot = str(targetSlot - 1)
        slotDir = '/DyberPet/Saves/' + saveSlot + '/data'
        docPath = (QStandardPaths.locate(QStandardPaths.DocumentsLocation, '', QStandardPaths.LocateDirectory))
        savePath = docPath + slotDir
        if not os.path.exists(savePath):
            os.makedirs(savePath)
        else:
            rmtree(savePath)

        # 写入文件
        copytree(src=dataPath, dst=savePath)

        # 对比文件并检查MD5，写的有点乱
        for root, ds, fs in os.walk(dataPath):
            for i in fs:
                fileStructureSource = os.path.join(root, i) # 带目录结构的/data文件
                sourceFileMD5 = checkMD5().checkFileMD5(targetFile=fileStructureSource) # 计算原文件的MD5
                filePathDst = docPath + '/DyberPet/Saves/' + saveSlot + '/' + fileStructureSource #获取存档文件的对应位置
                filePathDst = filePathDst.replace('\\', '/')
                filePathDst = filePathDst.replace('//', '/')
                if os.path.isfile(filePathDst): # 若文件存在
                    targetDataFileMD5 = checkMD5().checkFileMD5(targetFile=filePathDst) # 获取存档文件的MD5
                    if sourceFileMD5 == targetDataFileMD5: # 如果两个MD5一致，则检查通过
                        print('检查通过')
                    else:
                        print('检测到MD5不一致')
                        break
                else:
                    break
