import sys
from sys import platform
import ctypes
from tendo import singleton
import os
from DyberPet.utils import read_json
from DyberPet.DyberPet import PetWidget
from DyberPet.Notification import DPNote
from DyberPet.Accessory import DPAccessory
<<<<<<< HEAD
# 导入LLM相关模块
from DyberPet.llm_client import LLMClient
from DyberPet.llm_request_manager import LLMRequestManager
=======
>>>>>>> a7bfd1e3b84a17ead63f7ec2c751b2d8f0325181

from PySide6.QtWidgets import QApplication
from PySide6 import QtCore
from PySide6.QtCore import Qt, QLocale, QTimer, QDateTime, QDate, Signal, QTime

from qfluentwidgets import  FluentTranslator, setThemeColor
from DyberPet.DyberSettings.DyberControlPanel import ControlMainWindow
from DyberPet.Dashboard.DashboardUI import DashboardMainWindow

try:
    size_factor = 1 #ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
except:
    size_factor = 1

import DyberPet.settings as settings


# For translation:
# pylupdate5 langs.pro
# lrelease langs.zh_CN.ts

# For .exe:
# Now we use pyinstaller 6.5.0
# pyinstaller --noconsole --icon="000.ico" --hidden-import="pynput.mouse._win32" --hidden-import="pynput.keyboard._win32" run_DyberPet.py

# For Mac:
# pyinstaller --windowed --icon 000.icns --add-data="res:res" --add-data="DyberPet:DyberPet" --hidden-import="pynput.mouse._darwin" --hidden-import="pynput.keyboard._darwin" run_DyberPet.py


class DyberPetApp(QApplication):
    date_changed = Signal(QDate)

    def __init__(self, *args, **kwargs):
        super(DyberPetApp, self).__init__(*args, **kwargs)

        self.setQuitOnLastWindowClosed(False)
        screens = self.screens()
        primary_screen = self.primaryScreen()

        if primary_screen in screens:
            screens.insert(0, screens.pop(screens.index(primary_screen)))
        else:
            screens.insert(0, primary_screen)

        # internationalization
        fluentTranslator = FluentTranslator(QLocale(settings.language_code))
        self.installTranslator(fluentTranslator)
        self.installTranslator(settings.translator)
        if settings.themeColor:
            setThemeColor(settings.themeColor)
        
<<<<<<< HEAD
        # Pet Object
        self.p = PetWidget(screens=screens)

                # 初始化LLM客户端和请求管理器（如果启用）
        if settings.llm_config.get('enabled', False):
            print("LLM enabled")
            
            self.llm_client = LLMClient()
            self.p.setup_llm_client(self.llm_client)
            self.request_manager = self.p.request_manager
        else:
            print("LLM disabled")
            self.llm_client = None
            self.request_manager = None
        
        # 如果启用了LLM，将客户端和请求管理器连接到宠物对象
        # if self.llm_client and self.request_manager:
        #     print("LLM Client and Request Manager initialized.")
        #     self.p.llm_client = self.llm_client
        #     self.p.request_manager = self.request_manager
        # # 连接信号
        # self.llm_client.structured_response_ready.connect(self.p.handle_llm_response)
        # self.llm_client.error_occurred.connect(self.p.handle_llm_error)

=======

        # Pet Object
        self.p = PetWidget(screens=screens)

>>>>>>> a7bfd1e3b84a17ead63f7ec2c751b2d8f0325181
        # Notification System
        self.note = DPNote()

        # Accessory System
        self.acc = DPAccessory()

        # System Panel
        self.conp = ControlMainWindow()

        # Dashboard
        self.board = DashboardMainWindow()
<<<<<<< HEAD
        self.p.set_dashboard(self.board)
=======
>>>>>>> a7bfd1e3b84a17ead63f7ec2c751b2d8f0325181

        # Midnight Timer
        self.current_date = QDate.currentDate()
        self.set_midnight_timer()

        # Signal Links
        self.__connectSignalToSlot()

    def __connectSignalToSlot(self):
        # Main Widget - others
        self.p.setup_notification.connect(self.note.setup_notification)
        self.p.setup_bubbleText.connect(self.note.setup_bubbleText)
        self.p.change_note.connect(self.note.change_pet)
        self.p.change_note.connect(self.conp.charCardInterface._finishStateTooltip)
        self.p.close_bubble.connect(self.note.close_bubble)
        self.p.hptier_changed_main_note.connect(self.note.hpchange_note)
        self.p.fvlvl_changed_main_note.connect(self.note.fvchange_note)
        self.p.setup_acc.connect(self.acc.setup_accessory)
        self.p.move_sig.connect(self.acc.send_main_movement)
        self.p.move_sig.connect(self.note.send_main_movement)
        self.p.close_all_accs.connect(self.acc.closeAll)

        # System Widgets - others
        self.conp.settingInterface.ontop_changed.connect(self.acc.ontop_changed)
        self.conp.settingInterface.scale_changed.connect(self.acc.reset_size_sig)

        self.conp.settingInterface.ontop_changed.connect(self.p.ontop_update)
        self.conp.settingInterface.scale_changed.connect(self.p.reset_size)
        self.conp.settingInterface.lang_changed.connect(self.p.lang_changed)
        self.p.change_note.connect(self.conp.settingInterface._update_scale)

        self.conp.charCardInterface.change_pet.connect(self.p._change_pet)
        self.p.show_controlPanel.connect(self.conp.show_window)

        self.conp.gamesaveInterface.refresh_pet.connect(self.p.refresh_pet)

        # Dashboard - others
        self.p.show_dashboard.connect(self.board.show_window)
        self.note.noteToLog.connect(self.board.statusInterface._addNote)
        self.p.hp_updated.connect(self.board.statusInterface.StatusCard._updateHP)
        self.p.fv_updated.connect(self.board.statusInterface.StatusCard._updateFV)
        self.p.change_note.connect(self.board.statusInterface._changePet)
        self.board.statusInterface.changeStatus.connect(self.p._change_status)
        self.p.stopAllThread.connect(self.board.statusInterface.stopBuffThread)

        self.acc.acc_withdrawed.connect(self.board.backpackInterface.acc_withdrawed)
        self.board.backpackInterface.use_item_inven.connect(self.p.use_item)
        self.board.backpackInterface.item_note.connect(self.p.register_notification)
        self.board.backpackInterface.item_drop.connect(self.p.item_drop_anim)
        self.p.fvlvl_changed_main_inve.connect(self.board.backpackInterface.fvchange)
        self.p.fvlvl_changed_main_inve.connect(self.board.shopInterface.fvchange)
        self.p.addItem_toInven.connect(self.board.backpackInterface.add_items)
        self.p.compensate_rewards.connect(self.board.backpackInterface.compensate_rewards)
        self.p.refresh_bag.connect(self.board.backpackInterface.refresh_bag)
        self.p.autofeed.connect(self.board.backpackInterface.autofeed)
        self.p.refresh_bag.connect(self.board.shopInterface.refresh_shop)
        self.p.addCoins.connect(self.board.backpackInterface.addCoins)

        # Tasks and Timer
        self.board.taskInterface.focusPanel.start_pomodoro.connect(self.p.run_tomato)
        self.board.taskInterface.focusPanel.cancel_pomodoro.connect(self.p.cancel_tomato)
        self.board.taskInterface.focusPanel.start_focus.connect(self.p.run_focus)
        self.board.taskInterface.focusPanel.cancel_focus.connect(self.p.cancel_focus)
        self.p.taskUI_Timer_update.connect(self.board.taskInterface.focusPanel.update_Timer)
        self.p.taskUI_task_end.connect(self.board.taskInterface.focusPanel.taskFinished)
        self.p.single_pomo_done.connect(self.board.taskInterface.focusPanel.single_pomo_done)

        # Animation Panel
        self.board.animInterface.animatPanel.updateList.connect(self.p.updateList)
        self.board.animInterface.animatPanel.playAct.connect(self.p._show_act)
        self.p.refresh_acts.connect(self.board.animInterface.animatPanel.updateAct)
        self.p.refresh_acts.connect(self.board.animInterface.updateDesignUI)
        self.board.animInterface.loadNewAct.connect(self.p._addNewAct)
        self.board.animInterface.deletewAct.connect(self.p._deleteAct)

        # Midnight Trigger
        self.date_changed.connect(self.p._mightEventTrigger)
    
    def set_midnight_timer(self):
        now = QDateTime.currentDateTime()
        midnight = QDateTime(QDate.currentDate().addDays(1), QTime(0, 0, 0))  # Next midnight
        msecs_until_midnight = now.msecsTo(midnight)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.check_date)
        self.timer.start(msecs_until_midnight)
    
    def check_date(self):
        new_date = QDate.currentDate()
        if new_date != self.current_date:
            self.current_date = new_date
            self.date_changed.emit(new_date)
        self.set_midnight_timer()  # Reset the timer for the next midnight


        


if platform == 'win32':
    basedir = ''
else:
    basedir = os.path.dirname(__file__)

if __name__ == '__main__':

    # Avoid multiple process
    try:
        me = singleton.SingleInstance()
    except:
        sys.exit()


    # Create App
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    #QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    #QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = DyberPetApp(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    sys.exit(app.exec())


