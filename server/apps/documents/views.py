# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from server.apps.documents.forms import DocumentUploadForm
from server.apps.documents.models import Document
from server.apps.documents.services import create_document


@login_required
def document_list(request):
    documents = Document.objects.filter(
        user=request.user,
    )

    return render(
        request,
        'documents/list.html',
        {'documents': documents},
    )


@login_required
def document_upload(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():
            create_document(
                user=request.user,
                uploaded_file=form.cleaned_data['file'],
            )

            messages.success(
                request,
                'Документ успешно загружен.',
            )

            return redirect('documents:list')

    else:
        form = DocumentUploadForm()

    return render(
        request,
        'documents/upload.html',
        {'form': form},
    )
