import strawberry
import strawberry_django
from articles.models import ArticleComment
from users.types.user import UserType
from typing import List, Optional

@strawberry_django.type(ArticleComment)
class CommentType:
    id: int
    user: UserType
    content: str
    parent: Optional["CommentType"]
    created_at: str
    is_pinned: bool

    @strawberry.field
    def is_liked(self, info: strawberry.Info) -> bool:
        currentUser = info.context.request.user
        if currentUser.is_anonymous:
            return False
        return self.likes.filter(id=currentUser.id).exists()
    
    @strawberry.field
    def likes_count(self, info: strawberry.Info) -> int:
        return self.likes.count()
    
    @strawberry.field
    def replies_count(self, info: strawberry.Info) -> int:
        return ArticleComment.objects.filter(parent=self.id).count()
    