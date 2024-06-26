from django.forms import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# from django.contrib.auth import get_user_model
from users.models import CustomUser

from articles.models import Article
from .serializers import ArticleUploadSerializer, ArticleSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.decorators import api_view
from rest_framework.authentication import SessionAuthentication
from articles.models import Article
import datetime


User = CustomUser

# Create your views here.


class ArticleView(APIView):
    authentication_classes = [SessionAuthentication]

    def get_article(self, id):
        try:
            article = Article.objects.get(id=id)
            return article
        except Article.DoesNotExist:
            raise ValidationError({"message": "Article not found"})

    def post(self, request):
        article = Article.objects.create(author=request.user)
        serializer = ArticleSerializer(article)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        id = request.query_params.get("id")
        if id is None:
            return Response(
                {"message": "Article ID not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        article = self.get_article(id)
        article.delete()
        return Response(status=status.HTTP_200_OK)

    def patch(self, request):
        id = request.query_params.get("id")
        if id is None:
            return Response(
                {"message": "Article ID not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        article = self.get_article(id)
        tags = request.data.get("tags")
        if tags:
            article.tags.add(*tags)
            return Response({"message": "Tags added"}, status=status.HTTP_200_OK)
        updated_at = datetime.datetime.now()
        request.data["updated_at"] = updated_at
        serializer = ArticleSerializer(article, data=request.data, partial=True)
        if serializer.is_valid():
            print("valid")
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        id = request.query_params.get("id")
        if id:
            print(request.user)
            article = self.get_article(id)
            serializer = ArticleSerializer(article)
            data = serializer.data
            author_id = data["author"]
            author = User.objects.get(id=author_id)
            data["author"] = author.email
            return Response({"data": data, "is_owner": author == request.user})
        else:
            articles = Article.objects.all()
            serializer = ArticleSerializer(articles, many=True)
            data = serializer.data
            for article in data:
                author_id = article["author"]
                author = User.objects.get(id=author_id)
                article["author"] = author.first_name + " " + author.last_name
            return Response(data)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        if self.request.method == "PATCH":
            return [IsAuthenticated()]
        if self.request.method == "DELETE":
            return [IsAuthenticated()]
        return []


class CheckArticleOwner(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        article_id = request.query_params.get("id")
        article = Article.objects.get(id=article_id)
        print(request.user)
        if article.author == request.user:
            return Response({"status": True})
        return Response({"status": False})


class ArticleListView(APIView):
    def get(self, request):
        articles = Article.objects.all()
        serializer = ArticleSerializer(articles, many=True)
        data = serializer.data
        for article in data:
            author_id = article["author"]
            author = User.objects.get(id=author_id)
            article["author"] = author.first_name + " " + author.last_name
        return Response(data)


class CheckArticleBelongsToUser(APIView):
    def get(self, request):
        article_id = request.query_params.get("id")
        article = Article.objects.get(id=article_id)
        if article.author == request.user:
            return Response({"message": "Article belongs to user"})
        return Response({"message": "Article does not belong to user"})


@api_view(["POST"])
def uploadArticle(request):
    if request.method == "POST":
        serializer = ArticleUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
