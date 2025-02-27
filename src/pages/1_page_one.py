import streamlit as st
import polars as pl
from datetime import datetime, time
import requests  # импортируем requests для HTTP-запросов

from settings import db_connection
from insert_data import insert_event, update_event, delete_event, update_visit

ENG_TO_RU = {
    "attended": "Посетил",
    "late": "Опоздал",
    "missed": "Пропустил"
}
RU_TO_ENG = {v: k for k, v in ENG_TO_RU.items()}

def load_events():
    conn = db_connection()
    df = pl.read_database("SELECT * FROM events", connection=conn)
    conn.close()
    return df

def load_companies():
    conn = db_connection()
    company_df = pl.read_database("SELECT company_id, company FROM company", connection=conn)
    conn.close()

    name_to_id = {}
    for row in company_df.to_dicts():
        name_to_id[row["company"]] = row["company_id"]
    return name_to_id


st.title("Админка: таблица Events")
tab_view, tab_add, tab_edit, tab_delete, tab_visits = st.tabs(["Просмотр", "Добавить", "Редактировать", "Удалить", "Визиты"])

# ========= Вкладка "Просмотр" =========
with tab_view:
    st.subheader("Просмотр таблицы ивенты и задачи")
    df_events = load_events()
    if len(df_events) == 0:
        st.warning("Таблица events пуста.")
    else:
        # Для удобства чтения переименуем столбцы только для отображения
        df_display = df_events.rename({
            "event_id": "ID",
            "event_name": "Название события",
            "description": "Описание",
            "title": "Заголовок",
            "start_ds": "Начало",
            "end_ds": "Окончание",
            "status": "Статус",
            "event_type": "Тип события",
            "max_users": "Максимум пользователей",
            "coin": "Награда (coin)",
            "achievement_type_id": "ID ачивмента",
            "company_id": "ID компании"
        })
        st.dataframe(df_display)

# ========= Вкладка "Добавить" =========
with tab_add:
    st.subheader("Добавить новую запись (ивент, задача)")

    companies_dict = load_companies()
    company_names = list(companies_dict.keys())

    with st.form("add_form", clear_on_submit=True):
        st.write("**Основная информация**")
        event_name = st.text_input(
            "Название события (event_name)",
            placeholder="Введите название события...",
            help="Это поле соответствует колонке event_name"
        )
        description = st.text_area(
            "Описание (description)",
            placeholder="Краткое описание события...",
            help="Это поле соответствует колонке description"
        )
        title = st.text_input(
            "Заголовок (title)",
            placeholder="Введите заголовок...",
            help="Это поле соответствует колонке title"
        )

        st.write("---")
        st.write("**Время проведения**")
        # Разделим на колонки для удобства
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Дата начала (start_date)",
                value=datetime.now(),
                help="Дата начала события"
            )
            end_date = st.date_input(
                "Дата окончания (end_date)",
                value=datetime.now(),
                help="Дата завершения события"
            )
        with col2:
            start_time = st.time_input(
                "Время начала (start_time)",
                value=time(9, 0),
                help="Время начала события"
            )
            end_time = st.time_input(
                "Время окончания (end_time)",
                value=time(18, 0),
                help="Время завершения события"
            )
        start_ds = datetime.combine(start_date, start_time)
        end_ds = datetime.combine(end_date, end_time)

        st.write("---")
        st.write("**Дополнительные параметры**")
        status = "open"
        event_type = st.selectbox(
            "Тип события (event_type)",
            options=["event", "task"],
        )
        col_one, col_two = st.columns(2)
        max_users = col_one.number_input(
            "Макс. пользователей (max_users, int)",
            value=0,
            step=10,
            help="Ограничение по количеству участников"
        )
        coin = col_two.number_input(
            "Награда (coin, decimal)",
            value=5.0,
            step=5.0,
            help="Количество монет, выдаваемых за участие (если есть)"
        )
        achievement_type_id = st.number_input(
            "ID ачивмента (achievement_type_id, int)",
            value=0,
            step=1,
            help="Ссылка на achievement_type, при необходимости"
        )

        st.write("---")
        if len(company_names) > 0:
            chosen_company_name = st.selectbox(
                "Компания",
                company_names,
                help="Выберите компанию, к которой относится событие"
            )
            chosen_company_id = companies_dict[chosen_company_name]
        else:
            st.warning("В таблице company нет записей.")
            chosen_company_id = 0

        submitted = st.form_submit_button("Добавить запись")
        if submitted:
            conn = db_connection()
            insert_event(
                conn,
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
                chosen_company_id
            )
            conn.close()
            st.success("Запись успешно добавлена!")
            st.rerun()

# ========= Вкладка "Редактировать" =========
with tab_edit:
    st.subheader("Редактировать существующую запись в events")
    df_events = load_events()

    if len(df_events) == 0:
        st.warning("Таблица events пуста, нечего редактировать.")
    else:
        event_ids = df_events["event_id"].to_list()

        with st.form("update_form"):
            selected_id = st.selectbox("Выберите event_id для редактирования:", event_ids)

            row_to_edit = df_events.filter(pl.col("event_id") == selected_id).to_dicts()[0]

            st.write("**Основная информация**")
            new_event_name = st.text_input(
                "Название события (event_name)",
                value=row_to_edit["event_name"] or "",
                help="Поле event_name в таблице"
            )
            new_description = st.text_area(
                "Описание (description)",
                value=row_to_edit["description"] or ""
            )
            new_title = st.text_input(
                "Заголовок (title)",
                value=row_to_edit["title"] or ""
            )

            st.write("---")
            st.write("**Время проведения**")
            current_start_ds = row_to_edit["start_ds"] or datetime.now()
            current_end_ds = row_to_edit["end_ds"] or datetime.now()

            col1, col2 = st.columns(2)
            with col1:
                new_start_date = st.date_input(
                    "Дата начала (start_date)",
                    value=current_start_ds.date()
                )
                new_end_date = st.date_input(
                    "Дата окончания (end_date)",
                    value=current_end_ds.date()
                )
            with col2:
                new_start_time = st.time_input(
                    "Время начала (start_time)",
                    value=current_start_ds.time()
                )
                new_end_time = st.time_input(
                    "Время окончания (end_time)",
                    value=current_end_ds.time()
                )

            updated_start_ds = datetime.combine(new_start_date, new_start_time)
            updated_end_ds = datetime.combine(new_end_date, new_end_time)

            st.write("---")
            st.write("**Дополнительные параметры**")
            new_status = st.selectbox(
                "Статус события (status)",
                options=["open", "closed", "running"],
            )
            new_event_type = st.selectbox(
                "Тип события (event_type)",
                options=["event", "task"],
            )

            new_max_users = st.number_input(
                "Макс. пользователей (max_users, int)",
                value=int(row_to_edit["max_users"] or 0),
                step=1
            )
            new_coin = st.number_input(
                "Награда (coin, decimal)",
                value=float(row_to_edit["coin"] or 0.0),
                step=0.01
            )
            new_achievement_type_id = st.number_input(
                "ID ачивмента (achievement_type_id, int)",
                value=int(row_to_edit["achievement_type_id"] or 0),
                step=1
            )

            st.write("---")
            companies_dict = load_companies()
            company_names = list(companies_dict.keys())

            current_company_id = row_to_edit["company_id"] or 0
            current_company_name = None

            for cname, cid in companies_dict.items():
                if cid == current_company_id:
                    current_company_name = cname
                    break

            if current_company_name is None and len(company_names) > 0:
                current_company_name = company_names[0]

            if len(company_names) > 0:
                new_company_name = st.selectbox(
                    "Компания",
                    options=company_names,
                    index=company_names.index(current_company_name) if current_company_name in company_names else 0
                )
                new_company_id = companies_dict[new_company_name]
            else:
                st.warning("В таблице company нет записей.")
                new_company_id = 0

            save_changes = st.form_submit_button("Сохранить изменения")
            if save_changes:
                conn = db_connection()
                update_event(
                    conn,
                    selected_id,
                    new_event_name,
                    new_description,
                    new_title,
                    updated_start_ds,
                    updated_end_ds,
                    new_status,
                    new_event_type,
                    new_max_users,
                    new_coin,
                    new_achievement_type_id,
                    new_company_id
                )
                conn.close()
                st.success(f"Запись с event_id={selected_id} обновлена!")
                st.rerun()

# ========= Вкладка "Удалить" =========
with tab_delete:
    st.subheader("Удалить запись из таблицы events")
    df_events = load_events()
    if len(df_events) == 0:
        st.warning("Таблица events пуста, нечего удалять.")
    else:
        event_ids_delete = df_events["event_id"].to_list()
        with st.form("delete_form"):
            selected_id_delete = st.selectbox("Выберите event_id для удаления", event_ids_delete)
            delete_button = st.form_submit_button("Удалить")
            if delete_button:
                conn = db_connection()
                delete_event(conn, selected_id_delete)
                conn.close()
                st.success(f"Запись с event_id={selected_id_delete} успешно удалена!")
                st.rerun()


with tab_visits:
    st.subheader("Фильтр и редактирование посещаемости")

    # Форма фильтрации – два selectbox: для Event ID и Event Name
    with st.form("filter_form", clear_on_submit=False):
        conn = db_connection()
        df_events = pl.read_database("SELECT event_id, event_name FROM events", connection=conn)
        conn.close()

        if df_events.is_empty():
            st.error("Нет данных о событиях в таблице events.")
        events = df_events.to_dicts()
        event_ids = sorted({str(event["event_id"]) for event in events})
        event_names = sorted({event["event_name"] for event in events if event["event_name"] is not None})

        selected_event_id = st.selectbox("Фильтр по Event ID", options=["Все"] + event_ids)
        selected_event_name = st.selectbox("Фильтр по наименованию", options=["Все"] + event_names)

        if st.form_submit_button("Поиск"):
            st.session_state["selected_event_id"] = selected_event_id
            st.session_state["selected_event_name"] = selected_event_name
            st.rerun()

    filter_event_id = st.session_state.get("selected_event_id", "Все")
    filter_event_name = st.session_state.get("selected_event_name", "Все")

    conn = db_connection()
    df_visits = pl.read_database("SELECT * FROM event_user_visits", connection=conn)
    df_events = pl.read_database("SELECT event_id, event_name FROM events", connection=conn)
    df_users = pl.read_database("SELECT user_id, surname, name, last_surname FROM users", connection=conn)
    conn.close()

    df_visits = df_visits.with_columns(pl.col("event_id").cast(pl.Int64))
    df_events = df_events.with_columns(pl.col("event_id").cast(pl.Int64))
    df_visits = df_visits.with_columns(pl.col("user_id").cast(pl.Int64))
    df_users = df_users.with_columns(pl.col("user_id").cast(pl.Int64))

    df_visits = df_visits.join(df_events, on="event_id", how="left")
    df_visits = df_visits.join(df_users, on="user_id", how="left")

    if filter_event_id != "Все":
        try:
            df_visits = df_visits.filter(pl.col("event_id") == int(filter_event_id))
        except Exception as e:
            st.error(f"Ошибка фильтрации по Event ID: {e}")

    if filter_event_name != "Все":
        df_visits = df_visits.filter(pl.col("event_name") == filter_event_name)

    if df_visits.is_empty():
        st.info("Нет записей посещаемости по заданным фильтрам.")
    else:
        st.write("Отметьте галочкой, кто посетил событие, и нажмите «Сохранить изменения».")

        with st.form("visits_edit_form", clear_on_submit=False):
            col_event, col_surname, col_name, col_lastname, col_visit = st.columns(5)
            col_event.write("Название события")
            col_surname.write("Фамилия")
            col_name.write("Имя")
            col_lastname.write("Отчество")
            col_visit.write("Посетил")

            new_statuses = {}
            for idx, row in enumerate(df_visits.to_dicts()):
                cols = st.columns(5)
                cols[0].write(row.get("event_name", ""))
                cols[1].write(row.get("surname", ""))
                cols[2].write(row.get("name", ""))
                cols[3].write(row.get("last_surname", ""))
                # Если в базе статус "attended" – галочка установлена, иначе – снята
                visited = (row.get("visit") == "attended")
                cb_val = cols[4].checkbox("", value=visited, key=f"visit_{idx}")
                new_status = "attended" if cb_val else "missed"
                new_statuses[(row["event_id"], row["user_id"])] = new_status

            if st.form_submit_button("Сохранить изменения"):
                conn = db_connection()
                for (event_id, user_id), status in new_statuses.items():
                    update_visit(conn, event_id, user_id, status)
                    # Выполняем API-запрос для статуса "attended"
                    if status == "attended":
                        payload = {
                            "achievement_type_id": 10,  # здесь можно подставить нужное значение
                            "eventID": event_id,
                            "userID": user_id
                        }
                        response = requests.post(
                            "https://api.b8st.ru/admin/events/visit",
                            headers={
                                "accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            json=payload
                        )
                        # При необходимости можно добавить проверку статуса ответа:
                        if response.status_code != 200:
                            st.error(f"Ошибка при отправке запроса для eventID={event_id}, userID={user_id}")
                conn.close()
                st.success("Посещаемость успешно обновлена!")
                st.rerun()
