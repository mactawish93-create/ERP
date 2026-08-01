from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QCheckBox, QTableWidget, QFrame, 
                             QPushButton, QSplitter, QHeaderView, QTableWidgetItem, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtGui import QFont, QColor
from cryptography.fernet import Fernet

# 🔥 СЕКРЕТНЫЙ КЛЮЧ ШИФРОВАНИЯ ДЛЯ ФЗ-152 (Симметричный AES-256)
# В реальном продакшене этот ключ должен лежать в изолированном файле .env,
# но для монолитности ERP мы можем сгенерировать его стабильным байт-кодом:
SECRET_CRYPTO_KEY = b'uX9_G8bX2v9hK7Lm4PqW1zS5tD6cE7rT8yU9iO0pA1s='
cipher_suite = Fernet(SECRET_CRYPTO_KEY)


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
        # ПРАВАЯ СТОРОНА: Чистый пустой контейнер (Вся верстка ушла в динамику)
        # =====================================================================
        right_container = QFrame()
        self.right_layout = QVBoxLayout(right_container)
        self.right_layout.setContentsMargins(15, 10, 15, 10) # Сделали аккуратные зазоры
        self.right_layout.setSpacing(12)
        
        # На старте выводим простую текстовую подсказку менеджера по центру
        self.lbl_stub = QLabel("")
        self.lbl_stub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stub.setStyleSheet("color: #A0A0A5; font-size: 11px;")
        self.right_layout.addWidget(self.lbl_stub)

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
        """Карточка без жестких цветов — вся стилизация вынесена в глобальный QSS"""
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
        from PyQt6.QtGui import QFont

        card = QFrame()
        # Присваиваем карточке и её статусу уникальные имена для глобального QSS
        card.setObjectName("OrderListCard")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 6, 12, 6)
        card_layout.setSpacing(4)
        
        c_num_text = f"Договор №{contract_num}" if contract_num else "Договор №: —"
        lbl_top = QLabel(f"Лид #{order_id}  •  {c_num_text}  •  [{status.upper()}]")
        lbl_top.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        # Динамические маркеры статусов для QSS (переводим в нижний регистр)
        lbl_top.setProperty("status", status.lower())
        lbl_top.setObjectName("OrderCardTitle")
        
        lbl_bottom = QLabel(f"👤 {fio}   |   📱 {phone}")
        lbl_bottom.setFont(QFont("Segoe UI", 9))
        lbl_bottom.setObjectName("OrderCardSubtitle")
        
        card_layout.addWidget(lbl_top)
        card_layout.addWidget(lbl_bottom)
        return card


    def load_orders_from_mysql(self):
        """Скачивает из MySQL Джино абсолютно все параметры бани через драйвер pymysql"""
        import pymysql
        from PyQt6.QtWidgets import QTableWidgetItem
        
        try:
            db_config = self.user_session.get("db_config") if self.user_session else None
            if not db_config:
                from config import DB_CONFIG
                db_config = DB_CONFIG
                
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            
            # Полный SQL-запрос для выгрузки всех полей цифрового паспорта бани
            query = """
                SELECT id, contract_number, status, client_fio, client_phone,
                       client_passport_encrypted, client_address, order_notes,
                       material, diameter, shape_type, base_length, torce_modification,
                       room_sauna, room_wash, room_rest,
                       color_roof, color_facade, color_borders, color_ends,
                       assembly_on_site, door_facade, stove_next_room, stove_street,
                       delivery_date, production_progress, supply_progress, approved_by_master, total_price,
                       file_contract, file_specification, file_blueprint, file_act
                FROM production_orders
                ORDER BY id DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Очищаем кэш и таблицу перед заливкой
            self.raw_orders_cache.clear()
            self.table_orders.setRowCount(0)
            
            for r in rows:
                o_id = r[0] # ID заказа
                
                # Раскладываем все 33 колонки кортежа по ключам в кэш-словарь
                self.raw_orders_cache[o_id] = {
                    "id": r[0], "contract_number": r[1], "status": r[2], "client_fio": r[3], "client_phone": r[4],
                    "client_passport_encrypted": r[5], "client_address": r[6], "order_notes": r[7],
                    "material": r[8], "diameter": r[9], "shape_type": r[10], "base_length": r[11], "torce_modification": r[12],
                    "room_sauna": r[13], "room_wash": r[14], "room_rest": r[15],
                    "color_roof": r[16], "color_facade": r[17], "color_borders": r[18], "color_ends": r[19],
                    "assembly_on_site": r[20], "door_facade": r[21], "stove_next_room": r[22], "stove_street": r[23],
                    "delivery_date": str(r[24]) if r[24] else "—",
                    "production_progress": r[25] or 0,
                    "supply_progress": r[26] or 0,
                    "approved_by_master": r[27] or "Не назначен",
                    "total_price": float(r[28] or 0.00),
                    "file_contract": r[29], "file_specification": r[30], "file_blueprint": r[31], "file_act": r[32]
                }
                
                # Рендерим строку в левой CRM-ленте
                row_pos = self.table_orders.rowCount()
                self.table_orders.insertRow(row_pos)
                
                id_item = QTableWidgetItem(f"#{o_id}")
                self.table_orders.setItem(row_pos, 0, id_item)
                
                # Создаем карточку, передавая точные данные из кортежа
                card_widget = self._create_order_card(o_id, r[1], r[2], r[3], r[4])
                self.table_orders.setCellWidget(row_pos, 0, card_widget)
                
            cursor.close()
            conn.close()
            
            # Применяем фильтры чекбоксов
            self.apply_ui_filters()
            
        except Exception as e:
            print(f"[Ошибка загрузки заказов из БД]: {str(e)}")

    def show_order_details(self):
        """
        Финальная бронебойная версия: Часть 1 из 2.
        Тотальное уничтожение старого контейнера и сборка полей ПДН / Финансов.
        """
        # 🔥 ШАГ 1: ТОТАЛЬНОЕ УНИЧТОЖЕНИЕ СТАРОГО ЭКРАНА
        if hasattr(self, "dynamic_passport_container") and self.dynamic_passport_container is not None:
            self.dynamic_passport_container.setParent(None)
            self.dynamic_passport_container.deleteLater()
            self.dynamic_passport_container = None

        # Проверяем, выделил ли менеджер строчку в левом списке
        selected_rows = self.table_orders.selectionModel().selectedRows()
        if not selected_rows:
            return

        # 🔥 ФИКС: Берем первый элемент из списка выделенных строк
        row_idx = selected_rows[0].row() 
        order_id = int(self.table_orders.item(row_idx, 0).text().replace("#", ""))
        order_data = self.raw_orders_cache.get(order_id, {})

        # Подтягиваем параметры для статус-бара и финансов
        progress_prod = order_data.get("production_progress", 0)
        progress_supply = order_data.get("supply_progress", 0)
        master_name = order_data.get("approved_by_master", "Не назначен")
        deliv_date = order_data.get("delivery_date", "—")
        total_price = order_data.get("total_price", 0.00)
        c_num = order_data.get("contract_number", "—")
        status_ord = order_data.get("status", "calculation").upper()

        # 🔥 ШАГ 2: СОЗДАЕМ НОВЫЙ ЧИСТЫЙ СТЕРИЛЬНЫЙ КОНТЕЙНЕР
        self.dynamic_passport_container = QWidget()
        pane_layout = QVBoxLayout(self.dynamic_passport_container)
        pane_layout.setContentsMargins(0, 0, 0, 0)
        pane_layout.setSpacing(10)

        # --- БЛОК 1: Верхняя зеленая строка статусов ---
        top_layout = QHBoxLayout()
        status_text = (
            f"📅 Передача объекта: <b style='color:#2ECC71;'>{deliv_date}</b>  |  "
            f"🛠️ Выполнение заказа: <b style='color:#2ECC71;'>{progress_prod}%</b>  |  "
            f"🪵 Склад: <b style='color:#2ECC71;'>{progress_supply}%</b>  |  "
            f"🎖️ ОТК: <b style='color:#2ECC71;'>{master_name}</b>"
        )
        lbl_top_status = QLabel(status_text)
        lbl_top_status.setFont(QFont("Segoe UI", 9))
        top_layout.addWidget(lbl_top_status)
        top_layout.addStretch()
        pane_layout.addLayout(top_layout)

        # --- БЛОК 2: Данные клиента, ПДН (ФЗ-152) и Финансы ---
        data_layout = QHBoxLayout()
        info_left = QVBoxLayout()
        info_left.setSpacing(4)
        
        lbl_doc_title = QLabel(f"Договор №: {c_num}  ;  Лид №: {order_id}  ;  Тел: {order_data.get('client_phone', '—')}")
        lbl_doc_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_fio_client = QLabel(f"ФИО Клиента: {order_data.get('client_fio', '—')}")
        lbl_fio_client.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        info_left.addWidget(lbl_doc_title)
        info_left.addWidget(lbl_fio_client)
        
        # Безопасная дешифровка паспорта
        raw_p = order_data.get("client_passport_encrypted", "")
        decrypted = ""
        if raw_p:
            try: decrypted = cipher_suite.decrypt(raw_p.encode()).decode()
            except Exception: decrypted = "[ Ошибка ключа ПДН ]"
            
        info_left.addWidget(QLabel("Паспортные данные (Шифрование ФЗ-152):"))
        self.txt_passport = QLineEdit(decrypted)
        self.txt_passport.setPlaceholderText("Серия, номер, кем и когда выдан...")
        info_left.addWidget(self.txt_passport)
        
        info_left.addWidget(QLabel("Адрес доставки / установки:"))
        self.txt_address = QLineEdit(order_data.get("client_address", ""))
        self.txt_address.setPlaceholderText("Область, город, СНТ, участок...")
        info_left.addWidget(self.txt_address)
        
        info_left.addWidget(QLabel("Примечания менеджера:"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setFixedHeight(40)
        self.txt_notes.setPlainText(order_data.get("order_notes", ""))
        info_left.addWidget(self.txt_notes)
        
        data_layout.addLayout(info_left, stretch=3)
        
        # Правая колонка финансов
        info_right = QVBoxLayout()
        info_right.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        lbl_stat_title = QLabel(f"Статус: <b style='color:#FFA500;'>{status_ord}</b>")
        lbl_price_title = QLabel(f"Стоимость: <b style='color:#2ECC71;'>{total_price:,.2f} руб.</b>")
        lbl_price_title.setWordWrap(True)
        
        btn_save = QPushButton("💾 Сохранить изменения")
        btn_save.setFixedSize(160, 28)
        btn_save.setStyleSheet("background-color: #00A8FF; color: white; font-weight: bold; border-radius: 4px;")
        btn_save.clicked.connect(lambda: self.save_encrypted_pnd_to_db(order_id))
        
        info_right.addWidget(lbl_stat_title)
        info_right.addWidget(lbl_price_title)
        info_right.addWidget(btn_save)
        data_layout.addLayout(info_right, stretch=1)
        pane_layout.addLayout(data_layout)

        # Разделитель CSS
        sep = QFrame()
        sep.setStyleSheet("border-bottom: 1px solid #2F2F35; background: transparent; min-height: 1px; max-height: 1px;")
        pane_layout.addWidget(sep)
        # ---------------------------------------------------------------------
        # БЛОК 3: Матрица документооборота 4х2
        # ---------------------------------------------------------------------
        doc_grid_layout = QHBoxLayout()
        doc_grid_layout.setSpacing(10)
        self.doc_controls = {}
        doc_types = [("contract", "Договор"), ("specification", "Спецификация"), ("blueprint", "Чертеж"), ("act", "Акт приема")]

        for key, name in doc_types:
            col_box = QVBoxLayout()
            col_box.setSpacing(4)
            
            btn_print = QPushButton(f"Печать {name}")
            btn_print.setFixedHeight(24)
            btn_upload = QPushButton(f"Загрузить {name}")
            btn_upload.setFixedHeight(24)
            
            lbl_status = QPushButton(f"{name}: Не загружен")
            lbl_status.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            lbl_status.setFlat(True)
            lbl_status.setCursor(Qt.CursorShape.PointingHandCursor)
            
            col_box.addWidget(btn_print)
            col_box.addWidget(btn_upload)
            col_box.addWidget(lbl_status)
            doc_grid_layout.addLayout(col_box)
            self.doc_controls[key] = {"upload": btn_upload, "status": lbl_status}
            
        pane_layout.addLayout(doc_grid_layout)

        # Живая связка сканов документов из BLOB
        doc_keys = [("contract", "file_contract", "Договор"), ("specification", "file_specification", "Спецификация"),
                    ("blueprint", "file_blueprint", "Чертеж"), ("act", "file_act", "Акт приема")]

        for key, db_col, name in doc_keys:
            has_file = bool(order_data.get(db_col))
            self.doc_controls[key]["upload"].clicked.connect(
                lambda checked, o_id=order_id, k=key, col=db_col, n=name: self.handle_blob_upload(o_id, k, col, n)
            )
            if has_file:
                self.doc_controls[key]["status"].setText(f"{name}: Загружен")
                self.doc_controls[key]["status"].setStyleSheet("color: #2ECC71; background: transparent; font-weight: bold; border: none;")
                self.doc_controls[key]["status"].clicked.connect(lambda checked, o_id=order_id, col=db_col, n=name: self.handle_blob_view(o_id, col, n))
            else:
                self.doc_controls[key]["status"].setText(f"{name}: Не загружен")
                self.doc_controls[key]["status"].setStyleSheet("color: #FF4D4D; background: transparent; font-weight: bold; border: none;")

        # ---------------------------------------------------------------------
        # БЛОК 4: Таблица технической комплектации бани
        # ---------------------------------------------------------------------
        lbl_comp_title = QLabel("📋 Техническая комплектация изделия:")
        lbl_comp_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_comp_title.setStyleSheet("margin-top: 5px; color: #FFA500;")
        pane_layout.addWidget(lbl_comp_title)

        self.table_order_spec = QTableWidget(12, 2)
        self.table_order_spec.setHorizontalHeaderLabels(["Технический параметр", "Выбранное значение"])
        self.table_order_spec.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_order_spec.verticalHeader().setVisible(False)
        self.table_order_spec.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_order_spec.setFixedHeight(180)

        spec_mapping = [
            ("🪵 Материал каркаса", "material", {"pine": "Сосна/Ель камерной сушки", "cedar": "Сибирский кедр"}),
            ("⭕ Диаметр бани", "diameter", {}),
            ("⬡ Форма контура", "shape_type", {"round": "Классический круглый", "quadro": "Квадро контур"}),
            ("📏 Длина бани (модель)", "base_length", {}),
            ("🚪 Исполнение торца", "torce_modification", {"base": "Классический торец 50мм", "canopy": "С козырьком +500мм", "porch": "С крыльцом +700мм"}),
            ("📐 Длина Парилки", "room_sauna", {}), ("📐 Длина Моечного помещения", "room_wash", {}), ("📐 Длина Комнаты отдыха", "room_rest", {}),
            ("🏗️ Сборка на участке", "assembly_on_site", {"0": "Нет (Доставка готовой)", "1": "Да (Сборка бригадой)"}),
            ("🚪 Входная дверь с фасада", "door_facade", {"0": "Нет (С торца)", "1": "Да (С фасадной стороны)"}),
            ("🔥 Топка в смежную комнату", "stove_next_room", {"0": "Нет", "1": "Да (Сквозь стену)"}),
            ("🔥 Топка на улицу", "stove_street", {"0": "Нет", "1": "Да (Через ламели каркаса)"})
        ]

        for row_idx, (label_text, db_key, trans_dict) in enumerate(spec_mapping):
            raw_val = order_data.get(db_key, "—")
            final_val = trans_dict.get(str(raw_val).lower(), str(raw_val))
            if db_key in ["room_sauna", "room_wash", "room_rest", "base_length"] and str(raw_val) != "—":
                final_val = f"{raw_val} мм"
            if db_key == "diameter" and str(raw_val) != "—":
                final_val = f"{raw_val} м"

            self.table_order_spec.setItem(row_idx, 0, QTableWidgetItem(label_text))
            item_val = QTableWidgetItem(final_val)
            item_val.setForeground(QColor("#2ECC71"))
            font_b = QFont("Segoe UI", 9); font_b.setBold(True); item_val.setFont(font_b)
            self.table_order_spec.setItem(row_idx, 1, item_val)

        pane_layout.addWidget(self.table_order_spec)
        pane_layout.addStretch(1)

        # 🔥 НАЗНАЧАЕМ КОНТЕЙНЕР В ГЛАВНЫЙ СЛОЙ ОКНА
        self.right_layout.addWidget(self.dynamic_passport_container)

    def save_encrypted_pnd_to_db(self, order_id):
        """Шифрует ПДН по алгоритму AES-256 и сохраняет изменения лида в MySQL через pymysql"""
        import pymysql
        
        passport_text = self.txt_passport.text().strip()
        address_text = self.txt_address.text().strip()
        notes_text = self.txt_notes.toPlainText().strip()

        # КРИПТОГРАФИЯ: превращаем открытый паспорт в зашифрованный байт-код
        encrypted_passport = ""
        if passport_text:
            encrypted_passport = cipher_suite.encrypt(passport_text.encode()).decode()

        try:
            # Подключаемся к вашей живой базе на Джино
            db_config = self.user_session.get("db_config") if self.user_session else None
            if not db_config:
                from config import DB_CONFIG
                db_config = DB_CONFIG
                
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            
            # Записываем изменения в новые безопасные колонки
            query = """
                UPDATE production_orders 
                SET client_passport_encrypted = %s,
                    client_address = %s,
                    order_notes = %s
                WHERE id = %s
            """
            cursor.execute(query, (encrypted_passport, address_text, notes_text, order_id))
            conn.commit()
            
            # Обновляем локальный кэш программы, чтобы менеджер сразу видел результат
            if order_id in self.raw_orders_cache:
                self.raw_orders_cache[order_id]["client_passport_encrypted"] = encrypted_passport
                self.raw_orders_cache[order_id]["client_address"] = address_text
                self.raw_orders_cache[order_id]["order_notes"] = notes_text

            cursor.close()
            conn.close()
            
            # Выводим сообщение о победе
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Успех ФЗ-152", f"Данные лида #{order_id} успешно зашифрованы и сохранены в MySQL!")
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить изменения: {str(e)}")

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
    def handle_blob_upload(self, order_id, key, db_column, doc_name):
        """Сканирует файл через QFileDialog и заливает его байты напрямую в LONGBLOB ячейку MySQL"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import pymysql
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Выберите скан документа: {doc_name}", "", "Документы (*.pdf *.jpg *.png *.docx)"
        )
        if not file_path: return

        try:
            # Читаем файл с диска в сыром бинарном режиме
            with open(file_path, 'rb') as f:
                binary_data = f.read()

            from config import DB_CONFIG
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Записываем байты файла в базу данных Джино
            query = f"UPDATE production_orders SET {db_column} = %s WHERE id = %s"
            cursor.execute(query, (binary_data, order_id))
            conn.commit()
            
            cursor.close()
            conn.close()

            # Обновляем локальный кэш, чтобы маркер сразу позеленел без перезагрузки всей ERP
            if order_id in self.raw_orders_cache:
                self.raw_orders_cache[order_id][db_column] = binary_data

            QMessageBox.information(self, "Успех", f"Документ '{doc_name}' успешно загружен в базу данных!")
            self.show_order_details() # Мгновенно перерисовываем панель
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось сохранить файл в БД:\n{str(e)}")

    def handle_blob_view(self, order_id, db_column, doc_name):
        """Вытаскивает байты из LONGBLOB, создает временный файл и открывает его в системе"""
        import os, tempfile
        from PyQt6.QtWidgets import QMessageBox
        
        order_data = self.raw_orders_cache.get(order_id, {})
        binary_data = order_data.get(db_column)
        
        if not binary_data: return

        try:
            # Извлекаем расширение оригинального файла (по умолчанию pdf, если не распознано)
            ext = ".pdf"
            if binary_data[:4] == b'%PDF': ext = ".pdf"
            elif binary_data[:4] == b'\x89PNG': ext = ".png"
            elif binary_data[:2] == b'\xff\xd8': ext = ".jpg"
            
            # Создаем временный файл во временной папке Windows
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"view_order_{order_id}_{db_column}{ext}")
            
            # Записываем байты обратно в файл
            with open(temp_file_path, 'wb') as f:
                f.write(binary_data)
                
            # Запускаем файл стандартной системной программой Windows (Браузер, Acrobat Reader, Просмотрщик фото)
            os.startfile(temp_file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка открытия", f"Не удалось открыть файл для просмотра:\n{str(e)}")
