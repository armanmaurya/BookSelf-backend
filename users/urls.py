from django.contrib import admin
from django.urls import path, include
from users.views import LoginView, RegisterView, LogoutView, GoogleAuth, SendVerificationCodeView, VerifyCodeView, PersonalInfoView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('google-auth/', GoogleAuth.as_view(), name='google'),
    path('sendcode/', SendVerificationCodeView.as_view(), name='sendcode'),
    path('verifycode/', VerifyCodeView.as_view(), name='verifycode'),
    path("personal-info/", PersonalInfoView.as_view(), name="personal-info"),
]
