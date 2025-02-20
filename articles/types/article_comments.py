import strawberry
import strawberry_django
from articles.models import ArticleComment
from typing import List

@strawberry_django.type(ArticleComment)
class CommentType:
    id: strawberry.ID
    content: str