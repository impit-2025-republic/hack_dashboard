import os
import psycopg2
import boto3
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Константы для PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB   = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PWD  = os.getenv("POSTGRES_PWD")

# Константы для S3
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY   = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY   = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME  = os.getenv("S3_BUCKET_NAME")

def db_connection():
    """
    Устанавливает соединение с PostgreSQL
    и возвращает объект подключения.
    """
    connection = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PWD
    )
    return connection

def s3_client():
    """
    Создаёт и возвращает клиент S3 (boto3.client)
    с заданными параметрами (эндпоинт, ключи).
    """
    client = boto3.client(
        service_name="s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
    return client
