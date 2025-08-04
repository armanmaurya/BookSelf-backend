from django.forms import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# from django.contrib.auth import get_user_model
from users.models import CustomUser
from users.serializers import UserSerializer

from articles.models import Article, UserArticlesVisitHistory
from .serializers import ArticleUploadSerializer, ArticleSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.decorators import api_view
from rest_framework.authentication import SessionAuthentication
from articles.models import Article
from .utils import get_article_from_slug
from django.views.decorators.csrf import csrf_exempt


User = CustomUser

# Create your views here.


class GetChildrenArticle(APIView):
    def get(self, request):
        id = request.query_params.get("id")
        if id:
            articles = Article.objects.filter(parent=id)
            print(articles)

        return Response(status=status.HTTP_200_OK)


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
        # print(article.pk, "pk")

        # article2 = Article.objects.get(pk=article.pk)
        serializer = ArticleSerializer(article)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        slug = request.query_params.get("slug")
        if slug is None:
            return Response(
                {"message": "Article ID not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        article = self.get_article(slug)
        article.delete()
        return Response(status=status.HTTP_200_OK)

    def patch(self, request, slug):
        article = get_article_from_slug(slug)
        if article is None:
            return Response(
                {"message": "Article not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if article.author != request.user:
            return Response(
                {"message": "You are not the author of this article"},
                status=status.HTTP_403_FORBIDDEN,
            )

        draft_article = article.draft

        # Uploadd the Image 
        if request.FILES.get("image"):
            image = request.FILES["image"]
            draft_article.image = image
            draft_article.save()
            return Response(
                {"message": "Image uploaded successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "No image provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request):
        slug = request.query_params.get("slug")
        userId = request.query_params.get("userId")
        if slug:
            print(request.user)
            article = self.get_article(slug)
            serializer = ArticleSerializer(article)
            return Response(serializer.data)
        elif userId:
            articles = Article.objects.filter(author=userId)
            serializer = ArticleSerializer(articles, many=True)
            articleData = serializer.data
            for article in articleData:
                author_id = article["author"]
                author = User.objects.get(id=author_id)
                article["author"] = author.first_name + " " + author.last_name
            return Response(articleData)
        else:
            articles = Article.objects.all()
            serializer = ArticleSerializer(articles, many=True) 
            articleData = serializer.data
            # for article in articleData:
            #     author_id = article["author"]
            #     author = User.objects.get(id=author_id)
            #     article["username"] = author.username
            #     article["author"] = author.first_name + " " + author.last_name
            return Response(articleData)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        if self.request.method == "PATCH":
            return [IsAuthenticated()]
        if self.request.method == "DELETE":
            return [IsAuthenticated()]
        return []


class LikeArticle(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        slug = request.query_params.get("slug")
        article = Article.objects.get(slug=slug)
        if request.user in article.likes.all():
            article.likes.remove(request.user)
            return Response({"message": "Unliked"})
        article.likes.add(request.user)
        return Response({"message": "Liked"})


class CheckArticleOwner(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        article_id = request.query_params.get("id")
        article = Article.objects.get(id=article_id)
        print(request.user)
        if article.author == request.user:
            return Response({"status": True})
        return Response({"status": False})


class MyArticlesView(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        articles = Article.objects.filter(author=request.user)
        serializer = ArticleSerializer(articles, many=True)
        data = serializer.data
        for article in data:
            author_id = article["author"]
            author = User.objects.get(id=author_id)
            article["author"] = author.first_name + " " + author.last_name
        return Response(data)


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
    
@csrf_exempt
@api_view(["POST"])
def save_embedding_article(request):
    if request.method == "POST":
        article_id = request.data.get("article_id")
        embedding = request.data.get("embedding")
        if not article_id or not embedding:
            return Response(
                {"error": "Article ID and embedding are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            article = Article.objects.get(id=article_id)
            article.embedding = embedding
            article.save()
            return Response({"message": "Embedding saved successfully."}, status=status.HTTP_200_OK)
        except Article.DoesNotExist:
            return Response(
                {"error": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
    return Response(
        {"error": "Invalid request method."},
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )

