import strawberry
import strawberry_django
from users.types.user import UserType
from articles.models import Article
from typing import List
from strawberry.types import Info
from .article_comments import CommentType
# from django.contrib.auth.models import 

@strawberry_django.type(Article)
class ArticleType:
    id: strawberry.ID
    title: str | None
    slug: str
    content: str | None
    views: int
    created_at: str
    author: UserType
    
    @strawberry.field
    def likes(self, info: Info) -> List[UserType]:
        return self.likes.all()

    @strawberry.field
    def likes_count(self, info: Info) -> int:
        return self.likes.count()

    @strawberry.field
    def is_liked(self, info: Info) -> bool:
        currentUser = info.context.request.user
        if currentUser.is_anonymous:
            return False
        return self.likes.filter(id=currentUser.id).exists()
    
    @strawberry.field
    def comments(self, info: Info) -> List[CommentType]:
        return self.comments.all()

