from django.http import HttpResponse
from django.utils import timezone
import random
from socket import timeout
import string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail

from backend import settings
from users.models import EmailVerification
from .serializers import EmailVerificationSerializer, RegisterSerializer, VerifyCodeSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, ArticleGetSerializer, ArticleUploadSerializer
from articles.models import Article
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, login  # If used custom user model
from rest_framework.decorators import authentication_classes, api_view, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from collections import defaultdict
from rest_framework.authentication import SessionAuthentication, BasicAuthentication


User = get_user_model()


# class RegisterView(APIView):
#     def post(self, request):
#         serializer = RegistrationSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             refresh = RefreshToken.for_user(user)

#             return Response({
#                 'refresh': str(refresh),
#                 'access': str(refresh.access_token),
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)  # Log in the user
            request.session.set_expiry(12000000)  # Session expires when the browser is closed
            request.session['user_id'] = user.id  # Save user id in session
            return Response({'message': 'Registration successful'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            request.session['user_id'] = user.id
            login(request, user)
            request.session.save()
            return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class LoginView(APIView):
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             refresh = RefreshToken.for_user(user)

#             return Response({
#                 'refresh': str(refresh),
#                 'access': str(refresh.access_token),
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ArticleView(APIView):
    def post(self, request):
        serializer = ArticleUploadSerializer(data=request.data)
        if serializer.is_valid():

            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        id = request.query_params.get('id')
        print(id)
        if id:
            article = Article.objects.get(id=id)
            serializer = ArticleGetSerializer(article)
            data = serializer.data
            author_id = data['author']
            author = User.objects.get(id=author_id)
            data['author'] = author.first_name + ' ' + author.last_name
            return Response(data)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return []


class ArticleListView(APIView):
    def get(self, request):
        articles = Article.objects.all()
        serializer = ArticleGetSerializer(articles, many=True)
        data = serializer.data
        for article in data:
            author_id = article['author']
            author = User.objects.get(id=author_id)
            article['author'] = author.first_name + ' ' + author.last_name
        return Response(data)


class ProfileView(APIView):
    def get(self, request):
        user = request.user
        return Response({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        })

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return []
    
class UserArticles(APIView):
    def get(self, request):
        user = request.user
        articles = Article.objects.filter(author=user)
        serializer = ArticleGetSerializer(articles, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return []

from collections import defaultdict

class Search(APIView):
    def get(self, request):
        query:str = request.query_params.get('q').lower()
        # Split the query into individual words
        query_words = query.split()

        # Initialize a dictionary to store article scores
        article_scores = defaultdict(int)

        # Iterate over each word in the query and update article scores
        for word in query_words:
            # Filter articles that contain the current word
            articles = Article.objects.filter(title__icontains=word)
            # Update scores for matched articles
            for article in articles:
                article_scores[article.id] += 1

        # Sort article IDs based on their scores (descending order)
        sorted_article_ids = sorted(article_scores, key=lambda x: article_scores[x], reverse=True)

        # Retrieve articles based on sorted IDs
        sorted_articles = Article.objects.filter(pk__in=sorted_article_ids)

        # Serialize the sorted articles
        serializer = ArticleGetSerializer(sorted_articles, many=True)
        data = serializer.data

        # Replace author IDs with author names in the serialized data
        for article in data:
            author_id = article['author']
            author = User.objects.get(id=author_id)
            article['author'] = author.first_name + ' ' + author.last_name

        return Response(data)


class SendVerificationCodeView(APIView):
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            verification, created = EmailVerification.objects.get_or_create(email=email)
            if not created:
                verification.code = str(random.randint(1000, 9999))
                verification.created_at = timezone.now()
                verification.verified = False
                verification.save()
            send_mail(
                'Your verification code',
                f'Your verification code is {verification.code}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return Response({'message': 'Verification code sent.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            try:
                verification = EmailVerification.objects.get(email=email, code=code)
                if verification.is_valid():
                    verification.verified = True
                    verification.save()
                    return Response({'message': 'Email verified. You can now complete the registration.'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Verification code expired'}, status=status.HTTP_400_BAD_REQUEST)
            except EmailVerification.DoesNotExist:
                return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
def check_auth_status(request):
    if request.user.is_authenticated:
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_401_UNAUTHORIZED)




class ExampleView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        content = {
            'user': str(request.user),  # `django.contrib.auth.User` instance.
            'auth': str(request.auth),  # None
        }
        return Response(content) 