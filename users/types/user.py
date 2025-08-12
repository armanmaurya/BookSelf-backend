import strawberry
import strawberry_django
from articles.enums import ArticleSortBy
from users.models import CustomUser, Follow
from typing import List, Optional
from strawberry import LazyType
from strawberry.types import Info
from django.contrib.auth.models import AnonymousUser
from articles.models import UserArticlesVisitHistory, Collection, Article


@strawberry_django.type(CustomUser)
class UserType:
    id: strawberry.ID
    username: str
    email: str
    first_name: str
    last_name: str
    about: Optional[str] = None

    @strawberry.field
    def registration_methods(self, info: Info) -> List[str]:
        return [m.method for m in self.registration_methods.all()]

    @strawberry.field
    def profile_picture(self, info: Info) -> str:
        if self.profile_picture:
            return self.profile_picture.url
        return ""
    @strawberry.field
    def followers_count(self, info: Info) -> int:
        count = Follow.objects.filter(following=self).count()
        return count

    @strawberry.field
    def following_count(self, info: Info) -> int:
        count = Follow.objects.filter(user=self).count()
        return count
    
    @strawberry.field
    def articles_count(self, info: Info) -> int:
        return Article.objects.filter(author=self, status=Article.PUBLISHED).count()
    
    @strawberry.field
    def collections_count(self, info: Info) -> int:
        return Collection.objects.filter(user=self).count()

    @strawberry.field
    def followers(self, info: Info, number: int , lastId: Optional[int]= None,) -> List["UserType"]:
        if lastId:
            followers = Follow.objects.filter(following=self, id__lt=lastId).order_by("-created_at")[:number]
        else:
            followers = Follow.objects.filter(following=self).order_by("-created_at")[:number]
        return [follow.user for follow in followers]

    @strawberry.field
    def following(self, info: Info, number: int, lastId: Optional[int] = None) -> List["UserType"]:
        if lastId:
            following = Follow.objects.filter(user=self, id__lt=lastId).order_by("-created_at")[:number]
        else:
            following = Follow.objects.filter(user=self).order_by("-created_at")[:number]
        return [follow.following for follow in following]

    @strawberry.field
    def is_following(self, info: Info) -> bool:
        currentUser = info.context.request.user
        if isinstance(currentUser, AnonymousUser):
            return False
        return self.following.filter(user=info.context.request.user).exists()

    @strawberry.field
    def is_self(self, info: Info) -> bool:
        currentUser = info.context.request.user
        if isinstance(currentUser, AnonymousUser):
            return False
        return self.username == info.context.request.user.username
    
    @strawberry.field
    def articles(
        self,
        info: Info,
        sort_by: Optional[ArticleSortBy] = None
    ) -> List[LazyType["ArticleType", "articles.types.article"]]: # type: ignore
        qs = Article.objects.filter(author=self, status=Article.PUBLISHED)
        if sort_by == ArticleSortBy.POPULAR:
            qs = qs.order_by("-views", "-created_at")
        else:  # Default and 'recent'
            qs = qs.order_by("-created_at")
        return qs
    @strawberry.field
    def collections(self, info: Info, number: int,  last_id: Optional[int] = None) -> List[LazyType["CollectionType", "articles.types.collection"]]: # type: ignore
        if last_id:
           return Collection.objects.filter(user=self, id__lt=last_id).order_by("-created_at")[:number]
        return Collection.objects.filter(user=self).order_by("-created_at")[:number]
        

@strawberry.type
class SelfUserType(UserType):
    @strawberry.field
    def reading_history(self, info: Info, number:int, lastId: Optional[int] = None) -> List[LazyType["UserArticleReadHistoryType", "articles.types.UserArticleReadHistory"]]:  # type: ignore
        user = info.context.request.user
        if not user.is_authenticated:
            raise Exception("You must be logged in")

        if lastId:
            return UserArticlesVisitHistory.objects.filter(user=user, id__lt=lastId).order_by("-last_visited")[:number]
        return UserArticlesVisitHistory.objects.filter(user=user).order_by("-last_visited")[:number]

