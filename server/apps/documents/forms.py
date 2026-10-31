from pathlib import Path
from zipfile import BadZipFile, ZipFile

from django import forms

MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024  # 100 MB


class DocumentUploadForm(forms.Form):
    file = forms.FileField(
        label='Документ DOCX',
        widget=forms.ClearableFileInput(
            attrs={'accept': '.docx'},
        ),
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']

        if Path(uploaded_file.name).suffix.lower() != '.docx':
            raise forms.ValidationError(
                'Поддерживаются только файлы DOCX.',
            )

        if uploaded_file.size > MAX_DOCUMENT_SIZE:
            raise forms.ValidationError(
                'Размер файла не должен превышать 20 МБ.',
            )

        try:
            with ZipFile(uploaded_file) as archive:
                names = set(archive.namelist())

                required_files = {
                    '[Content_Types].xml',
                    'word/document.xml',
                }

                if not required_files.issubset(names):
                    raise forms.ValidationError(
                        'Файл не является корректным документом DOCX.',
                    )

                uncompressed_size = sum(
                    item.file_size for item in archive.infolist()
                )

                if uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                    raise forms.ValidationError(
                        'Содержимое документа слишком велико.',
                    )

                if len(names) > 2000:
                    raise forms.ValidationError(
                        'Документ содержит слишком много элементов.',
                    )

        except BadZipFile, OSError:
            raise forms.ValidationError(
                'Не удалось прочитать DOCX. Проверьте файл.',
            )

        finally:
            uploaded_file.seek(0)

        return uploaded_file
