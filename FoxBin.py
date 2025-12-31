import winshell, json, os, sys, ctypes, winreg
from ctypes import windll, wintypes
from send2trash import send2trash
from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QFileDialog, QVBoxLayout, QPushButton, QCheckBox, QComboBox, QLabel, QDialog, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QIcon, QPixmap

def sysThemeIsDark():
    registry = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
    value, _ = winreg.QueryValueEx(registry, "AppsUseLightTheme")
    return value == 0

def translatable(key:str):
    try: 
        return translation[key]
    except: 
        return key

class BinInfo(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('i64Size', ctypes.c_longlong),
        ('i64NumItems', ctypes.c_longlong),
    ]

class SettingsDialog(QDialog):
    def __init__(self, tray):
        super().__init__()
        self.tray = tray
        self.setWindowTitle(translatable("settings.title"))
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(350, 300)
        
        layout = QVBoxLayout()
        
        self.startup_checkbox = QCheckBox(translatable("element.add_startup"))
        self.startup_checkbox.setChecked(tray.isInStartup(settings["app_name"]))
        self.startup_checkbox.stateChanged.connect(self.toggleStartup)
        layout.addWidget(self.startup_checkbox)
        
        layout.addWidget(QLabel(translatable("element.lang_menu")))
        self.lang_combo = QComboBox()
        self.languages = {
            "Русский": "./lang/ru.json",
            "Беларусская": "./lang/be.json",
            "English": "./lang/en.json",
            "Français": "./lang/fr.json",
            "Deutsche": "./lang/de.json",
            "Español": "./lang/es.json",
            "Português": "./lang/pt.json",
            "Polski": "./lang/pl.json",
            "Italiano": "./lang/it.json",
            "中文": "./lang/zh.json",
            "日本語": "./lang/ja.json",
            "한국어": "./lang/ko.json"
        }
        
        current_lang_path = settings["lang"]
        current_lang_name = "English"
        for name, path in self.languages.items():
            self.lang_combo.addItem(name)
            if path == current_lang_path:
                current_lang_name = name
        
        self.lang_combo.setCurrentText(current_lang_name)
        self.lang_combo.currentTextChanged.connect(self.changeLangFromCombo)
        layout.addWidget(self.lang_combo)
        
        icon_empty_layout = QHBoxLayout()
        self.icon_empty_label = QLabel(translatable("settings.icon_empty"))
        icon_empty_layout.addWidget(self.icon_empty_label)
        
        self.icon_empty_preview = QLabel()
        self.icon_empty_preview.setFixedSize(30, 30)
        self.icon_empty_preview.setStyleSheet("background-color: #333333; border: 1px solid #555555; padding: 2px; border-radius: 4px;")
        icon_empty_layout.addWidget(self.icon_empty_preview)
        icon_empty_layout.addStretch()
        
        layout.addLayout(icon_empty_layout)
        
        icon_empty_buttons_layout = QHBoxLayout()
        self.btn_change_empty = QPushButton(translatable("element.change_icon"))
        self.btn_change_empty.clicked.connect(lambda: self.changeIcon("empty"))
        icon_empty_buttons_layout.addWidget(self.btn_change_empty)
        self.btn_reset_empty = QPushButton(translatable("element.reset_icon"))
        self.btn_reset_empty.clicked.connect(lambda: self.resetIcon("empty"))
        icon_empty_buttons_layout.addWidget(self.btn_reset_empty)
        layout.addLayout(icon_empty_buttons_layout)
        
        icon_full_layout = QHBoxLayout()
        self.icon_full_label = QLabel(translatable("settings.icon_full"))
        icon_full_layout.addWidget(self.icon_full_label)
        
        self.icon_full_preview = QLabel()
        self.icon_full_preview.setFixedSize(30, 30)
        self.icon_full_preview.setStyleSheet("background-color: #333333; border: 1px solid #555555; padding: 2px; border-radius: 4px;")
        icon_full_layout.addWidget(self.icon_full_preview)
        icon_full_layout.addStretch()
        
        layout.addLayout(icon_full_layout)
        
        icon_full_buttons_layout = QHBoxLayout()
        self.btn_change_full = QPushButton(translatable("element.change_icon"))
        self.btn_change_full.clicked.connect(lambda: self.changeIcon("full"))
        icon_full_buttons_layout.addWidget(self.btn_change_full)
        self.btn_reset_full = QPushButton(translatable("element.reset_icon"))
        self.btn_reset_full.clicked.connect(lambda: self.resetIcon("full"))
        icon_full_buttons_layout.addWidget(self.btn_reset_full)
        layout.addLayout(icon_full_buttons_layout)
        
        btn_close = QPushButton(translatable("element.close_settings"))
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog{background-color:#252525;color:#FFF}
            QLabel{color:#FFF;padding:5px}
            QCheckBox{color:#FFF;padding:5px}
            QComboBox{background-color:#333;color:#FFF;border:1px solid #555;padding:6px;border-radius:3px}
            QPushButton{background-color:#333;color:#FFF;border:1px solid #555;padding:6px;border-radius:3px;margin:2px}
            QPushButton:hover{background-color:#444}
        """)
        
        self.updateIconPreview("empty")
        self.updateIconPreview("full")
    
    def updateIconPreview(self, icon_type):
        icon_path = settings.get("icon_empty", "./assets/white_empty.ico") if icon_type == "empty" else settings.get("icon_full", "./assets/white_full.ico")
        preview_label = self.icon_empty_preview if icon_type == "empty" else self.icon_full_preview
        
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                preview_label.setPixmap(pixmap)
                preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                preview_label.clear()
        else:
            preview_label.clear()
    
    def toggleStartup(self, state):
        if state:
            self.tray.addToStartup(settings["app_name"])
            self.startup_checkbox.setText(translatable("element.remove_startup"))
        else:
            self.tray.removeFromStartup(settings["app_name"])
            self.startup_checkbox.setText(translatable("element.add_startup"))
    
    def changeLangFromCombo(self, lang_name):
        lang_path = self.languages.get(lang_name)
        if lang_path:
            self.tray.setLang(lang_path)
    
    def changeIcon(self, icon_type):
        file, _ = QFileDialog.getOpenFileName(self, translatable("filedialog.title"), "", "Images (*.png; *.jpg; *.jpeg; *.ico)")
        if file:
            settings["icon_empty" if icon_type == "empty" else "icon_full"] = file
            with open("./settings.json", "w") as f:
                json.dump(settings, f)
            self.tray.updateIcon()
            self.updateIconPreview(icon_type)
    
    def resetIcon(self, icon_type):
        settings["icon_empty" if icon_type == "empty" else "icon_full"] = "./assets/white_empty.ico" if icon_type == "empty" else "./assets/white_full.ico"
        with open("./settings.json", "w") as f:
            json.dump(settings, f)
        self.tray.updateIcon()
        self.updateIconPreview(icon_type)
    
    def closeEvent(self, event):
        self.hide()
        event.ignore()

class TrashTrayIcon(QSystemTrayIcon):
    def __init__(self, icon):
        super().__init__(icon)
        
        self.activated.connect(self.onTrayActivated)
        
        self.menu = QMenu()
        self.menu.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.menu.setStyleSheet("""
            QMenu{background-color:#252525;border:1px solid #555;padding:1px;border-radius:5px}
            QMenu::item{background-color:transparent;padding:6px 30px 6px 25px;margin:1px;color:#FFF}
            QMenu::item:selected{background-color:#333;color:#FFF}
            QMenu::item:disabled{color:#808080}
            QMenu::separator{height:1px;background-color:#C0C0C0;margin:3px 8px}
            QMenu::icon{margin-left:3px}
            QMenu::right-arrow{image:none;margin-right:3px}
        """)
        
        self.open_bin = self.menu.addAction(translatable("element.open"))
        self.open_bin.triggered.connect(self.openRecycleBin)
        self.clear_bin = self.menu.addAction(translatable("element.clear"))
        self.clear_bin.triggered.connect(self.clearBin)
        self.menu.addSeparator()
        self.settings_action = self.menu.addAction(translatable("element.settings"))
        self.settings_action.triggered.connect(self.openSettings)
        self.menu.addSeparator()
        self.exit_action = self.menu.addAction(translatable("element.close"))
        self.exit_action.triggered.connect(self.exitApp)
        
        self.tooltip_timer = QTimer()
        self.tooltip_timer.timeout.connect(self.formatTooltip)
        self.tooltip_timer.start(500)
        
        self.icon_timer = QTimer()
        self.icon_timer.timeout.connect(self.updateIcon)
        self.icon_timer.start(500)
        
        self.theme_timer = QTimer()
        self.theme_timer.timeout.connect(self.setIconTheme)
        self.theme_timer.start(5000)
        
        self.settings_dialog = None
        self.setContextMenu(self.menu)
    
    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.openRecycleBin()
    
    def openRecycleBin(self):
        try:
            os.startfile("shell:RecycleBinFolder")
        except:
            try:
                os.system('explorer shell:RecycleBinFolder')
            except:
                os.system('start shell:RecycleBinFolder')
    
    def exitApp(self):
        if self.settings_dialog:
            self.settings_dialog.close()
        QApplication.quit()
    
    def openSettings(self):
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        
        if self.settings_dialog.isHidden():
            self.settings_dialog.show()
        else:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
        
        self.menu.close()
    
    def isInStartup(self, name):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        
    def addToStartup(self, name):
        path = f"{os.path.dirname(os.path.abspath(sys.argv[0]))}\\{settings['app_name']}.exe"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
        winreg.CloseKey(key)
    
    def removeFromStartup(self, name):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
    
    def setIconTheme(self):
        if settings["icon_empty"] in ["./assets/white_empty.ico", "./assets/white_empty.ico"]:
            if sysThemeIsDark():
                settings["icon_empty"] = "./assets/white_empty.ico"
                settings["icon_full"] = "./assets/white_full.ico"
            else:
                settings["icon_empty"] = "./assets/white_empty.ico"
                settings["icon_full"] = "./assets/white_full.ico"
            
            with open("./settings.json", "w") as file:
                json.dump(settings, file)
            self.updateIcon()
    
    def updateIcon(self):
        has_files = bool(list(winshell.recycle_bin()))
        icon_path = settings.get("icon_full", "./assets/white_full.ico") if has_files else settings.get("icon_empty", "./assets/white_empty.ico")
        
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            default_icon = "./assets/white_full.ico" if has_files else "./assets/white_empty.ico"
            self.setIcon(QIcon(default_icon))
                
    def setLang(self, file): 
        settings["lang"] = file
        with open("./settings.json", "w") as f:
            json.dump(settings, f)
        with open(settings["lang"], "r+", encoding="UTF-8") as f:
            global translation
            translation = json.load(f)
        
        self.open_bin.setText(translatable("element.open"))
        self.clear_bin.setText(translatable("element.clear"))
        self.settings_action.setText(translatable("element.settings"))
        self.exit_action.setText(translatable("element.close"))
        
        if self.settings_dialog:
            self.settings_dialog.close()
            self.settings_dialog = None
        
        self.menu.update()
        self.menu.close()
        
    def formatTooltip(self):
        bin_size = self.getBinSize()
        file_count = len(list(winshell.recycle_bin()))
        
        if bin_size < 1024:
            size_text = f"{bin_size:.1f} {translatable('tooltip.kb')}"
        elif bin_size < 1048576:
            size_text = f"{bin_size/1024:.1f} {translatable('tooltip.mb')}"
        else:
            size_text = f"{bin_size/1048576:.1f} {translatable('tooltip.gb')}"
        
        file_word = self.getWordForm(file_count, translatable("tooltip.f1"), translatable("tooltip.f2"), translatable("tooltip.f3")) 
        self.setToolTip(f"{file_count} {file_word}\n{size_text}")
      
    def getWordForm(self, n, f1, f2, f3):
        n %= 100
        n1 = n % 10
        if n >= 10 and n <= 20:
            return f3
        elif n1 == 1:
            return f1
        elif 2 <= n1 <= 4:
            return f2
        return f3
    
    def getBinSize(self):
        bin_info = BinInfo()
        bin_info.cbSize = ctypes.sizeof(BinInfo)
        ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(bin_info))
        return bin_info.i64Size / 1024
            
    def clearBin(self):
        if list(winshell.recycle_bin()):
            winshell.recycle_bin().empty()
            self.updateIcon()
        self.menu.close()

class DragDropWindow(QWidget):
    def __init__(self, tray):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.01)
        self.setFixedSize(30, 40)
        self.move(1015, 676)
        self.tray = tray
        self.setAcceptDrops(True)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.onMousePosition)
        self.timer.start(50)

    def onMousePosition(self):
        cursor_pos = QCursor.pos()
        self.icon_rect = self.tray.geometry().getRect()
        x1, y1, w, h = self.icon_rect
        x2, y2 = x1 + w, y1 + h
        
        if x1 <= cursor_pos.x() <= x2 and y1 <= cursor_pos.y() <= y2 and windll.user32.GetKeyState(0x01) > 1:
            self.move(x1, y1)
            self.show()
        else:
            self.hide()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            event.setDropAction(Qt.DropAction.MoveAction)
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            files = [i.toLocalFile().replace("/", "\\") for i in event.mimeData().urls()]
            send2trash(files)
            self.tray.updateIcon()
            self.hide()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    
    with open("./settings.json") as file:
        settings = json.load(file)
    
    settings.setdefault("icon_empty", "./assets/white_empty.ico")
    settings.setdefault("icon_full", "./assets/white_full.ico")
    
    with open("./settings.json", "w") as file:
        json.dump(settings, file)
    
    with open(settings["lang"], "r+", encoding="UTF-8") as file:
        translation = json.load(file)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    icon = QIcon(settings["icon_empty"])
    tray = TrashTrayIcon(icon)
    tray.setVisible(True)
    
    window = DragDropWindow(tray)
    window.show()
    
    sys.exit(app.exec())
