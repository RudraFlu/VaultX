from django.urls import path
from . import views

urlpatterns = [
    path("", views.public_vault, name="home"),
    path("upload/", views.upload_doc, name="upload_doc"),
    path("my-vault/", views.my_vault, name="my_vault"),
    path("public-vault/", views.public_vault, name="public_vault"),
    path(
        "public-vault/download/<int:document_id>/",
        views.download_public_document,
        name="download_public_document",
    )
]