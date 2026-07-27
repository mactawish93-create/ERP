# database_system/auth_window.py
import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database_system.auth_core import verify_user_credentials

class LoginDialog(QDialog):
    """
    Промышленный изолированный модуль авторизации сотрудников фабрики.
    Защищает вход в ERP-систему, разделяет роли и поддерживает смену тем.
    """
    def __init__(self, is_dark_theme=True):
        super().__init__()
        self.is_dark_theme = is_dark_theme
        self.user_session = None # Сюда запишется паспорт роли при успешном входе

        self.setWindowTitle("БаБочки ERP — Авторизация")
        self.setFixedSize(360, 420)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)

        self._init_ui()
        self._apply_theme()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 40, 30, 40)
        self.layout.setSpacing(15)

        # Логотип/Заголовок
        self.lbl_title = QLabel("ВХОД В СИСТЕМУ")
        self.lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel("Управление фабрикой бань")
        self.lbl_subtitle.setFont(QFont("Segoe UI", 9))
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_subtitle)
        self.layout.addSpacing(15)

        # Поле ввода Логина
        self.txt_login = QLineEdit()
        self.txt_login.setPlaceholderText("Введите логин...")
        self.txt_login.setFixedHeight(38)
        self.layout.addWidget(self.txt_login)

        # Поле ввода Пароля
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Введите пароль...")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setFixedHeight(38)
        self.layout.addWidget(self.txt_password)

        # Информационная строка ошибок красным текстом
        self.lbl_error = QLabel("")
        self.lbl_error.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet("color: #FF4D4D;")
        self.layout.addWidget(self.lbl_error)
        self.layout.addStretch()

        # Кнопка Входа
        self.btn_login = QPushButton("ОТКРЫТЬ ERP СИСТЕМУ")
        self.btn_login.setFixedHeight(42)
        self.btn_login.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_login.clicked.connect(self._handle_login_attempt)
        self.layout.addWidget(self.btn_login)

    def _handle_login_attempt(self):
        """Проверяет введенные данные через крипто-ядро базы данных"""
        login = self.txt_login.text()
        password = self.txt_password.text()

        if not login or not password:
            self.lbl_error.setText("Заполните все поля ввода!")
            return

        # Сверяем хэши в бд
        result = verify_user_credentials(login, password)

        if result["success"]:
            self.user_session = result # Запоминаем паспорт сессии (ФИО, роль, ранг)
            self.accept() # Закрываем диалог с успехом, передаем управление в main_erp.py
        else:
            self.lbl_error.setText(result["error"])

    def _apply_theme(self):
        """Применяет QSS стили в зависимости от глобальной темы"""
        if self.is_dark_theme:
            self.setStyleSheet("""
                QDialog { background-color: #111114; }
                QLabel { color: #E0E0E6; font-family: 'Segoe UI'; }
                QLineEdit { 
                    background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #353540; 
                    border-radius: 4px; padding-left: 10px; font-family: 'Segoe UI';
                }
                QLineEdit:focus { border-color: #00A8FF; }
                QPushButton { 
                    background-color: #00A8FF; color: white; border: none; border-radius: 4px; 
                }
                QPushButton:hover { background-color: #0088CC; }
            """)
            self.lbl_title.setStyleSheet("color: #FF9F43;")
            self.lbl_subtitle.setStyleSheet("color: #656570;")
        else:
            self.setStyleSheet("""
                QDialog { background-color: #FFFFFF; }
                QLabel { color: #212529; font-family: 'Segoe UI'; }
                QLineEdit { 
                    background-color: #F8F9FA; color: #212529; border: 1px solid #CED4DA; 
                    border-radius: 4px; padding-left: 10px; font-family: 'Segoe UI';
                }
                QLineEdit:focus { border-color: #0056B3; }
                QPushButton { 
                    background-color: #0056B3; color: white; border: none; border-radius: 4px; 
                }
                QPushButton:hover { background-color: #004085; }
            """)
            self.lbl_title.setStyleSheet("color: #0056B3;")
            self.lbl_subtitle.setStyleSheet("color: #6C757D;")
