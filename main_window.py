### Файл: ui/main_window.py
# ui/main_window.py
# =====================================================================
# 🎛 ГЛАВНЫЙ КАРКАС ЭКОСИСТЕМЫ БаБочки ERP
#
# 🆕 ПОДДЕРЖКА ПОШАГОВОЙ ЗАГРУЗКИ:
#   • MainWindow(user_data)                      — классический режим,
#     все страницы строятся прямо в конструкторе (обратная совместимость).
#   • MainWindow(user_data, progressive=True)    — создаётся только
#     «каркас» (top_bar + sidebar + дашборд). Остальные страницы строятся
#     пошагово извне через метод get_loading_steps(). Это позволяет
#     показывать прогресс-бар в ui/loading_screen.py.
#
# 🆕 ДИСПЕТЧЕР ОБНОВЛЁН:
#   • «База заказов» → «Клиенты и заказы» (модуль с двумя вкладками).
#   • «Тест-модуль А» → «Модуль директора». Подстраховка на старое имя
#     оставлена в условии — если сайдбар вернётся к прежнему названию,
#     страница всё равно построится (не будет «в разработке»).
#
# Что где живёт:
#   • _init_skeleton()           — быстрая часть: менюшка, верхняя панель, стек.
#   • get_loading_steps()        — список шагов загрузки (label, callable).
#   • _build_page_for_section()  — единый диспетчер: по подстроке в названии
#                                  кнопки сайдбара создаёт нужную страницу.
#   • _register_page()           — кладёт страницу в стек и сопоставляет её
#                                  с индексом кнопки сайдбара.
#   • _apply_theme_and_wallpaper() — финальный шаг: тема + обои.
# =====================================================================

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.components.top_bar import TopBar
from ui.components.sidebar import DynamicSidebar
from ui.dashboard_screen import DashboardScreen

from database.connection import DBManager

class MainWindow(QMainWindow):
    """Главный каркас экосистемы БаБочки ERP (сборщик модулей и страниц)."""

    # =================================================================
    # 🧱 КОНСТРУКТОР
    # =================================================================
    def __init__(self, user_data, progressive: bool = False):
        super().__init__()
        self.user_data = user_data
        self.db = DBManager()

        # Ролевые доступы для сайдбара
        user_role = self.user_data.get('role', 'worker')
        self.user_data['allowed_modules'] = self.db.get_allowed_modules_for_role(user_role)

        # --- Служебное состояние сборки страниц ---
        self.page_mapping = {}          # индекс кнопки сайдбара → индекс в стеке
        self._current_page_idx = 1      # стек: 0 = дашборд, дальше по порядку

        # --- Шаг 1: быстрый каркас ---
        self._init_skeleton()

        # --- Шаг 2: если не прогрессивный — строим всё сразу ---
        if not progressive:
            for _label, builder in self.get_loading_steps():
                try:
                    builder()
                except Exception as e:
                    print(f"MainWindow: ошибка построения страницы: {e}")

    # =================================================================
    # 🏗 БЫСТРЫЙ КАРКАС
    # =================================================================
    def _init_skeleton(self):
        """Создаёт только «скелет»: топ-бар, сайдбар, пустой стек страниц,
        и первую страницу — Дашборд."""
        self.setWindowTitle("БаБочки DME — Экосистема Производства")
        self.setMinimumSize(1200, 750)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. ТУЛБАР
        self.top_bar = TopBar(self.user_data, self)
        self.top_bar.theme_changed.connect(self.apply_theme)
        self.top_bar.scale_changed.connect(self.handle_scale_change)
        self.top_bar.change_wallpaper_requested.connect(self.handle_wallpaper_selection)
        self.top_bar.change_color_requested.connect(self.handle_color_selection)
        main_layout.addWidget(self.top_bar)

        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        # 2. САЙДБАР
        self.sidebar = DynamicSidebar(self.user_data, self)
        self.sidebar.section_changed.connect(self.switch_page)
        workspace_layout.addWidget(self.sidebar)

        # 3. СТЕК СТРАНИЦ
        self.content_area = QStackedWidget()

        # Страница 0: Главный стол
        self.dashboard_page = DashboardScreen(self.user_data, self)
        self.content_area.addWidget(self.dashboard_page)
        self.page_mapping[0] = 0

        self._current_page_idx = 1

        workspace_layout.addWidget(self.content_area)
        main_layout.addLayout(workspace_layout)

    # =================================================================
    # 📋 СПИСОК ШАГОВ ЗАГРУЗКИ
    # =================================================================
    def get_loading_steps(self):
        """
        Возвращает список шагов загрузки: [(label, callable), ...].
        Здесь же — финальный шаг «Тема и обои».
        Порядок шагов совпадает с порядком модулей в сайдбаре.
        """
        steps = []

        for idx, btn in enumerate(self.sidebar.menu_buttons):
            if idx == 0:
                # Нулевой пункт — Дашборд, он уже создан в каркасе.
                continue

            text = btn.property("full_text") or f"модуль #{idx}"
            # Замыкаем idx и text корректно через фабрику
            steps.append((f"Модуль «{text}»", self._make_builder(idx, text)))

        # Финальный штрих — тема и обои
        steps.append(("🎨 Тема и оформление стола", self._apply_theme_and_wallpaper))
        return steps

    def _make_builder(self, idx: int, btn_text: str):
        """Возвращает функцию-строитель для конкретной кнопки сайдбара."""
        def _builder():
            self._build_page_for_section(idx, btn_text)
        return _builder

    # =================================================================
    # 🧩 ДИСПЕТЧЕР: СТРАНИЦА ПО РАЗДЕЛУ САЙДБАРА
    # =================================================================
    def _build_page_for_section(self, idx: int, btn_text: str):
        """Строит нужную страницу по подстроке в названии кнопки сайдбара."""
        if idx == 0:
            return

        # --- Проектирование ---
        if "Проектирование" in btn_text:
            from modules.constructor.constructor_ui import ConstructorUI
            from modules.constructor.constructor_controller import ConstructorController

            self.constructor_page = ConstructorUI(self)
            self.constructor_controller = ConstructorController(
                self.constructor_page, self.user_data
            )
            self._register_page(idx, self.constructor_page)
            return

        # --- Клиенты и заказы ---
        if "Клиенты и заказы" in btn_text:
            from modules.orders.orders_ui import OrdersUI
            self.orders_page = OrdersUI(self.user_data, self)
            self._register_page(idx, self.orders_page)
            return

        # --- Технический аудит ---
        if "Технический аудит" in btn_text:
            from modules.tech_audit.tech_audit_ui import TechAuditUI
            self.tech_audit_page = TechAuditUI(self.user_data, self)
            self._register_page(idx, self.tech_audit_page)
            return

        # --- Снабжение и Склад ---
        if "Снабжение и Склад" in btn_text:
            from modules.warehouse.warehouse_ui import WarehouseUI
            self.warehouse_page = WarehouseUI(self.user_data, self)
            self._register_page(idx, self.warehouse_page)
            return

        # --- Управление прайсами ---
        if "Управление прайсами" in btn_text:
            from modules.catalog.catalog_ui import CatalogUI
            self.catalog_page = CatalogUI(self)
            self._register_page(idx, self.catalog_page)
            return

        # --- Калькуляция модели ---
        if "Калькуляция модели" in btn_text:
            from modules.costing.costing_ui import CostingUI
            self.costing_page = CostingUI(self.user_data, self)
            self._register_page(idx, self.costing_page)
            return

        # --- Управление персоналом ---
        if "Управление персоналом" in btn_text:
            from modules.staff.staff_ui import StaffScreen
            self.staff_page = StaffScreen(self.user_data, self)
            self._register_page(idx, self.staff_page)
            return

        # --- Расчёт ЗП ---
        if "Расчёт ЗП" in btn_text:
            from modules.wage.wage_ui import WageUI
            self.wage_page = WageUI(self.user_data, self)
            self._register_page(idx, self.wage_page)
            return

        # --- Календарь фабрики ---
        if "Календарь фабрики" in btn_text:
            from modules.calendar.calendar_ui import CalendarUI
            self.calendar_page = CalendarUI(self.user_data, self)
            self._register_page(idx, self.calendar_page)
            return

        # --- Администрирование ---
        if "Администрирование" in btn_text:
            from modules.admin.admin_ui import AdminUI
            self.admin_page = AdminUI(self)
            self._register_page(idx, self.admin_page)
            return

        # --- 🎩 Модуль директора (было «Тест-модуль А») ---
        #     Ловим и новое название, и старое — чтобы страница
        #     всегда собралась, даже если сайдбар откатили.
        if "Модуль директора" in btn_text or "Тест-модуль А" in btn_text:
            from modules.director.director_ui import DirectorUI
            self.director_page = DirectorUI(self.user_data, self)
            self._register_page(idx, self.director_page)
            return

        # --- Прочие (ещё не написанные) — заглушка ---
        stub_page = QWidget()
        stub_layout = QVBoxLayout(stub_page)
        lbl_stub = QLabel(
            f"🛠️ Модуль «{btn_text}» находится в разработке...\n"
            "Скоро здесь появится полноценный рабочий интерфейс."
        )
        lbl_stub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_stub.setFont(QFont("Segoe UI", 14))
        lbl_stub.setStyleSheet(
            "color: #636d83; font-family: 'Segoe UI'; line-height: 150%;"
        )
        stub_layout.addWidget(lbl_stub)
        self._register_page(idx, stub_page)

    def _register_page(self, sidebar_idx: int, page_widget: QWidget):
        """Кладёт страницу в стек и сопоставляет с индексом кнопки сайдбара."""
        self.content_area.addWidget(page_widget)
        self.page_mapping[sidebar_idx] = self._current_page_idx
        self._current_page_idx += 1

    # =================================================================
    # 🎨 ФИНАЛЬНЫЙ ШАГ — ТЕМА И ОБОИ
    # =================================================================
    def _apply_theme_and_wallpaper(self):
        saved_theme = self.db.get_user_theme(self.user_data['id'])

        if saved_theme == "light":
            self.top_bar.current_theme = "light"
            self.top_bar.btn_theme.setText("🌙 Тёмная")
            self.top_bar.btn_theme.setStyleSheet(
                "background-color: #e5e7eb; border-radius: 4px; padding: 6px; "
                "color: #1f2937; font-weight: bold; border: 1px solid #d1d5db;"
            )

        self.apply_theme(saved_theme)

        initial_wallpaper = self.db.get_user_wallpaper(self.user_data['id'])
        self.dashboard_page.set_wallpaper(initial_wallpaper)

    # =================================================================
    # 🧭 ПЕРЕКЛЮЧЕНИЕ СТРАНИЦ
    # =================================================================
    def switch_page(self, button_index: int):
        """Переключает центральный модуль по индексу кнопки сайдбара."""
        target_page = self.page_mapping.get(button_index, 0)
        self.content_area.setCurrentIndex(target_page)

    # =================================================================
    # 🎨 ТЕМА
    # =================================================================
    def apply_theme(self, theme_name: str):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(current_dir, "styles", f"{theme_name}.qss")

        try:
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss_code = f.read()
                self.setStyleSheet(qss_code)
                DBManager.save_user_theme(self.user_data['id'], theme_name)
            else:
                print(f"⚠️ Файл стилей не найден: {qss_path}")
        except Exception as e:
            print(f"❌ Ошибка темы: {e}")

    # =================================================================
    # 🔍 МАСШТАБ ИНТЕРФЕЙСА
    # =================================================================
    def handle_scale_change(self, scale_value: float):
        DBManager.save_user_scale(self.user_data['id'], scale_value)

        msg = QMessageBox(self)
        msg.setWindowTitle("Масштаб интерфейса")
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            f"Установлен масштаб {int(scale_value * 100)}%.\n\n"
            "Пожалуйста, перезапустите программу."
        )
        msg.setStyleSheet("QLabel { color: black; }")
        msg.exec()

    # =================================================================
    # 🖼 ОБОИ И ЦВЕТ РАБОЧЕГО СТОЛА
    # =================================================================
    def handle_wallpaper_selection(self):
        """Проводник для выбора картинки-обоев рабочего стола."""
        import shutil

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение для фона", "",
            "Изображения (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            assets_dir = os.path.join(current_dir, "assets")
            os.makedirs(assets_dir, exist_ok=True)

            _, ext = os.path.splitext(file_path)
            destination_path = os.path.join(assets_dir, f"user_wallpaper{ext}")

            shutil.copy2(file_path, destination_path)

            DBManager.save_user_wallpaper(self.user_data['id'], destination_path)
            self.dashboard_page.set_wallpaper(destination_path)
        except Exception as e:
            print(f"Ошибка при сохранении файла обоев: {e}")

    def handle_color_selection(self, hex_code: str):
        """Сохраняет сплошной цвет фона рабочего стола."""
        color_marker = f"color:{hex_code}"
        DBManager.save_user_wallpaper(self.user_data['id'], color_marker)
        self.dashboard_page.set_wallpaper(color_marker)
# =====================================================================
# 🩹 ПАТЧ: ВЕТКА «ДИСПЕТЧЕР ПРОИЗВОДСТВА» В ДИСПЕТЧЕРЕ ГЛАВНОГО ОКНА
# ---------------------------------------------------------------------
# Зачем именно патч, а не правка тела класса:
#   • ui/main_window.py уже устоялся, тут тема, сайдбар, каркас, стеки;
#   • нам нужно добавить РОВНО ОДНУ ветку в _build_page_for_section.
#
# Что делает патч:
#   • запоминает оригинальный _build_page_for_section;
#   • подменяет его обёрткой: если в названии пункта сайдбара есть
#     «Диспетчер производства» — строит DispatcherUI и регистрирует
#     его в стеке. Во всех остальных случаях — работает как было.
#
# Патч применяется один раз при импорте модуля ui.main_window
# (APPEND дописывается в конец файла), ДО того как создаётся
# живой экземпляр MainWindow.
# =====================================================================

_ORIG_BUILD_PAGE_FOR_SECTION = MainWindow._build_page_for_section

def _patched_build_page_for_section(self, idx: int, btn_text: str):
    # --- 🎮 Диспетчер производства ---
    if "Диспетчер производства" in btn_text:
        try:
            from modules.production_dispatcher.dispatcher_ui import DispatcherUI
            self.dispatcher_page = DispatcherUI(self.user_data, self)
            self._register_page(idx, self.dispatcher_page)
            return
        except Exception as e:
            print(f"MainWindow patch: не удалось собрать Диспетчер производства: {e}")
            # Не break — упадём в оригинал, там будет заглушка «в разработке».

    # --- Всё остальное — как было ---
    _ORIG_BUILD_PAGE_FOR_SECTION(self, idx, btn_text)

MainWindow._build_page_for_section = _patched_build_page_for_section

# =====================================================================
# 🩹 ПАТЧ v2: РАСШИРЕННАЯ КАЛЬКУЛЯЦИЯ + НОВЫЙ МОДУЛЬ СПРАВОЧНИКОВ
# ---------------------------------------------------------------------
# Зачем именно патч, а не полная замена:
#   • ui/main_window.py — уже большой файл с темой, сайдбаром, стеками;
#   • нам нужно добавить/подменить РОВНО ДВЕ ветки в диспетчере
#     _build_page_for_section:
#         «Калькуляция модели» → ExtendedCostingUI (вкладки)
#         «Справочники»        → ReferencesUI (новый модуль)
#
# Как работает:
#   • ловим ветку «Калькуляция модели» — подсовываем ExtendedCostingUI
#     (вместо старого CostingUI);
#   • ловим ветку «Справочники» — создаём ReferencesUI;
#   • во всех остальных случаях — вызываем предыдущий патч v1
#     (он же вызывает настоящий _build_page_for_section).
# =====================================================================

_ORIG_V1_BUILD_PAGE = MainWindow._build_page_for_section

def _patched_build_page_for_section_v2(self, idx: int, btn_text: str):
    # --- 🎯 Калькуляция модели (расширенная: + Изделия и работы) ---
    if "Калькуляция модели" in btn_text:
        try:
            from modules.costing.costing_extended import ExtendedCostingUI
            self.costing_page = ExtendedCostingUI(self.user_data, self)
            self._register_page(idx, self.costing_page)
            return
        except Exception as e:
            print(f"MainWindow patch v2: ExtendedCostingUI упал — "
                  f"откатываюсь на оригинал: {e}")

    # --- 📚 Справочники (новый модуль на месте «Тест-модуля В») ---
    if "Справочники" in btn_text:
        try:
            from modules.references.references_ui import ReferencesUI
            self.references_page = ReferencesUI(self.user_data, self)
            self._register_page(idx, self.references_page)
            return
        except Exception as e:
            print(f"MainWindow patch v2: ReferencesUI упал — "
                  f"откатываюсь на заглушку: {e}")

    # --- Всё остальное — как было ---
    _ORIG_V1_BUILD_PAGE(self, idx, btn_text)

MainWindow._build_page_for_section = _patched_build_page_for_section_v2

# =====================================================================
# 🩹 ПАТЧ v3: «СИСТЕМНЫЕ НАСТРОЙКИ» — СНОВА ОТКРЫВАЕТ АДМИНКУ
# ---------------------------------------------------------------------
# ДИАГНОЗ:
#   В сайдбаре пункт переименован: «Администрирование» → «Системные
#   настройки» (см. ui/components/sidebar.py). Но диспетчер
#   _build_page_for_section искал подстроку «Администрирование» и,
#   не найдя её, отдавал заглушку «модуль в разработке».
#
# ЛЕЧЕНИЕ:
#   • ловим ЛЮБОЕ из двух имён — новое «Системные настройки»
#     и старое «Администрирование» (подстраховка на откат сайдбара);
#   • молча строим AdminUI — тот самый, что и раньше. Внутри него
#     уже собрана правильная раскладка «Системных настроек»:
#         • Доступы ролей
#         • 📥 Загрузка склада (Excel)
#         • Интеграции и API
#         • 🤖 ИИ-интеграции
#         • 🔢 Нумерация договоров
#         • Подключение к БД
#
# Как это встраивается в цепочку патчей main_window:
#   v3 (этот) → ловит «Системные настройки»
#   v2        → ловит «Калькуляция модели» и «Справочники»
#   v1        → ловит «Диспетчер производства»
#   оригинал  → всё остальное + заглушки
#
# Патч применяется ОДИН РАЗ при импорте модуля ui.main_window —
# до того, как будет создан живой экземпляр MainWindow.
# =====================================================================

_ORIG_V2_BUILD_PAGE = MainWindow._build_page_for_section

def _patched_build_page_for_section_v3(self, idx: int, btn_text: str):
    # --- ⚙ Системные настройки (бывшая Админка) ---
    if ("Системные настройки" in btn_text) or ("Администрирование" in btn_text):
        try:
            from modules.admin.admin_ui import AdminUI

            self.admin_page = AdminUI(self)
            self._register_page(idx, self.admin_page)
            return

        except Exception as e:
            # Не смогли — пусть сработает заглушка ниже по цепочке.
            print(f"MainWindow patch v3: AdminUI упал — "
                  f"откатываюсь на заглушку: {e}")

    # --- Всё остальное — по цепочке (v2 → v1 → оригинал) ---
    _ORIG_V2_BUILD_PAGE(self, idx, btn_text)

MainWindow._build_page_for_section = _patched_build_page_for_section_v3

# =====================================================================
# 🩹 ПАТЧ v4: «ПЕРСОНАЛ И ТАБЕЛЬ» — ХАБ С ДВУМЯ ВКЛАДКАМИ
# ---------------------------------------------------------------------
# Что делает патч:
#   • ловит пункт сайдбара «Управление персоналом» (а также
#     возможные новые имена «Персонал и Табель» / «Табель и Персонал»);
#   • вместо старого StaffScreen — строит StaffHubUI с двумя вкладками:
#         [👥 Персонал]  — то, что было раньше
#         [📋 Табель]    — новый вахтенный журнал
#     Первой вкладкой открывается «Персонал» — Джокер попросил
#     поменять местами (раньше хотели «Табель» первой).
#
# Порядок цепочки патчей main_window:
#   v4 (этот) → «Управление персоналом»
#   v3        → «Системные настройки»
#   v2        → «Калькуляция модели» / «Справочники»
#   v1        → «Диспетчер производства»
#   оригинал  → всё остальное
# =====================================================================

_ORIG_V3_BUILD_PAGE_HUB = MainWindow._build_page_for_section

def _patched_build_page_for_section_v4(self, idx: int, btn_text: str):
    # ---- 👥📋 Персонал и Табель ----
    if ("Управление персоналом" in btn_text
            or "Персонал и Табель" in btn_text
            or "Табель и Персонал" in btn_text):
        try:
            from modules.staff.staff_hub_ui import StaffHubUI
            self.staff_hub_page = StaffHubUI(self.user_data, self)
            self._register_page(idx, self.staff_hub_page)
            return
        except Exception as e:
            print(f"MainWindow patch v4: StaffHubUI упал — "
                  f"откатываюсь на стандартный StaffScreen: {e}")
            # Фолбэк: показать как было одиночным экраном
            try:
                from modules.staff.staff_ui import StaffScreen
                self.staff_page = StaffScreen(self.user_data, self)
                self._register_page(idx, self.staff_page)
                return
            except Exception as e2:
                print(f"MainWindow patch v4: StaffScreen тоже упал: {e2}")

    # ---- Всё остальное — по цепочке (v3 → v2 → v1 → оригинал) ----
    _ORIG_V3_BUILD_PAGE_HUB(self, idx, btn_text)

MainWindow._build_page_for_section = _patched_build_page_for_section_v4

# =====================================================================
# 🩹 ПАТЧ v5: «ПРОИЗВОДСТВЕННЫЙ КАЛЕНДАРЬ» — НОВОЕ ИМЯ МОДУЛЯ (этап 1)
# ---------------------------------------------------------------------
# ЧТО ИЗМЕНИЛОСЬ:
#   В сайдбаре пункт «Календарь фабрики» переименован в
#   «Производственный календарь» и поставлен под «Главный экран».
#
# ЧТО ДЕЛАЕТ ПАТЧ:
#   • ловит новое имя «Производственный календарь»;
#   • сохраняет подстраховку на старое имя «Календарь фабрики» —
#     если кто-то откатит sidebar.py, страница всё равно построится;
#   • во всех остальных случаях — отдаёт управление предыдущему
#     патчу v4 (Персонал и Табель), а тот — по цепочке до оригинала.
#
# Порядок цепочки патчей main_window теперь:
#   v5 (этот) → «Производственный календарь»
#   v4        → «Управление персоналом» (хаб с вкладками)
#   v3        → «Системные настройки»
#   v2        → «Калькуляция модели» / «Справочники»
#   v1        → «Диспетчер производства»
#   оригинал  → всё остальное
#
# Патч применяется один раз при импорте модуля ui.main_window.
# =====================================================================

_ORIG_V4_BUILD_PAGE = MainWindow._build_page_for_section

def _patched_build_page_for_section_v5(self, idx: int, btn_text: str):
    # --- 📅 Производственный календарь (бывшее «Календарь фабрики») ---
    if ("Производственный календарь" in btn_text
            or "Календарь фабрики" in btn_text):
        try:
            from modules.calendar.calendar_ui import CalendarUI
            self.calendar_page = CalendarUI(self.user_data, self)
            self._register_page(idx, self.calendar_page)
            return
        except Exception as e:
            print(f"MainWindow patch v5: CalendarUI упал — "
                  f"откатываюсь на заглушку: {e}")

    # --- Всё остальное — по цепочке (v4 → v3 → v2 → v1 → оригинал) ---
    _ORIG_V4_BUILD_PAGE(self, idx, btn_text)

MainWindow._build_page_for_section = _patched_build_page_for_section_v5

# =====================================================================
# 🩹 ПАТЧ v6 (ЭТАП 2 ПЕРЕЕЗДА):
#     «ТЕХНОЛОГИЯ И ЦЕНЫ» — ОБЪЕДИНЁННЫЙ МОДУЛЬ
# ---------------------------------------------------------------------
# ЧТО ИЗМЕНИЛОСЬ:
#   В сайдбаре два отдельных пункта —
#       «Калькуляция модели»  и  «Управление прайсами» —
#   объединены в ОДИН:
#       «🎯 Технология и цены»
#   Внутри — три вкладки:
#       🎯 Калькуляция моделей
#       🏭 Изделия и работы
#       💰 Прайсы и опции
#
# ЧТО ДЕЛАЕТ ПАТЧ:
#   • ловит новое имя «Технология и цены»;
#   • поддерживает СТАРЫЕ имена как подстраховку —
#     «Калькуляция модели» и «Управление прайсами». Так, если
#     кто-то откатит sidebar.py в прежний вид, страница всё равно
#     соберётся корректно (обе старые кнопки открывают новый модуль).
#   • строит ExtendedCostingUI и кладёт в стек.
#
# Порядок цепочки патчей main_window теперь:
#   v6 (этот) → «Технология и цены» / «Калькуляция модели» / «Управление прайсами»
#   v5        → «Производственный календарь»
#   v4        → «Управление персоналом» (хаб с вкладками)
#   v3        → «Системные настройки»
#   v2        → «Калькуляция модели» / «Справочники»
#   v1        → «Диспетчер производства»
#   оригинал  → всё остальное
#
# Патч применяется один раз при импорте модуля ui.main_window —
# до того, как будет создан живой экземпляр MainWindow.
# =====================================================================

_ORIG_V5_BUILD_PAGE = MainWindow._build_page_for_section

def _patched_build_page_for_section_v6(self, idx: int, btn_text: str):
    # --- 🎯 Технология и цены (объединение Калькуляции + Прайсов) ---
    if ("Технология и цены" in btn_text
            or "Калькуляция модели" in btn_text
            or "Управление прайсами" in btn_text):
        try:
            from modules.costing.costing_extended import ExtendedCostingUI
            self.costing_page = ExtendedCostingUI(self.user_data, self)
            self._register_page(idx, self.costing_page)

            # Если пришли по старому имени «Управление прайсами» —
            # сразу переключаем вкладку на «Прайсы и опции».
            if "Управление прайсами" in btn_text and hasattr(self.costing_page, "show_price_tab"):
                try:
                    self.costing_page.show_price_tab()
                except Exception as tab_err:
                    print(f"MainWindow patch v6: не удалось переключить "
                          f"вкладку на Прайсы: {tab_err}")
            return
        except Exception as e:
            print(f"MainWindow patch v6: ExtendedCostingUI упал — "
                  f"откатываюсь на предыдущую цепочку: {e}")

    # --- Всё остальное — по цепочке (v5 → v4 → v3 → v2 → v1 → оригинал) ---
    _ORIG_V5_BUILD_PAGE(self, idx, btn_text)

MainWindow._build_page_for_section = _patched_build_page_for_section_v6

# =====================================================================
# 🩹 ПАТЧ v7 (ФИНАЛЬНАЯ ПЕРЕСТАНОВКА):
#     • 🏭 «Производство»         — объединённый хаб
#     • 👥 «Персонал и Оплата»    — трёхвкладочный хаб
#     • 🎩 «Кабинет руководителя» — переименованный Модуль директора
# ---------------------------------------------------------------------
# Что делает патч:
#   • Ловит ТРИ новых названия пунктов сайдбара.
#   • Для каждого строит СВОЙ рабочий виджет:
#         «Производство»         → ProductionHubUI  (4 вкладки)
#         «Персонал и Оплата»    → StaffHubUI       (3 вкладки)
#         «Кабинет руководителя» → DirectorUI       (как и было)
#   • Все остальные пункты — по цепочке v6 → v5 → ... → оригинал.
#
# ЦЕПОЧКА ПАТЧЕЙ main_window после v7:
#   v7 (этот) → «Производство» / «Персонал и Оплата» / «Кабинет руководителя»
#   v6        → «Технология и цены» + старые имена Калькуляции/Прайсов
#   v5        → «Производственный календарь»
#   v4        → «Управление персоналом» / «Персонал и Табель» (старое имя)
#   v3        → «Системные настройки»
#   v2        → «Калькуляция модели» / «Справочники»
#   v1        → «Диспетчер производства» (старое имя)
#   оригинал  → «Клиенты и заказы» / «Технический аудит» / «Снабжение и Склад»
#               + заглушка «в разработке» для всего остального
#
# Патч применяется один раз при импорте модуля ui.main_window —
# до того как создаётся живой экземпляр MainWindow.
# =====================================================================

_ORIG_V6_BUILD_PAGE = MainWindow._build_page_for_section

def _patched_build_page_for_section_v7(self, idx: int, btn_text: str):
    # -----------------------------------------------------------------
    # 🏭 ПРОИЗВОДСТВО — объединённый хаб (Тех.аудит + Диспетчер)
    # -----------------------------------------------------------------
    # Ловим ТОЛЬКО точное имя «Производство» (btn_text == "Производство").
    # Старое «Диспетчер производства» содержит подстроку «производство» —
    # оно продолжит ловиться в патче v1 как раньше (страховка).
    # -----------------------------------------------------------------
    if btn_text.strip() == "Производство":
        try:
            from modules.production.production_hub_ui import ProductionHubUI
            self.production_hub_page = ProductionHubUI(self.user_data, self)
            self._register_page(idx, self.production_hub_page)
            return
        except Exception as e:
            print(f"MainWindow patch v7: ProductionHubUI упал — "
                  f"откатываюсь на цепочку: {e}")

    # -----------------------------------------------------------------
    # 👥 ПЕРСОНАЛ И ОПЛАТА — трёхвкладочный хаб
    # -----------------------------------------------------------------
    # Страховка на старое «Персонал и Табель» уже есть в патче v4 —
    # он использует тот же самый StaffHubUI, который мы сейчас
    # переделали на три вкладки. Значит, оба имени работают.
    # -----------------------------------------------------------------
    if btn_text.strip() == "Персонал и Оплата":
        try:
            from modules.staff.staff_hub_ui import StaffHubUI
            self.staff_hub_page = StaffHubUI(self.user_data, self)
            self._register_page(idx, self.staff_hub_page)
            return
        except Exception as e:
            print(f"MainWindow patch v7: StaffHubUI упал — "
                  f"откатываюсь на цепочку: {e}")

    # -----------------------------------------------------------------
    # 🎩 КАБИНЕТ РУКОВОДИТЕЛЯ — переименованный Модуль директора
    # -----------------------------------------------------------------
    # Модуль тот же самый (DirectorUI), просто показывается под новым
    # именем в сайдбаре. Старая ловушка «Модуль директора» из оригинала
    # тоже остаётся как страховка.
    # -----------------------------------------------------------------
    if "Кабинет руководителя" in btn_text:
        try:
            from modules.director.director_ui import DirectorUI
            self.director_page = DirectorUI(self.user_data, self)
            self._register_page(idx, self.director_page)
            return
        except Exception as e:
            print(f"MainWindow patch v7: DirectorUI упал — "
                  f"откатываюсь на цепочку: {e}")

    # -----------------------------------------------------------------
    # Всё остальное — по цепочке (v6 → v5 → ... → оригинал).
    # -----------------------------------------------------------------
    _ORIG_V6_BUILD_PAGE(self, idx, btn_text)

MainWindow._build_page_for_section = _patched_build_page_for_section_v7

# =====================================================================
# 🩹 ПАТЧ v8: АВТО-ПОДСТРОЙКА ТЕМЫ ПО ЯРКОСТИ ОБОЕВ И ЦВЕТА ФОНА
# ---------------------------------------------------------------------
# Что делаем:
#   • При выборе картинки-обоев — считаем среднюю яркость пикселей.
#       Очень тёмные (< 100)  → принудительно тёмная тема.
#       Очень светлые (> 180) → принудительно светлая тема.
#       Середина             → оставляем как есть (не дёргаем пользователя).
#   • При выборе сплошного цвета — то же по HEX.
#   • Кнопка темы в top_bar синхронизируется автоматически.
#
# Что НЕ трогаем:
#   • Кнопка «☀️ Светлая / 🌙 Тёмная» в топ-баре продолжает работать —
#     пользователь всегда может переопределить автоподбор.
# =====================================================================

from PySide6.QtWidgets import QFileDialog as _QFD
from PySide6.QtCore import Qt as _Qt

def _force_theme(window, theme_name: str):
    """Форсирует тему и синхронизирует кнопку в топ-баре."""
    try:
        window.top_bar.current_theme = theme_name
        if theme_name == "light":
            window.top_bar.btn_theme.setText("🌙 Тёмная")
            window.top_bar.btn_theme.setStyleSheet(
                "background-color: #e5e7eb; border-radius: 4px; padding: 6px; "
                "color: #1f2937; font-weight: bold; border: 1px solid #d1d5db;"
            )
        else:
            window.top_bar.btn_theme.setText("☀️ Светлая")
            window.top_bar.btn_theme.setStyleSheet(
                "background-color: #2c313c; border-radius: 4px; padding: 6px; "
                "color: white; font-weight: bold; border: none;"
            )
        window.apply_theme(theme_name)
    except Exception as e:
        print(f"_force_theme: {e}")

def _auto_theme_for_image(window, image_path: str):
    """
    Считает среднюю яркость картинки-обоев и, если она явно тёмная
    или явно светлая — переключает тему интерфейса.
    """
    try:
        from PySide6.QtGui import QImage
        img = QImage(image_path)
        if img.isNull():
            return
        # Уменьшаем до 32×32 для скорости — средняя яркость не изменится
        small = img.scaled(32, 32,
                           _Qt.AspectRatioMode.KeepAspectRatio,
                           _Qt.TransformationMode.SmoothTransformation)
        total = 0
        cnt = small.width() * small.height()
        if cnt <= 0:
            return
        for y in range(small.height()):
            for x in range(small.width()):
                c = small.pixelColor(x, y)
                total += 0.2126 * c.red() + 0.7152 * c.green() + 0.0722 * c.blue()
        avg = total / cnt

        suggested = None
        if avg < 100:
            suggested = "dark"
        elif avg > 180:
            suggested = "light"

        if suggested and suggested != window.top_bar.current_theme:
            _force_theme(window, suggested)
    except Exception as e:
        print(f"_auto_theme_for_image: {e}")

# --- Патч: handle_wallpaper_selection с авто-подстройкой темы ---
_ORIG_HANDLE_WALLPAPER_SEL = MainWindow.handle_wallpaper_selection

def _patched_handle_wallpaper_selection(self):
    import shutil

    file_path, _ = _QFD.getOpenFileName(
        self, "Выберите изображение для фона", "",
        "Изображения (*.png *.jpg *.jpeg)"
    )
    if not file_path:
        return

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(current_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)

        _, ext = os.path.splitext(file_path)
        destination_path = os.path.join(assets_dir, f"user_wallpaper{ext}")
        shutil.copy2(file_path, destination_path)

        DBManager.save_user_wallpaper(self.user_data['id'], destination_path)
        self.dashboard_page.set_wallpaper(destination_path)

        # 🆕 Авто-подбор темы по яркости фотографии
        _auto_theme_for_image(self, destination_path)
    except Exception as e:
        print(f"Ошибка при сохранении файла обоев: {e}")

MainWindow.handle_wallpaper_selection = _patched_handle_wallpaper_selection

# --- Патч: handle_color_selection с авто-подстройкой темы ---
_ORIG_HANDLE_COLOR_SEL = MainWindow.handle_color_selection

def _patched_handle_color_selection(self, hex_code: str):
    color_marker = f"color:{hex_code}"
    DBManager.save_user_wallpaper(self.user_data['id'], color_marker)
    self.dashboard_page.set_wallpaper(color_marker)

    # 🆕 Авто-подбор: светлый цвет → светлая тема, тёмный → тёмная
    try:
        from PySide6.QtGui import QColor as _QC
        c = _QC(hex_code)
        if c.isValid():
            lum = 0.2126 * c.red() + 0.7152 * c.green() + 0.0722 * c.blue()
            suggested = "dark" if lum < 110 else "light"
            if suggested != self.top_bar.current_theme:
                _force_theme(self, suggested)
    except Exception as e:
        print(f"_patched_handle_color_selection: {e}")

MainWindow.handle_color_selection = _patched_handle_color_selection

# =====================================================================
# 🩹 ПАТЧ v8: РАЗДЕЛ «❓ ПОМОЩЬ» — ИНСТРУКЦИИ ПО РАБОТЕ
# ---------------------------------------------------------------------
# Что делает:
#   • Ловит пункт сайдбара «Помощь» (ровно так, как он назван в
#     ui/components/sidebar.py).
#   • Строит модуль HelpUI — раздел с инструкциями по подсистемам ERP.
#   • Доступ к самому разделу — у всех. Раскладка внутри (какие
#     именно инструкции показать мастеру, а какие директору) —
#     определяется модулем HelpUI на основе уже существующей
#     матрицы прав (таблица permissions).
#
# ЦЕПОЧКА ПАТЧЕЙ main_window после v8:
#   v8 (этот) → «Помощь»
#   v7        → «Производство» / «Персонал и Оплата» / «Кабинет руководителя»
#   v6        → «Технология и цены» + старые имена Калькуляции/Прайсов
#   v5        → «Производственный календарь»
#   v4        → «Управление персоналом» / «Персонал и Табель»
#   v3        → «Системные настройки»
#   v2        → «Калькуляция модели» / «Справочники»
#   v1        → «Диспетчер производства»
#   оригинал  → всё остальное и заглушка «в разработке»
#
# Патч применяется один раз при импорте модуля ui.main_window —
# до того как будет создан живой экземпляр MainWindow.
# =====================================================================

_ORIG_V7_BUILD_PAGE_HELP = MainWindow._build_page_for_section

def _patched_build_page_for_section_v8(self, idx: int, btn_text: str):
    # --- ❓ Помощь — раздел с инструкциями по работе —------------
    if btn_text.strip() == "Помощь":
        try:
            from modules.help.help_ui import HelpUI
            self.help_page = HelpUI(self.user_data, self)
            self._register_page(idx, self.help_page)
            return
        except Exception as e:
            print(f"MainWindow patch v8: HelpUI упал — "
                  f"откатываюсь на заглушку: {e}")

    # --- Всё остальное — по цепочке ---
    _ORIG_V7_BUILD_PAGE_HELP(self, idx, btn_text)

MainWindow._build_page_for_section = _patched_build_page_for_section_v8