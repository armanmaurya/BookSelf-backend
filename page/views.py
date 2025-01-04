from django.shortcuts import render
from .models import Page
from .serializers import PageSerializer

# Create your views here.

def getNotebookPage(notebook, page_path):
    if page_path is None:
        return None
    path = page_path.split("/")
    print(path)
    page = None
    for p in path:
        if (p == ""):
            continue
        page = Page.objects.get(notebook=notebook, parent=page, slug=p)
    return page
