# modules/orders_manager/orders_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QCheckBox, QTableWidget, QHeaderView, 
                             QTableWidgetItem, QSplitter, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# 🔥 ИМПОРТИРУЕМ НАШУ НОВУЮ ЭКОСИСТЕМУ КОМПОНЕНТОВ
from modules.orders_manager.db_worker import fetch_all_orders
from modules.orders_manager.order_card import OrderListCard
from modules.orders_manager.digital_passport import DigitalPassportWidget

class OrdersManagerWidget(QWidget):
    """
    Главный диспетчер (Контроллер) вкладки 'База заказов'.
    Собирает воедино ленту карточек и цифровой паспорт бани.
    """
    def __init__(self, user_session=None, is_dark_theme=True):
        super().__init__()
        self.user_session = user_session
        self.is_dark_theme = is_dark_theme
        self.raw_orders_cache = {} # Кэш-хранилище всех 33 параметров базы Джино
        
        self._init_ui()
        
        # Первая стартовая загрузка данных из MySQL
        self.load_orders_from_mysql()

    def _init_ui(self):
        # Главный слой вкладки
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 10, 15, 10)
        self.main_layout.setSpacing(10)

        # Создаем резиновый разделитель экрана (Сплиттер)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("OrdersSplitter")

        # =====================================================================
        # ЛЕВАЯ СТОРОНА: Быстрый поиск, чекбоксы статусов и лента карточек
        # =====================================================================
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(8)

        lbl_left_title = QLabel("📋 Список договоров (Заказы)")
        lbl_left_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        left_layout.addWidget(lbl_left_title)

        # Строка быстрого поиска по ФИО или Номеру договора
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔎 Быстрый поиск по ФИО или договору...")
        self.txt_search.setFixedHeight(28)
        self.txt_search.textChanged.connect(self.apply_ui_filters)
        left_layout.addWidget(self.txt_search)

        # Сетка чекбоксов для фильтрации лидов по стадиям производства
        # 🔥 ФИКС: Создаем аккуратную двухрядную сетку для чекбоксов фильтров
        filter_grid = QGridLayout()
        filter_grid.setSpacing(6)
        
        # Полный список из 6 официальных статусов по вашему ТЗ
        self.status_boxes = {
            "calculation": QCheckBox("Расчет"),
            "signed": QCheckBox("Подписан"),
            "approved": QCheckBox("Утвержден"), # ← Вернули потерянный статус!
            "returned": QCheckBox("Возвращен"),
            "production": QCheckBox("В обработке"),
            "ready": QCheckBox("Выполнен")
        }
        
        # Раскладываем чекбоксы в сетку 2 строки на 3 колонки
        status_positions = [
            ("calculation", 0, 0), ("signed", 0, 1), ("approved", 0, 2),
            ("returned", 1, 0), ("production", 1, 1), ("ready", 1, 2)
        ]
        
        for key, row, col in status_positions:
            chk = self.status_boxes[key]
            chk.setChecked(True)
            chk.setFont(QFont("Segoe UI", 8)) # Делаем шрифт чуть компактнее, чтобы влезал
            chk.stateChanged.connect(self.apply_ui_filters)
            filter_grid.addWidget(chk, row, col)
            
        left_layout.addLayout(filter_grid)

        # Основная таблица-лента для вывода CRM-карточек
        self.table_orders = QTableWidget(0, 1)
        self.table_orders.horizontalHeader().setVisible(False)
        self.table_orders.verticalHeader().setVisible(False)
        self.table_orders.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_orders.setShowGrid(False)
        # Назначаем ширину левой колонки (под размер карточки)
        self.table_orders.setFixedWidth(330)
        
        # Привязываем клик по строке списка к отображению паспорта бани
        self.table_orders.itemSelectionChanged.connect(self.show_order_details)
        left_layout.addWidget(self.table_orders)

        # Добавляем левую сторону в сплиттер
        splitter.addWidget(left_container)

        # =====================================================================
        # ПРАВАЯ СТОРОНА: Наш новенький изолированный виджет цифрового паспорта
        # =====================================================================
        self.passport_widget = DigitalPassportWidget(self)
        splitter.addWidget(self.passport_widget)

        # Задаем стартовые пропорции: левая часть под карточки, правая — под паспорт
        splitter.setSizes([330, 700])
        self.main_layout.addWidget(splitter)
        
        # Применяем стартовую тему оформления к таблице и поиску
        self.set_theme_mode(self.is_dark_theme)

    def load_orders_from_mysql(self):
        """Скачивает данные через db_worker и наполняет левую CRM-ленту"""
        # Запрашиваем полный массив данных из слоя бэкенда
        self.raw_orders_cache = fetch_all_orders(self.user_session)
        
        # Замораживаем сигналы таблицы на время пересборки карточек, чтобы не было вылетов
        self.table_orders.blockSignals(True)
        self.table_orders.setRowCount(0)

        for o_id, order_data in self.raw_orders_cache.items():
            row_pos = self.table_orders.rowCount()
            self.table_orders.insertRow(row_pos)

            # Создаем скрытый текстовый элемент с хэштегом ID для работы поиска
            id_item = QTableWidgetItem(f"#{o_id}")
            id_item.setFlags(id_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table_orders.setItem(row_pos, 0, id_item)

            # Генерируем карточку из изолированного файла order_card.py
            card_widget = OrderListCard(
                order_id=o_id,
                contract_num=order_data.get("contract_number"),
                status=order_data.get("status", "calculation"),
                fio=order_data.get("client_fio", "—"),
                phone=order_data.get("client_phone", "—")
            )
            self.table_orders.setCellWidget(row_pos, 0, card_widget)
            
            # Подстраиваем высоту строки таблицы строго под размер карточки
            self.table_orders.setRowHeight(row_pos, 56)

        self.table_orders.blockSignals(False)
        # Применяем галочки чекбоксов к свежему списку
        self.apply_ui_filters()

    def show_order_details(self):
        """Перенаправляет отрисовку правого паспорта в изолированный виджет"""
        selected_rows = self.table_orders.selectionModel().selectedRows()
        if not selected_rows:
            return

        row_idx = selected_rows[0].row()
        # Вытаскиваем системный ID лида из ячейки
        id_text = self.table_orders.item(row_idx, 0).text()
        order_id = int(id_text.replace("#", ""))
        
        # Получаем данные этого лида из кэша
        order_data = self.raw_orders_cache.get(order_id, {})
        
        # 🔥 Даем команду правому паспорту перерисовать экран данными этого заказа!
        self.passport_widget.display_order(order_id, order_data)

    def apply_ui_filters(self):
        """Онлайн-фильтрация карточек по вводу букв в поиск и галочкам статусов"""
        search_query = self.txt_search.text().strip().lower()
        
        # Собираем список ключей статусов, которые сейчас отмечены галочками менеджера
        active_statuses = [k for k, chk in self.status_boxes.items() if chk.isChecked()]

        for row in range(self.table_orders.rowCount()):
            id_item = self.table_orders.item(row, 0)
            if not id_item: continue
            
            order_id = int(id_item.text().replace("#", ""))
            order_data = self.raw_orders_cache.get(order_id, {})
            
            # Извлекаем параметры для текстового поиска
            # 🔥 БРОНЕБОЙНЫЙ ФИКС: Защищаем поиск от NULL-значений (None) в MySQL
            fio = str(order_data.get("client_fio") or "").lower()
            contract = str(order_data.get("contract_number") or "").lower()
            status = str(order_data.get("status") or "calculation").lower()

            # Проверяем, подходит ли карточка под условия поиска и галочки
            match_search = (search_query in fio) or (search_query in contract) or (search_query in f"#{order_id}")
            match_status = (status in active_statuses)

            # Если карточка подходит — показываем строку таблицы, если нет — скрываем
            if match_search and match_status:
                self.table_orders.setRowHidden(row, False)
            else:
                self.table_orders.setRowHidden(row, True)

    def set_theme_mode(self, is_dark: bool):
        """Адаптирует фон левой ленты и поиска под переключатель тем ERP"""
        self.is_dark_theme = is_dark
        # Передаем значение темы в правый паспорт, чтобы его внутренности тоже знали о смене тем
        if hasattr(self, "passport_widget"):
            self.passport_widget.is_dark_theme = is_dark
            
        if not is_dark:
            self.table_orders.setStyleSheet("QTableWidget { background-color: #FFFFFF; border: none; }")
            self.txt_search.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #212529; border: 1px solid #CED4DA; border-radius: 4px; padding-left: 8px; }")
        else:
            self.table_orders.setStyleSheet("QTableWidget { background-color: #111114; border: none; }")
            self.txt_search.setStyleSheet("QLineEdit { background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #353540; border-radius: 4px; padding-left: 8px; }")
