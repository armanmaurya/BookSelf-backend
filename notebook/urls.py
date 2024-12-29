from django.urls import path, include
from .views import NoteBookView
urlpatterns = [
    path('<str:username>/<slug:slug>', NoteBookView.as_view()),
    path('<str:username>', NoteBookView.as_view()),
    path('', NoteBookView.as_view())
]