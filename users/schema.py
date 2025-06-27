from django.conf import settings
import strawberry
from users.types.user import UserType, SelfUserType
from users.models import CustomUser
from strawberry.types import Info
from typing import List, Optional
from strawberry.file_uploads import Upload
from .utils import google_get_access_token, google_get_user_info
from django.contrib.auth import login, logout
from .types.googleAuth import GoogleAuthType

@strawberry.type
class Query:
    @strawberry.field
    def users(self, info, username: Optional[str] = None) -> List[UserType]:
        if username:
            return CustomUser.objects.filter(username__icontains=username)
        return CustomUser.objects.all()

    @strawberry.field
    def user(self, info, username: str) -> UserType:
        return CustomUser.objects.get(username=username)
    
    @strawberry.field
    def me(self, info: Info) -> SelfUserType | None:
        user = info.context.request.user
        print("user", user)
        if user.is_authenticated:
            return user
        return None
    
    @strawberry.field
    def check_username(self, info: Info, username: str) -> bool:
        try:
            CustomUser.objects.get(username=username)
            return True
        except CustomUser.DoesNotExist:
            return False

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
            # Check if 'google' is in registration_methods
            if not user.registration_methods.filter(method="google").exists():
                raise Exception("Google login not enabled for this user.")
            info.context.request.session["user_id"] = user.id
            login(info.context.request, user)
            info.context.request.session.save()
            print(user.username)
            googleAuth.user = user
            return googleAuth
        except CustomUser.DoesNotExist:
            print("User does not exist")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")

            info.context.request.session["email"] = user_info.get("email")
            info.context.request.session["first_name"] = first_name
            info.context.request.session["last_name"] = last_name
            info.context.request.session["registration_method"] = "google"
            info.context.request.session.save()
            googleAuth.is_created = True
            return googleAuth
        
    @strawberry.mutation
    def logout(self, info: Info) -> bool:
        logout(info.context.request)
        return True
    
    @strawberry.mutation
    def update_profile(
        self,
        info: Info,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        about: Optional[str] = None
    ) -> SelfUserType:
        user = info.context.request.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if about is not None:
            user.about = about
        user.save()
        return user
    
    @strawberry.mutation
    def update_user(self, info: Info, first_name: Optional[Upload], last_name: Optional[Upload], profile_picture: Optional[Upload]) -> SelfUserType:
        user = info.context.request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return user
    
    @strawberry.mutation
    def delete_user(self, info: Info) -> bool:
        user = info.context.request.user
        user.delete()
        return True