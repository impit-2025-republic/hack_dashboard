# src/s3_utils.py
import uuid
import boto3
from settings import S3_BUCKET_NAME, S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY

def s3_client():
    """
    Создаёт и возвращает клиент для работы с S3.
    """
    return boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )

def upload_to_s3(file_bytes, original_filename):
    """
    Загружает файл (в байтах) в S3 и возвращает публичную ссылку на него.

    :param file_bytes: содержимое файла (bytes)
    :param original_filename: исходное имя файла (например, "bronze_case.png")
    :return: публичная ссылка на загруженный файл
    """
    s3 = s3_client()

    # Определяем Content-Type на основе расширения файла
    if original_filename.lower().endswith(('.jpg', '.jpeg')):
        content_type = 'image/jpeg'
    elif original_filename.lower().endswith('.png'):
        content_type = 'image/png'
    else:
        content_type = 'application/octet-stream'

    # Генерируем уникальное имя файла с сохранением оригинального имени,
    # например, помещая файлы в папку images/
    unique_name = f"images/{uuid.uuid4().hex}_{original_filename}"

    # Загружаем файл в бакет
    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=unique_name,
        Body=file_bytes,
        ContentType=content_type,
        ACL="public-read"  # делаем файл публично доступным
    )

    # Формируем публичную ссылку
    s3_url = f"{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{unique_name}"

    return s3_url

def list_s3_objects():
    """
    Возвращает список объектов (keys) в бакете S3.
    """
    s3 = s3_client()
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME)
    if "Contents" not in response:
        return []
    objects = response["Contents"]
    keys = [obj["Key"] for obj in objects]
    return keys

def delete_s3_object(key):
    """
    Удаляет объект (key) из S3-бакета.
    """
    s3 = s3_client()
    s3.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
