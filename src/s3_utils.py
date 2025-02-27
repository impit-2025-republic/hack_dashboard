# src/s3_utils.py
import uuid
from settings import s3_client, S3_BUCKET_NAME

def upload_to_s3(file_bytes, original_filename):
    """
    Загружает файл (в байтах) в S3 и возвращает сформированный URL или ключ.

    :param file_bytes: содержимое файла (bytes)
    :param original_filename: исходное имя файла (чтобы взять расширение и т.д.)
    :return: публичная ссылка (или путь) на загруженный файл
    """
    s3 = s3_client()

    # Можно придумать логику генерации уникального имени
    # Например, используем UUID + расширение из original_filename
    file_ext = ""
    if "." in original_filename:
        file_ext = "." + original_filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}{file_ext}"

    # Загружаем в бакет
    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=unique_name,
        Body=file_bytes,
        ContentType="image/jpeg"  # или что-то другое, если определяете тип
    )

    # Сформируем публичную ссылку. Иногда надо включать настройки "public-read".
    # Если у вас публичный бакет, ссылка может быть:
    s3_url = f"{S3_BUCKET_NAME}/{unique_name}"

    # Или, если у вас HTTPS-домен для S3, это будет
    # s3_url = f"https://{S3_BUCKET_NAME}.s3.your-endpoint/{unique_name}"

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
