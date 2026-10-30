from django.urls import path
from . import views

urlpatterns = [
    path("", views.public_vault, name="home"),
    path("upload/", views.upload_doc, name="upload_doc"),
    path("my-vault/", views.my_vault, name="my_vault"),
    path("public-vault/", views.public_vault, name="public_vault"),
    path(
        "shared-download/",
        views.download_shared_file,
        name="download_shared_file",
    ),
    path(
        "shared-preview/",
        views.preview_shared_file,
        name="preview_shared_file",
    ),
]