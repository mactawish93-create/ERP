# main_erp.py
import sys
from PyQt6.QtWidgets import QApplication, QDialog

# Чистый импорт из изолированных папок нашей экосистемы
from database_system.db_installer import initialize_database
from database_system.auth_window import LoginDialog
from modules.main_window import BabochkiErpCore

if __name__ == "__main__":
    # 1. Фоновая проверка и инициализация локальной базы данных
    initialize_database()

    app = QApplication(sys.argv)
    
    # 2. Запуск изолированного крипто-окна авторизации
    auth_dialog = LoginDialog(is_dark_theme=True)
    
    if auth_dialog.exec() == QDialog.DialogCode.Accepted:
        # 3. Если хэш совпал — передаем сессию и разворачиваем главное окно
        main_window = BabochkiErpCore(user_session=auth_dialog.user_session)
        main_window.show()
        sys.exit(app.exec())
    else:
        # Тихое закрытие, если на входе нажали отмену
        sys.exit(0)
