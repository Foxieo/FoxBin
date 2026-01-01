import winshell, json, os, sys, ctypes, winreg, time
from ctypes import windll, wintypes
from send2trash import send2trash
from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QFileDialog, QVBoxLayout, QPushButton, QCheckBox, QComboBox, QLabel, QDialog, QHBoxLayout, QGroupBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QIcon, QPixmap

# Кэш для темы Windows (TTL 5 секунд)
_theme_cache = {"time": 0, "value": None, "ttl": 5}

def sysThemeIsDark():
    """Проверяет, используется ли темная тема Windows с кэшированием"""
    global _theme_cache
    current_time = time.time()
    
    # Если кэш валиден, возвращаем сохраненное значение
    if _theme_cache["time"] + _theme_cache["ttl"] > current_time:
        return _theme_cache["value"]
    
    # Иначе обновляем кэш
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                          r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            result = value == 0
            _theme_cache = {"time": current_time, "value": result, "ttl": 5}
            return result
    except:
        # В случае ошибки возвращаем последнее сохраненное значение или True
        return _theme_cache["value"] if _theme_cache["value"] is not None else True

def translatable(key: str):
    """Получает переведенное значение по ключу"""
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
    # Константы путей к иконкам
    DEFAULT_ICON_PATHS = {
        "empty_dark": "./assets/white_empty.png",
        "full_dark": "./assets/white_full.png", 
        "empty_light": "./assets/black_empty.png",
        "full_light": "./assets/black_full.png"
    }
    
    def __init__(self, tray):
        super().__init__()
        self.tray = tray
        self.setWindowTitle(translatable("settings.title"))
        self.setFixedSize(260, 350)  # Увеличил высоту для рамок
        self.setWindowIcon(QIcon('FoxBin.ico'))
        
        # Создаем layout
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # === ГРУППА: ЯЗЫК ===
        lang_group = QGroupBox(translatable("element.lang_menu"))
        lang_group.setStyleSheet("""
            QGroupBox {
                color: #CCC;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        lang_layout = QVBoxLayout()
        lang_layout.setContentsMargins(10, 2, 10, 10)
        
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
        
        # Заполняем комбобокс и выбираем текущий язык
        current_lang = settings["lang"]
        current_lang_name = "English"
        for name, path in self.languages.items():
            self.lang_combo.addItem(name)
            if path == current_lang:
                current_lang_name = name
        
        self.lang_combo.setCurrentText(current_lang_name)
        self.lang_combo.currentTextChanged.connect(self.changeLangFromCombo)
        lang_layout.addWidget(self.lang_combo)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # === ГРУППА: АВТОЗАПУСК ===
        startup_group = QGroupBox(translatable("element.add_startup"))
        startup_group.setStyleSheet("""
            QGroupBox {
                color: #CCC;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        startup_layout = QVBoxLayout()
        startup_layout.setContentsMargins(10, 10, 10, 10)
        
        self.startup_checkbox = QCheckBox(translatable("element.add_startup"))
        self.startup_checkbox.setChecked(tray.isInStartup(settings["app_name"]))
        self.startup_checkbox.stateChanged.connect(self.toggleStartup)
        startup_layout.addWidget(self.startup_checkbox)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # === ГРУППА: ИКОНКА ПУСТОЙ КОРЗИНЫ ===
        icon_empty_group = QGroupBox(translatable("settings.icon_empty"))
        icon_empty_group.setStyleSheet("""
            QGroupBox {
                color: #CCC;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        icon_empty_layout = QVBoxLayout()
        icon_empty_layout.setContentsMargins(10, 10, 10, 10)

        # Основной layout для превью и кнопок В ОДНОЙ СТРОЧКЕ
        icon_empty_main_layout = QHBoxLayout()

        # Превью иконки
        self.icon_empty_preview = QLabel()
        self.icon_empty_preview.setFixedSize(30, 30)
        self.icon_empty_preview.setObjectName("preview_empty")
        self.icon_empty_preview.setStyleSheet("""
            background-color: #333333;
            border: 1px solid #555555;
            padding: 2px;
            border-radius: 4px;
        """)
        icon_empty_main_layout.addWidget(self.icon_empty_preview)
        icon_empty_main_layout.addSpacing(10)

        # КНОПКИ В ОДНОЙ СТРОЧКЕ (горизонтально)
        self.btn_change_empty = QPushButton(translatable("element.change_icon"))
        self.btn_change_empty.setObjectName("btn_change_empty")
        self.btn_change_empty.clicked.connect(lambda: self.changeIcon("empty"))
        icon_empty_main_layout.addWidget(self.btn_change_empty)

        self.btn_reset_empty = QPushButton(translatable("element.reset_icon"))
        self.btn_reset_empty.setObjectName("btn_reset_empty")
        self.btn_reset_empty.clicked.connect(lambda: self.resetIcon("empty"))
        icon_empty_main_layout.addWidget(self.btn_reset_empty)

        icon_empty_main_layout.addStretch()

        icon_empty_layout.addLayout(icon_empty_main_layout)
        icon_empty_group.setLayout(icon_empty_layout)
        layout.addWidget(icon_empty_group)

        # === ГРУППА: ИКОНКА ПОЛНОЙ КОРЗИНЫ ===
        icon_full_group = QGroupBox(translatable("settings.icon_full"))
        icon_full_group.setStyleSheet("""
            QGroupBox {
                color: #CCC;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        icon_full_layout = QVBoxLayout()
        icon_full_layout.setContentsMargins(10, 10, 10, 10)

        # Основной layout для превью и кнопок В ОДНОЙ СТРОЧКЕ
        icon_full_main_layout = QHBoxLayout()

        # Превью иконки
        self.icon_full_preview = QLabel()
        self.icon_full_preview.setFixedSize(30, 30)
        self.icon_full_preview.setObjectName("preview_full")
        self.icon_full_preview.setStyleSheet("""
            background-color: #333333;
            border: 1px solid #555555;
            padding: 2px;
            border-radius: 4px;
        """)
        icon_full_main_layout.addWidget(self.icon_full_preview)
        icon_full_main_layout.addSpacing(10)

        # КНОПКИ В ОДНОЙ СТРОЧКЕ (горизонтально)
        self.btn_change_full = QPushButton(translatable("element.change_icon"))
        self.btn_change_full.setObjectName("btn_change_full")
        self.btn_change_full.clicked.connect(lambda: self.changeIcon("full"))
        icon_full_main_layout.addWidget(self.btn_change_full)

        self.btn_reset_full = QPushButton(translatable("element.reset_icon"))
        self.btn_reset_full.setObjectName("btn_reset_full")
        self.btn_reset_full.clicked.connect(lambda: self.resetIcon("full"))
        icon_full_main_layout.addWidget(self.btn_reset_full)

        icon_full_main_layout.addStretch()

        icon_full_layout.addLayout(icon_full_main_layout)
        icon_full_group.setLayout(icon_full_layout)
        layout.addWidget(icon_full_group)
        
        # === КНОПКА ЗАКРЫТИЯ ===
        btn_close = QPushButton(translatable("element.close_settings"))
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
        
        # Отступ
        layout.addStretch()
        
        self.setLayout(layout)
        self.applyStyleSheet()
        
        # Обновляем превью иконок
        self.updateIconPreview("empty")
        self.updateIconPreview("full")
    
    def applyStyleSheet(self):
        """Применяет стили к диалогу"""
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
                color: #FFF;
            }
            QLabel {
                color: #FFF;
                padding: 4px 0px;
            }
            QCheckBox {
                color: #FFF;
                padding: 6px 1px;
                spacing: 8px;
            }
            QComboBox {
                background-color: #333;
                color: #FFF;
                border: 1px solid #555;
                padding: 4px;
                border-radius: 4px;
                min-height: 14px;
            }
            QComboBox:hover {
                border: 1px solid #666;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #333;
                color: #FFF;
                border: 1px solid #555;
                selection-background-color: #0078d4;
            }
            QPushButton {
                background-color: #333;
                color: #FFF;
                border: 1px solid #555;
                padding: 6px 12px;
                border-radius: 4px;
                min-height: 15px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """)
    
    def updateIconPreview(self, icon_type):
        """Обновляет превью иконки"""
        key = "icon_empty" if icon_type == "empty" else "icon_full"
        preview_label = self.icon_empty_preview if icon_type == "empty" else self.icon_full_preview
        
        if not preview_label:
            return
            
        icon_path = settings.get(key, "")
        
        # Если путь не указан или файл не существует, используем дефолтную иконку
        if not icon_path or not os.path.exists(icon_path):
            is_dark = sysThemeIsDark()
            if icon_type == "empty":
                icon_path = self.DEFAULT_ICON_PATHS["empty_dark" if is_dark else "empty_light"]
            else:
                icon_path = self.DEFAULT_ICON_PATHS["full_dark" if is_dark else "full_light"]
        
        # Загружаем и масштабируем иконку
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, 
                                      Qt.TransformationMode.SmoothTransformation)
                preview_label.setPixmap(pixmap)
                preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                return
        
        # Если что-то пошло не так, очищаем
        preview_label.clear()
    
    def toggleStartup(self, state):
        """Включает/выключает автозапуск"""
        if state:
            self.tray.addToStartup(settings["app_name"])
            self.startup_checkbox.setText(translatable("element.remove_startup"))
        else:
            self.tray.removeFromStartup(settings["app_name"])
            self.startup_checkbox.setText(translatable("element.add_startup"))
    
    def changeLangFromCombo(self, lang_name):
        """Меняет язык приложения"""
        lang_path = self.languages.get(lang_name)
        if lang_path:
            self.tray.setLang(lang_path)
    
    def changeIcon(self, icon_type):
        """Меняет иконку через диалог выбора файла"""
        file, _ = QFileDialog.getOpenFileName(
            self, 
            translatable("filedialog.title"), 
            "", 
            "Images (*.png; *.jpg; *.jpeg; *.ico)"
        )
        
        if file:
            key = "icon_empty" if icon_type == "empty" else "icon_full"
            settings[key] = file
            
            # Сохраняем настройки
            with open("./settings.json", "w", encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            # Обновляем иконки
            self.tray.updateIcon()
            self.updateIconPreview(icon_type)
    
    def resetIcon(self, icon_type):
        """Сбрасывает иконку на дефолтную"""
        is_dark = sysThemeIsDark()
        
        # Выбираем правильную дефолтную иконку
        if icon_type == "empty":
            new_path = self.DEFAULT_ICON_PATHS["empty_dark" if is_dark else "empty_light"]
        else:
            new_path = self.DEFAULT_ICON_PATHS["full_dark" if is_dark else "full_light"]
        
        # Сохраняем
        key = "icon_empty" if icon_type == "empty" else "icon_full"
        settings[key] = new_path
        
        with open("./settings.json", "w", encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        # Обновляем иконки
        self.tray.updateIcon()
        self.updateIconPreview(icon_type)
    
    def closeEvent(self, event):
        """Скрываем окно вместо закрытия"""
        self.hide()
        event.ignore()

class TrashTrayIcon(QSystemTrayIcon):
    def __init__(self, icon):
        super().__init__(icon)
        self.activated.connect(self.onTrayActivated)
        
        # Создаем меню
        self.menu = QMenu()
        self.menu.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.applyMenuStyle()
        
        # Создаем действия меню
        self.createMenuActions()
        
        # Таймеры
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
    
    def applyMenuStyle(self):
        """Применяет стили к меню"""
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #252525;
                border: 1px solid #555;
                padding: 1px;
                border-radius: 5px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 6px 30px 6px 25px;
                margin: 1px;
                color: #FFF;
            }
            QMenu::item:selected {
                background-color: #333;
                color: #FFF;
            }
            QMenu::item:disabled {
                color: #808080;
            }
            QMenu::separator {
                height: 1px;
                background-color: #C0C0C0;
                margin: 3px 8px;
            }
            QMenu::icon {
                margin-left: 3px;
            }
            QMenu::right-arrow {
                image: none;
                margin-right: 3px;
            }
        """)
    
    def createMenuActions(self):
        """Создает действия для меню"""
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
    
    def onTrayActivated(self, reason):
        """Обрабатывает клики по иконке в трее"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.openRecycleBin()
    
    def openRecycleBin(self):
        """Открывает корзину"""
        try:
            os.startfile("shell:RecycleBinFolder")
        except:
            # Резервный способ
            os.system('explorer shell:RecycleBinFolder')
    
    def exitApp(self):
        """Выход из приложения"""
        if self.settings_dialog:
            self.settings_dialog.close()
        QApplication.quit()
    
    def openSettings(self):
        """Открывает окно настроек"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        
        if self.settings_dialog.isHidden():
            self.settings_dialog.show()
        else:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
        
        self.menu.close()
    
    def isInStartup(self, name):
        """Проверяет, добавлено ли приложение в автозагрузку"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, name)
            return True
        except FileNotFoundError:
            return False
    
    def addToStartup(self, name):
        """Добавляет приложение в автозагрузку"""
        try:
            exe_path = os.path.abspath(sys.argv[0])
            if exe_path.endswith('.py'):
                cmd = f'"{sys.executable}" "{exe_path}"'
            else:
                cmd = f'"{exe_path}"'
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, cmd)
        except Exception as e:
            print(f"Ошибка добавления в автозагрузку: {e}")
    
    def removeFromStartup(self, name):
        """Удаляет приложение из автозагрузки"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except Exception as e:
            print(f"Ошибка удаления из автозагрузки: {e}")
    
    def setIconTheme(self):
        """Обновляет иконки в зависимости от темы Windows"""
        # Определяем дефолтные иконки
        default_icons = {
            "./assets/white_empty.png",
            "./assets/white_full.png",
            "./assets/black_empty.png",
            "./assets/black_full.png"
        }
        
        # Если используется дефолтная иконка, проверяем тему
        if settings.get("icon_empty", "") in default_icons:
            is_dark = sysThemeIsDark()
            
            if is_dark:
                settings["icon_empty"] = "./assets/white_empty.png"
                settings["icon_full"] = "./assets/white_full.png"
            else:
                settings["icon_empty"] = "./assets/black_empty.png"
                settings["icon_full"] = "./assets/black_full.png"
            
            # Сохраняем настройки
            with open("./settings.json", "w", encoding='utf-8') as file:
                json.dump(settings, file, ensure_ascii=False, indent=2)
            
            self.updateIcon()
    
    def updateIcon(self):
        """Обновляет иконку в трее в зависимости от состояния корзины"""
        has_files = bool(list(winshell.recycle_bin()))
        icon_key = "icon_full" if has_files else "icon_empty"
        icon_path = settings.get(icon_key, "")
        
        # Если путь не указан или файл не существует, используем дефолтную иконку
        if not icon_path or not os.path.exists(icon_path):
            is_dark = sysThemeIsDark()
            if has_files:
                icon_path = "./assets/white_full.png" if is_dark else "./assets/black_full.png"
            else:
                icon_path = "./assets/white_empty.png" if is_dark else "./assets/black_empty.png"
        
        self.setIcon(QIcon(icon_path))
    
    def setLang(self, file):
        """Устанавливает язык приложения"""
        settings["lang"] = file
        
        # Сохраняем настройки
        with open("./settings.json", "w", encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        # Загружаем переводы
        try:
            with open(file, "r", encoding="UTF-8") as f:
                global translation
                translation = json.load(f)
        except:
            translation = {}
        
        # Обновляем текст в меню
        self.open_bin.setText(translatable("element.open"))
        self.clear_bin.setText(translatable("element.clear"))
        self.settings_action.setText(translatable("element.settings"))
        self.exit_action.setText(translatable("element.close"))
        
        # Закрываем диалог настроек, если он открыт
        if self.settings_dialog:
            self.settings_dialog.close()
            self.settings_dialog = None
    
    def formatTooltip(self):
        """Форматирует всплывающую подсказку"""
        bin_size = self.getBinSize()
        file_count = len(list(winshell.recycle_bin()))
        
        # Определяем единицы измерения
        if bin_size < 1024:
            size_text = f"{bin_size:.1f} {translatable('tooltip.kb')}"
        elif bin_size < 1048576:
            size_text = f"{bin_size / 1024:.1f} {translatable('tooltip.mb')}"
        else:
            size_text = f"{bin_size / 1048576:.1f} {translatable('tooltip.gb')}"
        
        # Определяем правильную форму слова "файл"
        file_word = self.getWordForm(
            file_count,
            translatable("tooltip.f1"),
            translatable("tooltip.f2"),
            translatable("tooltip.f3")
        )
        
        self.setToolTip(f"{file_count} {file_word}\n{size_text}")
    
    def getWordForm(self, n, f1, f2, f3):
        """Возвращает правильную форму слова в зависимости от числа"""
        n %= 100
        n1 = n % 10
        
        if 10 <= n <= 20:
            return f3
        elif n1 == 1:
            return f1
        elif 2 <= n1 <= 4:
            return f2
        return f3
    
    def getBinSize(self):
        """Возвращает размер корзины в килобайтах"""
        bin_info = BinInfo()
        bin_info.cbSize = ctypes.sizeof(BinInfo)
        ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(bin_info))
        return bin_info.i64Size / 1024 if bin_info.i64Size else 0
    
    def clearBin(self):
        """Очищает корзину"""
        if list(winshell.recycle_bin()):
            winshell.recycle_bin().empty()
            self.updateIcon()
        self.menu.close()

class DragDropWindow(QWidget):
    def __init__(self, tray):
        super().__init__()
        self.tray = tray
        
        # Настройки окна
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowOpacity(0.01)
        self.setFixedSize(30, 40)
        self.move(1015, 676)
        self.setAcceptDrops(True)
        
        # Таймер для отслеживания положения мыши
        self.timer = QTimer()
        self.timer.timeout.connect(self.onMousePosition)
        self.timer.start(50)
    
    def onMousePosition(self):
        """Показывает окно при перетаскивании над иконкой"""
        cursor_pos = QCursor.pos()
        
        try:
            geo = self.tray.geometry()
            x1, y1, w, h = geo.x(), geo.y(), geo.width(), geo.height()
            
            # Проверяем, находится ли курсор над иконкой и зажата ли левая кнопка мыши
            left_button_pressed = windll.user32.GetKeyState(0x01) & 0x8000
            
            if (x1 <= cursor_pos.x() <= x1 + w and 
                y1 <= cursor_pos.y() <= y1 + h and 
                left_button_pressed):
                self.move(x1, y1)
                self.show()
            else:
                self.hide()
        except:
            self.hide()
    
    def dragEnterEvent(self, event):
        """Принимает перетаскиваемые файлы"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            event.setDropAction(Qt.DropAction.MoveAction)
    
    def dropEvent(self, event):
        """Обрабатывает сброс файлов в корзину"""
        if event.mimeData().hasUrls():
            files = [
                url.toLocalFile().replace("/", "\\") 
                for url in event.mimeData().urls()
            ]
            
            try:
                send2trash(files)
                self.tray.updateIcon()
            except Exception as e:
                print(f"Ошибка при удалении файлов: {e}")
            
            self.hide()

def load_settings():
    """Загружает настройки из файла"""
    default_settings = {
        "app_name": "FoxBin",
        "lang": "./lang/ru.json",
        "icon_empty": "./assets/white_empty.png",
        "icon_full": "./assets/white_full.png"
    }
    
    try:
        with open("./settings.json", "r", encoding='utf-8') as f:
            loaded_settings = json.load(f)
            # Объединяем с дефолтными значениями
            return {**default_settings, **loaded_settings}
    except:
        # Если файл не существует или поврежден, создаем новый
        with open("./settings.json", "w", encoding='utf-8') as f:
            json.dump(default_settings, f, ensure_ascii=False, indent=2)
        return default_settings

def load_translation(lang_file):
    """Загружает переводы из файла"""
    try:
        with open(lang_file, "r", encoding="UTF-8") as f:
            return json.load(f)
    except:
        return {}

if __name__ == "__main__":
    # Устанавливаем рабочую директорию
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    
    # Загружаем настройки и переводы
    settings = load_settings()
    translation = load_translation(settings["lang"])
    
    # Проверяем тему и обновляем дефолтные иконки при необходимости
    is_dark = sysThemeIsDark()
    default_empty = "./assets/white_empty.png" if is_dark else "./assets/black_empty.png"
    default_full = "./assets/white_full.png" if is_dark else "./assets/black_full.png"
    
    # Если используются дефолтные иконки, обновляем их
    default_icon_paths = {
        "./assets/white_empty.png",
        "./assets/black_empty.png",
        "./assets/white_full.png", 
        "./assets/black_full.png"
    }
    
    if settings.get("icon_empty", "") in default_icon_paths:
        settings["icon_empty"] = default_empty
        settings["icon_full"] = default_full
        
        # Сохраняем обновленные настройки
        with open("./settings.json", "w", encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    
    # Создаем приложение
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon('FoxBin.ico'))
    
    # Создаем иконку в трее
    icon = QIcon(settings["icon_empty"])
    tray = TrashTrayIcon(icon)
    tray.setVisible(True)
    
    # Создаем окно для перетаскивания
    drag_window = DragDropWindow(tray)
    drag_window.show()
    
    # Запускаем приложение
    sys.exit(app.exec())
