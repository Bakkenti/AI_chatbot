from minio import Minio
from dotenv import load_dotenv
import os

project_root = os.path.join(os.path.dirname(__file__), "..")
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BUCKET_NAME = os.getenv("MINIO_BUCKET", "files")

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_USER,
    secret_key=MINIO_PASSWORD,
    secure=True,
)

if not client.bucket_exists(BUCKET_NAME):
    client.make_bucket(BUCKET_NAME)
