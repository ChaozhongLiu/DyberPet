'''
By: Marcus
Created: 2023-03-15 03: 32 P.M.
Last Modified: 2023-03-25 04:58 P.M.
Function: This file helps the program to start automatically when booting
功能：开机自启
'''

import platform
import os
import json
from DyberPet.document_path import *
from PyQt5.QtCore import QSettings

self_startup_status = "off"
self_startup_application_path = ""

# 这个class是给Win32用的
class auto_start_for_win_32():
    def check_auto_start(self):
        # 此函数会检查开机自启是否启用，未启用返回0，启用则返回1
        # 如果此函数返回2，则代表DyberPet可能被移动或者修改
        auto_start_check = QSettings("HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", QSettings.NativeFormat)
        try:
            auto_start_status = auto_start_check.value("DyberPet")
            if auto_start_status == "":
                print("[INFO] Auto start disabled")
                return 0
            else:
                if auto_start_status != document_application_path:
                    print("[WARN] Auto start path incorrect")
                    return 2
                else:
                    print("[INFO] Auto start enabled")
                    return 1
        except:
            return 0

    def install_auto_start(self):
        # 注册
        auto_start_install = QSettings("HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", QSettings.NativeFormat)
        auto_start_install.setValue("DyberPet", document_application_path)

        # 检查自启是否安装成功，成功则返回1，反之则返回0
        auto_start_check_after_install = auto_start_for_win_32().check_auto_start()
        if auto_start_check_after_install == 1:
            return 1
        else:
            return 0

    def uninstall_auto_start(self):
        auto_start_uninstall = QSettings("HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", QSettings.NativeFormat)
        auto_start_uninstall.remove("DyberPet")

        # 检查自启是否安装成功，成功则返回1，反之则返回0
        auto_start_check_after_install = auto_start_for_win_32().check_auto_start()
        if auto_start_check_after_install == 0:
            return 1
        else:
            return 0