from django.contrib import admin
from .models import Category, Document, Tag

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields=("name",)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields=("name",)
    

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "visibility",
        "category",
        "downloads",
        "created_at",
    )

    list_filter = ("visibility", "category", "created_at")
    search_fields = ("title", "description", "owner__username")
    readonly_fields = ("file_size", "file_type", "downloads", "created_at", "updated_at")
