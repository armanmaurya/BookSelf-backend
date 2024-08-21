from django.contrib import admin
from django.urls import path, include
from articles.views import ArticleView, uploadArticle, CheckArticleOwner, MyArticlesView
urlpatterns = [
   path("", ArticleView.as_view()),
   path("myarticles/", MyArticlesView.as_view()),
   path("upload/", uploadArticle),
   path("checkowner/", CheckArticleOwner.as_view())
]
