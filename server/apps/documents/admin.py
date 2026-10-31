from django.contrib import admin

from server.apps.documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'original_name',
        'user',
        'file_size',
        'created_at',
    )
    list_filter = ('created_at',)
    search_fields = ('original_name',)
    readonly_fields = ('created_at',)
