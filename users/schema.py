import strawberry
from .types.user import UserType
from users.models import CustomUser
from typing import List


@strawberry.type
class Query:
    @strawberry.field
    def users(self, info) -> List[UserType]:
        return CustomUser.objects.all()

    @strawberry.field
    def user(self, info, username: str) -> UserType:
        return CustomUser.objects.get(username=username)
