from django.contrib import admin
from django.urls import path, include
from articles.views import ArticleView, uploadArticle
urlpatterns = [
   path("", ArticleView.as_view()),
   path("upload/", uploadArticle),
]
