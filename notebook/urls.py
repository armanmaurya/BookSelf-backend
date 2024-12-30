from django.urls import path, include
from .views import NoteBookPageView, NoteBookView, UserNoteBookView
urlpatterns = [
    path('<str:username>/<slug:slug>/<path:path>', NoteBookPageView.as_view()),
    path('<str:username>/<slug:slug>/', NoteBookPageView.as_view()),
    path('<str:username>/', UserNoteBookView.as_view()),
    path('', NoteBookPageView.as_view())
]