'''
by: Marcus
created on: 2023-02-24 09:50 A.M.
last modified: 2023-02-24 22:02 P.M.
function: Quick backup /data folder
功能：快速备份/data文件夹
'''

'''
return 信息
0: 进程成功完成
1: 丢失文件
2: MD5检查不通过
'''
import hashlib
import os

from PyQt5.QtCore import QStandardPaths
from zipfile import *
from hashlib import *
from sys import platform
from shutil import copyfile, rmtree, copytree

'''
# 定义了变量dataPath，指向程序所使用的data文件夹
if platform == 'win32':
    dataPath = os.path.abspath(os.path.join(os.getcwd(), ""))
    dataPath = dataPath.replace('\\', '/')
    dataPath = '/'.join(dataPath.split('/')[:-1])
    dataPath = dataPath + '/data/'
    print(dataPath)
else:
    dataPath = os.path.abspath(os.path.join(os.getcwd(), "../"))
    dataPath = dataPath.replace('\\', '/')
    dataPath = '/'.join(dataPath.split('/')[:-1])
    dataPath = dataPath + '/data/'
    print(dataPath)
'''
from DyberPet.settings import *
dataPath = newpath = os.path.join(basedir, 'data')
print (dataPath)

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

        # 对比文件并检查MD5，写得有点乱
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

class readData():
    # 快速读取：仅将备份覆盖到data，而不是从压缩文件获取，不验证MIME类型，验证备份文件是否存在，验证文件MD5 （待办，验证模块需要重构）
    # 和快速保存用的是一套代码，不过是路径反过来
    def quickRead(self, targetSlot):
        # 获取备份位置
        saveSlot = str(targetSlot - 1)
        slotDir = '/DyberPet/Saves/' + saveSlot + '/data'
        docPath = (QStandardPaths.locate(QStandardPaths.DocumentsLocation, '', QStandardPaths.LocateDirectory))
        saveSlotDir = docPath + '/DyberPet/Saves/' + saveSlot + '/'
        savePath = docPath + slotDir

        # 清空data
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)
        else:
            rmtree(dataPath)

        # 写入文件
        copytree(src=savePath, dst=dataPath)