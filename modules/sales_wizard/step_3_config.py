# modules/sales_wizard/step_3_config.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QRadioButton, QButtonGroup, QFrame, QListView, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class Step3ConfigWidget(QWidget):
    """Геометрический конфигуратор заготовки бани с умным выбором цветов и колеровки RAL"""
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 15, 30, 15)
        self.layout.setSpacing(10)

        lbl_title = QLabel("ЭТАП 3: ГЕОМЕТРИЧЕСКИЙ КОНФИГУРАТОР ЗАГОТОВКИ")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #FF9F43;")
        self.layout.addWidget(lbl_title)

        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)

        # 1. МАТЕРИАЛ, ФОРМА, ДЛИНА, ДИАМЕТР
        form_layout.addWidget(QLabel("🪵 Материал обшивки каркаса:"))
        self.cb_material = QComboBox()
        self.cb_material.setView(QListView())
        self.cb_material.addItems(["Сосна / Ель камерной сушки (Базовый тариф)", "Кедр сибирский (Премиум тариф +30%)"])
        form_layout.addWidget(self.cb_material)

        form_layout.addWidget(QLabel("📐 Габаритный размер (Диаметр торца бани):"))
        self.cb_diameter = QComboBox()
        self.cb_diameter.setView(QListView())
        self.cb_diameter.addItems(["Размер — 2.0 метра (Базовая цена)", "Размер — 2.15 метра (+7% к базовой стоимости)", "Размер — 2.3 метра (+10% к базовой стоимости)"])
        form_layout.addWidget(self.cb_diameter)

        form_layout.addWidget(QLabel("⬡ Геометрическая форма контура сечения:"))
        self.cb_shape_type = QComboBox()
        self.cb_shape_type.setView(QListView())
        self.cb_shape_type.addItems(["Классический круглый контур", "Оквадраченный контур (Квадро-бочка | +7% к стоимости)"])
        form_layout.addWidget(self.cb_shape_type)

        form_layout.addWidget(QLabel("📏 Модель бани и габаритная длина ламелей:"))
        self.cb_length = QComboBox()
        self.cb_length.setView(QListView())
        self.cb_length.addItems(["Баня 2000 мм («Двоечка»)", "Баня 3000 мм («Троечка»)", "Баня 3500 мм («Троечка Плюс»)", "Баня 4000 мм («Четверочка»)", "Баня 4500 мм («Четверочка Плюс»)", "Баня 5000 мм («Пятерочка»)", "Баня 5500 мм («Пятерочка Плюс»)", "Баня 6000 мм («Шестерочка»)"])
        self.cb_length.currentIndexChanged.connect(self._check_length_limits)
        form_layout.addWidget(self.cb_length)

        # 2. 🔥 ВНЕДРЕНО: БЛОК ЭСТЕТИКИ И ЦВЕТОВ (RAL)
        form_layout.addWidget(QLabel("🔍 Цвет кровли (Мягкая черепица):"))
        self.cb_color_roof = QComboBox()
        self.cb_color_roof.setView(QListView())
        self.cb_color_roof.addItems(["Красный рубин", "Зеленый мох", "Коричневый шоколад", "Серый графит"])
        form_layout.addWidget(self.cb_color_roof)

        form_layout.addWidget(QLabel("🔍 Цвет наружного фасада:"))
        self.cb_color_facade = QComboBox()
        self.cb_color_facade.setView(QListView())
        self.cb_color_facade.addItems(["Палисандр", "Орех", "Махагон", "Белый иней", "[Свой цвет / Колеровка]"])
        self.cb_color_facade.currentIndexChanged.connect(lambda idx: self.txt_ral_facade.setVisible(idx == 4))
        form_layout.addWidget(self.cb_color_facade)
        
        self.txt_ral_facade = QLineEdit()
        self.txt_ral_facade.setPlaceholderText("Укажите код RAL или название цвета (например: RAL 7016)...")
        self.txt_ral_facade.hide() # По умолчанию скрыто
        form_layout.addWidget(self.txt_ral_facade)

        form_layout.addWidget(QLabel("🔍 Цвет обналички и торцов бани:"))
        self.cb_color_borders = QComboBox()
        self.cb_color_borders.setView(QListView())
        self.cb_color_borders.addItems(["В цвет фасада", "В цвет кровли", "Палисандр (Контраст)", "[Свой цвет / Колеровка]"])
        self.cb_color_borders.currentIndexChanged.connect(lambda idx: self.txt_ral_borders.setVisible(idx == 3))
        form_layout.addWidget(self.cb_color_borders)

        self.txt_ral_borders = QLineEdit()
        self.txt_ral_borders.setPlaceholderText("Укажите код RAL для торцов...")
        self.txt_ral_borders.hide()
        form_layout.addWidget(self.txt_ral_borders)

        # 3. МОДИФИКАЦИЯ ТОРЦА
        form_layout.addWidget(QLabel("🚪 Конструктивное исполнение торцевой зоны (Вход):"))
        self.bg_torce = QButtonGroup(self)
        self.rb_base = QRadioButton("Классический прямой торец (В заготовку без вылетов)")
        self.rb_canopy = QRadioButton("Модификация с защитным козырьком (+500 мм)")
        self.rb_porch = QRadioButton("Модификация с уличным крыльцом и сиденьями (+700 мм)")
        self.rb_base.setChecked(True)
        
        for idx, rb in enumerate([self.rb_base, self.rb_canopy, self.rb_porch]):
            self.bg_torce.addButton(rb, idx)
            form_layout.addWidget(rb)

        self.layout.addWidget(form_frame)
        self.layout.addStretch()

    def _check_length_limits(self, index: int):
        if index == 7:
            self.rb_base.setChecked(True)
            self.rb_canopy.setEnabled(False)
            self.rb_porch.setEnabled(False)
        else:
            self.rb_canopy.setEnabled(True)
            self.rb_porch.setEnabled(True)

    def collect_data(self) -> dict:
        mat_key = "pine" if self.cb_material.currentIndex() == 0 else "cedar"
        diameter_val = ["2.0", "2.15", "2.3"][self.cb_diameter.currentIndex()]
        shape_key = "round" if self.cb_shape_type.currentIndex() == 0 else "quadro"
        length_val = [2000, 3000, 3500, 4000, 4500, 5000, 5500, 6000][self.cb_length.currentIndex()]
        torce_key = ["base", "canopy", "porch"][self.bg_torce.checkedId()]

        # Умный сбор цветов с учетом текстовой колеровки RAL
        facade_color = self.txt_ral_facade.text().strip() if self.cb_color_facade.currentIndex() == 4 else self.cb_color_facade.currentText()
        borders_color = self.txt_ral_borders.text().strip() if self.cb_color_borders.currentIndex() == 3 else self.cb_color_borders.currentText()

        return {
            "material": mat_key, "diameter": diameter_val, "shape_type": shape_key,
            "base_length": length_val, "torce_modification": torce_key,
            "color_roof": self.cb_color_roof.currentText(),
            "color_facade": facade_color if facade_color else "Палисандр",
            "color_borders": borders_color if borders_color else "В цвет фасада"
        }
