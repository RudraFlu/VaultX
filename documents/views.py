from pathlib import Path
from django.shortcuts import render,redirect,get_object_or_404
from django.http import FileResponse, Http404
from django.utils.http import http_date
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DocUploadForm
from .models import Document
from .services import get_shared_items, resolve_shared_path
from .search_index import search_documents
PREVIEW_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

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
    relative_path = request.GET.get("path", "").strip()
    query = request.GET.get("q", "").strip()

    if query:
        current_items = get_shared_items(relative_path)

        terms = query.casefold().split()

        name_matches = []
        matched_paths = set()

        if current_items:
            for item in current_items:
                if item["is_dir"]:
                    matched = all(term in item["name"].casefold() for term in terms)
                else:
                    matched = any(term in item["name"].casefold() for term in terms)

                if matched:
                    item["result_type"] = "name_match"
                    name_matches.append(item)
                    matched_paths.add(item["path"].casefold())

        results = search_documents(query, limit=100)

        other_results = []

        for result in results:
            if result["path"].casefold() in matched_paths:
                continue

            other_results.append({
                "name": result["filename"],
                "is_dir": False,
                "path": result["path"],
                "excerpt": result["excerpt"],
                "relevance": result["relevance"],
                "result_type": "content_match",
            })

        items = name_matches + other_results

    else:
        items = get_shared_items(relative_path)

    breadcrumbs = []
    current_path = ""

    for part in relative_path.replace("\\", "/").split("/"):
        if part:
            current_path = (
                f"{current_path}/{part}" if current_path else part
            )
            breadcrumbs.append({
                "name": part,
                "path": current_path,
            })

    return render(
        request,
        "documents/public_vault.html",
        {
            "items": items,
            "current_path": relative_path,
            "breadcrumbs": breadcrumbs,
            "share_available": items is not None,
            "query": query,
            "is_search": bool(query),
        },
    )

def download_shared_file(request):
    relative_path = request.GET.get("path", "")
    file_path = resolve_shared_path(relative_path)

    if file_path is None or not file_path.is_file():
        raise Http404("File not found.")

    try:
        return FileResponse(
            file_path.open("rb"),
            as_attachment=True,
            filename=file_path.name,
        )
    except OSError:
        raise Http404("File is unavailable.")


def preview_shared_file(request):
    relative_path = request.GET.get("path", "")
    file_path = resolve_shared_path(relative_path)

    if file_path is None or not file_path.is_file():
        raise Http404("File not found.")

    content_type = PREVIEW_TYPES.get(file_path.suffix.lower())

    if content_type is None:
        raise Http404("Preview is not supported for this file type.")

    try:
        response = FileResponse(
            file_path.open("rb"),
            content_type=content_type,
        )
        response["Content-Disposition"] = "inline"
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response
    except OSError:
        raise Http404("File is unavailable.")