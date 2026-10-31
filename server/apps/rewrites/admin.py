from django.contrib import admin

from server.apps.rewrites.models import RewriteTask


@admin.register(RewriteTask)
class RewriteTaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'document',
        'status',
        'total_paragraphs',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'document__original_name',
        'error_message',
    )
    readonly_fields = (
        'created_at',
        'started_at',
        'completed_at',
    )
