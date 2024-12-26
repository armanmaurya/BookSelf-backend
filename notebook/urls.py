from django.urls import path, include
from .views import NoteBookView
urlpatterns = [
    path('', NoteBookView.as_view())
]