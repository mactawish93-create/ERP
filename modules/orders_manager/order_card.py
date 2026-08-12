# modules/orders_manager/order_card.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class OrderListCard(QFrame):
    """
    Изолированный компонент карточки заказа для левой CRM-ленты.
    Полностью управляется через глобальный QSS-файл стилей.
    """
    def __init__(self, order_id, contract_num, status, fio, phone):
        super().__init__()
        self.order_id = order_id
        self.contract_num = contract_num
        self.status = status
        self.fio = fio
        self.phone = phone
        
        self._init_ui()

    def _init_ui(self):
        # Назначаем объектное имя для подхвата стилей из theme_styles.py
        self.setObjectName("OrderListCard")
        
        # Настраиваем внутренний слой карточки
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(12, 6, 12, 6)
        card_layout.setSpacing(4)
        
        # Формируем верхнюю строку заголовка карточки
        c_num_text = f"Договор №{self.contract_num}" if self.contract_num else "Договор №: —"
        lbl_top = QLabel(f"Лид #{self.order_id}  •  {c_num_text}  •  [{self.status.upper()}]")
        lbl_top.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        # Динамические маркеры статусов для селекторов QSS
        lbl_top.setProperty("status", self.status.lower())
        lbl_top.setObjectName("OrderCardTitle")
        
        # Формируем нижнюю строку с контактами клиента
        lbl_bottom = QLabel(f"👤 {self.fio}   |   📱 {self.phone}")
        lbl_bottom.setFont(QFont("Segoe UI", 9))
        lbl_bottom.setObjectName("OrderCardSubtitle")
        
        # Добавляем элементы на карточку
        card_layout.addWidget(lbl_top)
        card_layout.addWidget(lbl_bottom)
