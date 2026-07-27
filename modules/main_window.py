# modules/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QLabel, QFrame, QCheckBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import TABS_SPECIFICATION
from modules.administration.admin_panel import AdminPanelWidget
from modules.price_manager.price_panel import PriceManagerWidget
import theme_manager

# 🔥 ВАЖНЕЙШИЙ ИМПОРТ: Подключаем живой конвейер шагов проектирования
from modules.sales_wizard.main_wizard import SalesWizardMainController

class BabochkiErpCore(QMainWindow):
    """Главная рабочая оболочка ERP-системы с динамическим сайдбаром"""
    def __init__(self, user_session):
        super().__init__()
        self.user_session = user_session
        self.is_dark_theme = True 

        self.setWindowTitle("БаБочки ERP — Автоматизация производства")
        self.setFixedSize(1250, 720)

        self._init_ui()
        self._apply_role_access_matrix()
        self._update_theme_view()

    def _init_ui(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Верхняя панель информеров
        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar")
        self.top_bar.setFixedHeight(50)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_logo = QLabel("БАБОЧКИ ERP")
        top_layout.addWidget(self.lbl_logo)
        top_layout.addStretch()

        right_panel = QHBoxLayout()
        right_panel.setSpacing(15)

        self.lbl_pulse = QLabel("⏳ 12  |  ⚙️ 4  |  ✅ 8")
        right_panel.addWidget(self.lbl_pulse)

        v_line = QFrame()
        v_line.setFrameShape(QFrame.Shape.VLine)
        v_line.setStyleSheet("background-color: #353540;")
        right_panel.addWidget(v_line)

        user_name = self.user_session.get("full_name", "Сотрудник")
        user_role = self.user_session.get("role", "worker").upper()
        self.lbl_user = QLabel(f"Добрый день: {user_name} [{user_role}]")
        self.lbl_user.setFont(QFont("Segoe UI", 9))
        right_panel.addWidget(self.lbl_user)

        self.theme_switch = QCheckBox("Тёмная")
        self.theme_switch.setChecked(True)
        self.theme_switch.clicked.connect(self._toggle_theme)
        right_panel.addWidget(self.theme_switch)

        top_layout.addLayout(right_panel)
        self.main_layout.addWidget(self.top_bar)

        # 2. Нижний рабочий блок
        body_frame = QFrame()
        body_layout = QHBoxLayout(body_frame)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Боковой сайдбар
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 15, 10, 15)
        self.sidebar_layout.setSpacing(6)

        self.tabs_pool = []
        for i, tab_info in enumerate(TABS_SPECIFICATION):
            btn = QPushButton(tab_info["title"])
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            self.sidebar_layout.addWidget(btn)
            self.tabs_pool.append(btn)

        self.sidebar_layout.addStretch()
        
        self.widget_status_box = QFrame()
        self.widget_status_box.setObjectName("status_widget")
        self.widget_status_box.setFixedHeight(60)
        status_layout = QVBoxLayout(self.widget_status_box)
        self.lbl_widget_text = QLabel("Панель информеров\n(В разработке)")
        self.lbl_widget_text.setFont(QFont("Segoe UI", 9))
        self.lbl_widget_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.lbl_widget_text)
        self.sidebar_layout.addWidget(self.widget_status_box)

        body_layout.addWidget(self.sidebar)

        # Правая сцена контента (Многоэкранная стопка)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("canvas_panel")
        self.canvas_pool = []
        
        for i, tab_info in enumerate(TABS_SPECIFICATION):
            # 🔥 ИНТЕГРАЦИЯ: Для первой вкладки инициализируем живую воронку
            if i == 0:
                canvas = SalesWizardMainController()
            # 🔥 ИНТЕГРАЦИЯ: Привязываем живой редактор прайсов на 7-ю вкладку сайдбара (индекс 6)
            elif i == 6:
                canvas = PriceManagerWidget()
            # 🔥 ИНТЕГРАЦИЯ: Привязываем живую панель админки на 8-ю вкладку сайдбара (индекс 7)
            elif i == 7:
                canvas = AdminPanelWidget()
            else:
                # Остальные вкладки пока остаются пустыми мольбертами
                canvas = QFrame()
                canvas_layout = QVBoxLayout(canvas)
                lbl_demo = QLabel(f"[ Место под макет / скриншот вкладки:\n{tab_info['title']} ]")
                lbl_demo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                canvas_layout.addWidget(lbl_demo)
            
            self.stacked_widget.addWidget(canvas)
            self.canvas_pool.append(canvas)
            
        body_layout.addWidget(self.stacked_widget, stretch=1)
        self.main_layout.addWidget(body_frame, stretch=1)

    def _apply_role_access_matrix(self):
        user_rank = self.user_session.get("access_level", 1)
        first_visible_idx = None

        for idx, tab_info in enumerate(TABS_SPECIFICATION):
            min_required = tab_info["min_level"]
            btn = self.tabs_pool[idx]
            if user_rank < min_required:
                btn.hide()
            else:
                btn.show()
                if first_visible_idx is None: first_visible_idx = idx

        if first_visible_idx is not None:
            self._switch_tab(first_visible_idx)

    def _switch_tab(self, index: int):
        """Переключает центральный экран на выбранный модуль из сайдбара"""
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.tabs_pool):
            btn.setChecked(i == index)

    def _toggle_theme(self):
        self.is_dark_theme = self.theme_switch.isChecked()
        self.theme_switch.setText("Тёмная" if self.is_dark_theme else "Светлая")
        self._update_theme_view()

    def _update_theme_view(self):
        theme_manager.apply_app_theme(self, self.is_dark_theme)
