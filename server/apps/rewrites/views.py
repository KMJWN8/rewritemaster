from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from server.apps.documents.models import Document
from server.apps.rewrites.models import RewriteTask
from server.apps.rewrites.services import create_rewrite_task


@login_required
def rewrite_history(request):
    tasks = RewriteTask.objects.filter(
        document__user=request.user,
    ).select_related('document')

    return render(
        request,
        'rewrites/history.html',
        {'tasks': tasks},
    )


@login_required
@require_POST
def rewrite_create(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        user=request.user,
    )

    task = create_rewrite_task(document)

    messages.success(
        request,
        'Задача рерайта создана.',
    )

    return redirect('rewrites:detail', task_id=task.id)


@login_required
def rewrite_detail(request, task_id):
    task = get_object_or_404(
        RewriteTask.objects.select_related('document'),
        id=task_id,
        document__user=request.user,
    )

    return render(
        request,
        'rewrites/detail.html',
        {'task': task},
    )


@login_required
def rewrite_download(request, task_id):
    task = get_object_or_404(
        RewriteTask,
        id=task_id,
        document__user=request.user,
    )

    if task.status != RewriteTask.Status.COMPLETED or not task.result_file:
        raise Http404('Результат рерайта недоступен.')

    return FileResponse(
        task.result_file.open('rb'),
        as_attachment=True,
        filename=task.result_file.name.rsplit('/', 1)[-1],
    )
