# modules/sales_wizard/main_wizard.py
import pymysql
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import DB_CONFIG

from modules.sales_wizard.step_1_contacts import Step1ContactsWidget
from modules.sales_wizard.step_2_category import Step2CategoryWidget
from modules.sales_wizard.step_3_config import Step3ConfigWidget
from modules.sales_wizard.step_4_estimate import Step4EstimateWidget

class SalesWizardMainController(QWidget):
    """Генеральный диспетчер воронки расчетов, привязанный к облачным прайсам"""
    def __init__(self):
        super().__init__()
        self.order_data = {
            "db_id": None, "client_fio": "", "client_phone": "", "lead_source": "",
            "category": "bath", "product_line": "round_quadro", "diameter": "2.0",
            "shape_type": "round", "material": "pine", "base_length": 2000,
            "torce_modification": "base", "color_roof": "Серый графит",
            "color_facade": "Палисандр", "color_borders": "В цвет фасада"
        }
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        self.step_stacked = QStackedWidget()
        
        self.step_1 = Step1ContactsWidget()
        self.step_2 = Step2CategoryWidget()
        self.step_3 = Step3ConfigWidget()
        self.step_4 = Step4EstimateWidget()
        
        self.step_5 = self._create_stub_step("ЭТАП 5: 2D ПЛАНИРОВЩИК ИНТЕРЬЕРА", "[ Вид сверху. Математика высот контура сечения Безье ]")
        self.step_6 = self._create_stub_step("ЭТАП 6: ЮРИДИЧЕСКИЙ БЛОК И ДОГОВОР", "[ Авто-генерация PDF бланков спецификаций ]")

        self.step_stacked.addWidget(self.step_1)
        self.step_stacked.addWidget(self.step_2)
        self.step_stacked.addWidget(self.step_3)
        self.step_stacked.addWidget(self.step_4)
        self.step_stacked.addWidget(self.step_5)
        self.step_stacked.addWidget(self.step_6)

        self.main_layout.addWidget(self.step_stacked, stretch=1)

        nav_frame = QFrame()
        nav_frame.setFixedHeight(50)
        nav_frame.setStyleSheet("background-color: transparent; border-top: 1px solid #25252D;")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_progress = QLabel("Шаг 1 из 6")
        self.lbl_progress.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_progress.setStyleSheet("color: #656570;")
        nav_layout.addWidget(self.lbl_progress)

        nav_layout.addStretch()

        self.btn_back = QPushButton("◀  Назад")
        self.btn_back.setFixedSize(100, 32)
        self.btn_back.setEnabled(False)
        self.btn_back.clicked.connect(self._go_back)
        nav_layout.addWidget(self.btn_back)

        self.btn_next = QPushButton("Далее  ▶")
        self.btn_next.setFixedSize(100, 32)
        self.btn_next.setStyleSheet("background-color: #00A8FF; color: white; font-weight: bold;")
        self.btn_next.clicked.connect(self._go_next)
        nav_layout.addWidget(self.btn_next)

        self.main_layout.addWidget(nav_frame)

    def _go_next(self):
        current_idx = self.step_stacked.currentIndex()

        if current_idx == 0:
            self.order_data.update(self.step_1.collect_data())
            if not self.order_data["client_fio"] or not self.order_data["client_phone"]:
                self.lbl_progress.setText("Ошибка: Введите ФИО и Телефон клиента!")
                self.lbl_progress.setStyleSheet("color: #FF4D4D;")
                return
            self.lbl_progress.setStyleSheet("color: #656570;")
            self._save_phantom_order_to_cloud()

        elif current_idx == 1:
            self.order_data.update(self.step_2.collect_data())
            self._save_phantom_order_to_cloud()

        elif current_idx == 2:
            self.order_data.update(self.step_3.collect_data())
            self._save_phantom_order_to_cloud()
            # Пробрасываем геометрию в облачную смету Шага 4
            self.step_4.refresh_calculations(self.order_data)

        if current_idx < 5:
            self.step_stacked.setCurrentIndex(current_idx + 1)
            self._update_navigation_controls()

    def _go_back(self):
        current_idx = self.step_stacked.currentIndex()
        if current_idx > 0:
            self.step_stacked.setCurrentIndex(current_idx - 1)
            self._update_navigation_controls()

    def _save_phantom_order_to_cloud(self):
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS production_orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    client_fio VARCHAR(100) NOT NULL,
                    client_phone VARCHAR(50) NOT NULL,
                    lead_source VARCHAR(50),
                    category VARCHAR(30),
                    product_line VARCHAR(50),
                    diameter VARCHAR(10),
                    shape_type VARCHAR(30),
                    material VARCHAR(30),
                    base_length INT,
                    torce_modification VARCHAR(30),
                    color_roof VARCHAR(50),
                    color_facade VARCHAR(100),
                    color_borders VARCHAR(100),
                    status VARCHAR(30) DEFAULT 'calculation'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            if self.order_data["db_id"] is None:
                sql = """
                    INSERT INTO production_orders (client_fio, client_phone, lead_source, category, product_line, diameter, shape_type, material, base_length, torce_modification, color_roof, color_facade, color_borders)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    self.order_data["client_fio"], self.order_data["client_phone"], self.order_data["lead_source"],
                    self.order_data["category"], self.order_data["product_line"], self.order_data["diameter"], self.order_data["shape_type"],
                    self.order_data["material"], self.order_data["base_length"], self.order_data["torce_modification"],
                    self.order_data["color_roof"], self.order_data["color_facade"], self.order_data["color_borders"]
                ))
                self.order_data["db_id"] = conn.insert_id()
                print(f"[CRM Облако Сейв]: Создан заказ #{self.order_data['db_id']}")
            else:
                sql = """
                    UPDATE production_orders SET 
                    client_fio=%s, client_phone=%s, lead_source=%s, category=%s, product_line=%s, diameter=%s, shape_type=%s, material=%s, base_length=%s, torce_modification=%s, color_roof=%s, color_facade=%s, color_borders=%s
                    WHERE id=%s
                """
                cursor.execute(sql, (
                    self.order_data["client_fio"], self.order_data["client_phone"], self.order_data["lead_source"],
                    self.order_data["category"], self.order_data["product_line"], self.order_data["diameter"], self.order_data["shape_type"],
                    self.order_data["material"], self.order_data["base_length"], self.order_data["torce_modification"],
                    self.order_data["color_roof"], self.order_data["color_facade"], self.order_data["color_borders"],
                    self.order_data["db_id"]
                ))
                print(f"[CRM Облако Апдейт]: Заказ #{self.order_data['db_id']} обновлен ТТХ и цветами.")

            conn.commit()
            cursor.close()
            conn.close()
        except pymysql.MySQLError as e:
            print(f"[Ошибка CRM в MySQL]: {e}")

    def _update_navigation_controls(self):
        idx = self.step_stacked.currentIndex()
        self.lbl_progress.setText(f"Шаг {idx + 1} из 6")
        self.btn_back.setEnabled(idx > 0)
        if idx == 5:
            self.btn_next.setText("Финиш 🚀")
            self.btn_next.setStyleSheet("background-color: #28A745; color: white; font-weight: bold;")
        else:
            self.btn_next.setText("Далее  ▶")
            self.btn_next.setStyleSheet("background-color: #00A8FF; color: white; font-weight: bold;")

    def _create_stub_step(self, title_text, placeholder_text):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        lbl_title = QLabel(title_text)
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #FF9F43;")
        layout.addWidget(lbl_title)
        work_zone = QFrame()
        work_zone.setStyleSheet("border: 1px dashed #353540; border-radius: 6px;")
        inner_layout = QVBoxLayout(work_zone)
        lbl_ph = QLabel(placeholder_text)
        lbl_ph.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ph.setStyleSheet("color: #353540;")
        inner_layout.addWidget(lbl_ph)
        layout.addWidget(work_zone, stretch=1)
        return widget
