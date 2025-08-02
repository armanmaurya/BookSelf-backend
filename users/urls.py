from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from users.views import (
    LoginView,
    RegisterView,
    LogoutView,
    GoogleAuth,
    SendVerificationCodeView,
    VerifyCodeView,
    PersonalInfoView,
    UserNameView,
    TempUserView,
    IsUserNameAvailable,
    GetUserName,
    UserView,
    GetProfileFromUserName,
    FollowView,
    upload_profile_picture
)

urlpatterns = [
    path("", UserView.as_view(), name="user"),
    path("follow/<str:username>/", csrf_exempt(FollowView.as_view()), name="follow"),
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("google-auth/", GoogleAuth.as_view(), name="google"),
    path("sendcode/", SendVerificationCodeView.as_view(), name="sendcode"),
    path("verifycode/", VerifyCodeView.as_view(), name="verifycode"),
    path("personal-info/", PersonalInfoView.as_view(), name="personal-info"),
    path("username/", UserNameView.as_view(), name="username"),
    path("tempuser/", TempUserView.as_view(), name="tempuser"),
    path("checkusername/", IsUserNameAvailable.as_view(), name="checkusername"),
    path("getusername/", GetUserName.as_view(), name="getusername"),
    path("profile/<str:username>/", GetProfileFromUserName.as_view()),
    path("upload-profile-pic/", upload_profile_picture, name="upload_profile_picture"),
]
