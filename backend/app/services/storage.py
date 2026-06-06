import io
import logging
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to ensure MinIO bucket exists: {e}")
            raise e

    def upload_file(self, object_name: str, data: io.BytesIO, length: int, content_type: str = "application/octet-stream") -> str:
        """
        Uploads a file to the MinIO bucket.
        Returns the object name / storage key.
        """
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=data,
                length=length,
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            logger.error(f"Failed to upload object {object_name}: {e}")
            raise e

    def get_file(self, object_name: str) -> bytes:
        """
        Retrieves a file's content as bytes from MinIO.
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as e:
            logger.error(f"Failed to get object {object_name}: {e}")
            raise e

    def delete_file(self, object_name: str) -> None:
        """
        Deletes a file from the MinIO bucket.
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            logger.error(f"Failed to delete object {object_name}: {e}")
            raise e

    def delete_prefix(self, prefix: str) -> None:
        """
        Deletes all objects starting with the given prefix (e.g. for a tenant or assistant).
        """
        try:
            # List objects under prefix and delete them
            objects_to_delete = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            for obj in objects_to_delete:
                self.client.remove_object(
                    bucket_name=self.bucket_name,
                    object_name=obj.object_name
                )
        except S3Error as e:
            logger.error(f"Failed to delete prefix {prefix}: {e}")
            raise e

    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """
        Generates a presigned URL to retrieve an object.
        """
        try:
            return self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires_seconds
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            raise e

# Global storage client instance
storage_service = StorageService()
