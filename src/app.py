# app.py
import streamlit as st

def main():
    """
    Это главная страница вашего приложения.
    При наличии папки `pages`,
    Streamlit автоматически создаёт меню для страниц внутри неё.
    """
    st.title("Главная страница")
    st.write("Перейдите в боковое меню (слева) и выберите `1_page_one`.")

if __name__ == "__main__":
    main()
