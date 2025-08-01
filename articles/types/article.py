import strawberry
import strawberry_django
from users.types.user import UserType
from articles.models import Article
from typing import List, Optional
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
    status: str

    @strawberry.field
    def is_self(self, info: Info) -> bool:
        currentUser = info.context.request.user
        if currentUser.is_anonymous:
            return False
        return self.author.id == currentUser.id

    @strawberry.field
    def related_articles(self, info: Info) -> List["ArticleType"]:
        return self.related()

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
    def comments(
        self,
        info: Info,
        number: int,
        parentId: Optional[int] = None,
        lastId: Optional[int] = None,
    ) -> List[CommentType]:
        parent_comment = None
        if parentId:
            parent_comment = self.comments.get(id=parentId)
        if lastId:
            return self.comments.filter(id__lt=lastId, parent=parent_comment).order_by(
                "-created_at"
            )[:number]
        return self.comments.filter(parent=parent_comment).order_by("-created_at")[
            :number
        ]

    @strawberry.field
    def comments_count(self, info: Info) -> int:
        return self.comments.filter(parent=None).count()
    
    @strawberry.field
    def total_comments_count(self, info: Info) -> int:
        return self.comments.count()

    @strawberry.field
    def replies_count(self, info: Info, parent: int) -> int:
        return self.comments.filter(parent=parent).count()
    

