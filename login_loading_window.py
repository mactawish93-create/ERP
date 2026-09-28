# ui/login_loading_window.py
# =====================================================================
# 🚪🚀 ОБЪЕДИНЁННЫЙ ЭКРАН «ЛОГИН + ЗАГРУЗКА»
#
# 🎯 ЗАЧЕМ ОБЪЕДИНИЛИ:
#   Раньше путь был такой:
#       заставка → окно логина → экран загрузки → главное окно
#   Пользователь вводил пароль, окно закрывалось, потом ЕЩЁ РАЗ
#   ждал на экране загрузки. Двойная пауза.
#
#   Теперь:
#       заставка → ОБЪЕДИНЁННЫЙ ЭКРАН → главное окно
#
#   • Одновременно с вводом пароля в фоне идёт «тихая» предзагрузка
#     модулей (самое тяжёлое — импорты Python).
#   • Пользователь набирает логин/пароль — прогресс уже бежит.
#   • Нажал «Войти» — собираем MainWindow. Импорты сделаны, всё быстро.
#
# 🔐 Пароль-чек «принудительная смена» встроен внутрь.
#
# 📌 Старый LoadingScreen и старый LoginWindow НЕ удалены — они
#    остались рабочими на случай откатов. main.py просто вызывает
#    наш объединённый экран.
# =====================================================================

import os
import sys
import traceback

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QFrame, QListWidget, QListWidgetItem, QApplication,
    QDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont

from database.connection import DBManager
from ui.components.password_dialog import PasswordDialog

# =====================================================================
# 📚 СПИСОК «ТЯЖЁЛЫХ» МОДУЛЕЙ ДЛЯ ТИХОЙ ПРЕДЗАГРУЗКИ
# ---------------------------------------------------------------------
# Импортируем эти модули ЗАРАНЕЕ — пока пользователь вводит пароль.
# Импорт каждого занимает 20–150 мс. Все вместе — заметная задержка,
# которую мы «растворяем» в тишине.
#
# Порядок не важен. Модуль, у которого не получится импорт, вежливо
# запишется в журнал — приложение не упадёт.
# =====================================================================
PREFETCH_LIST = [
    # ---- Виджеты рабочего стола ----
    "widgets.calendar_widget",
    "widgets.orders_widget",
    "widgets.production_load_widget",
    "widgets.finance_widget",
    "widgets.hot_leads_widget",
    "widgets.warehouse_alerts_widget",
    "widgets.payments_due_widget",
    "widgets.urgent_orders_widget",
    "widgets.my_tasks_widget",

    # ---- Воронка конструктора -----
    "modules.constructor.constructor_ui",
    "modules.constructor.constructor_controller",
    "modules.constructor.steps.step1_client",
    "modules.constructor.steps.step2_direction",
    "modules.constructor.steps.step3_config",
    "modules.constructor.steps.step4_ui",
    "modules.constructor.steps.step4_print",

    # ---- База заказов / клиенты ----
    "modules.orders.orders_ui",

    # ---- Цех ----
    "modules.tech_audit.tech_audit_ui",
    "modules.production_dispatcher.dispatcher_ui",
    "modules.production.production_hub_ui",

    # ---- Склад ----
    "modules.warehouse.warehouse_ui",
    "modules.warehouse.excel_import_ui",

    # ---- Персонал и оплата ----
    "modules.staff.staff_ui",
    "modules.staff.timesheet_ui",
    "modules.staff.staff_hub_ui",
    "modules.wage.wage_ui",

    # ---- Календарь ----
    "modules.calendar.calendar_ui",

    # ---- Технология и цены ----
    "modules.costing.costing_extended",

    # ---- Справочники ----
    "modules.references.references_ui",

    # ---- Админка ----
    "modules.admin.admin_ui",

    # ---- Директор ----
    "modules.director.director_ui",
]

# =====================================================================
# 🚪🚀 ГЛАВНОЕ ОКНО
# =====================================================================
class UnifiedLoginLoadingWindow(QWidget):
    """
    Окно одновременно: логин + экран подготовки системы.
    По готовности отдаёт наружу `finished(main_window)`.
    """

    finished = Signal(object)

    # -----------------------------------------------------------------
    # 🧱 ИНИЦИАЛИЗАЦИЯ
    # -----------------------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("БаБочки DME — Вход в систему")
        self.setFixedSize(580, 680)
        self.setWindowFlags(
            Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint |
            Qt.WindowCloseButtonHint
        )

        # --- Состояние ---
        self._prefetch_total = len(PREFETCH_LIST)
        self._prefetch_done = 0
        self._prefetch_ok = []
        self._prefetch_fail = []
        self._prefetch_stopped = False    # остановить префетч, если уже строим

        self._main_window = None
        self._user_data = None
        self._build_steps = []
        self._build_step_idx = 0
        self._total_steps = max(1, self._prefetch_total)

        self._apply_builtin_style()
        self._build_ui()

    # =================================================================
    # 🎨 ВСТРОЕННЫЙ СТИЛЬ (тема приложения ещё не применена)
    # =================================================================
    def _apply_builtin_style(self):
        self.setStyleSheet("""
            QWidget#LoginRoot { background-color: #1a1c23; }

            QLabel#LoginTitle {
                color: #4bb34b; font-size: 24px; font-weight: bold;
                font-family: 'Segoe UI';
            }
            QLabel#LoginSubtitle {
                color: #8a92a6; font-size: 11px;
                font-family: 'Segoe UI';
            }
            QLabel#LoginCaption {
                color: #d0d0d6; font-size: 12px;
                font-family: 'Segoe UI';
            }
            QLabel#LoginError {
                color: #ff6b6b; font-size: 11px;
                font-family: 'Segoe UI';
            }
            QLabel#LoginStepLabel {
                color: #b0b0b8; font-size: 11px;
                font-family: 'Segoe UI';
                padding: 3px 0;
            }

            QFrame#LoginCard {
                background-color: #21252b;
                border: 1px solid #2c313c;
                border-radius: 10px;
            }
            QFrame#StepsCard {
                background-color: #16191f;
                border: 1px solid #2c313c;
                border-radius: 8px;
            }

            QLineEdit#LoginInput {
                background-color: #282c34;
                border: 1px solid #3f4451;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                color: #ffffff;
                font-family: 'Segoe UI';
            }
            QLineEdit#LoginInput:focus { border: 1px solid #4bb34b; }
            QLineEdit#LoginInput:disabled {
                background-color: #1a1c23; color: #5c6370;
            }

            QPushButton#LoginBtn {
                background-color: #4bb34b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 11px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }
            QPushButton#LoginBtn:hover:enabled { background-color: #3ca03c; }
            QPushButton#LoginBtn:disabled {
                background-color: #2c313c; color: #5c6370;
            }

            QProgressBar {
                background-color: #21252b;
                border: 1px solid #2c313c;
                border-radius: 6px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                font-family: 'Segoe UI';
                min-height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4bb34b;
                border-radius: 5px;
            }

            QListWidget#StepLog {
                background-color: #16191f;
                border: none;
                color: #b0b0b8;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                outline: none;
                padding: 4px;
            }
            QListWidget#StepLog::item { padding: 2px 6px; }
        """)

    # =================================================================
    # 🧱 СБОРКА UI
    # =================================================================
    def _build_ui(self):
        wrap = QVBoxLayout(self)
        wrap.setContentsMargins(0, 0, 0, 0)

        root = QWidget()
        root.setObjectName("LoginRoot")
        wrap.addWidget(root)

        lay = QVBoxLayout(root)
        lay.setContentsMargins(30, 22, 30, 22)
        lay.setSpacing(12)

        # --- Шапка ---
        title = QLabel("🦋 БаБочки DME")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("Digital Manufacturing Ecosystem")
        sub.setObjectName("LoginSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)

        lay.addSpacing(6)

        # --- КАРТОЧКА ЛОГИНА ---
        card = QFrame()
        card.setObjectName("LoginCard")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(22, 16, 22, 16)
        card_lay.setSpacing(8)

        self.lbl_form_title = QLabel("Вход в систему")
        self.lbl_form_title.setStyleSheet(
            "color: #d0d0d6; font-size: 13px; font-weight: bold; "
            "font-family: 'Segoe UI';"
        )
        card_lay.addWidget(self.lbl_form_title)

        lbl_user = QLabel("Логин сотрудника:")
        lbl_user.setObjectName("LoginCaption")
        card_lay.addWidget(lbl_user)

        self.input_login = QLineEdit()
        self.input_login.setObjectName("LoginInput")
        self.input_login.setPlaceholderText("Введите ваш логин...")
        self.input_login.textChanged.connect(self._reset_error)
        self.input_login.returnPressed.connect(self._focus_password)
        card_lay.addWidget(self.input_login)

        lbl_pass = QLabel("Пароль:")
        lbl_pass.setObjectName("LoginCaption")
        card_lay.addWidget(lbl_pass)

        self.input_pass = QLineEdit()
        self.input_pass.setObjectName("LoginInput")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setPlaceholderText("Введите ваш пароль...")
        self.input_pass.textChanged.connect(self._reset_error)
        self.input_pass.returnPressed.connect(self._handle_login_clicked)
        card_lay.addWidget(self.input_pass)

        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("LoginError")
        self.lbl_error.setWordWrap(True)
        card_lay.addWidget(self.lbl_error)

        self.btn_login = QPushButton("🚀 Войти в систему")
        self.btn_login.setObjectName("LoginBtn")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.clicked.connect(self._handle_login_clicked)
        card_lay.addWidget(self.btn_login)

        lay.addWidget(card)

        # --- БЛОК ПОДГОТОВКИ ---
        load_row = QHBoxLayout()
        load_row.setSpacing(8)

        lbl_load_title = QLabel("Подготовка системы")
        lbl_load_title.setStyleSheet(
            "color: #8a92a6; font-size: 11px; font-weight: bold; "
            "font-family: 'Segoe UI';"
        )
        load_row.addWidget(lbl_load_title)
        load_row.addStretch()

        self.lbl_overall = QLabel("0%")
        self.lbl_overall.setObjectName("LoginSubtitle")
        load_row.addWidget(self.lbl_overall)

        lay.addLayout(load_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, max(1, self._total_steps))
        self.progress.setValue(0)
        self.progress.setFormat("%v / %m")
        lay.addWidget(self.progress)

        self.lbl_current_step = QLabel("💤 Ожидание входа пользователя...")
        self.lbl_current_step.setObjectName("LoginStepLabel")
        self.lbl_current_step.setWordWrap(True)
        self.lbl_current_step.setMinimumHeight(28)
        lay.addWidget(self.lbl_current_step)

        # --- ЖУРНАЛ ШАГОВ ---
        steps_card = QFrame()
        steps_card.setObjectName("StepsCard")
        steps_card_lay = QVBoxLayout(steps_card)
        steps_card_lay.setContentsMargins(6, 6, 6, 6)

        self.log = QListWidget()
        self.log.setObjectName("StepLog")
        self.log.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.log.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        steps_card_lay.addWidget(self.log)

        lay.addWidget(steps_card, stretch=1)

    # =================================================================
    # 🚀 СТАРТ
    # =================================================================
    def start(self):
        """Запускает тихую предзагрузку модулей и ждёт ввода пароля."""
        self._log("🚀 Система готова принимать данные для входа.", "#8a92a6")
        self._log("💡 Пока вы вводите пароль — идёт подготовка модулей.", "#4aa3ff")

        # Небольшая пауза, чтобы окно успело красиво отрисоваться.
        QTimer.singleShot(180, self._prefetch_next)

    # -----------------------------------------------------------------
    def _prefetch_next(self):
        """Импортирует один модуль и запускает следующий шаг."""
        if self._prefetch_stopped:
            return

        if self._prefetch_done >= self._prefetch_total:
            self._on_prefetch_complete()
            return

        module_name = PREFETCH_LIST[self._prefetch_done]
        self.lbl_current_step.setText(f"⏳ Подготовка: {module_name}")

        try:
            __import__(module_name)
            self._prefetch_ok.append(module_name)
            self._log(f"✅ {module_name}", "#4bb34b")
        except Exception as e:
            err = str(e).strip() or e.__class__.__name__
            self._prefetch_fail.append((module_name, err))
            print(f"Prefetch: не удалось импортировать {module_name}: {e}")
            self._log(f"⚠ {module_name}  —  {err[:60]}", "#ff9800")

        self._prefetch_done += 1
        self.progress.setValue(self._prefetch_done)
        self._update_overall()

        # Даём Qt перерисовать изменения.
        QTimer.singleShot(12, self._prefetch_next)

    def _on_prefetch_complete(self):
        n_ok = len(self._prefetch_ok)
        n_fail = len(self._prefetch_fail)

        if n_fail == 0:
            self._log(f"✅ Подготовлено модулей: {n_ok}", "#4bb34b")
            self.lbl_current_step.setText(
                "🟢 Система готова. Введите логин и пароль, чтобы продолжить."
            )
        else:
            self._log(
                f"⚠ Подготовлено: {n_ok}, с замечаниями: {n_fail}",
                "#ff9800"
            )
            self.lbl_current_step.setText(
                "🟡 Система готова с замечаниями. Можно входить."
            )

    # =================================================================
    # 🔐 ЛОГИН
    # =================================================================
    def _focus_password(self):
        self.input_pass.setFocus()

    def _reset_error(self):
        if self.lbl_error.text():
            self.lbl_error.setText("")

    def _handle_login_clicked(self):
        username = self.input_login.text().strip()
        password = self.input_pass.text()

        if not username or not password:
            self.lbl_error.setText("Заполните все поля ввода!")
            return

        # Блокируем форму на время проверки.
        self._set_form_enabled(False)
        self.lbl_error.setText("⏳ Проверка данных...")

        # Авторизация (sync — быстро, MySQL уже подключён на заставке).
        user_data = DBManager.authenticate_user(username, password)

        if not user_data:
            self._set_form_enabled(True)
            self.lbl_error.setText(
                "Неверный логин или пароль! Доступ отклонён."
            )
            self.input_pass.selectAll()
            self.input_pass.setFocus()
            return

        self.lbl_error.setText("")

        # --- 🔐 Принудительная смена пароля ---
        if user_data.get("must_change_password"):
            dlg = PasswordDialog(
                user_id=user_data["id"], forced=True, parent=self
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                self._set_form_enabled(True)
                self.lbl_error.setText(
                    "Смена пароля отменена. Вход невозможен до её завершения."
                )
                return

        # --- Успех ---
        self._user_data = user_data
        self._proceed_to_build_main_window()

    def _set_form_enabled(self, enabled: bool):
        self.input_login.setEnabled(enabled)
        self.input_pass.setEnabled(enabled)
        self.btn_login.setEnabled(enabled)

    # =================================================================
    # 🏗 ПОСТРОЕНИЕ MAIN WINDOW
    # =================================================================
    def _proceed_to_build_main_window(self):
        # Останавливаем тихую предзагрузку — дальше строим главное окно.
        self._prefetch_stopped = True

        self.lbl_form_title.setText("Синхронизация модулей...")
        self.lbl_current_step.setText("🏗 Собираю главное окно...")
        self._log("🚪 Вход выполнен. Готовлю рабочее место...", "#4bb34b")
        self.btn_login.setText("⏳ Идёт подготовка...")

        # --- Создаём каркас MainWindow (быстро — только скелет) ---
        try:
            from ui.main_window import MainWindow
            self._main_window = MainWindow(self._user_data, progressive=True)
            self._log("🏗 Каркас главного окна готов.", "#8a92a6")
        except Exception as e:
            full = traceback.format_exc()
            print(full)
            self._log(f"❌ Не удалось создать главное окно: {e}", "#ff6b6b")
            self.lbl_error.setText(f"Ошибка сборки: {e}")
            self._set_form_enabled(True)
            self.btn_login.setText("🚀 Войти в систему")
            return

        # --- Список шагов сборки страниц ---
        try:
            self._build_steps = list(self._main_window.get_loading_steps())
        except Exception as e:
            self._log(f"⚠ Не удалось получить список шагов: {e}", "#ff9800")
            self._build_steps = []

        self._build_step_idx = 0
        self._total_steps = max(1, self._prefetch_total + len(self._build_steps))
        self.progress.setRange(0, self._total_steps)
        self.progress.setValue(self._prefetch_done)
        self._update_overall()

        QTimer.singleShot(60, self._build_next_step)

    def _build_next_step(self):
        if self._build_step_idx >= len(self._build_steps):
            self._finish_and_emit()
            return

        label, builder = self._build_steps[self._build_step_idx]
        self.lbl_current_step.setText(f"⏳ Модуль: {label}")

        try:
            builder()
            self._log(f"✅ {label}", "#4bb34b")
        except Exception as e:
            print(f"Unified: ошибка шага «{label}»: {e}")
            self._log(f"⚠ {label}  —  {e}", "#ff9800")

        self._build_step_idx += 1
        self.progress.setValue(self._prefetch_done + self._build_step_idx)
        self._update_overall()

        QTimer.singleShot(18, self._build_next_step)

    def _finish_and_emit(self):
        self.lbl_current_step.setText(
            "✅ Система готова. Открываю рабочее место..."
        )
        self._log("🎉 Все модули на связи.", "#4bb34b")
        self.progress.setValue(self.progress.maximum())
        self._update_overall()

        QTimer.singleShot(260, lambda: self.finished.emit(self._main_window))

    # =================================================================
    # 🧰 СЕРВИС
    # =================================================================
    def _update_overall(self):
        m = self.progress.maximum()
        v = self.progress.value()
        pct = int(round((v / m) * 100)) if m else 0
        self.lbl_overall.setText(f"{pct}%")

    def _log(self, text: str, color: str = "#b0b0b8"):
        item = QListWidgetItem(text)
        item.setForeground(QColor(color))
        self.log.addItem(item)

        # Держим журнал компактным — старые строки «выталкиваются».
        while self.log.count() > 80:
            self.log.takeItem(0)
        self.log.scrollToBottom()

    # -----------------------------------------------------------------
    def closeEvent(self, event):
        """Если пользователь закрыл окно до завершения — просто отпускаем."""
        super().closeEvent(event)