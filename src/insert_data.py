# insert_data.py

def insert_event(conn, event_name, description, title,
                 start_ds, end_ds, status, event_type,
                 max_users, coin, achievement_type_id, company_id):
    with conn.cursor() as cur:
        query = """
        INSERT INTO events
        (event_name, description, title, start_ds, end_ds, status, event_type,
         max_users, coin, achievement_type_id, company_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (
            event_name,
            description,
            title,
            start_ds,
            end_ds,
            status,
            event_type,
            max_users,
            coin,
            achievement_type_id,
            company_id
        ))
    conn.commit()

def update_event(conn, event_id, event_name, description, title,
                 start_ds, end_ds, status, event_type,
                 max_users, coin, achievement_type_id, company_id):
    with conn.cursor() as cur:
        query = """
        UPDATE events
        SET event_name=%s,
            description=%s,
            title=%s,
            start_ds=%s,
            end_ds=%s,
            status=%s,
            event_type=%s,
            max_users=%s,
            coin=%s,
            achievement_type_id=%s,
            company_id=%s
        WHERE event_id=%s
        """
        cur.execute(query, (
            event_name,
            description,
            title,
            start_ds,
            end_ds,
            status,
            event_type,
            max_users,
            coin,
            achievement_type_id,
            company_id,
            event_id
        ))
    conn.commit()

def delete_event(conn, event_id):
    with conn.cursor() as cur:
        query = "DELETE FROM events WHERE event_id=%s"
        cur.execute(query, (event_id,))
    conn.commit()


def update_visit(conn, event_id, user_id, new_visit):
    """Обновляет статус посещаемости в базе (attended или missed)."""
    with conn.cursor() as cur:
        query = """
        UPDATE event_user_visits
        SET visit = %s
        WHERE event_id = %s AND user_id = %s
        """
        cur.execute(query, (new_visit, event_id, user_id))
    conn.commit()


# src/insert_data.py (примерный файл для вспомогательных функций)

def add_product_to_db(conn, name, price, description, image, availability, category, case_type_id=None):
    """
    Добавляет новый товар (мерч или кейс) в таблицу product.
    Если это кейс, case_type_id должен быть не None.
    """
    query = """
        INSERT INTO product (name, price, description, image, avalibility, product_category, case_type_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        cur.execute(query, (name, price, description, image, availability, category, case_type_id))
    conn.commit()

def delete_product(conn, product_id):
    """
    Удаляет товар из таблицы product по product_id.
    В реальном проекте обычно сначала проверяем, нет ли ссылок на этот товар.
    """
    query = "DELETE FROM product WHERE product_id = %s"
    with conn.cursor() as cur:
        cur.execute(query, (product_id,))
    conn.commit()

def update_product(conn, product_id, name, price, description, image, availability, category, case_type_id=None):
    """
    Обновляет товар в таблице product по product_id.
    """
    query = """
        UPDATE product
           SET name = %s,
               price = %s,
               description = %s,
               image = %s,
               avalibility = %s,
               product_category = %s,
               case_type_id = %s
         WHERE product_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (name, price, description, image, availability, category, case_type_id, product_id))
    conn.commit()

def update_case_probabilities(conn, case_type_id, product_id, new_probability):
    """
    Обновляет вероятность выпадения товара (product_id) в данном кейсе (case_type_id).
    Предполагаем, что запись уже существует в case_product_probability.
    """
    query = """
        UPDATE case_product_probability
           SET drop_probability = %s
         WHERE case_type_id = %s
           AND product_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (new_probability, case_type_id, product_id))
    conn.commit()

def insert_case_probability(conn, case_type_id, product_id, probability):
    """
    Если нужно вставить новую связь (case_type_id, product_id) в case_product_probability.
    """
    query = """
        INSERT INTO case_product_probability (case_type_id, product_id, drop_probability)
        VALUES (%s, %s, %s)
    """
    with conn.cursor() as cur:
        cur.execute(query, (case_type_id, product_id, probability))
    conn.commit()

def delete_case_probability(conn, case_type_id, product_id):
    """
    Удаляет связь (case_type_id, product_id) из case_product_probability.
    """
    query = """
        DELETE FROM case_product_probability
         WHERE case_type_id = %s
           AND product_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (case_type_id, product_id))
    conn.commit()

def create_case_type(conn, name, description):
    """
    Создаёт новую запись в таблице case_type (например, 'Платиновый кейс').
    """
    query = "INSERT INTO case_type (name, description) VALUES (%s, %s)"
    with conn.cursor() as cur:
        cur.execute(query, (name, description))
    conn.commit()

def delete_case_type(conn, case_type_id):
    """
    Удаляет запись из таблицы case_type.
    В реальном проекте стоит проверить, нет ли связанных записей в product и case_product_probability.
    """
    query = "DELETE FROM case_type WHERE case_type_id = %s"
    with conn.cursor() as cur:
        cur.execute(query, (case_type_id,))
    conn.commit()

def update_case_type(conn, case_type_id, new_name, new_description):
    """
    Обновляет запись в таблице case_type.
    """
    query = """
        UPDATE case_type
           SET name = %s,
               description = %s
         WHERE case_type_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (new_name, new_description, case_type_id))
    conn.commit()

def update_winning_delivery(conn, user_winning_id, delivered, delivered_by):
    """
    Выдача товара (обновляет поле delivered, delivered_at и delivered_by).
    """
    query = """
        UPDATE user_winnings
           SET delivered = %s,
               delivered_at = CURRENT_TIMESTAMP,
               delivered_by = %s
         WHERE user_winning_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (delivered, delivered_by, user_winning_id))
    conn.commit()
