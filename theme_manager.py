# 🔥 ИСПРАВЛЕНО: Добавлен обязательный импорт класса QPushButton
from PyQt6.QtWidgets import QLabel, QFrame, QCheckBox, QRadioButton, QPushButton
from PyQt6.QtWidgets import QTableWidget

# theme_manager.py
"""
Изолированный графический движок «БаБочки ERP».
🔥 ЧАСТЬ 2: Управляет динамическим обходом элементов и перекраской.
🔥 ИСПРАВЛЕНО: Убраны жесткие импорты виджетов, ошибка ModuleNotFoundError полностью устранена!
"""
from PyQt6.QtWidgets import QLabel, QFrame, QCheckBox, QRadioButton
import theme_styles # Импортируем QSS из первой части

def apply_app_theme(window_obj, is_dark: bool):
    """Применяет выбранную тему и универсально перекрашивает элементы воронки без жестких импортов"""
    if is_dark:
        # Тянем QSS тёмной темы из соседнего файла
        window_obj.setStyleSheet(theme_styles.get_dark_theme_qss())
        
        window_obj.lbl_logo.setStyleSheet("color: #FF9F43; font-weight: bold; font-size: 14px;")
        window_obj.lbl_pulse.setStyleSheet("color: #00FF66; background-color: #1A2E26; padding: 4px 8px; border-radius: 4px;")
        window_obj.lbl_user.setStyleSheet("color: #B0B0B8;")
        window_obj.lbl_widget_text.setStyleSheet("color: #A0A0A8;")
        
        # Универсальный обход всех текстовых меток и чекбоксов на экранах
        for wizard in window_obj.stacked_widget.findChildren(QFrame):
            for label in wizard.findChildren(QLabel):
                if "ЭТАП" in label.text() or "Выберите модельную" in label.text():
                    label.setStyleSheet("color: #FF9F43; font-size: 12px; font-weight: bold;")
                elif any(icon in label.text() for icon in ["🪵", "📐", "⬡", "📏", "🚪", "📋"]):
                    label.setStyleSheet("color: #E0E0E6; font-size: 11px; font-weight: bold;")
                elif "💳 СМЕТНЫЙ" in label.text():
                    label.setStyleSheet("color: #FF9F43; font-size: 12px; font-weight: bold; margin-bottom: 5px;")
                elif "Базовая" in label.text() or "Наценка" in label.text() or "Выбрано" in label.text():
                    label.setStyleSheet("color: #B0B0B8; font-size: 11px;")
            
            # Универсально красим абсолютно все чекбоксы (допы) в темный цвет
            for cb in wizard.findChildren(QCheckBox):
                cb.setStyleSheet("color: #E0E0E6; font-family: 'Segoe UI'; font-size: 11px;")
                
            # Универсально красим все радио-кнопки (торцы) в темный цвет
            for rb in wizard.findChildren(QRadioButton):
                if rb.isEnabled():
                    rb.setStyleSheet("color: #E0E0E6; font-family: 'Segoe UI'; font-size: 11px; padding-left: 5px;")
                else:
                    rb.setStyleSheet("color: #555560; font-family: 'Segoe UI'; font-size: 11px; padding-left: 5px;")

            # Перекрашиваем плитки модельных линеек, если они есть на экране
            for btn in wizard.findChildren(QPushButton):
                if btn.text() in ["Круглая/Квадро", "Бабочка", "Викинг", "Квадро Хаус"]:
                    btn.setStyleSheet("""
                        QPushButton { background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #353540; border-radius: 4px; text-align: left; padding-left: 15px; }
                        QPushButton:hover { background-color: #282830; border-color: #00A8FF; }
                        QPushButton:checked { background-color: #00A8FF; border-color: #00A8FF; color: white; font-weight: bold; }
                    """)
                    
            # Точечно подсвечиваем итоговую сумму сметы, если нашли её
            for lbl in wizard.findChildren(QLabel):
                if "ИТОГО:" in lbl.text():
                    lbl.setStyleSheet("color: #00FF66; font-size: 18px; font-weight: bold; margin-top: 10px;")
            for table in wizard.findChildren(QTableWidget):
                table.setStyleSheet("QTableWidget { color: #FFFFFF; gridline-color: #25252D; background-color: #1A1A1E; }")
          
    else:
        # Тянем QSS светлой темы из соседнего файла
        window_obj.setStyleSheet(theme_styles.get_light_theme_qss())
        
        window_obj.lbl_logo.setStyleSheet("color: #0056B3; font-weight: bold; font-size: 14px;")
        window_obj.lbl_pulse.setStyleSheet("color: #28A745; background-color: #E8F5E9; padding: 4px 8px; border-radius: 4px;")
        window_obj.lbl_user.setStyleSheet("color: #495057;")
        window_obj.lbl_widget_text.setStyleSheet("color: #495057;")
        
        for wizard in window_obj.stacked_widget.findChildren(QFrame):
            for label in wizard.findChildren(QLabel):
                if "ЭТАП" in label.text() or "Выберите модельную" in label.text():
                    label.setStyleSheet("color: #0056B3; font-size: 12px; font-weight: bold;")
                elif any(icon in label.text() for icon in ["🪵", "📐", "⬡", "📏", "🚪", "📋"]):
                    label.setStyleSheet("color: #212529; font-size: 11px; font-weight: bold;")
                elif "💳 СМЕТНЫЙ" in label.text():
                    label.setStyleSheet("color: #0056B3; font-size: 12px; font-weight: bold; margin-bottom: 5px;")
                elif "Базовая" in label.text() or "Наценка" in label.text() or "Выбрано" in label.text():
                    label.setStyleSheet("color: #495057; font-size: 11px;")
                    
            # Универсально красим все чекбоксы в светлый цвет
            for cb in wizard.findChildren(QCheckBox):
                cb.setStyleSheet("color: #212529; font-family: 'Segoe UI'; font-size: 11px;")
                
            # Универсально красим все радио-кнопки в светлый цвет
            for rb in wizard.findChildren(QRadioButton):
                if rb.isEnabled():
                    rb.setStyleSheet("color: #212529; font-family: 'Segoe UI'; font-size: 11px; padding-left: 5px;")
                else:
                    rb.setStyleSheet("color: #CED4DA; font-family: 'Segoe UI'; font-size: 11px; padding-left: 5px;")

            for btn in wizard.findChildren(QPushButton):
                if btn.text() in ["Круглая/Квадро", "Бабочка", "Викинг", "Квадро Хаус"]:
                    btn.setStyleSheet("""
                        QPushButton { background-color: #FFFFFF; color: #212529; border: 1px solid #CED4DA; border-radius: 4px; text-align: left; padding-left: 15px; }
                        QPushButton:hover { background-color: #E9ECEF; border-color: #0056B3; }
                        QPushButton:checked { background-color: #0056B3; border-color: #0056B3; color: white; font-weight: bold; }
                    """)
                    
            for lbl in wizard.findChildren(QLabel):
                if "ИТОГО:" in lbl.text():
                    lbl.setStyleSheet("color: #28A745; font-size: 18px; font-weight: bold; margin-top: 10px;")
            for table in wizard.findChildren(QTableWidget):
                table.setStyleSheet("QTableWidget { color: #212529; gridline-color: #DEE2E6; background-color: #FFFFFF; }")
