from django.urls import path, include
from .views import NoteBookPageView, manageNotebookCover
urlpatterns = [
    path('cover/<slug:slug>/', manageNotebookCover, name='manage-notebook-cover'),
    path('<str:username>/<slug:slug>/<path:path>', NoteBookPageView.as_view()),
    path('<str:username>/<slug:slug>/', NoteBookPageView.as_view()),
    path('<str:username>/', NoteBookPageView.as_view()),
    path('', NoteBookPageView.as_view()),
]