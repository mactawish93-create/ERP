# database_system/db_installer.py
import pymysql
import hashlib
import os
from config import DB_CONFIG

def initialize_database():
    """Подключается к облачной MySQL на хостинге и разворачивает всю экосистему таблиц"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                login VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                salt VARCHAR(32) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role ENUM('worker', 'supply', 'sales', 'master', 'director', 'admin') NOT NULL,
                access_level INT NOT NULL,
                require_password_change BOOLEAN DEFAULT TRUE,
                is_active BOOLEAN DEFAULT TRUE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 2. ТАБЛИЦА СТАТИЧНЫХ БАЗОВЫХ ЦЕН ИЗДЕЛИЙ (СОСНА)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS base_prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_line VARCHAR(50) NOT NULL,
                base_length INT NOT NULL,
                price INT NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 3. ТАБЛИЦА ДОП. ОПЦИЙ И КОЭФФИЦИЕНТОВ СПЕЦИФИКАЦИИ
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS options_prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                option_key VARCHAR(50) UNIQUE NOT NULL,
                option_name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                price INT NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Забиваем дефолтного админа, если пусто
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            salt = os.urandom(16).hex()
            computed_hash = hashlib.sha256((salt + "Bani2026").encode('utf-8')).hexdigest()
            cursor.execute("""
                INSERT INTO users (login, password_hash, salt, full_name, role, access_level, require_password_change, is_active)
                VALUES ('admin', %s, %s, 'Главный Администратор', 'admin', 6, 1, 1)
            """, (computed_hash, salt))

        # Забиваем базовые цены сосны из твоих Excel (Двоечка и Шестерочка)
        cursor.execute("SELECT COUNT(*) FROM base_prices")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO base_prices (product_line, base_length, price) VALUES (%s, %s, %s)
            """, [
                ("round_quadro", 2000, 212300),
                ("round_quadro", 3000, 250000),
                ("round_quadro", 3500, 280000),
                ("round_quadro", 4000, 320000),
                ("round_quadro", 4500, 340000),
                ("round_quadro", 5000, 360000),
                ("round_quadro", 5500, 370000),
                ("round_quadro", 6000, 376100)
            ])

        # Забиваем реальные цены допов из твоих бланков спецификаций
        cursor.execute("SELECT COUNT(*) FROM options_prices")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO options_prices (option_key, option_name, category, price) VALUES (%s, %s, %s, %s)
            """, [
                ("sborka", "Сборка на участке фабрики", "construct", 18000),
                ("pokraska", "Покраска наружного фасада (2 слоя)", "construct", 10250),
                ("obruch", "Усиленный обруч стяжки из нерж. стали", "construct", 4500),
                ("vynos", "Замена стандартного козырька на выносной", "construct", 6000),
                ("door_glass", "Дверь входная стеклянная (матовая)", "doors", 11700),
                ("door_iron", "Дверь входная металлическая (сейф)", "doors", 24500),
                ("window_lipa", "Окно липа 300х400 в парную", "doors", 3400),
                ("window_wash", "Окно открывающееся в мыльную", "doors", 4800),
                ("stove_vezuv", "Печь Везувий (Топка с улицы)", "stoves", 11000),
                ("stove_grild", "Печь Грильд (Премиум каменка)", "stoves", 32000),
                ("bak_water", "Бак для горячей воды на 60 литров", "stoves", 7500),
                ("screen_min", "Защитный экран печи из минерита", "stoves", 3800),
                ("polog_osina", "Полок двухъярусный (Осина)", "interior", 8500),
                ("polog_wash", "Полок раскладной в мыльную", "interior", 5400),
                ("table_lipa", "Столик съемный (Липа)", "interior", 3400),
                ("back_cedar", "Комплект спинок из кедра", "interior", 5100)
            ])

        conn.commit()
        cursor.close()
        conn.close()
        print("[Облако MySQL Успех]: База полностью обновлена. Все прайсы залиты.")
    except pymysql.MySQLError as e:
        print(f"[Ошибка развертывания БД]: {e}")
