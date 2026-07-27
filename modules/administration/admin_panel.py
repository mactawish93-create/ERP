# modules/administration/admin_panel.py
import pymysql
import hashlib
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import DB_CONFIG, ACCESS_LEVELS

class AdminPanelWidget(QWidget):
    """
    Изолированный управляющий модуль Вкладки 8 'Администрирование'.
    🔥 ОЖИВЛЕН: Подключен онлайн-вывод пользователей и регистрация с SHA-256 хэшированием!
    """
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.load_users_from_mysql() # Автоматически загружаем штат при старте

    def _init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # ЛЕВАЯ ЧАСТЬ: ФОРМА УПРАВЛЕНИЯ ПЕРСОНАЛОМ
        left_frame = QFrame()
        left_frame.setFixedWidth(280)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        lbl_section = QLabel("🔐 УПРАВЛЕНИЕ ДОСТУПОМ")
        lbl_section.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        left_layout.addWidget(lbl_section)

        left_layout.addWidget(QLabel("Логин сотрудника (латиница):"))
        self.txt_login = QLineEdit()
        self.txt_login.setPlaceholderText("ivan_master")
        self.txt_login.setFixedHeight(34)
        left_layout.addWidget(self.txt_login)

        left_layout.addWidget(QLabel("ФИО сотрудника полностью:"))
        self.txt_fullname = QLineEdit()
        self.txt_fullname.setPlaceholderText("Петров Иван Сергеевич")
        self.txt_fullname.setFixedHeight(34)
        left_layout.addWidget(self.txt_fullname)

        left_layout.addWidget(QLabel("Производственная роль:"))
        self.cb_role = QComboBox()
        for r_key in ACCESS_LEVELS.keys():
            self.cb_role.addItem(f"{r_key} (Ранг {ACCESS_LEVELS[r_key]})", r_key)
        self.cb_role.setFixedHeight(34)
        left_layout.addWidget(self.cb_role)

        left_layout.addWidget(QLabel("Стартовый временный пароль:"))
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Например: Ceh2026")
        self.txt_password.setFixedHeight(34)
        left_layout.addWidget(self.txt_password)

        # Строка уведомлений о статусе операции
        self.lbl_status = QLabel("")
        self.lbl_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.lbl_status.setStyleSheet("color: #FF9F43;")
        left_layout.addWidget(self.lbl_status)

        left_layout.addSpacing(5)

        # Кнопки действий
        self.btn_register = QPushButton("➕ Зарегистрировать в базу")
        self.btn_register.setFixedHeight(38)
        self.btn_register.setStyleSheet("background-color: #00A8FF; color: white; font-weight: bold;")
        self.btn_register.clicked.connect(self.register_new_worker) # Подключили клик!
        left_layout.addWidget(self.btn_register)

        self.btn_reset_pass = QPushButton("🔄 Сбросить пароль сотруднику")
        self.btn_reset_pass.setFixedHeight(34)
        left_layout.addWidget(self.btn_reset_pass)

        self.btn_toggle_active = QPushButton("🚫 Заблокировать доступ")
        self.btn_toggle_active.setFixedHeight(34)
        left_layout.addWidget(self.btn_toggle_active)

        left_layout.addStretch()
        self.main_layout.addWidget(left_frame)

        # ПРАВАЯ ЧАСТЬ: ТАБЛИЦА ВСЕХ СОТРУДНИКОВ ФАБРИКИ
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        lbl_table_title = QLabel("📊 ТЕКУЩИЙ ШТАТ И СТАТУСЫ ДОСТУПА СМАРТФОНОВ/ПК (ОНЛАЙН MySQL)")
        lbl_table_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        right_layout.addWidget(lbl_table_title)

        self.table_users = QTableWidget()
        self.table_users.setColumnCount(6)
        self.table_users.setHorizontalHeaderLabels(["ID", "Логин", "ФИО Сотрудника", "Роль", "Ранг", "Статус аккаунта"])
        self.table_users.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_users.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_users.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
                
        right_layout.addWidget(self.table_users)
        self.main_layout.addWidget(right_frame, stretch=1)

    def load_users_from_mysql(self):
        """🔥 ВНЕДРЕНО: Скачивает штат сотрудников из облака MySQL и выводит в таблицу"""
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, login, full_name, role, access_level, is_active FROM users")
            rows = cursor.fetchall()
            
            self.table_users.setRowCount(len(rows))
            
            for row_idx, data in enumerate(rows):
                # Раскладываем данные по столбцам
                u_id, login, full_name, role, level, is_active = data
                
                status_text = "✅ Активен" if is_active else "🚫 Заблокирован"
                
                self.table_users.setItem(row_idx, 0, QTableWidgetItem(str(u_id)))
                self.table_users.setItem(row_idx, 1, QTableWidgetItem(str(login)))
                self.table_users.setItem(row_idx, 2, QTableWidgetItem(str(full_name)))
                self.table_users.setItem(row_idx, 3, QTableWidgetItem(str(role).upper()))
                self.table_users.setItem(row_idx, 4, QTableWidgetItem(f"Ранг {level}"))
                self.table_users.setItem(row_idx, 5, QTableWidgetItem(status_text))
                
            cursor.close()
            conn.close()
        except pymysql.MySQLError as e:
            self.lbl_status.setText("Ошибка загрузки таблицы!")
            print(f"[Ошибка MySQL в Админке]: {e}")

    def register_new_worker(self):
        """🔥 ВНЕДРЕНО: Берет данные из полей, хэширует SHA-256 с солью и делает INSERT в MySQL"""
        login = self.txt_login.text().strip()
        fullname = self.txt_fullname.text().strip()
        password = self.txt_password.text().strip()
        role = self.cb_role.currentData() # Берем чистый ключ роли (например, 'master')
        level = ACCESS_LEVELS[role] # Автоматически подтягиваем ранг доступов

        if not login or not fullname or not password:
            self.lbl_status.setText("⚠️ Заполните все поля!")
            self.lbl_status.setStyleSheet("color: #FF4D4D;")
            return

        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Генерируем уникальную крипто-соль
            salt = os.urandom(16).hex()
            raw_string = salt + password
            computed_hash = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

            sql = """
                INSERT INTO users (login, password_hash, salt, full_name, role, access_level, require_password_change, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (login, computed_hash, salt, fullname, role, level, True, True))
            conn.commit()
            
            cursor.close()
            conn.close()

            self.lbl_status.setText("✅ Пользователь успешно создан!")
            self.lbl_status.setStyleSheet("color: #00FF66;")
            
            # Очищаем поля ввода для следующего сотрудника
            self.txt_login.clear()
            self.txt_fullname.clear()
            self.txt_password.clear()
            
            # Перезагружаем таблицу, чтобы новый человек сразу появился на экране
            self.load_users_from_mysql()

        except pymysql.MySQLError as e:
            if "Duplicate entry" in str(e):
                self.lbl_status.setText("⚠️ Такой логин уже занят!")
            else:
                self.lbl_status.setText("⚠️ Ошибка записи в MySQL!")
            self.lbl_status.setStyleSheet("color: #FF4D4D;")
            print(f"[Ошибка регистрации в MySQL]: {e}")
