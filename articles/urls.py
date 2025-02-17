from django.contrib import admin
from django.urls import path, include
from articles.views import ArticleView, uploadArticle, CheckArticleOwner, MyArticlesView, GetChildrenArticle, LikeArticle
urlpatterns = [
   path("", ArticleView.as_view()),
   path("like/", LikeArticle.as_view()),
   path("myarticles/", MyArticlesView.as_view()),
   path("upload/", uploadArticle),
   path("checkowner/", CheckArticleOwner.as_view()),
   path("get-children/", GetChildrenArticle.as_view())
]
