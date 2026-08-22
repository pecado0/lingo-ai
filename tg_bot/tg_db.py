import backend.db as db

import ydb

DRIVER = db.get_ydb_driver()
POOL = ydb.SessionPool(DRIVER)

def link_tg_user(telegram_id: str, user_id: str):
    """Связываем id пользователя в БД с его telegram id"""

    query = """
    DECLARE $user_id AS Utf8;
    DECLARE $telegram_id AS Utf8;

    INSERT INTO tg_Users(id, tg_id) 
    VALUES($user_id, $telegram_id);
    """

    parameters = {
        "$user_id": user_id,
        "$telegram_id": telegram_id
    }

    try:
        POOL.retry_operation_sync(
            lambda session: db._execute_query(session, query, parameters)
        )
        return True
    except Exception as e:
        print(f"Ошибка при привязке профиля telegram {e}")
        return False

def get_tg_user(telegram_id: str):
    """Получаем id пользователя в БД с помощью его telegram id"""

    query = """
        DECLARE $telegram_id AS Utf8;
    
        SELECT id FROM `tg_Users` WHERE tg_id = $telegram_id;
        """

    parameters = {
            "$telegram_id": telegram_id
        }

    try:
        result = POOL.retry_operation_sync(
            lambda session: db._execute_query(session, query, parameters)
        )

        if not result[0].rows:
            return None
        
        user_id = db.decode_val(result[0].rows[0]['id'])
        return user_id
    except Exception as e:
        print(f"Ошибка при получении id пользователя {e}")
        return False