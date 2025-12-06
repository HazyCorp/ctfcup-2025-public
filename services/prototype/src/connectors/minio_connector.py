import os
from functools import lru_cache
import urllib3

import minio
import json
from io import BytesIO
from minio.credentials.providers import EnvMinioProvider
from connectors.generator import create_username, create_password, create_bucket_name

from connectors.policies import restricted_policy, readonly_bucket_anon

HTTP_CLIENT = urllib3.PoolManager(
    maxsize=100,  # Увеличен пул соединений
    num_pools=20,  # Количество пулов
    block=False,
    timeout=urllib3.Timeout(connect=3.0, read=15.0),  # Уменьшены таймауты
    retries=urllib3.Retry(
        total=2,  # Меньше ретраев для быстрого fail-fast
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
)

connection_dict = {
    "endpoint": os.getenv("MINIO_ENDPOINT"),
    "credentials": EnvMinioProvider(),
    "secure": False,
    "http_client": HTTP_CLIENT
}

MAX_ACCESS_KEY_LENGTH = 20
MAX_SECRET_KEY_LENGTH = 40

@lru_cache(maxsize=500)  # Увеличен кэш клиентов
def get_minio_client(access_key: str, secret_key: str) -> minio.Minio:
    return minio.Minio(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=access_key,
        secret_key=secret_key,
        secure=False,
        http_client=HTTP_CLIENT
    )

_admin_client = None

def get_admin_minio_client() -> minio.MinioAdmin:
    """Get cached MinIO admin client."""
    global _admin_client
    if _admin_client is None:
        _admin_client = minio.MinioAdmin(**connection_dict)
    return _admin_client

def create_account() -> tuple[str, str]:
    bucket_name = create_bucket_name()
    policy_content = restricted_policy(bucket_name)
    policy_name = f"policy-{bucket_name}"  # Уникальное имя политики

    admin_mc_client = get_admin_minio_client()

    admin_mc_client.policy_add(policy_name, policy=policy_content)
    access_key, secret_key = create_username()[:MAX_ACCESS_KEY_LENGTH], create_password()[:MAX_SECRET_KEY_LENGTH]
    admin_mc_client.add_service_account(
        access_key=access_key,
        secret_key=secret_key,
        policy=policy_content
    )

    mc = get_minio_client(access_key, secret_key)
    mc.make_bucket(bucket_name)
    mc.set_bucket_policy(bucket_name, json.dumps(readonly_bucket_anon(bucket_name)))

    return access_key, secret_key

def upload_file_to_publish(access_key: str, secret_key: str, filename: str, file: bytes):
    mc = get_minio_client(access_key, secret_key)

    buckets = mc.list_buckets()
    file_stream = BytesIO(file)
    file_size = len(file)

    result = mc.put_object(
        bucket_name=buckets.pop().name,
        object_name=filename,
        data=file_stream,
        length=file_size,
        content_type="application/octet-stream"
    )

    return f"{result.bucket_name}/{result.object_name}"
