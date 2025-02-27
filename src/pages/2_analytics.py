import streamlit as st
import polars as pl
import plotly.express as px
import random
from datetime import datetime, timedelta

# ВАЖНО: для динамического прогноза нужно установить numpy и scikit-learn:
import numpy as np
from sklearn.linear_model import LinearRegression

# Для воспроизводимости
random.seed(42)

# Обязательно первым вызовом Streamlit – установка конфигурации страницы!
st.set_page_config(page_title="Аналитика мерча", layout="wide")

# ==============================
# Глобальные константы
# ==============================
MERCH_ITEMS = ["Футболка", "Худи", "Кепка", "Плакат", "Наклейка", "Сумка"]
ACHIEVEMENTS = [
    "Первый заказ", "Большой покупатель", "Коллекционер",
    "Лояльный клиент", "Активный пользователь", "Социальный активист"
]
# Начальные запасы для прогнозирования остатков
MERCH_INITIAL_INVENTORY = {
    "Футболка": 150,
    "Худи": 100,
    "Кепка": 200,
    "Плакат": 50,
    "Наклейка": 300,
    "Сумка": 80
}

# ====================================================
# 1. Генерация синтетических данных
# ====================================================
def generate_users_data(n_users=200):
    """
    Генерация данных пользователей.
    Поля: user_id, username, registration_date.
    """
    users = []
    base_date = datetime.now() - timedelta(days=365)
    for i in range(1, n_users + 1):
        registration_date = base_date + timedelta(days=random.randint(0, 365))
        users.append({
            "user_id": i,
            "username": f"user_{i}",
            "registration_date": registration_date
        })
    return pl.DataFrame(users)

def generate_transactions_data(users_df: pl.DataFrame, n_transactions=1000):
    """
    Генерация данных транзакций.
    Поля: transaction_date, user_id, item, quantity, price_each, total_amount.
    """
    transactions = []
    now = datetime.now()
    for _ in range(n_transactions):
        user = users_df.sample(1).to_dicts()[0]
        delta_days = (now - user["registration_date"]).days
        trans_day = user["registration_date"] + timedelta(days=random.randint(0, max(1, delta_days)))
        item = random.choice(MERCH_ITEMS)
        quantity = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        price_each = round(random.uniform(10, 100), 2)
        total_amount = round(price_each * quantity, 2)
        transactions.append({
            "transaction_date": trans_day,
            "user_id": user["user_id"],
            "item": item,
            "quantity": quantity,
            "price_each": price_each,
            "total_amount": total_amount
        })
    return pl.DataFrame(transactions)

def generate_login_events(users_df: pl.DataFrame, n_events=2000):
    """
    Генерация данных событий входа (login events).
    Поля: login_date, user_id.
    """
    events = []
    now = datetime.now()
    for _ in range(n_events):
        user = users_df.sample(1).to_dicts()[0]
        delta_days = (now - user["registration_date"]).days
        login_date = user["registration_date"] + timedelta(days=random.randint(0, max(1, delta_days)))
        events.append({
            "login_date": login_date,
            "user_id": user["user_id"]
        })
    return pl.DataFrame(events)

def generate_achievements_data(users_df: pl.DataFrame, n_events=300):
    """
    Генерация данных достижений, полученных пользователями.
    Поля: unlock_date, user_id, achievement.
    """
    achievements_data = []
    now = datetime.now()
    for _ in range(n_events):
        user = users_df.sample(1).to_dicts()[0]
        delta_days = (now - user["registration_date"]).days
        unlock_date = user["registration_date"] + timedelta(days=random.randint(0, max(1, delta_days)))
        achievement = random.choice(ACHIEVEMENTS)
        achievements_data.append({
            "unlock_date": unlock_date,
            "user_id": user["user_id"],
            "achievement": achievement
        })
    return pl.DataFrame(achievements_data)

# ====================================================
# 2. Функции агрегации и отображения графиков
# ====================================================
def show_daily_active_users(login_df: pl.DataFrame, start_date, end_date):
    """
    Линейный график ежедневной активности (уникальные логины).
    """
    df_filtered = login_df.filter(
        (pl.col("login_date") >= start_date) & (pl.col("login_date") <= end_date)
    )
    df_filtered = df_filtered.with_columns(
        pl.col("login_date").dt.truncate("1d").alias("login_day")
    )
    df_daily = df_filtered.group_by("login_day").agg(
        pl.col("user_id").n_unique().alias("active_users")
    ).sort("login_day")

    fig = px.line(
        df_daily.to_pandas(),
        x="login_day",
        y="active_users",
        title="Ежедневная активность пользователей",
        labels={"login_day": "Дата", "active_users": "Активных пользователей"},
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

def show_daily_revenue(trans_df: pl.DataFrame, start_date, end_date):
    """
    Линейный график ежедневного дохода магазина.
    """
    df_filtered = trans_df.filter(
        (pl.col("transaction_date") >= start_date) & (pl.col("transaction_date") <= end_date)
    )
    df_filtered = df_filtered.with_columns(
        pl.col("transaction_date").dt.truncate("1d").alias("trans_day")
    )
    df_daily = df_filtered.group_by("trans_day").agg(
        pl.col("total_amount").sum().alias("daily_revenue")
    ).sort("trans_day")

    fig = px.line(
        df_daily.to_pandas(),
        x="trans_day",
        y="daily_revenue",
        title="Ежедневный доход магазина",
        labels={"trans_day": "Дата", "daily_revenue": "Доход"},
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

def show_top_spenders(trans_df: pl.DataFrame, users_df: pl.DataFrame, top_n=10, start_date=None, end_date=None):
    """
    Бар-чарт топ-пользователей по сумме покупок.
    """
    df_filtered = trans_df
    if start_date and end_date:
        df_filtered = df_filtered.filter(
            (pl.col("transaction_date") >= start_date) & (pl.col("transaction_date") <= end_date)
        )
    df_user = df_filtered.group_by("user_id").agg(
        pl.col("total_amount").sum().alias("total_spent")
    ).sort("total_spent", descending=True).limit(top_n)

    users_pd = users_df.to_pandas()
    df_user_pd = df_user.to_pandas().merge(users_pd, on="user_id")

    fig = px.bar(
        df_user_pd,
        x="username",
        y="total_spent",
        title=f"Топ-{top_n} покупателей по сумме покупок",
        labels={"username": "Пользователь", "total_spent": "Потрачено ($)"},
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

def show_achievements(ach_df: pl.DataFrame, start_date, end_date):
    """
    Бар-чарт количества полученных достижений по типу.
    """
    df_filtered = ach_df.filter(
        (pl.col("unlock_date") >= start_date) & (pl.col("unlock_date") <= end_date)
    )
    df_ach = df_filtered.group_by("achievement").agg(
        pl.count("achievement").alias("count")
    ).sort("count", descending=True)

    fig = px.bar(
        df_ach.to_pandas(),
        x="achievement",
        y="count",
        title="Полученные достижения",
        labels={"achievement": "Достижение", "count": "Количество"},
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

def show_top_achievements(ach_df: pl.DataFrame, top_n=5, start_date=None, end_date=None):
    """
    Круговая диаграмма топ-достижений по количеству получений.
    """
    df_filtered = ach_df
    if start_date and end_date:
        df_filtered = df_filtered.filter(
            (pl.col("unlock_date") >= start_date) & (pl.col("unlock_date") <= end_date)
        )
    df_top = df_filtered.group_by("achievement").agg(
        pl.count("achievement").alias("total")
    ).sort("total", descending=True).limit(top_n)

    fig = px.pie(
        df_top.to_pandas(),
        names="achievement",
        values="total",
        title=f"Топ-{top_n} достижений",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# ====================================================
# 3. Функция прогнозирования продаж и остатков (с линейной регрессией)
# ====================================================
def show_forecasting(trans_df: pl.DataFrame, start_dt: datetime, end_dt: datetime):
    """
    Прогноз будущего дохода (на 7 дней) и прогноз остатков товаров
    с помощью простой линейной регрессии.
    """
    forecast_days = 7

    # -------------------------------------------------------
    # 1. Прогноз выручки (Revenue Forecast)
    # -------------------------------------------------------
    df_rev = (
        trans_df
        .filter((pl.col("transaction_date") >= start_dt) & (pl.col("transaction_date") <= end_dt))
        .with_columns(pl.col("transaction_date").dt.truncate("1d").alias("trans_day"))
        .group_by("trans_day")
        .agg(pl.col("total_amount").sum().alias("daily_revenue"))
        .sort("trans_day")
    )

    # Если данных нет или только 1 точка, fallback на среднее
    if df_rev.height < 2:
        if df_rev.height == 1:
            avg_daily_revenue = df_rev["daily_revenue"][0]
        else:
            avg_daily_revenue = 0.0
        forecast_dates = [end_dt.date() + timedelta(days=i+1) for i in range(forecast_days)]
        forecast_values = [avg_daily_revenue] * forecast_days
    else:
        # Линейная регрессия по daily_revenue
        df_pd = df_rev.to_pandas()
        # Преобразуем даты в "номер дня" относительно минимальной даты
        df_pd["day_index"] = (df_pd["trans_day"] - df_pd["trans_day"].min()).dt.days

        X = df_pd[["day_index"]].values  # (n_samples, 1)
        y = df_pd["daily_revenue"].values

        model = LinearRegression()
        model.fit(X, y)

        # Прогнозируем на следующие forecast_days
        last_day_index = df_pd["day_index"].max()
        future_day_indices = np.arange(last_day_index+1, last_day_index+forecast_days+1)

        forecast_values = model.predict(future_day_indices.reshape(-1, 1))
        # Ограничиваем отрицательные прогнозы (исправление)
        forecast_values = np.maximum(forecast_values, 0)
        # Даты для прогноза
        last_date = df_pd["trans_day"].max()
        forecast_dates = [last_date.date() + timedelta(days=i) for i in range(1, forecast_days+1)]

    # Собираем DataFrame с результатом
    forecast_rev_df = pl.DataFrame({
        "date": forecast_dates,
        "forecasted_revenue": forecast_values.tolist()  # преобразуем в список для совместимости
    })

    # Построение графика
    fig_rev = px.line(
        forecast_rev_df.to_pandas(),
        x="date",
        y="forecasted_revenue",
        title="Прогноз будущего дохода (на 7 дней)",
        labels={"date": "Дата", "forecasted_revenue": "Прогноз дохода"},
        template="plotly_white"
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    # -------------------------------------------------------
    # 2. Прогноз остатков товаров (Inventory Forecast)
    # -------------------------------------------------------
    # Считаем дневные продажи каждого товара
    df_sales = (
        trans_df
        .with_columns(pl.col("transaction_date").dt.truncate("1d").alias("trans_day"))
        .group_by(["item", "trans_day"])
        .agg(pl.col("quantity").sum().alias("daily_sold"))
        .sort(["item", "trans_day"])
    )

    # Подготовим итоговую структуру для графика и таблицы
    forecast_plot_data = []
    stockout_data = []

    for item in MERCH_ITEMS:
        init_stock = MERCH_INITIAL_INVENTORY.get(item, 100)

        # Фильтруем продажи по конкретному товару
        df_item = df_sales.filter(pl.col("item") == item)

        # Суммарные продажи, чтобы понять текущий остаток
        total_sold_item = df_item["daily_sold"].sum() if df_item.height > 0 else 0
        current_inventory = max(init_stock - total_sold_item, 0)

        # Если у нас нет исторических данных или только одна дата – fallback на средние продажи
        if df_item.height < 2:
            if df_item.height == 1:
                avg_daily_sales = df_item["daily_sold"][0]
            else:
                avg_daily_sales = 0
            # Прогноз на 7 дней – одна линия
            forecast_sales = [avg_daily_sales] * forecast_days
            # Начнём прогноз с сегодняшней даты (или можно брать max из trans_day)
            last_date_item = datetime.now()
        else:
            # Линейная регрессия
            df_item_pd = df_item.to_pandas()
            min_date_item = df_item_pd["trans_day"].min()
            df_item_pd["day_index"] = (df_item_pd["trans_day"] - min_date_item).dt.days

            X = df_item_pd[["day_index"]].values
            y = df_item_pd["daily_sold"].values

            model = LinearRegression()
            model.fit(X, y)

            last_day_index_item = df_item_pd["day_index"].max()
            future_day_indices_item = np.arange(last_day_index_item+1, last_day_index_item+forecast_days+1)
            forecast_sales = model.predict(future_day_indices_item.reshape(-1, 1))
            # Не допускаем отрицательные прогнозы
            forecast_sales = np.maximum(forecast_sales, 0)

            last_date_item = df_item_pd["trans_day"].max()

        # Даты прогноза (7 дней вперёд от последней даты продаж)
        forecast_dates_item = [last_date_item + timedelta(days=i) for i in range(1, forecast_days+1)]

        # Накапливаем продажи и считаем остатки
        cum_sales = 0
        for i, pred_sales in enumerate(forecast_sales):
            cum_sales += pred_sales
            forecast_inv = max(current_inventory - cum_sales, 0)

            forecast_plot_data.append({
                "item": item,
                "date": forecast_dates_item[i],
                "forecast_inventory": forecast_inv
            })

        # Оценка дней до исчерпания (простейший вариант – средняя из forecast_sales)
        mean_future_sales = np.mean(forecast_sales) if len(forecast_sales) > 0 else 0
        if current_inventory == 0:
            days_to_stockout = "Запасы уже 0"
        elif mean_future_sales <= 0.01:
            days_to_stockout = "Нет продаж/минимальные"
        else:
            days_to_stockout = round(current_inventory / mean_future_sales, 1)

        stockout_data.append({
            "item": item,
            "текущий остаток": current_inventory,
            "средние продажи (по регрессии)": round(mean_future_sales, 2),
            "прогноз дней до исчерпания": days_to_stockout
        })

    # Построим график остатков
    forecast_inv_df = pl.DataFrame(forecast_plot_data).sort(["item", "date"])
    fig_inv = px.line(
        forecast_inv_df.to_pandas(),
        x="date",
        y="forecast_inventory",
        color="item",
        title="Прогноз остатков инвентаря (на 7 дней)",
        labels={"date": "Дата", "forecast_inventory": "Остатки"},
        template="plotly_white"
    )
    st.plotly_chart(fig_inv, use_container_width=True)

    # Таблица с прогнозом исчерпания запасов
    st.subheader("Прогноз исчерпания запасов")
    st.dataframe(stockout_data)

# ====================================================
# 4. Основная функция приложения с фильтрами в главном интерфейсе
# ====================================================
def main():
    # Основной заголовок
    st.title("Аналитика магазина мерча")

    # Фильтры, размещённые в основном интерфейсе
    col1, col2, col3 = st.columns(3)
    with col1:
        date_range = st.date_input(
            "Выберите период анализа",
            [datetime.now() - timedelta(days=30), datetime.now()]
        )
    with col2:
        merch_filter = st.multiselect("Выберите товары мерча", options=MERCH_ITEMS, default=MERCH_ITEMS)
    with col3:
        achievement_filter = st.multiselect("Выберите достижения", options=ACHIEVEMENTS, default=ACHIEVEMENTS)

    start_date, end_date = date_range
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Генерация данных
    users_df = generate_users_data(n_users=200)
    trans_df = generate_transactions_data(users_df, n_transactions=1000)
    login_df = generate_login_events(users_df, n_events=2000)
    ach_df = generate_achievements_data(users_df, n_events=300)

    # Приведение дат к нужному типу
    trans_df = trans_df.with_columns([pl.col("transaction_date").cast(pl.Datetime("us")).alias("transaction_date")])
    login_df = login_df.with_columns([pl.col("login_date").cast(pl.Datetime("us")).alias("login_date")])
    ach_df = ach_df.with_columns([pl.col("unlock_date").cast(pl.Datetime("us")).alias("unlock_date")])

    # Фильтрация по выбранным товарам и достижениям
    trans_df = trans_df.filter(pl.col("item").is_in(merch_filter))
    ach_df = ach_df.filter(pl.col("achievement").is_in(achievement_filter))

    # Вкладки аналитики
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Пользовательская активность",
        "Продажи",
        "Достижения",
        "Топ пользователи",
        "Прогнозирование"
    ])

    with tab1:
        st.subheader("Ежедневная активность пользователей")
        show_daily_active_users(login_df, start_dt, end_dt)

    with tab2:
        st.subheader("Дневной доход магазина")
        show_daily_revenue(trans_df, start_dt, end_dt)

    with tab3:
        st.subheader("Анализ достижений")
        show_achievements(ach_df, start_dt, end_dt)
        st.subheader("Топ достижений")
        show_top_achievements(ach_df, top_n=5, start_date=start_dt, end_date=end_dt)

    with tab4:
        st.subheader("Топ покупателей")
        top_n = st.slider("Выберите количество топ-пользователей", min_value=3, max_value=20, value=10)
        show_top_spenders(trans_df, users_df, top_n=top_n, start_date=start_dt, end_date=end_dt)

    with tab5:
        st.subheader("Прогнозирование продаж и остатков")
        show_forecasting(trans_df, start_dt, end_dt)

if __name__ == "__main__":
    main()
