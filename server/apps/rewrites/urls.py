from django.urls import path

from server.apps.rewrites import views

app_name = 'rewrites'

urlpatterns = [
    path('', views.rewrite_history, name='history'),
    path(
        'create/<uuid:document_id>/',
        views.rewrite_create,
        name='create',
    ),
    path(
        '<uuid:task_id>/',
        views.rewrite_detail,
        name='detail',
    ),
    path(
        '<uuid:task_id>/download/',
        views.rewrite_download,
        name='download',
    ),
]
