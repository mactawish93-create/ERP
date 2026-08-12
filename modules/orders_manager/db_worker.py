# modules/orders_manager/db_worker.py
import pymysql
from cryptography.fernet import Fernet

# Единый ключ шифрования для ФЗ-152
SECRET_CRYPTO_KEY = b'uX9_G8bX2v9hK7Lm4PqW1zS5tD6cE7rT8yU9iO0pA1s='
cipher_suite = Fernet(SECRET_CRYPTO_KEY)

def get_db_config(user_session):
    """Вспомогательный метод получения конфига БД"""
    db_config = user_session.get("db_config") if user_session else None
    if not db_config:
        from config import DB_CONFIG
        db_config = DB_CONFIG
    return db_config

def fetch_all_orders(user_session):
    """Скачивает абсолютно все колонки заказов из MySQL для кэша"""
    db_config = get_db_config(user_session)
    cache = {}
    
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 🔥 ФИКС: Добавили advance_payment и client_reg_address_encrypted в SQL-запрос
        query = """
            SELECT id, contract_number, status, client_fio, client_phone,
                   client_passport_encrypted, client_address, order_notes,
                   material, diameter, shape_type, base_length, torce_modification,
                   room_sauna, room_wash, room_rest,
                   color_roof, color_facade, color_borders, color_ends,
                   assembly_on_site, door_facade, stove_next_room, stove_street,
                   delivery_date, production_progress, supply_progress, approved_by_master, total_price,
                   file_contract, file_specification, file_blueprint, file_act,
                   advance_payment, client_reg_address_encrypted
            FROM production_orders
            ORDER BY id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for r in rows:
            o_id = r[0]
            cache[o_id] = {
                "id": r[0], "contract_number": r[1], "status": r[2], "client_fio": r[3], "client_phone": r[4],
                "client_passport_encrypted": r[5], "client_address": r[6], "order_notes": r[7],
                "material": r[8], "diameter": r[9], "shape_type": r[10], "base_length": r[11], "torce_modification": r[12],
                "room_sauna": r[13], "room_wash": r[14], "room_rest": r[15],
                "color_roof": r[16], "color_facade": r[17], "color_borders": r[18], "color_ends": r[19],
                "assembly_on_site": r[20], "door_facade": r[21], "stove_next_room": r[22], "stove_street": r[23],
                "delivery_date": str(r[24]) if r[24] else "—",
                "production_progress": r[25] or 0,
                "supply_progress": r[26] or 0,
                "approved_by_master": r[27] or "Не назначен",
                "total_price": float(r[28] or 0.00),
                "file_contract": r[29], "file_specification": r[30], "file_blueprint": r[31], "file_act": r[32],
                # 🔥 Упаковываем новые поля в кэш программы
                "advance_payment": float(r[33] or 0.00),
                "client_reg_address_encrypted": r[34] or ""
            }
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[Ошибка db_worker.fetch_all_orders]: {str(e)}")
        
    return cache

def update_encrypted_pnd(user_session, order_id, passport_text, reg_address_text, address_text, notes_text, advance_val, schedule_json_str=None):
    """Шифрует паспорт и адрес регистрации по AES-256, сохраняет финансы и JSON рассрочки в MySQL"""
    db_config = get_db_config(user_session)
    
    encrypted_passport = ""
    if passport_text:
        encrypted_passport = cipher_suite.encrypt(passport_text.encode()).decode()
        
    encrypted_reg_address = ""
    if reg_address_text:
        encrypted_reg_address = cipher_suite.encrypt(reg_address_text.encode()).decode()
        
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 🔥 SQL-ЗАПРОС С ПОЛНОЙ ПОДДЕРЖКОЙ ГРАФИКА РАССРОЧКИ
        query = """
            UPDATE production_orders 
            SET client_passport_encrypted = %s,
                client_reg_address_encrypted = %s,
                client_address = %s,
                order_notes = %s,
                advance_payment = %s,
                payment_schedule_json = %s
            WHERE id = %s
        """
        cursor.execute(query, (encrypted_passport, encrypted_reg_address, address_text, notes_text, advance_val, schedule_json_str, order_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True, encrypted_passport, encrypted_reg_address
    except Exception as e:
        return False, str(e), ""

def upload_document_blob(user_session, order_id, db_column, binary_data):
    """Заливает сырые байты любого скана документа в ячейку LONGBLOB"""
    db_config = get_db_config(user_session)
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        query = f"UPDATE production_orders SET {db_column} = %s WHERE id = %s"
        cursor.execute(query, (binary_data, order_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[Ошибка db_worker.upload_document_blob]: {str(e)}")
        return False

def decrypt_passport_string(encrypted_str):
    """Дешифрует хэш обратно в читаемую строку серии/номера паспорта или адреса"""
    if not encrypted_str: return ""
    try:
        return cipher_suite.decrypt(encrypted_str.encode()).decode()
    except Exception:
        return "[ Ошибка ключа ПДН ]"
