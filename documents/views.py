from django.shortcuts import render,redirect,get_object_or_404
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DocUploadForm
from .models import Document
from pathlib import Path
def home(request):
    return render(request,"home.html")

@login_required
def upload_doc(request):
    if request.method == "POST":
        form = DocUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit = False)
            document.owner = request.user
            document.visibility = "PRIVATE"
        
            document.file_size = document.file.size
            document.file_type = document.file.name.split(".")[-1].lower()

            document.save()
            form.save_m2m()

        messages.success(request, "Document uploaded successfully!")
        return redirect("upload_document")

    else:
        form = DocUploadForm()

    return render(
        request,
        "documents/upload.html",
        {"form": form},
    )
    
@login_required
def my_vault(request):
    doc = Document.objects.filter(owner=request.user).order_by("-created_at")
    return render(
        request,
        "documents/my_vault.html",
        {"documents": doc}
    )
    
def public_vault(request):
    query = request.GET.get("q", "").strip()

    documents = Document.objects.filter(
        visibility=Document.Visibility.PUBLIC
    )

    if query:
        documents = documents.filter(title__icontains=query)

    results = []

    for document in documents.order_by("title"):
        results.append({
    "id": document.id,
    "name": document.title,
    "file_type": document.file_type,
    "size": f"{document.file_size / (1024 * 1024):.2f} MB",
    "modified": document.updated_at.strftime("%d %b %Y"),
})

    return render(
        request,
        "documents/public_vault.html",
        {
            "documents": results,
            "query": query,
        },
    )
def download_public_document(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        visibility=Document.Visibility.PUBLIC,
    )

    if not document.file:
        raise Http404("File not found.")

    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=Path(document.file.name).name,
    )