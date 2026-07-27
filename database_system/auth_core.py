# database_system/auth_core.py
import pymysql
import hashlib
from config import DB_CONFIG

def verify_user_credentials(login_input: str, password_input: str) -> dict:
    """Сверяет логин/пароль с облачной базой данных MySQL на хостинге через хэширование"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            port=DB_CONFIG["port"]
        )
        cursor = conn.cursor()

        # В MySQL запросы пишутся через экранирование %s для защиты от SQL-инъекций хакеров
        cursor.execute("""
            SELECT password_hash, salt, full_name, role, access_level, require_password_change, is_active 
            FROM users WHERE login = %s
        """, (login_input.strip(),))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return {"success": False, "error": "Пользователь не найден в облачной базе!"}

        db_hash, db_salt, full_name, role, access_level, require_change, is_active = row

        if not is_active:
            return {"success": False, "error": "Эта учетная запись заблокирована админом!"}

        # Вычисляем SHA-256 хэш по соли из облака
        raw_string = db_salt + password_input
        computed_hash = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

        if computed_hash == db_hash:
            return {
                "success": True,
                "full_name": full_name,
                "role": role,
                "access_level": access_level,
                "require_change": bool(require_change)
            }
        
        return {"success": False, "error": "Неверный пароль!"}

    except pymysql.MySQLError as e:
        return {"success": False, "error": f"Ошибка сети хостинга: {e}"}
