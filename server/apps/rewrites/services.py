from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files import File
from django.utils import timezone

from server.apps.documents.models import Document
from server.apps.rewrites.models import RewriteTask


def create_rewrite_task(document: Document) -> RewriteTask:
    return RewriteTask.objects.create(document=document)


def execute_rewrite_task(task: RewriteTask, client) -> RewriteTask:
    if task.status != RewriteTask.Status.PENDING:
        raise ValueError('Можно выполнять только ожидающие задачи.')

    task.status = RewriteTask.Status.PROCESSING
    task.started_at = timezone.now()
    task.error_message = ''
    task.save(
        update_fields=['status', 'started_at', 'error_message'],
    )

    try:
        from server.rewrite_engine.pipeline import rewrite_document

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'rewritten.docx'

            parsed_document = rewrite_document(
                source_path=Path(task.document.file.path),
                output_path=output_path,
                client=client,
            )

            total_paragraphs = len(parsed_document.rewritable())

            with output_path.open('rb') as result:
                task.result_file.save(
                    f'{task.document.original_name.rsplit(".", 1)[0]}_rewritten.docx',
                    File(result),
                    save=False,
                )

        task.status = RewriteTask.Status.COMPLETED
        task.total_paragraphs = total_paragraphs
        task.completed_at = timezone.now()
        task.save()

    except Exception as exc:
        task.status = RewriteTask.Status.FAILED
        task.error_message = str(exc)
        task.completed_at = timezone.now()
        task.save(
            update_fields=[
                'status',
                'error_message',
                'completed_at',
            ],
        )
        raise

    return task
