from django.urls import path

from api.views import Search, ExampleView
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import GoogleAuth, LogoutView

urlpatterns = [
    # path('send-verification-code/', SendVerificationCodeView.as_view(),
    #      name='send-verification-code'),
    # path('verify-email/', VerifyCodeView.as_view(), name='verify-email'),
    # path('register/', RegisterView.as_view()),
    # path('login/', LoginView.as_view()),
    # path('articles/', ArticleListView.as_view()),
    # path('article/', ArticleView.as_view()),
    # path('article/user/', UserArticles.as_view()),
    # path('token/verify/', check_auth_status),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('search/', Search.as_view()),
    # path('anyauth/', anyprotectedview),
    path('example/', ExampleView.as_view()),
    # path("auth/login/google/", GoogleAuth.as_view(), name="google-login"),
    # path("auth/logout/", LogoutView.as_view(), name="logout"),
]
