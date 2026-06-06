from datetime import timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.quotas import (
    ALLOWED_DOCUMENT_FILE_TYPES,
    MAX_UPLOAD_SIZE_BYTES,
    get_tenant_quotas,
)
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.services.storage import StorageService, storage_service


def test_storage_service_import_is_lazy():
    assert isinstance(storage_service, StorageService)
    assert storage_service._client is None


def test_storage_presigned_url_uses_timedelta_expiry():
    class FakeClient:
        def presigned_get_object(self, bucket_name, object_name, expires):
            assert bucket_name == "test-bucket"
            assert object_name == "tenant/t1/docs/d1/file.txt"
            assert expires == timedelta(seconds=120)
            return "https://example.test/presigned"

    service = StorageService()
    service.bucket_name = "test-bucket"
    service._client = FakeClient()

    assert service.get_presigned_url("tenant/t1/docs/d1/file.txt", expires_seconds=120) == (
        "https://example.test/presigned"
    )


def test_quota_limits_include_upload_and_storage_caps():
    starter = get_tenant_quotas("starter")
    pro = get_tenant_quotas("pro")
    business = get_tenant_quotas("business")

    assert MAX_UPLOAD_SIZE_BYTES == 10 * 1024 * 1024
    assert starter.max_upload_size_bytes == MAX_UPLOAD_SIZE_BYTES
    assert starter.max_storage_bytes == starter.max_documents * MAX_UPLOAD_SIZE_BYTES
    assert pro.max_storage_bytes == pro.max_documents * MAX_UPLOAD_SIZE_BYTES
    assert business.max_storage_bytes is None
    assert ALLOWED_DOCUMENT_FILE_TYPES == frozenset({"pdf", "docx", "txt"})


def test_document_schemas_reject_unknown_status_and_file_type():
    payload = {
        "id": uuid4(),
        "assistant_id": uuid4(),
        "filename": "guide.pdf",
        "file_type": "pdf",
        "status": "ready",
        "chunk_count": 4,
        "error_message": None,
        "created_at": "2026-06-06T12:00:00Z",
    }

    assert DocumentResponse(**payload).status == "ready"

    with pytest.raises(ValidationError):
        DocumentResponse(**{**payload, "file_type": "text/plain"})

    with pytest.raises(ValidationError):
        DocumentStatusResponse(
            id=uuid4(),
            status="complete",
            chunk_count=None,
            error_message=None,
        )
