# theme_styles.py
"""
Изолированная база графических QSS-стилей экосистемы «БаБочки ERP».
🔥 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ: Тотальный контроль выпадающих списков!
"""

def get_dark_theme_qss() -> str:
    """Возвращает фирменный цеховой тёмный стиль QSS"""
    return """
        QMainWindow { background-color: #111114; }
        QLabel { color: #E0E0E6; font-family: 'Segoe UI'; font-size: 11px; font-weight: bold; }
        QCheckBox { color: #E0E0E6; font-family: 'Segoe UI'; font-size: 11px; }
        
        QRadioButton { color: #E0E0E6; font-family: 'Segoe UI'; font-size: 11px; }
        QRadioButton::indicator { width: 14px; height: 14px; }
        QRadioButton:disabled { color: #454550; }
        
        QComboBox { 
            background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #353540; 
            border-radius: 4px; padding-left: 10px; font-family: 'Segoe UI'; font-size: 12px;
        }
        QComboBox:focus { border-color: #00A8FF; }
        
        /* Глубокий QSS для выпадающего списка в ТЕМНОЙ теме */
        QComboBox QListView {
            background-color: #1A1A1E;
            border: 1px solid #353540;
        }
        QComboBox QListView::item {
            color: #FFFFFF;
            background-color: #1A1A1E;
            padding: 6px;
        }
        QComboBox QListView::item:selected {
            background-color: #00A8FF;
            color: #FFFFFF;
        }
        
        QTableWidget { 
            color: #FFFFFF; background-color: #1A1A1E; gridline-color: #25252D; 
            border: 1px solid #25252D; border-radius: 4px; font-family: 'Segoe UI';
        }
        QHeaderView::section { background-color: #162421; color: #E0E0E6; border: 1px solid #25252D; }
        
        QTabWidget::pane { border: 1px solid #25252D; background-color: #1A1A1E; border-radius: 4px; }
        QTabBar::tab { background: #111114; color: #B0B0B8; border: 1px solid #25252D; padding: 6px 12px; font-size: 10px; font-weight: bold; }
        QTabBar::tab:hover { background: #282830; color: #FFF; }
        QTabBar::tab:selected { background: #1A1A1E; color: #00A8FF; border-bottom-color: #1A1A1E; }
        
        QFrame#financial_board { background-color: #162421; border: 1px solid #25252D; border-radius: 6px; }
        
        QFrame#top_bar { background-color: #162421; border-bottom: 1px solid #25252D; }
        QFrame#sidebar { background-color: #141E1B; border-right: 1px solid #25252D; }
        QFrame#status_widget { background-color: #111114; border: 1px solid #25252D; border-radius: 4px; }
        QFrame#canvas_panel { background-color: #111114; }
        
        QPushButton { 
            background-color: #1A1A1E; color: #B0B0B8; border: 1px solid #353540; 
            border-radius: 4px; font-size: 11px; font-weight: bold; text-align: left; padding-left: 12px;
            font-family: 'Segoe UI';
        }
        QPushButton:hover { background-color: #282830; border-color: #00A8FF; color: #FFF; }
        QPushButton:checked { background-color: #00A8FF; border-color: #00A8FF; color: #FFF; font-weight: bold; }
    """

def get_light_theme_qss() -> str:
    """Возвращает светлый офисный стиль QSS для менеджеров"""
    return """
        QMainWindow { background-color: #FFFFFF; }
        QLabel { color: #212529; font-family: 'Segoe UI'; font-size: 11px; font-weight: bold; }
        QCheckBox { color: #212529; font-family: 'Segoe UI'; font-size: 11px; }
        
        QRadioButton { color: #212529; font-family: 'Segoe UI'; font-size: 11px; }
        QRadioButton::indicator { width: 14px; height: 14px; }
        QRadioButton:disabled { color: #CED4DA; }
        
        QComboBox { 
            background-color: #FFFFFF; color: #212529; border: 1px solid #CED4DA; 
            border-radius: 4px; padding-left: 10px; font-family: 'Segoe UI'; font-size: 12px;
        }
        QComboBox:focus { border-color: #0056B3; }
        
        /* Глубокий QSS для выпадающего списка в СВЕТЛОЙ теме */
        QComboBox QListView {
            background-color: #FFFFFF;
            border: 1px solid #CED4DA;
        }
        QComboBox QListView::item {
            color: #212529;
            background-color: #FFFFFF;
            padding: 6px;
        }
        QComboBox QListView::item:selected {
            background-color: #0056B3;
            color: #FFFFFF;
        }
        
        QTableWidget { 
            color: #212529; background-color: #FFFFFF; gridline-color: #DEE2E6; 
            border: 1px solid #DEE2E6; border-radius: 4px; font-family: 'Segoe UI';
        }
        QHeaderView::section { background-color: #F8F9FA; color: #495057; border: 1px solid #DEE2E6; }
        
        QTabWidget::pane { border: 1px solid #DEE2E6; background-color: #FFFFFF; border-radius: 4px; }
        QTabBar::tab { background: #F8F9FA; color: #495057; border: 1px solid #DEE2E6; padding: 6px 12px; font-size: 10px; font-weight: bold; }
        QTabBar::tab:hover { background: #E9ECEF; color: #0056B3; }
        QTabBar::tab:selected { background: #FFFFFF; color: #0056B3; border-bottom-color: #FFFFFF; }
        
        QFrame#financial_board { background-color: #F8F9FA; border: 1px solid #DEE2E6; border-radius: 6px; }
        
        QFrame#top_bar { background-color: #F8F9FA; border-bottom: 1px solid #DEE2E6; }
        QFrame#sidebar { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
        QFrame#status_widget { background-color: #FFFFFF; border: 1px solid #CED4DA; border-radius: 4px; }
        QFrame#canvas_panel { background-color: #FFFFFF; }
        
        QPushButton { 
            background-color: #FFFFFF; color: #495057; border: 1px solid #CED4DA; 
            border-radius: 4px; font-size: 11px; font-weight: bold; text-align: left; padding-left: 12px;
            font-family: 'Segoe UI';
        }
        QPushButton:hover { background-color: #E9ECEF; border-color: #0056B3; color: #0056B3; }
        QPushButton:checked { background-color: #0056B3; border-color: #0056B3; color: #FFF; font-weight: bold; }
    """
