# modules/sales_wizard/step_4_estimate.py
import pymysql
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTabWidget, QCheckBox, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import DB_CONFIG

class Step4EstimateWidget(QWidget):
    """Интерактивный сметный калькулятор, качающий прайсы онлайн из закрытой MySQL"""
    def __init__(self):
        super().__init__()
        self.base_price = 0
        self.shape_markup = 0
        self.diameter_markup = 0
        self.options_sum = 0
        self.total_price = 0
        
        # Хранилище связок: {Объект_Чекбокса: Точная_Цена_Из_MySQL}
        self.checkbox_price_map = {}
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.setSpacing(25)

        # ЛЕВАЯ ПАНЕЛЬ С ВКЛАДКАМИ ОПЦИЙ
        left_panel = QVBoxLayout()
        lbl_title = QLabel("ЭТАП 4: РАСЧЕТ СПЕЦИФИКАЦИИ И ДОПОЛНИТЕЛЬНЫХ ОПЦИЙ")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #FF9F43;")
        left_panel.addWidget(lbl_title)

        self.tabs_options = QTabWidget()
        self.tabs_options.setObjectName("spec_tabs")
        
        # Создаем пустые прокручиваемые зоны под категории
        self.tab_construct = self._create_scroll_pane()
        self.tab_doors = self._create_scroll_pane()
        self.tab_stoves = self._create_scroll_pane()
        self.tab_interior = self._create_scroll_pane()

        self.tabs_options.addTab(self.tab_construct, "🏗️ Конструктив")
        self.tabs_options.addTab(self.tab_doors, "🚪 Окна/Двери")
        self.tabs_options.addTab(self.tab_stoves, "🔥 Оборудование")
        self.tabs_options.addTab(self.tab_interior, "🛋️ Интерьер")
        left_panel.addWidget(self.tabs_options, stretch=1)
        self.main_layout.addLayout(left_panel, stretch=2)

        # ПРАВАЯ ПАНЕЛЬ: ЗАКРЕПЛЕННОЕ ФИНАНСОВОЕ ТАБЛО
        self.right_frame = QFrame()
        self.right_frame.setObjectName("financial_board")
        self.right_frame.setFixedWidth(320)
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(20, 25, 20, 25)
        right_layout.setSpacing(15)

        lbl_board_title = QLabel("💳 СМЕТНЫЙ РАСЧЕТ (ОНЛАЙН ПРАЙС)")
        lbl_board_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_board_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(lbl_board_title)

        self.lbl_base = QLabel("Базовая комплектация: 0 ₽")
        self.lbl_shape = QLabel("Наценка за Квадро (7%): 0 ₽")
        self.lbl_diameter = QLabel("Наценка за диаметр: 0 ₽")
        self.lbl_options = QLabel("Выбрано доп. опций: 0 ₽")
        
        for lbl in [self.lbl_base, self.lbl_shape, self.lbl_diameter, self.lbl_options]:
            right_layout.addWidget(lbl)

        h_line = QFrame()
        h_line.setFrameShape(QFrame.Shape.HLine)
        h_line.setStyleSheet("background-color: #353540;")
        right_layout.addWidget(h_line)

        self.lbl_total = QLabel("ИТОГО: 0 ₽")
        self.lbl_total.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.lbl_total)

        right_layout.addStretch()
        self.main_layout.addWidget(self.right_frame)

    def _create_scroll_pane(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll

    def refresh_calculations(self, wizard_data: dict):
        """🔥 СЕРДЦЕ СМЕТЫ: Скачивает цены из MySQL хостинга и выстраивает расчет"""
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 1. Загружаем базовую цену модели из таблицы base_prices
            base_len = wizard_data.get("base_length", 2000)
            cursor.execute("SELECT price FROM base_prices WHERE base_length = %s", (base_len,))
            row_base = cursor.fetchone()
            self.base_price = row_base[0] if row_base else 212300

            # Накрутка за Кедр (+30%)
            if wizard_data.get("material") == "cedar":
                self.base_price = int(self.base_price * 1.3)

            # 2. Скан процентов из бланков Excel
            shape = wizard_data.get("shape_type", "round")
            diameter = wizard_data.get("diameter", "2.0")

            shape_pct = 7 if shape == "quadro" else 0
            self.shape_markup = int(self.base_price * (shape_pct / 100))

            dia_pct = 0
            if diameter == "2.15": dia_pct = 7
            elif diameter == "2.3": dia_pct = 10
            self.diameter_markup = int(self.base_price * (dia_pct / 100))

            # 3. Динамическая генерация чекбоксов из облачной таблицы options_prices
            self.checkbox_price_map.clear()
            categories_panes = {
                "construct": self.tab_construct, "doors": self.tab_doors,
                "stoves": self.tab_stoves, "interior": self.tab_interior
            }

            # Чистим старые чекбоксы с экранов перед перерисовкой
            for pane in categories_panes.values():
                widget = pane.widget()
                # Удаляем старую разметку
                old_layout = widget.layout()
                if old_layout:
                    while old_layout.count():
                        child = old_layout.takeAt(0)
                        if child.widget(): child.widget().deleteLater()

            # Скачиваем допы из MySQL
            cursor.execute("SELECT option_name, category, price FROM options_prices")
            rows_options = cursor.fetchall()

            for opt_name, cat, price in rows_options:
                if cat in categories_panes:
                    pane = categories_panes[cat]
                    layout = pane.widget().layout()
                    
                    # Создаем живой чекбокс с выводом реальной цены из базы!
                    cb = QCheckBox(f"{opt_name}  ( + {price:,} ₽ )".replace(",", " "))
                    cb.stateChanged.connect(self._on_option_clicked)
                    
                    # Запоминаем связь в нашей карте памяти
                    self.checkbox_price_map[cb] = price
                    
                    # Вставляем на экран (перед stretch)
                    layout.insertWidget(layout.count() - 1, cb)

            cursor.close()
            conn.close()

            # Обновляем табло
            self.lbl_base.setText(f"Базовая комплектация: {self.base_price:,} ₽".replace(",", " "))
            self.lbl_shape.setText(f"Наценка за Квадро ({shape_pct}%): {self.shape_markup:,} ₽".replace(",", " "))
            self.lbl_diameter.setText(f"Наценка за диаметр ({dia_pct}%): {self.diameter_markup:,} ₽".replace(",", " "))
            
            self.options_sum = 0
            self._update_total_sum_display()

        except pymysql.MySQLError as e:
            print(f"[Ошибка онлайн калькуляции в MySQL]: {e}")

    def _on_option_clicked(self, state):
        """Живой пересчет сметы по реальным ценам из карты памяти"""
        self.options_sum = 0
        for cb, price in self.checkbox_price_map.items():
            if cb.isChecked():
                self.options_sum += price
                    
        self.lbl_options.setText(f"Выбрано доп. опций: {self.options_sum:,} ₽".replace(",", " "))
        self._update_total_sum_display()

    def _update_total_sum_display(self):
        self.total_price = self.base_price + self.shape_markup + self.diameter_markup + self.options_sum
        self.lbl_total.setText(f"ИТОГО: {self.total_price:,} ₽".replace(",", " "))
