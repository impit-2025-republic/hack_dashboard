# src/pages/shop.py
import streamlit as st
import polars as pl
from settings import db_connection
from s3_utils import upload_to_s3, list_s3_objects  # <-- ваши функции S3
from insert_data import (
    add_product_to_db,
    delete_product,
    update_product,
    update_case_probabilities,
    insert_case_probability,
    delete_case_probability,
    create_case_type,
    delete_case_type,
    update_case_type,
    update_winning_delivery
)

def shop_page():
    st.title("Управление магазином (с загрузкой изображений в S3)")

    conn = db_connection()

    # Создаем 9 вкладок (добавил "Просмотр S3" отдельно)
    tabs = st.tabs([
        "Добавление товаров",      # index 0
        "Удаление товаров",        # index 1
        "Редактирование товаров",  # index 2
        "Изменение вероятностей",  # index 3
        "Создание кейсов",         # index 4
        "Удаление кейсов",         # index 5
        "Редактирование кейсов",   # index 6
        "Выдача товаров (призы)",  # index 7
        "Просмотр S3"             # index 8
    ])

    # -------------------------------------
    # Tab 0. Добавление товаров
    # -------------------------------------
    with tabs[0]:
        st.subheader("Добавление товаров")

        product_name = st.text_input("Название товара")
        product_price = st.number_input("Цена", step=0.01)
        product_description = st.text_area("Описание")
        product_availability = st.number_input("Количество на складе", step=1, value=100)
        product_category = st.selectbox("Категория товара", ["merch", "case"])

        uploaded_file = st.file_uploader("Загрузить изображение", type=["jpg", "jpeg", "png"])

        # Если это кейс, выберем тип кейса
        case_type_id = None
        if product_category == "case":
            df_case_types = pl.read_database("SELECT case_type_id, name FROM case_type", connection=conn)
            if len(df_case_types) > 0:
                case_types_list = [(r["case_type_id"], r["name"]) for r in df_case_types.to_dicts()]
                chosen_case_type = st.selectbox("Выберите тип кейса", case_types_list, format_func=lambda x: x[1])
                if chosen_case_type:
                    case_type_id = chosen_case_type[0]
            else:
                st.warning("Нет типов кейсов в базе.")

        if st.button("Добавить товар"):
            if not product_name:
                st.error("Укажите название товара.")
                st.stop()

            # Ссылка на изображение
            image_url = None
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                image_url = upload_to_s3(file_bytes, uploaded_file.name)

            add_product_to_db(
                conn,
                name=product_name,
                price=product_price,
                description=product_description,
                image=image_url,
                availability=product_availability,
                category=product_category,
                case_type_id=case_type_id
            )
            st.success("Товар успешно добавлен!")

    # -------------------------------------
    # Tab 1. Удаление товаров
    # -------------------------------------
    with tabs[1]:
        st.subheader("Удаление товаров")

        df_products = pl.read_database("""
            SELECT product_id, name, product_category
              FROM product
             ORDER BY product_id
        """, connection=conn)

        if len(df_products) == 0:
            st.info("Нет товаров для удаления.")
        else:
            pd_products = df_products.to_pandas()
            product_options = [(r.product_id, r.name) for r in pd_products.itertuples()]
            choice = st.selectbox("Выберите товар для удаления", product_options, format_func=lambda x: x[1])

            if choice:
                chosen_product_id = choice[0]
                if st.button("Удалить выбранный товар"):
                    delete_product(conn, chosen_product_id)
                    st.success(f"Товар (ID={chosen_product_id}) удалён.")

    # -------------------------------------
    # Tab 2. Редактирование товаров
    # -------------------------------------
    with tabs[2]:
        st.subheader("Редактирование товаров")

        df_products = pl.read_database("SELECT * FROM product ORDER BY product_id", connection=conn)
        if len(df_products) == 0:
            st.info("Нет товаров для редактирования.")
        else:
            pd_products = df_products.to_pandas()
            product_options = [(r.product_id, r.name) for r in pd_products.itertuples()]
            choice = st.selectbox("Выберите товар для редактирования", product_options, format_func=lambda x: x[1])

            if choice:
                chosen_product_id = choice[0]
                row = pd_products.loc[pd_products["product_id"] == chosen_product_id].iloc[0]

                edit_name = st.text_input("Название товара", value=row["name"] or "")
                edit_price = st.number_input("Цена", step=0.01, value=float(row["price"] or 0.0))
                edit_description = st.text_area("Описание", value=row["description"] or "")
                edit_aval = st.number_input("Количество на складе", step=1, value=int(row["avalibility"] or 0), key="x")
                edit_category = st.selectbox("Категория", ["merch", "case"],
                                             index=0 if row["product_category"] == "merch" else 1)

                # Показать текущее изображение
                if row["image"]:
                    st.image(row["image"], caption="Текущее изображение", use_column_width=True)
                else:
                    st.write("Нет загруженного изображения.")

                # Файл для замены картинки
                uploaded_file_edit = st.file_uploader(
                    "Загрузить новое изображение (чтобы заменить текущее)",
                    type=["jpg", "jpeg", "png"]
                )
                new_image_url = row["image"]  # по умолчанию оставляем старую ссылку

                edit_case_type = row["case_type_id"]
                if edit_category == "case":
                    # Если товар - кейс, выбираем тип кейса
                    df_case_types = pl.read_database("SELECT case_type_id, name FROM case_type", connection=conn)
                    if len(df_case_types) > 0:
                        case_type_list = [(r["case_type_id"], r["name"]) for r in df_case_types.to_dicts()]

                        # Определим индекс для selectbox
                        def find_index(lst, val):
                            for i, x in enumerate(lst):
                                if x[0] == val:
                                    return i
                            return 0
                        idx_case = find_index(case_type_list, edit_case_type)
                        select_case_type = st.selectbox("Тип кейса", case_type_list,
                                                        index=idx_case, format_func=lambda x: x[1])
                        edit_case_type = select_case_type[0]
                    else:
                        st.warning("Нет типов кейсов в базе.")
                else:
                    edit_case_type = None

                if st.button("Сохранить изменения"):
                    # Если загрузили новую картинку
                    if uploaded_file_edit is not None:
                        file_bytes = uploaded_file_edit.read()
                        new_image_url = upload_to_s3(file_bytes, uploaded_file_edit.name)

                    update_product(
                        conn,
                        product_id=chosen_product_id,
                        name=edit_name,
                        price=edit_price,
                        description=edit_description,
                        image=new_image_url,
                        availability=edit_aval,
                        category=edit_category,
                        case_type_id=edit_case_type
                    )
                    st.success("Товар обновлён.")

    # -------------------------------------
    # Tab 3. Изменение вероятностей
    # -------------------------------------
    with tabs[3]:
        st.subheader("Изменение вероятностей выпадения (case_product_probability)")

        df_case_types = pl.read_database("SELECT case_type_id, name FROM case_type ORDER BY case_type_id", connection=conn)
        if len(df_case_types) == 0:
            st.info("Пока нет доступных типов кейсов.")
        else:
            case_options = [(r["case_type_id"], r["name"]) for r in df_case_types.to_dicts()]
            selected_case_type = st.selectbox("Выберите кейс", case_options, format_func=lambda x: x[1])
            if selected_case_type:
                current_case_id = selected_case_type[0]

                query_probs = f"""
                    SELECT cpp.case_type_id, cpp.product_id, cpp.drop_probability,
                           p.name AS product_name
                      FROM case_product_probability cpp
                      JOIN product p ON p.product_id = cpp.product_id
                     WHERE cpp.case_type_id = {current_case_id}
                     ORDER BY cpp.product_id
                """
                df_probs = pl.read_database(query_probs, connection=conn)

                if len(df_probs) == 0:
                    st.info("Пока нет товаров в данном кейсе.")
                else:
                    # Проходим по записям и для каждого товара даём возможность менять вероятность
                    for i, row_prob in enumerate(df_probs.to_dicts()):
                        product_id = row_prob["product_id"]
                        product_name = row_prob["product_name"]
                        old_prob = float(row_prob["drop_probability"])

                        # Генерируем уникальный ключ для каждого товара,
                        # чтобы не было дубликатов ID внутри Streamlit
                        unique_key = f"prob_input_{current_case_id}_{product_id}_{i}"

                        new_prob = st.number_input(
                            label=f"{product_name} (ID={product_id}):",
                            min_value=0.0,
                            max_value=100.0,
                            step=1.0,
                            value=old_prob,
                            key=unique_key  # уникальный ключ
                        )
                        # Если пользователь изменил значение
                        if new_prob != old_prob:
                            update_case_probabilities(conn, current_case_id, product_id, new_prob)
                            st.info(f"Обновлена вероятность для {product_name}: {new_prob}%")

                # Добавить новую связь товар → кейс
                st.write("---")
                st.write("**Добавить новую связь (product -> case)**")

                all_merch = pl.read_database(
                    "SELECT product_id, name FROM product WHERE product_category = 'merch' ORDER BY product_id",
                    connection=conn
                )
                if len(all_merch) > 0:
                    merch_options = [(m["product_id"], m["name"]) for m in all_merch.to_dicts()]
                    chosen_merch = st.selectbox("Товар для добавления", merch_options, format_func=lambda x: x[1])

                    # Аналогично: даём key для number_input
                    new_prob_key = f"new_prob_input_{current_case_id}"
                    prob_input = st.number_input(
                        "Вероятность (%)",
                        0.0,
                        100.0,
                        step=1.0,
                        key=new_prob_key
                    )
                    if st.button("Добавить связь в кейс"):
                        insert_case_probability(conn, current_case_id, chosen_merch[0], prob_input)
                        st.success("Связь добавлена.")

                # Удалить связь
                st.write("**Удалить связь (product -> case)**")
                # Нужно заново перечитать df_probs, если вы только что добавили запись (по желанию)
                # Но для простоты оставим как есть
                df_probs_after = pl.read_database(query_probs, connection=conn)
                if len(df_probs_after) > 0:
                    remove_merch_choice = st.selectbox(
                        "Выберите для удаления",
                        [(r["product_id"], r["product_name"]) for r in df_probs_after.to_dicts()],
                        format_func=lambda x: f"{x[1]} (ID={x[0]})"
                    )
                    if remove_merch_choice and st.button("Удалить связь"):
                        delete_case_probability(conn, current_case_id, remove_merch_choice[0])
                        st.warning(f"Связь удалена: {remove_merch_choice[1]}")


    # -------------------------------------
    # Tab 4. Создание кейсов
    # -------------------------------------
    with tabs[4]:
        st.subheader("Создание новых типов кейсов")
        new_case_name = st.text_input("Название кейса (например, 'Платиновый')")
        new_case_desc = st.text_area("Описание кейса")

        if st.button("Создать новый кейс"):
            if new_case_name:
                create_case_type(conn, new_case_name, new_case_desc)
                st.success("Новый кейс добавлен!")
            else:
                st.error("Введите название кейса.")

    # -------------------------------------
    # Tab 5. Удаление кейсов
    # -------------------------------------
    with tabs[5]:
        st.subheader("Удаление типов кейсов")
        df_ctypes = pl.read_database("SELECT case_type_id, name FROM case_type ORDER BY case_type_id", connection=conn)
        if len(df_ctypes) == 0:
            st.info("Нет кейсов для удаления.")
        else:
            ct_options = [(r["case_type_id"], r["name"]) for r in df_ctypes.to_dicts()]
            chosen_ct = st.selectbox("Выберите кейс для удаления", ct_options, format_func=lambda x: x[1])
            if chosen_ct and st.button("Удалить кейс"):
                delete_case_type(conn, chosen_ct[0])
                st.warning(f"Кейс '{chosen_ct[1]}' удалён.")

    # -------------------------------------
    # Tab 6. Редактирование кейсов
    # -------------------------------------
    with tabs[6]:
        st.subheader("Редактирование типов кейсов")
        df_ctypes = pl.read_database("SELECT case_type_id, name, description FROM case_type ORDER BY case_type_id", connection=conn)
        if len(df_ctypes) == 0:
            st.info("Нет кейсов для редактирования.")
        else:
            ct_options = [(r["case_type_id"], r["name"]) for r in df_ctypes.to_dicts()]
            chosen_ct = st.selectbox("Выберите кейс для редактирования", ct_options, format_func=lambda x: x[1])
            if chosen_ct:
                row_ct = next((x for x in df_ctypes.to_dicts() if x["case_type_id"] == chosen_ct[0]), None)
                if row_ct:
                    new_name = st.text_input("Название кейса", value=row_ct["name"])
                    new_desc = st.text_area("Описание кейса", value=row_ct["description"] or "")

                    if st.button("Сохранить изменения кейса"):
                        update_case_type(conn, chosen_ct[0], new_name, new_desc)
                        st.success("Кейс обновлён.")

    # -------------------------------------
    # Tab 7. Выдача товаров (призы)
    # -------------------------------------
    with tabs[7]:
        st.subheader("Выдача товаров (призы) пользователям")
        delivered_filter = st.selectbox("Показать:", ["Все", "Только невыданные", "Только выданные"])

        filter_query = """
            SELECT uw.user_winning_id, uw.user_id, uw.product_id, uw.delivered, uw.delivered_at, uw.delivered_by,
                   p.name AS product_name
              FROM user_winnings uw
              JOIN product p ON uw.product_id = p.product_id
        """
        if delivered_filter == "Только невыданные":
            filter_query += " WHERE uw.delivered = FALSE"
        elif delivered_filter == "Только выданные":
            filter_query += " WHERE uw.delivered = TRUE"

        df_winnings = pl.read_database(filter_query, connection=conn)

        if len(df_winnings) == 0:
            st.info("Нет призов по выбранному фильтру.")
        else:
            pd_winnings = df_winnings.to_pandas()
            st.dataframe(pd_winnings)

            # Выберем приз для выдачи
            not_delivered = pd_winnings[pd_winnings["delivered"] == False]
            if not_delivered.shape[0] > 0:
                winning_options = [
                    (r.user_winning_id, f"User {r.user_id}, Товар {r.product_name}")
                    for r in not_delivered.itertuples()
                ]
                chosen_winning = st.selectbox("Отметить приз как выданный", winning_options, format_func=lambda x: x[1])
                if chosen_winning:
                    if st.button("Выдать приз"):
                        admin_id = 999  # условный админ
                        update_winning_delivery(conn, chosen_winning[0], True, admin_id)
                        st.success(f"Приз (ID={chosen_winning[0]}) выдан.")

    # -------------------------------------
    # Tab 8. Просмотр S3
    # -------------------------------------
    with tabs[8]:
        st.subheader("Просмотр загруженных объектов в S3")
        objects = list_s3_objects()
        if not objects:
            st.info("В бакете нет объектов.")
        else:
            st.write("Список ключей (файлов) в бакете:")
            for obj_key in objects:
                st.write(obj_key)

    conn.close()

if __name__ == "__main__":
    shop_page()
