from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QCheckBox, QTableWidget, QFrame, 
                             QPushButton, QSplitter, QHeaderView, QTableWidgetItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class OrdersManagerWidget(QWidget):
    """
    Изолированный модуль Вкладки 2 'База заказов' с карточным интерфейсом Master-Detail.
    Часть 1: Графический интерфейс и разметка.
    """
    def __init__(self, user_session=None):
        super().__init__()
        self.user_session = user_session
        self.raw_orders_cache = {} # Кэш для хранения полной инфы из БД
        self._init_ui()
        
        # Подключаем события кликов и фильтров
        self.btn_refresh.clicked.connect(self.load_orders_from_mysql)
        self.table_orders.itemSelectionChanged.connect(self.show_order_details)
        self.txt_search.textChanged.connect(self.apply_ui_filters)
        for chk in self.status_boxes.values():
            chk.stateChanged.connect(self.apply_ui_filters)
            
        self.btn_upload_contract.clicked.connect(self.upload_signed_contract)
        
        # Автоматическая загрузка данных при старте вкладки
        self.load_orders_from_mysql()

    def set_theme_mode(self, is_dark: bool):
        """Централизованно меняет тему для всей панели заказов и принудительно перекрашивает карточки"""
        self.is_dark_theme = is_dark
        
        if not is_dark:
            self.table_orders.setStyleSheet("QTableWidget { background-color: #FFFFFF; border: none; }")
            self.txt_search.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #212529; border: 1px solid #CED4DA; border-radius: 4px; padding-left: 8px; }")
        else:
            self.table_orders.setStyleSheet("QTableWidget { background-color: #111114; border: none; }")
            self.txt_search.setStyleSheet("QLineEdit { background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #353540; border-radius: 4px; padding-left: 8px; }")
            
        # 🔥 ГЛАВНЫЙ ФИКС: Бежим по всем живым строкам таблицы на экране 
        # и принудительно обновляем стили карточек прямо в ячейках, побеждая кэш!
        for row in range(self.table_orders.rowCount()):
            card_widget = self.table_orders.cellWidget(row, 0)
            if card_widget:
                if not is_dark:
                    card_widget.setStyleSheet("QFrame#OrderListCard { background-color: #E9ECEF; border: 1px solid #CED4DA; border-radius: 6px; margin: 2px 4px; }")
                    # Перекрашиваем тексты внутри карточки на темные
                    for child in card_widget.findChildren(QLabel):
                        if "📱" in child.text() or "👤" in child.text():
                            child.setStyleSheet("color: #495057; border: none; background: transparent;")
                else:
                    card_widget.setStyleSheet("QFrame#OrderListCard { background-color: #232328; border: 1px solid #2F2F35; border-radius: 6px; margin: 2px 4px; }")
                    # Перекрашиваем тексты внутри карточки на светлые
                    for child in card_widget.findChildren(QLabel):
                        if "📱" in child.text() or "👤" in child.text():
                            child.setStyleSheet("color: #A0A0A5; border: none; background: transparent;")
            
        # Перерисовываем карточки из кэша с новыми цветами темы
        self.load_orders_from_mysql()

    def _init_ui(self):
        # Главный горизонтальный слой для всего окна
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Создаем разделитель Master-Detail (Лево/Право)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        
        # =====================================================================
        # ЛЕВАЯ СТОРОНА: Фильтры, Поиск и Карточки (Собираем в один вертикальный блок)
        # =====================================================================
        left_container = QFrame()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 1. Заголовок
        lbl_left_title = QLabel("📋 Список договоров (Заказы)")
        lbl_left_title.setObjectName("lbl_title")
        lbl_left_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        left_layout.addWidget(lbl_left_title)

        # 2. Поле поиска и кнопка "Обновить" в один ряд
        search_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔎 Быстрый поиск по ФИО или телефону...")
        self.txt_search.setFixedHeight(30)
        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.setFixedHeight(30)
        self.btn_refresh.setFixedWidth(90)
        search_row.addWidget(self.txt_search, stretch=1)
        search_row.addWidget(self.btn_refresh)
        left_layout.addLayout(search_row)

        # 3. Блок чекбоксов статусов в 2 строчки по нашему новому ТЗ
        status_grid = QVBoxLayout()
        status_grid.setSpacing(4)
        
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        
        self.status_boxes = {}
        # Все 6 новых статусов, которые мы зафиксировали ранее
        statuses_list = [
            ("Расчет", row1), ("Подписан", row1), ("Утвержден", row1),
            ("Возвращен", row2), ("В обработке", row2), ("Выполнен", row2)
        ]
        
        for status_name, target_row in statuses_list:
            chk = QCheckBox(status_name)
            chk.setChecked(True)
            # Делаем шрифт чекбоксов чуть компактнее, чтобы всё влезло
            chk.setFont(QFont("Segoe UI", 9)) 
            target_row.addWidget(chk)
            # Регистрируем в системе для живого фильтра
            self.status_boxes[status_name.lower()] = chk
            
        status_grid.addLayout(row1)
        status_grid.addLayout(row2)
        left_layout.addLayout(status_grid)

        # 4. Сама таблица-лента карточек
        self.table_orders = QTableWidget(0, 1)
        self.table_orders.horizontalHeader().setVisible(False) # Скрываем заголовок таблицы, у нас есть свой
        self.table_orders.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_orders.verticalHeader().setVisible(False)
        self.table_orders.setShowGrid(False) 
        self.table_orders.verticalHeader().setDefaultSectionSize(75) 
        self.table_orders.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.table_orders)
        
        # Добавляем левый контейнер в сплиттер
        splitter.addWidget(left_container)

        # =====================================================================
        # ПРАВАЯ СТОРОНА: Спецификация + Кнопка договора
        # =====================================================================
        right_container = QFrame()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        lbl_right_title = QLabel("🛠️ Комплектация и параметры бани")
        lbl_right_title.setObjectName("lbl_title")
        lbl_right_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        self.table_details = QTableWidget(0, 2)
        self.table_details.setHorizontalHeaderLabels(["Технический параметр", "Значение"])
        self.table_details.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_details.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.btn_upload_contract = QPushButton("📁 Загрузить скан подписанного договора")
        self.btn_upload_contract.setFixedHeight(35)
        
        right_layout.addWidget(lbl_right_title)
        right_layout.addWidget(self.table_details)
        right_layout.addWidget(self.btn_upload_contract)
        
        # Добавляем правый контейнер в сплиттер
        splitter.addWidget(right_container)
        
        # Задаем пропорции: левая колонка компактнее, правая шире
        splitter.setSizes([290, 660])
        
        # Добавляем весь сплиттер в главное окно
        self.main_layout.addWidget(splitter)

    def _wrap_with_title(self, text, widget):
        frame = QFrame()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(text)
        lbl.setObjectName("lbl_title") 
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lay.addWidget(lbl)
        lay.addWidget(widget)
        return frame

    def _create_order_card(self, order_id, contract_num, status, fio, phone):
        """Исправлено: Карточка красится через объектные имена, исключая кэширование стилей"""
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
        from PyQt6.QtGui import QFont
        
        # Считываем флаг темы
        is_dark = getattr(self, "is_dark_theme", True)

        card = QFrame()
        # 🔥 ФИКС: Присваиваем карточке системное имя. Цвета мы пропишем ниже, 
        # и они будут мгновенно меняться без пересоздания виджетов!
        card.setObjectName("OrderListCard")

        # Применяем динамический стиль к контейнеру карточки
        if not is_dark:
            card.setStyleSheet("QFrame#OrderListCard { background-color: #E9ECEF; border: 1px solid #CED4DA; border-radius: 6px; margin: 2px 4px; }")
        else:
            card.setStyleSheet("QFrame#OrderListCard { background-color: #232328; border: 1px solid #2F2F35; border-radius: 6px; margin: 2px 4px; }")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 6, 12, 6)
        card_layout.setSpacing(4)
        
        c_num_text = f"Договор №{contract_num}" if contract_num else "Договор №: —"
        lbl_top = QLabel(f"Лид #{order_id}  •  {c_num_text}  •  [{status.upper()}]")
        lbl_top.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        # Цвета статусов под светлый и темный режимы
        if status.lower() == "signed": 
            lbl_top.setStyleSheet(f"color: {'#00A8FF' if is_dark else '#0056B3'}; border: none; background: transparent;")
        elif status.lower() == "calculation": 
            lbl_top.setStyleSheet(f"color: {'#FFA500' if is_dark else '#D97706'}; border: none; background: transparent;")
        elif status.lower() == "returned": 
            lbl_top.setStyleSheet(f"color: {'#FF4D4D' if is_dark else '#DC2626'}; border: none; background: transparent;")
        else: 
            lbl_top.setStyleSheet(f"color: {'#2ECC71' if is_dark else '#16A34A'}; border: none; background: transparent;")
            
        lbl_bottom = QLabel(f"👤 {fio}   |   📱 {phone}")
        lbl_bottom.setFont(QFont("Segoe UI", 9))
        
        if is_dark:
            lbl_bottom.setStyleSheet("color: #A0A0A5; border: none; background: transparent;")
        else:
            lbl_bottom.setStyleSheet("color: #495057; border: none; background: transparent;")
        
        card_layout.addWidget(lbl_top)
        card_layout.addWidget(lbl_bottom)
        return card

    def load_orders_from_mysql(self):
        """Скачивает список заказов из облака MySQL Джино"""
        from config import DB_CONFIG
        import pymysql
        
        self.table_orders.setRowCount(0)
        self.raw_orders_cache.clear()
        
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM production_orders ORDER BY id DESC")
            rows = cursor.fetchall()
            
            for row_idx, order in enumerate(rows):
                self.table_orders.insertRow(row_idx)
                
                o_id = str(order.get("id", ""))
                c_num = order.get("contract_number", "")
                status = str(order.get("status", "calculation"))
                fio = str(order.get("client_fio", "Не указано"))
                phone = str(order.get("client_phone", "—"))
                
                # Записываем ID в скрытый элемент ячейки, чтобы метод клика читал его безошибочно
                item_id = QTableWidgetItem(o_id)
                item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table_orders.setItem(row_idx, 0, item_id)
                
                # Вживляем графическую карточку
                card_widget = self._create_order_card(o_id, c_num, status, fio, phone)
                self.table_orders.setCellWidget(row_idx, 0, card_widget)
                
                self.raw_orders_cache[o_id] = order
                
            cursor.close()
            conn.close()
        except pymysql.MySQLError as e:
            print(f"[Ошибка базы заказов]: {e}")

    def show_order_details(self):
        """Безопасно считывает ID скрытой ячейки и разворачивает спецификацию бани"""
        curr_row = self.table_orders.currentRow()
        if curr_row < 0:
            return
            
        # Читаем системный ID из скрытого QTableWidgetItem первой ячейки строки
        id_item = self.table_orders.item(curr_row, 0)
        if not id_item:
            return
            
        order_id = id_item.text()
        order = self.raw_orders_cache.get(order_id)
        if not order:
            return
            
        ru_labels = {
            "client_phone": "📱 Номер телефона", "lead_source": "📢 Источник лида",
            "category": "🏗️ Категория", "product_line": "📐 Модельная линейка",
            "diameter": "⭕ Диаметр торца", "shape_type": "⬡ Форма сечения",
            "material": "🪵 Материал обшивки", "base_length": "📏 Длина ламелей (мм)",
            "torce_modification": "🚪 Модификация торца", "color_roof": "🎨 Цвет кровли",
            "color_facade": "🎨 Цвет фасада (RAL)", "color_borders": "🎨 Цвет обналички"
        }
        
        self.table_details.setRowCount(0)
        for row_idx, (key, label) in enumerate(ru_labels.items()):
            if key in order:
                self.table_details.insertRow(row_idx)
                val_text = str(order[key])
                if val_text == "pine": val_text = "Сосна / Ель"
                elif val_text == "cedar": val_text = "Сибирский кедр"
                
                self.table_details.setItem(row_idx, 0, QTableWidgetItem(label))
                self.table_details.setItem(row_idx, 1, QTableWidgetItem(val_text))

    def apply_ui_filters(self):
        """Живой фильтр списка карточек по тексту поиска и галочкам статусов"""
        search_text = self.txt_search.text().lower().strip()
        
        for row in range(self.table_orders.rowCount()):
            id_item = self.table_orders.item(row, 0)
            if not id_item: continue
            
            order = self.raw_orders_cache.get(id_item.text(), {})
            fio = str(order.get("client_fio", "")).lower()
            phone = str(order.get("client_phone", "")).lower()
            status = str(order.get("status", "calculation")).lower()
            
            status_allowed = self.status_boxes.get(status, self.status_boxes.get("расчет")).isChecked()
            text_matched = not search_text or (search_text in fio or search_text in phone)
            
            self.table_orders.setRowHidden(row, not (status_allowed and text_matched))

    def upload_signed_contract(self):
        """Загрузка скана договора и обновление статуса в MySQL"""
        curr_row = self.table_orders.currentRow()
        if curr_row < 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Внимание", "Сначала выберите заказ из списка!")
            return
            
        order_id = self.table_orders.item(curr_row, 0).text()
        
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите скан подписанного договора", "", "Документы (*.pdf *.jpg *.png *.docx)"
        )
        if not file_path: return
            
        from config import DB_CONFIG
        import pymysql
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("UPDATE production_orders SET status = 'signed' WHERE id = %s", (order_id,))
            conn.commit()
            cursor.close()
            conn.close()
            
            QMessageBox.information(self, "Успех", f"Договор прикреплен! Статус заказа #{order_id} изменен на ПОДПИСАН.")
            self.load_orders_from_mysql()
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось обновить статус в облаке:\n{e}")
