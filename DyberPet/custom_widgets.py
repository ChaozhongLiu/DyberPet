# coding:utf-8
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QPoint

class SystemTray(QSystemTrayIcon):
    def __init__(self, menu, parent=None):
        super(SystemTray, self).__init__(parent)

        # Set an icon for the tray
        self.setIcon(QIcon('path_to_your_icon.png'))

        # Set the provided menu for the tray
        self.setMenu(menu)

        # Connect the activated signal to our custom slot
        self.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Context:
            # Get the current position of the cursor
            cursor_pos = QApplication.desktop().cursor().pos()

            # Adjust the position. Here, we're moving it 100 pixels upward.
            new_pos = cursor_pos - QPoint(0, 200)
            self.contextMenu().popup(new_pos)

    def setMenu(self, menu):
        """ Set a new context menu for the tray """
        old_menu = self.contextMenu()
        if old_menu:
            old_menu.hide()
            old_menu.deleteLater()
            
        super().setContextMenu(menu)
