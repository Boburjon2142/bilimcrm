from django.urls import path

from . import views

urlpatterns = [
    path("sync/push", views.sync_push, name="sync_push"),
    path("sync/pull", views.sync_pull, name="sync_pull"),
]
