from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from server.apps.documents.models import Document

User = get_user_model()


@transaction.atomic
def create_document(
    *,
    user: User,
    uploaded_file: UploadedFile,
) -> Document:
    original_name = Path(
        uploaded_file.name.replace('\\', '/'),
    ).name

    return Document.objects.create(
        user=user,
        file=uploaded_file,
        original_name=original_name,
        file_size=uploaded_file.size,
    )
