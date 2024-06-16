from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail

from articles.serializers import ArticleSerializer
from articles.models import Article
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model  # If used custom user model
from collections import defaultdict
from rest_framework.authentication import SessionAuthentication
from collections import defaultdict


User = get_user_model()



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
        serializer = ArticleSerializer(sorted_articles, many=True)
        data = serializer.data

        # Replace author IDs with author names in the serialized data
        for article in data:
            author_id = article['author']
            author = User.objects.get(id=author_id)
            article['author'] = author.first_name + ' ' + author.last_name

        return Response(data)





class ExampleView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        content = {
            'user': str(request.user),  # `django.contrib.auth.User` instance.
            'auth': str(request.auth),  # None
        }
        # request.session['user_id'] = 1
        return Response({'message': 'Hello, World!'}) 