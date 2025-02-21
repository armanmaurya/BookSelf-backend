import strawberry
import strawberry_django
from users.models import CustomUser
from typing import List
from strawberry.types import Info
from django.contrib.auth.models import AnonymousUser

@strawberry_django.type(CustomUser)
class UserType:
    id: strawberry.ID
    username: str
    email: str
    first_name: str
    last_name: str
    registration_method: str

    @strawberry.field
    def followers_count(self, info: Info) -> int:
        return self.followers.count()
    
    @strawberry.field
    def following_count(self, info: Info) -> int:
        return self.following.count()
    
    @strawberry.field
    def followers(self, info: Info) -> List["UserType"]:
        return [follow.user for follow in self.followers.all()]
    
    @strawberry.field
    def following(self, info: Info) -> List["UserType"]:
        return [follow.following for follow in self.following.all()]
    
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

