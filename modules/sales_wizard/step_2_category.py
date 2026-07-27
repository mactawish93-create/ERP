# modules/sales_wizard/step_2_category.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class Step2CategoryWidget(QWidget):
    """
    Шаг 2 воронки: Выбор категории и динамических подкатегорий (модельных линеек).
    🔥 ОЖИВЛЕН: Поддерживает выбор Круг/Квадро, Бабочка, Викинг, Квадро Хаус.
    """
    def __init__(self):
        super().__init__()
        self.selected_category = "bath" # Главная категория
        self.selected_sub_line = "round_quadro" # Подкатегория (линейка) по умолчанию
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(20)

        # 1. ЗАГОЛОВОК
        lbl_title = QLabel("ЭТАП 2: ВЫБОР НАПРАВЛЕНИЯ СТРОИТЕЛЬСТВА")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #FF9F43;")
        self.layout.addWidget(lbl_title)

        # 2. ВЕРХНЯЯ СЕТКА ГЛАВНЫХ КАТЕГОРИЙ (ПЛИТКИ СВЕРХУ)
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(15)

        self.btn_bb = QPushButton("Бани Бочки")
        self.btn_mb = QPushButton("Мини Брус")
        self.btn_pk = QPushButton("Покраска")
        self.btn_pr = QPushButton("Прочее")

        self.btns_pool = [self.btn_bb, self.btn_mb, self.btn_pk, self.btn_pr]
        categories_keys = ["bath", "timber", "paint", "other"]

        for idx, btn in enumerate(self.btns_pool):
            btn.setCheckable(True)
            btn.setMinimumHeight(80)
            btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            btn.clicked.connect(lambda checked, key=categories_keys[idx], i=idx: self._select_main_cat(key, i))
            grid_layout.addWidget(btn)

        self.btn_bb.setChecked(True) # По умолчанию выбрана первая плитка
        self.layout.addLayout(grid_layout)

        # 3. 🔥 ДИНАМИЧЕСКИЙ БЛОК ПОДРАЗДЕЛОВ (ПОЯВЛЯЕТСЯ ДЛЯ БАНЬ БОЧЕК)
        self.sub_frame = QFrame()
        self.sub_frame.setStyleSheet("background-color: transparent; border: none;")
        self.sub_layout = QVBoxLayout(self.sub_frame)
        self.sub_layout.setContentsMargins(0, 10, 0, 0)
        self.sub_layout.setSpacing(10)

        self.lbl_sub_title = QLabel("📋 Выберите модельную линейку бани:")
        self.sub_layout.addWidget(self.lbl_sub_title)

        # Создаем вертикальный список белых карточек строго по вашему макету
        self.sub_btn_1 = QPushButton("Круглая/Квадро")
        self.sub_btn_2 = QPushButton("Бабочка")
        self.sub_btn_3 = QPushButton("Викинг")
        self.sub_btn_4 = QPushButton("Квадро Хаус")

        self.sub_btns_pool = [self.sub_btn_1, self.sub_btn_2, self.sub_btn_3, self.sub_btn_4]
        sub_keys = ["round_quadro", "babochka", "viking", "quadro_house"]

        for idx, s_btn in enumerate(self.sub_btns_pool):
            s_btn.setCheckable(True)
            s_btn.setFixedHeight(45)
            s_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            # Настраиваем стиль белых карточек с выравниванием по левому краю
            s_btn.clicked.connect(lambda checked, key=sub_keys[idx], i=idx: self._select_sub_line(key, i))
            self.sub_layout.addWidget(s_btn)

        self.sub_btn_1.setChecked(True) # По умолчанию активна первая линейка
        self.layout.addWidget(self.sub_frame)
        self.layout.addStretch()

    def _select_main_cat(self, key: str, index: int):
        """Переключает главную категорию и управляет видимостью подразделов"""
        self.selected_category = key
        for i, btn in enumerate(self.btns_pool):
            btn.setChecked(i == index)

        # Если выбраны Бани Бочки — плавно показываем подразделы, иначе прячем их с экрана
        if key == "bath":
            self.sub_frame.show()
        else:
            self.sub_frame.hide()

    def _select_sub_line(self, key: str, index: int):
        """Управляет западанием кнопок внутри списка линеек"""
        self.selected_sub_line = key
        for i, s_btn in enumerate(self.sub_btns_pool):
            s_btn.setChecked(i == index)

    def collect_data(self) -> dict:
        """Передает выбранную категорию и линейку в общее хранилище воронки"""
        # Если выбрана не баня, подкатегорию сбрасываем в None
        sub_val = self.selected_sub_line if self.selected_category == "bath" else None
        return {
            "category": self.selected_category,
            "product_line": sub_val
        }
