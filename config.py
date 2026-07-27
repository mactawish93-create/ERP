# config.py
"""
Глобальные конфигурационные константы и параметры безопасности системы БаБочки ERP.
"""

# Матрица рангов цифровой безопасности (Уровни доступа сотрудников)
ACCESS_LEVELS = {
    "worker": 1,     # Сотрудник / Рабочий цеха
    "supply": 2,     # Снабженец / Логист
    "sales": 3,      # Менеджер по продажам
    "master": 4,     # Мастер производства / Технолог
    "director": 5,   # Директор / Руководство
    "admin": 6       # Системный Администратор / Полный доступ
}

# Наименования глобальных вкладок системы и их минимальный требуемый ранг доступа
TABS_SPECIFICATION = [
    {"title": "Проектирование",       "min_level": ACCESS_LEVELS["sales"]},
    {"title": "База заказов",         "min_level": ACCESS_LEVELS["worker"]},
    {"title": "Технический аудит",     "min_level": ACCESS_LEVELS["master"]},
    {"title": "Диспетчер производства",       "min_level": ACCESS_LEVELS["master"]},
    {"title": "Снабжение и Склад",     "min_level": ACCESS_LEVELS["supply"]},
    {"title": "Аналитика / Отчеты",   "min_level": ACCESS_LEVELS["director"]},
    {"title": "Управление прайсами", "min_level": ACCESS_LEVELS["sales"]},
    {"title": "Администрирование",    "min_level": ACCESS_LEVELS["admin"]}
]

# === ПАРАМЕТРЫ ПОДКЛЮЧЕНИЯ К ОБЛАЧНОЙ MySQL НА ХОСТИНГЕ ===
# Замените эти фантомные данные на реальные параметры из личного кабинета вашего хостинга!
DB_CONFIG = {
    "host": "mysql.6c7a6d3bbaa2.hosting.myjino.ru",
    "user": "j50485596",
    "password": "8vhsUem7E",
    "database": "j50485596_babochky",
    "port": 3306 # Стандартный порт MySQL, сисадмины обычно оставляют его
}
