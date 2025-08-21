from django.urls import path
from articles.views import ArticleView, manage_image_attachments, save_embedding_article, uploadArticle, CheckArticleOwner, MyArticlesView, GetChildrenArticle, LikeArticle, manageArticleThumbnail
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
   path("like/", LikeArticle.as_view()),
   # path("<slug:slug>/comments/", ),
   path("myarticles/", MyArticlesView.as_view()),
   path("upload/", uploadArticle),
   path("checkowner/", CheckArticleOwner.as_view()),
   path("get-children/", GetChildrenArticle.as_view()),
   path("save-embedding/", save_embedding_article),
   path("<slug:slug>/thumbnail/", manageArticleThumbnail),
   path("<slug:slug>/", csrf_exempt(ArticleView.as_view())),
   path("<slug:slug>/images/", manage_image_attachments),
]