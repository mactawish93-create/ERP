# modules/sales_wizard/step_3_config.py
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QTableWidget, QHeaderView, 
                             QTableWidgetItem, QFrame, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIntValidator, QPixmap

# Импортируем нашу полную базу из 213 цветов RAL Classic
from modules.sales_wizard.ral_palette import RAL_PALETTE

class Step3ConfigWidget(QWidget):
    """
    Шаг 3: Полностью готовый геометрический конфигуратор бани.
    Часть 1: Верхняя зона визуализации и колеровки RAL.
    """
    def __init__(self, parent_controller=None):
        super().__init__()
        self.parent_controller = parent_controller
        self.widgets = {} # Хранилище для всех полей ввода и комбобоксов
        self._init_ui()

    def _init_ui(self):
        # Главный вертикальный слой всего шага
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 10, 20, 10)
        self.main_layout.setSpacing(8)

        # Статичный заголовок этапа
        lbl_title = QLabel("ЭТАП 3: ГЕОМЕТРИЧЕСКИЙ КОНФИГУРАТОР И СПЕЦИФИКАЦИЯ ИЗДЕЛИЯ")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setObjectName("lbl_title")
        self.main_layout.addWidget(lbl_title)

        # =====================================================================
        # ВЕРХНЯЯ ЗОНА: Центрированная верстка 3D-графики и полей колеровки
        # =====================================================================
        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(35) 
        
        # Две пружины (слева и справа) зажмут графику строго по центру экрана
        top_row_layout.addStretch()

        # ЛЕВАЯ ЧАСТЬ: Изолированный контейнер для 3D-разреза и стрелочек строго под ним
        visual_container = QFrame()
        visual_container.setObjectName("blueprint_main_box")
        visual_container.setFixedSize(520, 184) 
        visual_container.setStyleSheet("QFrame#blueprint_main_box { background: transparent; border: none; }")
        
        visual_box = QVBoxLayout(visual_container)
        visual_box.setContentsMargins(0, 0, 0, 0)
        visual_box.setSpacing(4) 

        # Виджет для самой 3D картинки
        self.lbl_blueprint = QLabel()
        self.lbl_blueprint.setObjectName("blueprint_display_zone")
        self.lbl_blueprint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_blueprint.setFixedSize(520, 160) 
        self.lbl_blueprint.setStyleSheet("QLabel#blueprint_display_zone { border-radius: 6px; border: 1px solid #353540; }")
        visual_box.addWidget(self.lbl_blueprint)

        # Текстовый информер-размерник (Стрелочки ГОСТ)
        self.lbl_size_line = QLabel("├─── Размер парилки: 2000 мм ───┤")
        self.lbl_size_line.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_size_line.setStyleSheet("color: #FF9F43; background: transparent;")
        self.lbl_size_line.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visual_box.addWidget(self.lbl_size_line)

        top_row_layout.addWidget(visual_container)

        # ПРАВАЯ ЧАСТЬ: Изолированный контейнер для полей цветов RAL
        colors_container = QFrame()
        colors_container.setObjectName("colors_main_box") 
        colors_container.setFixedWidth(260) 
        colors_container.setFixedHeight(184) 
        colors_container.setStyleSheet("QFrame#colors_main_box { background: transparent; border: none; }")

        colors_box = QVBoxLayout(colors_container)
        colors_box.setContentsMargins(0, 0, 0, 0)
        colors_box.setSpacing(2) 

        color_fields = [
            ("color_roof", "Цвет кровли:"),
            ("color_facade", "Цвет наружного фасада:"),
            ("color_borders", "Цвет обналички:"),
            ("color_ends", "Цвет торцов:")
        ]

        for key, label_text in color_fields:
            item_layout = QVBoxLayout()
            item_layout.setSpacing(1)
            
            lbl_name = QLabel(label_text)
            lbl_name.setFont(QFont("Segoe UI", 9))
            
            input_row = QHBoxLayout()
            input_row.setSpacing(6)
            
            txt_input = QLineEdit()
            txt_input.setFixedHeight(24) 
            txt_input.setFixedWidth(220) 
            txt_input.setPlaceholderText("Название или код RAL...")
            self.widgets[key] = txt_input 
            
            btn_preview = QPushButton()
            btn_preview.setFixedSize(24, 24)
            btn_preview.setStyleSheet("background-color: #353540; border-radius: 4px; border: 1px solid #454550;")
            btn_preview.setToolTip("Нажмите, чтобы открыть плашку цвета на весь экран")
            self.widgets[f"{key}_preview"] = btn_preview
            
            input_row.addWidget(txt_input)
            input_row.addWidget(btn_preview)
            
            item_layout.addWidget(lbl_name)
            item_layout.addLayout(input_row)
            colors_box.addLayout(item_layout)

        colors_box.addStretch()
        top_row_layout.addWidget(colors_container)
        
        # Вторая пружина для центровки верхнего блока
        top_row_layout.addStretch() 
        self.main_layout.addLayout(top_row_layout)
        # =====================================================================
        # НИЖНЯЯ ЗОНА: Большая таблица спецификации (15 строк)
        # =====================================================================
        self.table_spec = QTableWidget(15, 2)
        self.table_spec.setHorizontalHeaderLabels(["Технический параметр бани", "Выбранное значение / текст"])
        self.table_spec.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_spec.verticalHeader().setVisible(False) 

        # --- 1. Базовая геометрия (QComboBox) ---
        self.widgets["material"] = QComboBox()
        self.widgets["material"].addItems(["pine", "cedar"])
        self.widgets["material"].setItemText(0, "Сосна / Ель (Базовый тариф)")
        self.widgets["material"].setItemText(1, "Сибирский кедр (+30% к стоимости)")

        self.widgets["diameter"] = QComboBox()
        self.widgets["diameter"].addItems(["2.0", "2.15", "2.3"])
        self.widgets["diameter"].setItemText(0, "2.0 м (Базовая цена)")
        self.widgets["diameter"].setItemText(1, "2.15 м (+7%)")
        self.widgets["diameter"].setItemText(2, "2.3 м (+10%)")

        self.widgets["shape_type"] = QComboBox()
        self.widgets["shape_type"].addItems(["round", "quadro"])
        self.widgets["shape_type"].setItemText(0, "Круглый контур")
        self.widgets["shape_type"].setItemText(1, "Квадро контур (+7%)")

        self.widgets["base_length"] = QComboBox()
        self.widgets["base_length"].addItems(["2000", "3000", "3200", "4000", "4200", "4500", "4700", "5000", "5500", "5700", "6000"])
        self.widgets["base_length"].setItemText(0, "Баня 2000 мм («Двоечка»)")
        self.widgets["base_length"].setItemText(1, "Баня 3000 мм («Троечка»)")
        self.widgets["base_length"].setItemText(2, "Баня 3200 мм («Троечка +» с козырьком/крыльцом)")
        self.widgets["base_length"].setItemText(3, "Баня 4000 мм («Четверочка»)")
        self.widgets["base_length"].setItemText(4, "Баня 4200 мм («Четверочка +» с козырьком)")
        self.widgets["base_length"].setItemText(5, "Баня 4500 мм («Четверочка +» с крыльцом / без козырька)")
        self.widgets["base_length"].setItemText(6, "Баня 4700 мм («Четверочка +» с крыльцом и козырьком)")
        self.widgets["base_length"].setItemText(7, "Баня 5000 мм («Пятерочка»)")
        self.widgets["base_length"].setItemText(8, "Баня 5500 мм («Пятерочка +» с козырьком)")
        self.widgets["base_length"].setItemText(9, "Баня 5700 мм («Пятерочка +» с крыльцом / козырьком)")
        self.widgets["base_length"].setItemText(10, "Баня 6000 мм («Шестерочка»)")

        self.widgets["torce_modification"] = QComboBox()
        self.widgets["torce_modification"].addItems(["base", "canopy", "porch"])
        self.widgets["torce_modification"].setItemText(0, "Классический торец 50 мм (Без вылетов)")
        self.widgets["torce_modification"].setItemText(1, "Модификация с защитным козырьком (+500 мм)")
        self.widgets["torce_modification"].setItemText(2, "Модификация с уличным крыльцом и сиденьями (+700 мм)")

        # --- 2. Изменяемые размеры комнат ---
        only_ints = QIntValidator(0, 6000)
        for key, default_val in [("room_sauna", "2000"), ("room_wash", "0"), ("room_rest", "0")]:
            self.widgets[key] = QLineEdit()
            self.widgets[key].setValidator(only_ints)
            self.widgets[key].setMaxLength(4)
            self.widgets[key].setText(default_val)
            self.widgets[key].setFixedHeight(26)

        # --- 3. Чекбоксы Да/Нет для производства ---
        new_prod_fields = [
            ("assembly_on_site", "Нет", "Да (Сборка силами бригады на участке)"),
            ("door_facade", "Нет", "Да (Входная дверь устанавливается с фасада)"),
            ("stove_next_room", "Нет", "Да (Топливный канал печи выходит сквозь диск)"),
            ("stove_street", "Нет", "Да (Топка выносится наружу через ламели каркаса)")
        ]
        for key, opt_no, opt_yes in new_prod_fields:
            self.widgets[key] = QComboBox()
            self.widgets[key].addItems(["0", "1"])
            self.widgets[key].setItemText(0, opt_no)
            self.widgets[key].setItemText(1, opt_yes)

        # --- 4. Наполняем строки таблицы ---
        labels_spec = [
            "🪵 Материал бани:", "⭕ Диаметр бани:", "⬡ Форма бани:", "📏 Модель бани и длина:",
            "🚪 Исполнение торцевой зоны:", "📐 Длина Парилки, мм (Изменяемый размер):",
            "📐 Длина Моечного помещения, мм (Изменяемый размер):", "📐 Длина Комнаты отдыха, мм (Изменяемый размер):",
            "🏗️ Сборка бани на участке заказчика:", "🚪 Дверь входная с фасадной стороны:",
            "🔥 Печь с топкой выходящей в смежное помещение:", "🔥 Печь с топкой выходящей на улицу:",
            "🎨 Доп. примечание по кровле (системное):", "🎨 Доп. примечание по фасаду (системное):",
            "🎨 Доп. примечание по обналичиванию (системное):"
        ]

        row_keys = [
            "material", "diameter", "shape_type", "base_length", "torce_modification", 
            "room_sauna", "room_wash", "room_rest",
            "assembly_on_site", "door_facade", "stove_next_room", "stove_street",
            "color_roof", "color_facade", "color_borders"
        ]
        
        for idx, key in enumerate(row_keys):
            item_lbl = QTableWidgetItem(labels_spec[idx])
            item_lbl.setFlags(item_lbl.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table_spec.setItem(idx, 0, item_lbl)
            
            if idx >= 12:
                stub_item = QTableWidgetItem("Управляется из верхней панели колеровки")
                stub_item.setFlags(stub_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table_spec.setItem(idx, 1, stub_item)
            else:
                self.table_spec.setCellWidget(idx, 1, self.widgets[key])

        # Скрываем 3 последние системные строки цветов из таблицы на экране менеджера
        self.table_spec.setRowHidden(12, True)
        self.table_spec.setRowHidden(13, True)
        self.table_spec.setRowHidden(14, True)

        # Отдаем таблице всю свободную высоту Full Screen монитора
        self.main_layout.addWidget(self.table_spec, stretch=1)

        # Связываем сигналы событий и живые триггеры
        self.widgets["base_length"].currentIndexChanged.connect(self._auto_adjust_rooms)
        self.widgets["shape_type"].currentIndexChanged.connect(self._update_blueprint_graphics)
        self._connect_color_signals()
        
        # Запускаем первичное обновление графики и линий при старте окна
        self._update_blueprint_graphics()
    def _auto_adjust_rooms(self, index):
        """Автоматически подставляет базовые размеры комнат при выборе длины"""
        if index == 0: total_len = 2000
        elif index == 1: total_len = 3000
        elif index == 2: total_len = 3200
        elif index == 3: total_len = 4000
        elif index == 4: total_len = 4200
        elif index == 5: total_len = 4500
        elif index == 6: total_len = 4700
        elif index == 7: total_len = 5000
        elif index == 8: total_len = 5500
        elif index == 9: total_len = 5700
        else: total_len = 6000
        
        if total_len == 2000:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("0")
            self.widgets["room_rest"].setText("0")
        elif total_len == 3000:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("1000")
            self.widgets["room_rest"].setText("0")
        elif total_len == 3200:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("0")
            self.widgets["room_rest"].setText("1200")
        elif total_len == 4000:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("0")
            self.widgets["room_rest"].setText("2000")
        elif total_len == 4200:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("0")
            self.widgets["room_rest"].setText("2200")
        elif total_len == 4500:
            self.widgets["room_sauna"].setText("1700")
            self.widgets["room_wash"].setText("1100")
            self.widgets["room_rest"].setText("1700")
        elif total_len == 4700:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("0")
            self.widgets["room_rest"].setText("2700")
        elif total_len == 5000:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("1000")
            self.widgets["room_rest"].setText("2000")
        elif total_len == 5500:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("1000")
            self.widgets["room_rest"].setText("2500")
        elif total_len == 5700:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("1000")
            self.widgets["room_rest"].setText("2700")
        else:
            self.widgets["room_sauna"].setText("2000")
            self.widgets["room_wash"].setText("1500")
            self.widgets["room_rest"].setText("2500")

        self._update_blueprint_graphics()

    def _update_blueprint_graphics(self):
        """Меняет 3D-рендеры и перестраивает размерную линию"""
        shape_idx = self.widgets["shape_type"].currentIndex()
        shape_prefix = "quadro" if shape_idx == 1 else "round"
        idx = self.widgets["base_length"].currentIndex()
        
        if idx == 0: len_file = "len_2000.png"
        elif idx == 1 or idx == 2: len_file = "len_3000.png"
        elif idx >= 3 and idx <= 6: len_file = "len_4000.png"
        elif idx == 7: len_file = "len_5000.png"
        else: len_file = "len_6000.png"

        target_file = f"{shape_prefix}_{len_file}"
        image_path = os.path.join("assets", "images", target_file)
        
        if not os.path.exists(image_path) and shape_prefix == "quadro":
            target_file = f"round_{len_file}"
            image_path = os.path.join("assets", "images", target_file)

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled = pixmap.scaled(self.lbl_blueprint.width() - 20, self.lbl_blueprint.height() - 20, 
                                   Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_blueprint.setPixmap(scaled)
        else:
            self.lbl_blueprint.clear()
            self.lbl_blueprint.setText(f"📸 Рендер: [ {target_file} ]")

        p_len = self.widgets["room_sauna"].text()
        m_len = self.widgets["room_wash"].text()
        k_len = self.widgets["room_rest"].text()
        
        lens = ["2000", "3000", "3200", "4000", "4200", "4500", "4700", "5000", "5500", "5700", "6000"]
        total_len = int(lens[idx])
        
        if total_len == 2000:
            self.lbl_size_line.setText(f"├─── Парилка: {p_len} мм ───┤")
        elif m_len == "0" or m_len == "" or m_len == "0000":
            self.lbl_size_line.setText(f"├───  Парилка: {p_len} мм  ───┼───  Комната отдыха: {k_len} мм  ───┤")
        elif k_len == "0" or k_len == "" or k_len == "0000":
            self.lbl_size_line.setText(f"├───  Парилка: {p_len} мм  ───┼───  Комната отдыха: {m_len} мм  ───┤")
        else:
            self.lbl_size_line.setText(f"├──  П: {p_len} мм  ──┼──  М: {m_len} мм  ──┼──  КО: {k_len} мм  ──┤")

    def _connect_color_signals(self):
        """Связывает текстовые поля ввода с живыми индикаторами RAL"""
        for key in ["color_roof", "color_facade", "color_borders", "color_ends"]:
            self.widgets[key].textChanged.connect(lambda text, k=key: self._update_ral_indicator(k, text))
            self.widgets[f"{key}_preview"].clicked.connect(lambda checked, k=key: self._open_large_color_preview(k))

    def _update_ral_indicator(self, key, text):
        """На лету ищет код RAL в тексте и окрашивает кнопку-квадратик"""
        import re
        match = re.search(r'\d{4}', text)
        if match:
            ral_code = match.group(0)
            if ral_code in RAL_PALETTE:
                hex_color = RAL_PALETTE[ral_code]
                self.widgets[f"{key}_preview"].setStyleSheet(f"QPushButton {{ background-color: {hex_color}; border: 1px solid #FFFFFF; border-radius: 4px; }}")
                return
        self.widgets[f"{key}_preview"].setStyleSheet("QPushButton { background-color: #353540; border: 1px solid #454550; border-radius: 4px; }")

    def _open_large_color_preview(self, key):
        """Всплывающее окно: разворачивает плашку выбранного цвета на весь экран"""
        import re
        text = self.widgets[key].text()
        match = re.search(r'\d{4}', text)
        ral_code = match.group(0) if match else None
        
        if not ral_code or ral_code not in RAL_PALETTE:
            return 

        hex_color = RAL_PALETTE[ral_code]
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        
        dial = QDialog(self)
        dial.setWindowTitle(f"Каталог RAL — Цвет {ral_code}")
        dial.setFixedSize(300, 300)
        
        layout = QVBoxLayout(dial)
        layout.setContentsMargins(15, 15, 15, 15)
        
        color_block = QLabel()
        color_block.setStyleSheet(f"background-color: {hex_color}; border-radius: 8px; border: 2px solid #FFFFFF;")
        
        lbl_info = QLabel(f"Код колеровки: RAL {ral_code}\nHEX: {hex_color.upper()}")
        lbl_info.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(color_block, stretch=1)
        layout.addWidget(lbl_info)
        dial.exec()

    def collect_data(self):
        """Собирает все параметры из полей и таблицы для MySQL"""
        data = {}
        combo_keys = ["material", "shape_type", "torce_modification", "assembly_on_site", "door_facade", "stove_next_room", "stove_street"]
        for key in combo_keys:
            idx = self.widgets[key].currentIndex()
            if key == "material": data[key] = "pine" if idx == 0 else "cedar"
            elif key == "shape_type": data[key] = "round" if idx == 0 else "quadro"
            elif key == "torce_modification": data[key] = "base" if idx == 0 else ("canopy" if idx == 1 else "porch")
            else: data[key] = str(idx) 
            
        lens = ["2000", "3000", "3200", "4000", "4200", "4500", "4700", "5000", "5500", "5700", "6000"]
        data["base_length"] = lens[self.widgets["base_length"].currentIndex()]
        
        diams = ["2.0", "2.15", "2.3"]
        data["diameter"] = diams[self.widgets["diameter"].currentIndex()]

        text_keys = ["room_sauna", "room_wash", "room_rest", "color_roof", "color_facade", "color_borders", "color_ends"]
        for key in text_keys:
            data[key] = self.widgets[key].text().strip()

        return data
