from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __self__(self):
        return self.name
    
class Tag(models.Model):
    name = models.CharField(max_length=50,unique=True)
    def __self__(self):
            return self.name
        
class Document(models.Model):

    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", "Private"
        PUBLIC = "PUBLIC", "Public"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    file = models.FileField(upload_to="documents/%Y/%m/")
    file_size = models.PositiveBigIntegerField(default=0)
    file_type = models.CharField(max_length=100, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )

    tags = models.ManyToManyField(Tag, blank=True)

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )

    downloads = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
