import asyncio
import boto3
from botocore.client import Config
from src.config import settings

# Initialize boto3 S3 client for MinIO/S3 connection
# Ensure endpoint starts with http/https
endpoint = settings.MINIO_ENDPOINT
if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
    endpoint = f"http://{endpoint}"

s3_client = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

BUCKET_NAME = "moreclient-storage"

def _ensure_bucket_exists():
    try:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
    except Exception:
        # Ignore errors if bucket already exists
        pass

# Initialize the storage bucket synchronously on startup
_ensure_bucket_exists()

def tenant_path(tenant_id: str | object, filename: str) -> str:
    """Enforces tenant-prefixed folder paths for all files."""
    return f"tenants/{str(tenant_id)}/{filename}"

async def upload_file(tenant_id: str | object, filename: str, data: bytes) -> str:
    """Upload data to the isolated tenant directory in MinIO."""
    key = tenant_path(tenant_id, filename)
    await asyncio.to_thread(
        s3_client.put_object,
        Bucket=BUCKET_NAME,
        Key=key,
        Body=data
    )
    return key

async def download_file(tenant_id: str | object, filename: str) -> bytes:
    """Download data from the isolated tenant directory in MinIO."""
    key = tenant_path(tenant_id, filename)
    response = await asyncio.to_thread(
        s3_client.get_object,
        Bucket=BUCKET_NAME,
        Key=key
    )
    # Read the body in the thread pool to avoid blocking on socket reads
    return await asyncio.to_thread(response["Body"].read)

async def delete_file(tenant_id: str | object, filename: str) -> None:
    """Delete a file from the isolated tenant directory in MinIO."""
    key = tenant_path(tenant_id, filename)
    await asyncio.to_thread(
        s3_client.delete_object,
        Bucket=BUCKET_NAME,
        Key=key
    )
