from django.conf import settings
import strawberry
from users.types.user import UserType
from users.models import CustomUser
from strawberry.types import Info
from typing import List
from .utils import google_get_access_token, google_get_user_info
from django.contrib.auth import login, logout
from .types.googleAuth import GoogleAuthType

@strawberry.type
class Query:
    @strawberry.field
    def users(self, info) -> List[UserType]:
        return CustomUser.objects.all()

    @strawberry.field
    def user(self, info, username: str) -> UserType:
        return CustomUser.objects.get(username=username)
    
    @strawberry.field
    def me(self, info: Info) -> UserType | None:
        user = info.context.request.user
        print("user", user)
        if user.is_authenticated:
            return user
        return None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def google_auth(self, info: Info, token: str, redirectPath: str) -> GoogleAuthType:
        redirect_uri = f"{settings.BASE_FRONTEND_URL}{redirectPath}"
        access_token = google_get_access_token(code=token, redirect_uri=redirect_uri)

        user_info = google_get_user_info(access_token=access_token)
        googleAuth = GoogleAuthType(user=None, is_created=False)
        try:
            user = CustomUser.objects.get(email=user_info["email"])
            info.context.request.session["user_id"] = user.id
            login(info.context.request, user)
            info.context.request.session.save()
            print(user.username)
            googleAuth.user = user
            return googleAuth
        except CustomUser.DoesNotExist:
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")

            info.context.request.session["email"] = user_info.get("email")
            info.context.request.session["first_name"] = first_name
            info.context.request.session["last_name"] = last_name
            info.context.request.session.save()
            googleAuth.is_created = True
            return googleAuth
