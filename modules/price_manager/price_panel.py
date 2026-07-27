# modules/price_manager/price_panel.py
import pymysql
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import DB_CONFIG

class PriceManagerWidget(QWidget):
    """
    Изолированный управляющий модуль Вкладки 7 'Управление прайсами'.
    Выводит базовые тарифы бань и допы из MySQL с возможностью редактирования 'на лету'.
    """
    def __init__(self):
        super().__init__()
        self.is_loading = False # Блокиратор триггера, чтобы не слать апдейты во время первой загрузки
        self._init_ui()
        self.load_all_prices_from_cloud()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Верхняя панель заголовка и кнопка обновления
        top_panel = QHBoxLayout()
        lbl_title = QLabel("💰 ЦЕНТРАЛЬНЫЙ ПУЛЬТ УПРАВЛЕНИЯ ПРАЙС-ЛИСТАМИ ФАБРИКИ")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #FF9F43;")
        top_panel.addWidget(lbl_title)
        top_panel.addStretch()

        self.btn_refresh = QPushButton("🔄 Обновить данные")
        self.btn_refresh.setFixedSize(140, 32)
        self.btn_refresh.clicked.connect(self.load_all_prices_from_cloud)
        top_panel.addWidget(self.btn_refresh)
        self.main_layout.addLayout(top_panel)

        # Строка уведомлений
        self.lbl_status = QLabel("Дважды кликните по ячейке цены, измените её и нажмите Enter для сохранения.")
        self.lbl_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.lbl_status.setStyleSheet("color: #656570;")
        self.main_layout.addWidget(self.lbl_status)

        # Сетка таблиц: делим экран пополам горизонтально
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(20)

        # ЛЕВАЯ ТАБЛИЦА: БАЗОВЫЕ ЦЕНЫ БАНЬ
        left_box = QVBoxLayout()
        left_box.addWidget(QLabel("📐 Базовые комплектации (Сосна/Ель):"))
        self.table_base = QTableWidget()
        self.table_base.setColumnCount(4)
        self.table_base.setHorizontalHeaderLabels(["ID", "Линейка изделия", "Длина (мм)", "Базовая цена (₽)"])
        self.table_base.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Привязываем живой эвент изменения ячейки
        self.table_base.itemChanged.connect(self._on_base_price_changed)
        left_box.addWidget(self.table_base)
        tables_layout.addLayout(left_box, stretch=1)

        # ПРАВАЯ ТАБЛИЦА: СЛОВАРЬ ДОП. ОПЦИЙ
        right_box = QVBoxLayout()
        right_box.addWidget(QLabel("🛋️ Дополнительные опции спецификации:"))
        self.table_options = QTableWidget()
        self.table_options.setColumnCount(5)
        self.table_options.setHorizontalHeaderLabels(["ID", "Системный ключ", "Название опции", "Категория", "Цена (₽)"])
        self.table_options.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Привязываем живой эвент изменения ячейки
        self.table_options.itemChanged.connect(self._on_option_price_changed)
        right_box.addWidget(self.table_options)
        tables_layout.addLayout(right_box, stretch=1)

        self.main_layout.addLayout(tables_layout)

        # Применяем общие стили ячеек, чтобы они сочетались с темной/светлой темой
        table_style = """
            QTableWidget { color: #FFFFFF; gridline-color: #25252D; background-color: #1A1A1E; }
            QTableWidget::item { padding: 5px; }
        """
        self.table_base.setStyleSheet(table_style)
        self.table_options.setStyleSheet(table_style)

    def load_all_prices_from_cloud(self):
        """Онлайн скачивание всех прайс-листов из MySQL хостинга"""
        self.is_loading = True # Блокируем отправку ложных апдейтов во время очистки/заливки
        self.lbl_status.setText("Синхронизация с облаком MySQL...")
        self.lbl_status.setStyleSheet("color: #FF9F43;")

        try:
            conn = pymysql.connect(**DB_CONFIG)
            
            # 1. Загрузка базовых цен бань
            cursor = conn.cursor()
            cursor.execute("SELECT id, product_line, base_length, price FROM base_prices")
            rows_base = cursor.fetchall()
            self.table_base.setRowCount(len(rows_base))
            
            for row_idx, (b_id, line, length, price) in enumerate(rows_base):
                # ID, Линейку и длину делаем нередактируемыми (только для чтения)
                item_id = QTableWidgetItem(str(b_id)); item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item_line = QTableWidgetItem(str(line)); item_line.setFlags(item_line.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item_len = QTableWidgetItem(f"{length} мм"); item_len.setFlags(item_len.flags() ^ Qt.ItemFlag.ItemIsEditable)
                
                # Цену оставляем открытой для редактирования!
                item_price = QTableWidgetItem(str(price))
                
                self.table_base.setItem(row_idx, 0, item_id)
                self.table_base.setItem(row_idx, 1, item_line)
                self.table_base.setItem(row_idx, 2, item_len)
                self.table_base.setItem(row_idx, 3, item_price)

            # 2. Загрузка доп. опций
            cursor.execute("SELECT id, option_key, option_name, category, price FROM options_prices")
            rows_opts = cursor.fetchall()
            self.table_options.setRowCount(len(rows_opts))
            
            for row_idx, (o_id, key, name, cat, price) in enumerate(rows_opts):
                item_id = QTableWidgetItem(str(o_id)); item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item_key = QTableWidgetItem(str(key)); item_key.setFlags(item_key.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item_name = QTableWidgetItem(str(name)); item_name.setFlags(item_name.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item_cat = QTableWidgetItem(str(cat)); item_cat.setFlags(item_cat.flags() ^ Qt.ItemFlag.ItemIsEditable)
                
                item_price = QTableWidgetItem(str(price))
                
                self.table_options.setItem(row_idx, 0, item_id)
                self.table_options.setItem(row_idx, 1, item_key)
                self.table_options.setItem(row_idx, 2, item_name)
                self.table_options.setItem(row_idx, 3, item_cat)
                self.table_options.setItem(row_idx, 4, item_price)

            cursor.close()
            conn.close()
            
            self.lbl_status.setText("✅ Данные синхронизированы. Прайсы актуальны.")
            self.lbl_status.setStyleSheet("color: #00FF66;")

        except pymysql.MySQLError as e:
            self.lbl_status.setText("❌ Ошибка связи с хостингом!")
            self.lbl_status.setStyleSheet("color: #FF4D4D;")
            print(f"[Ошибка загрузки прайсов]: {e}")
            
        self.is_loading = False

    def _on_base_price_changed(self, item):
        """Вызывается автоматически, когда ты меняешь базовую цену бани в левой таблице"""
        if self.is_loading: return
        
        row = item.row()
        # Выдергиваем ID строки и новое введенное значение цены
        db_id = self.table_base.item(row, 0).text()
        new_price_text = item.text().strip()

        try:
            new_price = int(new_price_text)
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Отправляем UPDATE на хостинг
            cursor.execute("UPDATE base_prices SET price = %s WHERE id = %s", (new_price, db_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            self.lbl_status.setText(f"✅ Базовый тариф ID {db_id} успешно обновлен в MySQL: {new_price} ₽")
            self.lbl_status.setStyleSheet("color: #00FF66;")
        except ValueError:
            self.lbl_status.setText("⚠️ Ошибка: Цена должна быть целым числом!")
            self.lbl_status.setStyleSheet("color: #FF4D4D;")

    def _on_option_price_changed(self, item):
        """Вызывается автоматически, когда ты меняешь цену доп. опции в правой таблице"""
        if self.is_loading: return
        
        row = item.row()
        db_id = self.table_options.item(row, 0).text()
        new_price_text = item.text().strip()

        try:
            new_price = int(new_price_text)
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Отправляем UPDATE допов на хостинг
            cursor.execute("UPDATE options_prices SET price = %s WHERE id = %s", (new_price, db_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            self.lbl_status.setText(f"✅ Опция ID {db_id} успешно обновлена в MySQL: {new_price} ₽")
            self.lbl_status.setStyleSheet("color: #00FF66;")
        except ValueError:
            self.lbl_status.setText("⚠️ Ошибка: Цена допа должна быть целым числом!")
            self.lbl_status.setStyleSheet("color: #FF4D4D;")
