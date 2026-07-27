# modules/sales_wizard/step_1_contacts.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class Step1ContactsWidget(QWidget):
    """Шаг 1 воронки: Первичный контакт клиента (ФИО, телефон, источник)"""
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        # Заголовок
        lbl_title = QLabel("ЭТАП 1: РЕГИСТРАЦИЯ ПЕРВИЧНОГО ОБРАЩЕНИЯ КЛИЕНТА")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #FF9F43;")
        self.layout.addWidget(lbl_title)

        # Поля ввода
        self.layout.addWidget(QLabel("ФИО Клиента (Обязательно):"))
        self.txt_fio = QLineEdit()
        self.txt_fio.setPlaceholderText("Иванов Иван Иванович")
        self.txt_fio.setFixedHeight(38)
        self.layout.addWidget(self.txt_fio)

        self.layout.addWidget(QLabel("Номер телефона (Обязательно):"))
        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("+7 (999) 123-45-67")
        self.txt_phone.setFixedHeight(38)
        self.layout.addWidget(self.txt_phone)

        self.layout.addWidget(QLabel("Источник рекламы (Лид):"))
        self.cb_source = QComboBox()
        self.cb_source.addItems(["Сайт (Заявка)", "Авито", "Прямой звонок", "По рекомендации", "Прочее"])
        self.cb_source.setFixedHeight(38)
        self.layout.addWidget(self.cb_source)

        self.layout.addStretch()

    def collect_data(self) -> dict:
        """Собирает введенные менеджером данные для передачи в общий словарь"""
        return {
            "client_fio": self.txt_fio.text().strip(),
            "client_phone": self.txt_phone.text().strip(),
            "lead_source": self.cb_source.currentText()
        }
