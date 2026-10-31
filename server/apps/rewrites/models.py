import uuid

from django.db import models

from server.apps.documents.models import Document


class RewriteTask(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        PROCESSING = 'processing', 'Обрабатывается'
        COMPLETED = 'completed', 'Завершена'
        FAILED = 'failed', 'Ошибка'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name='rewrite_tasks',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    result_file = models.FileField(
        upload_to='rewrites/results/%Y/%m/%d/',
        blank=True,
    )
    total_paragraphs = models.PositiveIntegerField(default=0)
    rewritten_paragraphs = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Rewrite {self.id} ({self.get_status_display()})'
