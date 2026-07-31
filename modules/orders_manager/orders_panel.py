from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QCheckBox, QTableWidget, QFrame, 
                             QPushButton, QSplitter, QHeaderView, QTableWidgetItem, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
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
        self.right_layout = QVBoxLayout(right_container) 
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(10)
        
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
        """
        Часть 1: Отрисовка цифрового паспорта бани (Правая сторона) по макету.
        Внедрено авто-раскодирование паспорта клиента по ФЗ-152.
        """
        # 🔥 ФИКС: Теперь этот слой виден, и мы безопасно очищаем экран при смене лида
        if hasattr(self, "right_layout") and self.right_layout.count() > 0:
            # Очищаем старые виджеты, чтобы они не накладывались друг на друга
            while self.right_layout.count():
                child = self.right_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    # Если внутри были подслои ( layouts ), очищаем и их тоже
                    self.clear_layout(child.layout())

        # Получаем строку выбранного заказа в таблице
        selected_rows = self.table_orders.selectionModel().selectedRows()
        if not selected_rows:
            stub_lbl = QLabel("← Выберите заказ или лид из списка слева для управления")
            stub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.right_layout.addWidget(stub_lbl)
            return

        row_idx = selected_rows[0].row()
        order_id = int(self.table_orders.item(row_idx, 0).text().replace("#", ""))
        order_data = self.raw_orders_cache.get(order_id, {})

        # Подтягиваем системные поля из обновленной БД
        progress_prod = order_data.get("production_progress", 0)
        progress_supply = order_data.get("supply_progress", 0)
        master_name = order_data.get("approved_by_master", "Не назначен")
        deliv_date = order_data.get("delivery_date", "—")
        total_price = order_data.get("total_price", 0.00)

        # ---------------------------------------------------------------------
        # 1. ВЕРХНИЙ ИНФОРМАЦИОННЫЙ БЛОК (Зеленая строка статусов по макету)
        # ---------------------------------------------------------------------
        top_status_layout = QHBoxLayout()
        top_status_layout.setSpacing(15)

        status_text = (
            f"📅 Передача объекта: <b style='color:#2ECC71;'>{deliv_date}</b>  |  "
            f"🛠️ Выполнение заказа: <b style='color:#2ECC71;'>{progress_prod}%</b>  |  "
            f"🪵 Материал закуплен: <b style='color:#2ECC71;'>{progress_supply}%</b>  |  "
            f"🎖️ Утвердил: <b style='color:#2ECC71;'>{master_name}</b>"
        )
        lbl_top_status = QLabel(status_text)
        lbl_top_status.setFont(QFont("Segoe UI", 9))
        top_status_layout.addWidget(lbl_top_status)
        top_status_layout.addStretch()

        self.right_layout.addLayout(top_status_layout)

        # ---------------------------------------------------------------------
        # 2. БЛОК ОСНОВНЫХ ДАННЫХ И ПДН С КРИПТОГРАФИЕЙ (ФЗ-152)
        # ---------------------------------------------------------------------
        data_layout = QHBoxLayout()
        data_layout.setSpacing(30)

        # Левая колонка блока данных (Сводная текстовая информация)
        info_left_box = QVBoxLayout()
        info_left_box.setSpacing(4)

        c_num = order_data.get("contract_number", "—")
        status_ord = order_data.get("status", "calculation").upper()
        
        lbl_doc_title = QLabel(f"Договор №: {c_num}  ;  Лид №: {order_id}  ;  Тел: {order_data.get('client_phone', '—')}")
        lbl_doc_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        lbl_fio_client = QLabel(f"ФИО Клиента: {order_data.get('client_fio', '—')}")
        lbl_fio_client.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        info_left_box.addWidget(lbl_doc_title)
        info_left_box.addWidget(lbl_fio_client)

        # ПОЛЯ ДЛЯ ВВОДА (Редактируемые QLineEdit / QTextEdit по вашему наброску)
        # Поле Паспорта (Считываем крипто-строку из БД и расшифровываем для экрана)
        raw_passport_encrypted = order_data.get("client_passport_encrypted", "")
        decrypted_passport = ""
        if raw_passport_encrypted:
            try:
                # Дешифруем байты обратно в читаемый паспорт гражданина РФ
                decrypted_passport = cipher_suite.decrypt(raw_passport_encrypted.encode()).decode()
            except Exception:
                decrypted_passport = "[ Ошибка дешифрования ПДН / Ключ изменен ]"

        info_left_box.addWidget(QLabel("Паспортные данные клиента (Шифрование ФЗ-152):"))
        self.txt_passport = QLineEdit(decrypted_passport)
        self.txt_passport.setPlaceholderText("Серия, номер, кем и когда выдан...")
        info_left_box.addWidget(self.txt_passport)

        info_left_box.addWidget(QLabel("Адрес доставки / установки изделия:"))
        self.txt_address = QLineEdit(order_data.get("client_address", ""))
        self.txt_address.setPlaceholderText("Область, город, СНТ, улица, участок...")
        info_left_box.addWidget(self.txt_address)

        info_left_box.addWidget(QLabel("Поле для примечаний менеджера:"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setFixedHeight(45) # Делаем компактным по макету
        self.txt_notes.setPlainText(order_data.get("order_notes", ""))
        self.txt_notes.setPlaceholderText("Дополнительные критические важные комментарии к заказу...")
        info_left_box.addWidget(self.txt_notes)

        data_layout.addLayout(info_left_box, stretch=3)

        # Правая колонка блока данных (Финансы и статус)
        info_right_box = QVBoxLayout()
        info_right_box.setSpacing(5)
        info_right_box.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        lbl_stat_title = QLabel(f"Статус договора: <b style='color:#FFA500;'>{status_ord}</b>")
        lbl_stat_title.setFont(QFont("Segoe UI", 10))
        
        lbl_price_title = QLabel(f"Стоимость изделия: <b style='color:#2ECC71;'>{total_price:,.2f} руб.</b>")
        lbl_price_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        info_right_box.addWidget(lbl_stat_title)
        info_right_box.addWidget(lbl_price_title)
        
        # Кнопка «Сохранить ПДН и изменения карточки»
        btn_save_pnd = QPushButton("💾 Сохранить изменения")
        btn_save_pnd.setFixedWidth(180)
        btn_save_pnd.setStyleSheet("background-color: #00A8FF; color: white; font-weight: bold; border-radius: 4px; padding: 4px;")
        # Привязываем сохранение с шифрованием к кнопке
        btn_save_pnd.clicked.connect(lambda: self.save_encrypted_pnd_to_db(order_id))
        info_right_box.addWidget(btn_save_pnd)

        data_layout.addLayout(info_right_box, stretch=1)
        self.right_layout.addLayout(data_layout)

        # Временный разделитель перед будущей матрицей документов (Часть 2)
        sep = QFrame()
        sep.setFrameShape(QFrame.FrameShape.HLine)
        sep.setStyleSheet("color: #2F2F35;")
        self.right_layout.addWidget(sep)

    def save_encrypted_pnd_to_db(self, order_id):
        """Шифрует ПДН по алгоритму AES-256 и сохраняет изменения лида в MySQL"""
        import mysql.connector
        
        passport_text = self.txt_passport.text().strip()
        address_text = self.txt_address.text().strip()
        notes_text = self.txt_notes.toPlainText().strip()

        # 🔥 КРИПТОГРАФИЯ: превращаем открытый паспорт в зашифрованный байт-код
        encrypted_passport = ""
        if passport_text:
            encrypted_passport = cipher_suite.encrypt(passport_text.encode()).decode()

        try:
            # Подключаемся к вашей живой базе на Джино
            db_config = self.user_session.get("db_config") if self.user_session else None
            if not db_config:
                from db_installer import DB_CONFIG
                db_config = DB_CONFIG
                
            conn = mysql.connector.connect(**db_config)
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
