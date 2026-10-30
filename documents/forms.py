from django import forms
from .models import Document
import os
class DocUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            "title",
            "description",
            "file",
            "category",
            "tags"
        ]
    def clean_file(self):
        uploaded_file=self.cleaned_data["file"]
        if uploaded_file.size >100*1024*1024:
            raise forms.ValidationError(
                "File size cannot exceed 100MB"
            )
        allowed_extensions = {
            ".pdf",".doc",".docx",".ppt",".pptx",
            ".xls",".xlsx",".txt", ".csv",
        }
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in allowed_extensions:
            raise forms.ValidationError(
                "Unsupported File type"
            )
        return uploaded_file
        