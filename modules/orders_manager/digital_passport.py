# modules/orders_manager/digital_passport.py
import os
import tempfile
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QFrame, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# Импортируем методы из нашего слоя базы данных db_worker
from modules.orders_manager.db_worker import (decrypt_passport_string, 
                                              update_encrypted_pnd, 
                                              upload_document_blob)

class DigitalPassportWidget(QWidget):
    """
    Самостоятельный UI-компонент цифрового паспорта бани (Правая сторона панели).
    Изолирует верстку ПДН (ФЗ-152), финансовых расчетов и таблицы спецификаций.
    """
    def __init__(self, parent_panel):
        super().__init__()
        self.parent_panel = parent_panel # Ссылка на главный контроллер для обновления кэша
        self.dynamic_passport_container = None
        self._init_ui()

    def _init_ui(self):
        # Стартовый плоский слой-контейнер
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 10, 15, 10)
        self.main_layout.setSpacing(12)
        
        # На старте программы выводим аккуратную текстовую заглушку
        self.lbl_stub = QLabel("← Выберите заказ или лид из списка слева для управления")
        self.lbl_stub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stub.setStyleSheet("color: #A0A0A5; font-size: 11px;")
        self.main_layout.addWidget(self.lbl_stub)

    def display_order(self, order_id, order_data):
        """Отрисовывает паспорт конкретного выбранного заказа с полной зачисткой экрана"""
        # 1. ЖЕСТКАЯ ОЧИСТКА СТАРОГО ЭКРАНА С УДАЛЕНИЕМ ИЗ ПАМЯТИ
        if self.lbl_stub:
            self.lbl_stub.deleteLater()
            self.lbl_stub = None
            
        if self.dynamic_passport_container is not None:
            self.dynamic_passport_container.setParent(None)
            self.dynamic_passport_container.deleteLater()
            self.dynamic_passport_container = None

        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Извлекаем системные переменные для шапки и финансов
        progress_prod = order_data.get("production_progress", 0)
        progress_supply = order_data.get("supply_progress", 0)
        master_name = order_data.get("approved_by_master", "Не назначен")
        deliv_date = order_data.get("delivery_date", "—")
        total_price = float(order_data.get("total_price") or 0.00)
        c_num = order_data.get("contract_number", "—")
        status_ord = order_data.get("status", "calculation").upper()
        
        # 🔥 ФИНАНСОВЫЙ ДВИЖОК: Считываем аванс и вычисляем остаток
        advance_pay = float(order_data.get("advance_payment") or 0.00)
        balance_pay = total_price - advance_pay

        # 2. СОЗДАЕМ НОВЫЙ ЧИСТЫЙ ДИНАМИЧЕСКИЙ ВИДЖЕТ
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
        
        # Безопасная дешифровка паспорта и нового адреса регистрации по ФЗ-152 через db_worker
        decrypted_passport = decrypt_passport_string(order_data.get("client_passport_encrypted", ""))
        decrypted_reg_address = decrypt_passport_string(order_data.get("client_reg_address_encrypted", ""))
            
        info_left.addWidget(QLabel("Паспортные данные (Шифрование ФЗ-152):"))
        self.txt_passport = QLineEdit(decrypted_passport)
        self.txt_passport.setPlaceholderText("Серия, номер, кем и когда выдан...")
        info_left.addWidget(self.txt_passport)
        
        # 🔥 НОВОЕ КРИПТО-ПОЛЕ: Адрес регистрации
        info_left.addWidget(QLabel("Адрес регистрации по паспорту (Шифрование ФЗ-152):"))
        self.txt_reg_address = QLineEdit(decrypted_reg_address)
        self.txt_reg_address.setPlaceholderText("Индекс, область, город, улица, дом, кв...")
        info_left.addWidget(self.txt_reg_address)
        
        info_left.addWidget(QLabel("Адрес доставки / установки бани:"))
        self.txt_address = QLineEdit(order_data.get("client_address", ""))
        self.txt_address.setPlaceholderText("Область, город, СНТ, участок...")
        info_left.addWidget(self.txt_address)
        
        info_left.addWidget(QLabel("Примечания менеджера:"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setFixedHeight(40)
        self.txt_notes.setPlainText(order_data.get("order_notes", ""))
        info_left.addWidget(self.txt_notes)
        
        data_layout.addLayout(info_left, stretch=3)
        
        # --- Правая колонка финансов (Модернизация: Стандарт / Рассрочка) ---
        info_right = QVBoxLayout()
        info_right.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        info_right.setSpacing(6)
        
        lbl_stat_title = QLabel(f"Статус: <b style='color:#FFA500;'>{status_ord}</b>")
        lbl_stat_title.setFont(QFont("Segoe UI", 10))
        
        lbl_price_title = QLabel(f"Стоимость: <span style='color:#2ECC71;'>{total_price:,.2f} ₽</span>")
        lbl_price_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        lbl_adv_caption = QLabel("Внесенный аванс (₽):")
        self.txt_advance = QLineEdit(f"{advance_pay:.2f}")
        self.txt_advance.setFixedWidth(165)
        self.txt_advance.setFixedHeight(24)
        self.txt_advance.textChanged.connect(lambda text: self._recalculate_balance(total_price, text))
        
        self.lbl_balance_title = QLabel(f"Остаток: <span style='color:#FF4D4D;'>{balance_pay:,.2f} ₽</span>")
        self.lbl_balance_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        # 🔥 НОВЫЙ БЛОК: Выбор метода оплаты
        info_right.addWidget(QLabel("Метод оплаты:"))
        self.cmb_payment_type = QComboBox()
        self.cmb_payment_type.setFixedWidth(165)
        self.cmb_payment_type.addItems(["💳 Стандартная", "📈 Рассрочка фабрики"])
        
        # Поле ввода количества месяцев рассрочки (скрытое по умолчанию)
        self.lbl_months_caption = QLabel("Срок рассрочки (мес):")
        self.txt_installment_months = QLineEdit("4") # Базово ставим 4 месяца
        self.txt_installment_months.setFixedWidth(165)
        self.txt_installment_months.setPlaceholderText("От 1 до 12...")
        
        # Динамическая интерактивная таблица графика взносов
        self.table_installment = QTableWidget(0, 2)
        self.table_installment.setFixedWidth(165)
        self.table_installment.setFixedHeight(120)
        self.table_installment.setHorizontalHeaderLabels(["Сумма (₽)", "Дата сдачи"])
        self.table_installment.verticalHeader().setDefaultSectionSize(20)
        self.table_installment.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Прячем элементы рассрочки по умолчанию
        self.lbl_months_caption.hide()
        self.txt_installment_months.hide()
        self.table_installment.hide()
        
        # Связываем сигналы тумблера и изменения месяцев с нашими алгоритмами
        self.cmb_payment_type.currentIndexChanged.connect(lambda idx: self._toggle_payment_mode(total_price))
        self.txt_installment_months.textChanged.connect(lambda text: self._generate_auto_schedule(total_price, text))
        
        btn_save = QPushButton("💾 Сохранить изменения")
        btn_save.setFixedSize(165, 28)
        btn_save.setStyleSheet("background-color: #00A8FF; color: white; font-weight: bold; border-radius: 4px;")
        btn_save.clicked.connect(lambda: self._trigger_pnd_save(order_id))
        
        # Выстраиваем строгую иерархию виджетов в панели
        info_right.addWidget(lbl_stat_title)
        info_right.addWidget(lbl_price_title)
        info_right.addWidget(lbl_adv_caption)
        info_right.addWidget(self.txt_advance)
        info_right.addWidget(self.lbl_balance_title)
        
        # Вшиваем элементы управления рассрочкой
        info_right.addWidget(self.cmb_payment_type)
        info_right.addWidget(self.lbl_months_caption)
        info_right.addWidget(self.txt_installment_months)
        info_right.addWidget(self.table_installment)
        
        info_right.addWidget(btn_save)
        data_layout.addLayout(info_right, stretch=1)
        pane_layout.addLayout(data_layout)

        # Разделительная линия
        sep = QFrame()
        sep.setStyleSheet("border-bottom: 1px solid #2F2F35; background: transparent; min-height: 1px; max-height: 1px;")
        pane_layout.addWidget(sep)
        

        
        # 🔥 ЖЕСТКИЙ ПОРЯДОК ОТОБРАЖЕНИЯ (Строго по ТЗ):
        info_right.addWidget(lbl_stat_title)        # 1. Статус (Расчет)
        info_right.addWidget(lbl_price_title)       # 2. Общая стоимость бани
        info_right.addWidget(lbl_adv_caption)       # 3. Текст-подпись "Внесенный аванс"
        info_right.addWidget(self.txt_advance)      # 4. Белое поле для ввода цифр аванса
        info_right.addWidget(self.lbl_balance_title) # 5. Итоговый остаток (Стоимость минус Аванс)
        info_right.addWidget(btn_save)              # 6. Кнопка "Сохранить"
        
        data_layout.addLayout(info_right, stretch=1)
        pane_layout.addLayout(data_layout)

        # Разделительная линия
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

        # Связка кнопок со сканами файлов LONGBLOB из кэша
        doc_keys = [("contract", "file_contract", "Договор"), ("specification", "file_specification", "Спецификация"),
                    ("blueprint", "file_blueprint", "Чертеж"), ("act", "file_act", "Акт приема")]

        for key, db_col, name in doc_keys:
            has_file = bool(order_data.get(db_col))
            self.doc_controls[key]["upload"].clicked.connect(
                lambda checked, o_id=order_id, k=key, col=db_col, n=name: self._handle_upload(o_id, k, col, n)
            )
            if has_file:
                self.doc_controls[key]["status"].setText(f"{name}: Загружен")
                self.doc_controls[key]["status"].setStyleSheet("color: #2ECC71; background: transparent; font-weight: bold; border: none;")
                self.doc_controls[key]["status"].clicked.connect(
                    lambda checked, o_id=order_id, col=db_col, n=name: self._handle_view(o_id, col, n)
                )
            else:
                self.doc_controls[key]["status"].setText(f"{name}: Не загружен")
                self.doc_controls[key]["status"].setStyleSheet("color: #FF4D4D; background: transparent; font-weight: bold; border: none;")

        # ---------------------------------------------------------------------
        # БЛОК 4: Таблица технической комплектации бани из Шага 3
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
            font_b = QFont("Segoe UI", 9)
            font_b.setBold(True)
            item_val.setFont(font_b)
            self.table_order_spec.setItem(row_idx, 1, item_val)

        pane_layout.addWidget(self.table_order_spec)
        pane_layout.addStretch(1)

        # Выводим собранный контейнер в основной слой виджета
        self.main_layout.addWidget(self.dynamic_passport_container)
    # ---------------------------------------------------------------------
    # ЛОГИЧЕСКИЕ И ВАЛИДАЦИОННЫЕ МЕТОДЫ ПО ФЗ-152 И ФИНАНСАМ
    # ---------------------------------------------------------------------
    def _recalculate_balance(self, total_price, advance_text):
        """Реактивный калькулятор: пересчитывает остаток к оплате прямо при вводе аванса менеджером"""
        try:
            clean_text = advance_text.replace(",", ".").replace(" ", "").strip()
            advance_val = float(clean_text) if clean_text else 0.0
        except ValueError:
            advance_val = 0.0
            
        balance_val = total_price - advance_val
        
        # Подсвечиваем остаток красивым зеленым, если долга нет, или тревожным красным
        color = "#2ECC71" if balance_val <= 0 else "#FF4D4D"
        self.lbl_balance_title.setText(f"Остаток: <span style='color:{color};'>{balance_val:,.2f} ₽</span>")

    def _toggle_payment_mode(self, total_price):
        """Переключатель: мгновенно скрывает или показывает поля рассрочки на экране"""
        mode = self.cmb_payment_type.currentText()
        if "Рассрочка" in mode:
            self.lbl_months_caption.show()
            self.txt_installment_months.show()
            self.table_installment.show()
            # Сразу генерируем базовый график под текущий текст в поле месяцев
            self._generate_auto_schedule(total_price, self.txt_installment_months.text())
        else:
            self.lbl_months_caption.hide()
            self.txt_installment_months.hide()
            self.table_installment.hide()
            # Возвращаем стандартную подсветку остатка
            self._recalculate_balance(total_price, self.txt_advance.text())

    def _generate_auto_schedule(self, total_price, months_text):
        """
        Бронебойный алгоритм: рассчитывает круглые рубли на основные месяцы рассрочки,
        а все остатки округления и копейки принудительно закидывает в самый последний платеж!
        """
        try:
            clean_adv = self.txt_advance.text().replace(",", ".").replace(" ", "").strip()
            advance_val = float(clean_adv) if clean_adv else 0.0
        except ValueError:
            advance_val = 0.0

        balance_val = total_price - advance_val

        try:
            months = int(months_text.strip())
            if months < 1: months = 1
            if months > 12: months = 12 # Ограничиваем жестким лимитом директора
        except ValueError:
            months = 4 # По умолчанию 4 месяца, если ввели некорректный символ

        # Меняем количество строк в таблице интерфейса под выбранный срок
        self.table_installment.setRowCount(months)

        if balance_val <= 0:
            # Если баня уже оплачена авансом полностью — обнуляем график
            for row in range(months):
                self.table_installment.setItem(row, 0, QTableWidgetItem("0.00"))
                self.table_installment.setItem(row, 1, QTableWidgetItem(f"Этап {row+1}"))
            return

        # 🔥 НАШ КРУТОЙ МАТЕМАТИЧЕСКИЙ ДВИЖОК:
        # 1. Считаем базовый платеж без копеек (отсекаем дробную часть)
        base_pay_no_cents = int(balance_val // months)

        distributed_sum = 0
        import datetime
        current_date = datetime.date.today()

        for row in range(months):
            # Рассчитываем дату каждого взноса: плюс 30 дней на каждый этап вперед
            pay_date = (current_date + datetime.timedelta(days=(row + 1) * 30)).strftime("%d.%m.%Y")
            
            if row < (months - 1):
                # Для всех месяцев, кроме последнего — пишем круглую сумму рублей без копеек
                row_amount = float(base_pay_no_cents)
                distributed_sum += base_pay_no_cents
            else:
                # В финальный месяц закидываем весь оставшийся хвост (с копейками от стоимости бани)
                row_amount = balance_val - distributed_sum

            # Заносим рассчитанные данные в ячейки нашей динамической таблицы
            item_amt = QTableWidgetItem(f"{row_amount:.2f}")
            item_date = QTableWidgetItem(pay_date)
            
            # Делаем ячейку даты изменяемой менеджером вручную, если клиент просит сдвинуть график
            self.table_installment.setItem(row, 0, item_amt)
            self.table_installment.setItem(row, 1, item_date)

        # Подсвечиваем остаток желтым (активная рассрочка от фабрики)
        self.lbl_balance_title.setText(f"Остаток: <span style='color:#FFA500;'>{balance_val:,.2f} ₽ (Рассрочка)</span>")

    def _trigger_pnd_save(self, order_id):
        """Собирает данные из интерфейса, пакует рассрочку в JSON и отправляет в бэкенд на Джино"""
        import json # Импортируем стандартную библиотеку JSON
        
        passport_text = self.txt_passport.text().strip()
        reg_address_text = self.txt_reg_address.text().strip() 
        address_text = self.txt_address.text().strip()
        notes_text = self.txt_notes.toPlainText().strip()
        
        try:
            clean_adv = self.txt_advance.text().replace(",", ".").replace(" ", "").strip()
            advance_val = float(clean_adv) if clean_adv else 0.00
        except ValueError:
            advance_val = 0.00

        # СБОР ГРАФИКА РАССРОЧКИ: если выбран режим рассрочки, пакуем таблицу в JSON массив
        schedule_list = []
        payment_mode = self.cmb_payment_type.currentText()
        
        if "Рассрочка" in payment_mode:
            row_count = self.table_installment.rowCount()
            for r in range(row_count):
                amt_item = self.table_installment.item(r, 0)
                date_item = self.table_installment.item(r, 1)
                
                amount_str = amt_item.text().strip() if amt_item else "0.00"
                date_str = date_item.text().strip() if date_item else "—"
                
                try:
                    amount_val = float(amount_str.replace(",", ".").replace(" ", ""))
                except ValueError:
                    amount_val = 0.00
                    
                schedule_list.append({
                    "num": r + 1,
                    "amount": amount_val,
                    "date": date_str
                })
                
        # Превращаем массив в плоскую JSON-строку для записи в ячейку TEXT MySQL
        schedule_json_str = json.dumps(schedule_list, ensure_ascii=False) if schedule_list else None

        # Отправляем расширенный пакет данных в db_worker
        # (Примечание: В db_worker.py нам нужно будет передать schedule_json_str, обновим в следующем шаге)
        success, result_passport, result_reg = update_encrypted_pnd(
            self.parent_panel.user_session, order_id, passport_text, reg_address_text, address_text, notes_text, advance_val, schedule_json_str
        )
        
        if success:
            # Обновляем локальный оперативный кэш программы, чтобы всё летало без перезагрузок
            if order_id in self.parent_panel.raw_orders_cache:
                self.parent_panel.raw_orders_cache[order_id]["client_passport_encrypted"] = result_passport
                self.parent_panel.raw_orders_cache[order_id]["client_reg_address_encrypted"] = result_reg
                self.parent_panel.raw_orders_cache[order_id]["client_address"] = address_text
                self.parent_panel.raw_orders_cache[order_id]["order_notes"] = notes_text
                self.parent_panel.raw_orders_cache[order_id]["advance_payment"] = advance_val
                self.parent_panel.raw_orders_cache[order_id]["payment_schedule_json"] = schedule_json_str
                
                tot_p = float(self.parent_panel.raw_orders_cache[order_id].get("total_price") or 0.0)
                self.parent_panel.raw_orders_cache[order_id]["balance_payment"] = tot_p - advance_val
                
            QMessageBox.information(self, "Успех", f"Данные лида #{order_id}, включая график рассрочки, сохранены на Джино!")
            self.display_order(order_id, self.parent_panel.raw_orders_cache[order_id])
        else:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить изменения: {result_passport}")

    def _handle_upload(self, order_id, key, db_column, doc_name):
        """Обрабатывает выбор файла и передает его бинарник в db_worker"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Выберите скан документа: {doc_name}", "", "Документы (*.pdf *.jpg *.png *.docx)"
        )
        if not file_path: return

        try:
            with open(file_path, 'rb') as f:
                binary_data = f.read()

            success = upload_document_blob(self.parent_panel.user_session, order_id, db_column, binary_data)
            if success:
                if order_id in self.parent_panel.raw_orders_cache:
                    self.parent_panel.raw_orders_cache[order_id][db_column] = binary_data
                QMessageBox.information(self, "Успех", f"Документ '{doc_name}' успешно загружен в базу данных!")
                self.display_order(order_id, self.parent_panel.raw_orders_cache[order_id])
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось залить бинарный файл в MySQL.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка чтения файла:\n{str(e)}")

    def _handle_view(self, order_id, db_column, doc_name):
        """Извлекает байты из кэша и открывает временный файл в ОС"""
        order_data = self.parent_panel.raw_orders_cache.get(order_id, {})
        binary_data = order_data.get(db_column)
        if not binary_data: return

        try:
            ext = ".pdf"
            if binary_data[:4] == b'%PDF': ext = ".pdf"
            elif binary_data[:4] == b'\x89PNG': ext = ".png"
            elif binary_data[:2] == b'\xff\xd8': ext = ".jpg"
            
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"view_order_{order_id}_{db_column}{ext}")
            
            with open(temp_file_path, 'wb') as f:
                f.write(binary_data)
                
            os.startfile(temp_file_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка открытия", f"Не удалось открыть файл:\n{str(e)}")
