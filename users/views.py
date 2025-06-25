from urllib.parse import urlencode
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import redirect
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile

from .mixins import PublicApiMixin, ApiErrorsMixin
from .utils import google_get_access_token, google_get_user_info
from users.models import CustomUser as User, EmailVerification, RegistrationMethod
from users.serializers import (
    GoogleAuthInputSerializer,
    RegisterSerializer,
    LoginSerializer,
    EmailVerificationSerializer,
    UserSerializer,
    VerifyCodeSerializer,
)
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout  # If used custom user model
from django.core.mail import send_mail
from django.utils import timezone
import random
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt

from .models import RegisterAccountTemp, Follow


TEMP_ID = "tempUser_id"


def generate_tokens_for_user(user):
    """
    Generate access and refresh tokens for the given user
    """
    serializer = TokenObtainPairSerializer()
    token_data = serializer.get_token(user)
    access_token = token_data.access_token
    refresh_token = token_data
    return access_token, refresh_token


class FollowView(APIView):
    authentication_classes = [SessionAuthentication]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        if self.request.method == "PATCH":
            return [IsAuthenticated()]
        if self.request.method == "DELETE":
            return [IsAuthenticated()]
        return []

    # Get All the followers of the user
    def get(self, request, username):
        type = request.query_params.get("type")
        user = get_object_or_404(User, username=username)
        if type == "following":
            following = Follow.objects.filter(user=user).select_related("following")
            serializer = UserSerializer(
                [follow.following for follow in following],
                many=True,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif type == "followers":
            followers = Follow.objects.filter(following=user).select_related("user")
            serializer = UserSerializer(
                [follow.user for follow in followers],
                many=True,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"error": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, username):
        user = User.objects.get(username=username)

        # Check if the user is trying to follow themselves
        if request.user == user:
            return Response(
                {"message": "You can't follow yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the user is already following the user
        follow, created = Follow.objects.get_or_create(
            user=request.user, following=user
        )

        # If the user is already following the user, then unfollow
        if not created:
            follow.delete()
            return Response({"message": "Unfollowed"}, status=status.HTTP_200_OK)

        return Response({"message": "Followed"}, status=status.HTTP_200_OK)


class UserView(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        # / is called and user is authenticated
        if request.user.is_authenticated:
            user = request.user
            response = self.profile(user)
            return response
        # if ?code= is called
        elif request.GET.get("code"):
            response = self.google_authencation(request)
            return response

    def profile(self, user: User):
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def google_authencation(self, request):
        input_serializer = GoogleAuthInputSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        code = validated_data.get("code")
        error = validated_data.get("error")
        print("code", code)

        # redirect_path = validated_data.get("redirect_path")

        # login_url = f"{settings.BASE_FRONTEND_URL}/login"

        # if error or not code:
        #     params = urlencode({"error": error})
        #     return Response(
        #         {"message": "Login failed"}, status=status.HTTP_400_BAD_REQUEST
        #     )
        #     # print(f'{login_url}?{params}')
        #     # return redirect(f'{login_url}?{params}')

        # redirect_uri = f"{settings.BASE_FRONTEND_URL}{redirect_path}"
        # access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)

        # user_data = google_get_user_info(access_token=access_token)

        # try:
        #     user = User.objects.get(email=user_data["email"])
        #     request.session["user_id"] = user.id
        #     # login(request, user)
        #     request.session.save()
        #     serializer = UserSerializer(user)
        #     return Response(serializer.data, status=status.HTTP_200_OK)
        # except User.DoesNotExist:
        #     first_name = user_data.get("given_name", "")
        #     last_name = user_data.get("family_name", "")

        #     # tempUser = RegisterAccountTemp.objects.get_or_create(
        #     #     email=user_data['email'],
        #     #     first_name=first_name,
        #     #     last_name=last_name,
        #     # )

        #     # request.session[TEMP_ID] = tempUser[0].id
        #     request.session["email"] = user_data.get("email")
        #     request.session["first_name"] = first_name
        #     request.session["last_name"] = last_name
        #     request.session.save()

        #     response = Response(status=status.HTTP_201_CREATED)
        #     # response.set_cookie(TEMP_ID, tempUser[0].id)
        #     return response
        return Response({"message": "Login successful"}, status=status.HTTP_200_OK)


class GetProfileFromUserName(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request, username):
        user = User.objects.get(username=username)
        serializer = UserSerializer(user)
        data = serializer.data

        if not request.user.is_authenticated:
            data["is_following"] = False
        elif request.user != user:
            try:
                follow = Follow.objects.get(user=request.user, following=user)
                data["is_following"] = True
            except Follow.DoesNotExist:
                data["is_following"] = False

        data["followers"] = Follow.objects.filter(following=user).count()
        data["following"] = Follow.objects.filter(user=user).count()
        return Response(data, status=status.HTTP_200_OK)


class GetUserName(APIView):
    def get(self, request):
        user_id = request.session.get("user_id")
        if not user_id:
            return Response(
                {"error": "User not found in session"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.get(id=user_id)
        return Response({"username": user.username}, status=status.HTTP_200_OK)


class PersonalInfoView(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        user = request.user
        return Response(
            {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )


class IsUserNameAvailable(APIView):
    def post(self, request):
        username = request.data.get("username")
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username is not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": "Username is available"}, status=status.HTTP_200_OK)


class GoogleAuth(PublicApiMixin, ApiErrorsMixin, APIView):

    def get(self, request, *args, **kwargs):
        input_serializer = GoogleAuthInputSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        code = validated_data.get("code")
        error = validated_data.get("error")
        redirect_path = validated_data.get("redirect_path")

        login_url = f"{settings.BASE_FRONTEND_URL}/login"

        if error or not code:
            params = urlencode({"error": error})
            return Response(
                {"message": "Login failed"}, status=status.HTTP_400_BAD_REQUEST
            )
            # print(f'{login_url}?{params}')
            # return redirect(f'{login_url}?{params}')

        redirect_uri = f"{settings.BASE_FRONTEND_URL}{redirect_path}"
        access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)

        user_data = google_get_user_info(access_token=access_token)

        try:
            user = User.objects.get(email=user_data["email"])
            request.session["user_id"] = user.id
            login(request, user)
            request.session.save()
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            first_name = user_data.get("given_name", "")
            last_name = user_data.get("family_name", "")

            # tempUser = RegisterAccountTemp.objects.get_or_create(
            #     email=user_data['email'],
            #     first_name=first_name,
            #     last_name=last_name,
            # )

            # request.session[TEMP_ID] = tempUser[0].id
            request.session["email"] = user_data.get("email")
            request.session["first_name"] = first_name
            request.session["last_name"] = last_name
            request.session.save()
            response = Response(status=status.HTTP_201_CREATED)
            # response.set_cookie(TEMP_ID, tempUser[0].id)
            return response


class TempUserView(APIView):
    def get(self, request):
        try:
            first_name = request.session.get("first_name")
            last_name = request.session.get("last_name")
            if (first_name is None) or (last_name is None):
                return Response(
                    {"error": "Temp user not found"}, status=status.HTTP_404_NOT_FOUND
                )
            # tempUser = RegisterAccountTemp.objects.get(id=user_id)
            return Response(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                },
                status=status.HTTP_200_OK,
            )
        except RegisterAccountTemp.DoesNotExist:
            return Response(
                {"error": "Temp user not found"}, status=status.HTTP_404_NOT_FOUND
            )
        # if not user_id:


class UserNameView(APIView):
    def post(self, request):
        user_id = request.session.get(TEMP_ID)
        if not user_id:
            return redirect(f"{settings.BASE_FRONTEND_URL}/signup")
        try:
            tempUser = RegisterAccountTemp.objects.get(id=user_id)
            username = request.data.get("username")
            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            User.objects.create_user(
                username=username,
                email=tempUser.email,
                first_name=first_name,
                last_name=last_name,
            )

        except RegisterAccountTemp.DoesNotExist:
            return redirect(f"{settings.BASE_FRONTEND_URL}/signup")


class RegisterView(APIView):
    def post(self, request):
        email = request.session.get("email")
        if not email:
            return Response(
                {"error": "Email not found in session"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.data["email"] = email

        # Get the registration methods from session
        registration_method = request.session.get("registration_method")
        method, created = RegistrationMethod.objects.get_or_create(
            method=registration_method
        )
        request.data["first_name"] = request.session.get("first_name", "")
        request.data["registration_methods"] = [method.id] if method else []

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)  # Log in the user
            request.session.set_expiry(12000000)
            # request.session['user_id'] = user.id  # Save user id in session
            request.session.save()
            return Response(
                {"message": "Registration successful"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            request.session["user_id"] = user.id
            login(request, user)
            request.session.save()
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def get(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


class SendVerificationCodeView(APIView):
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            verification, created = EmailVerification.objects.get_or_create(email=email)
            if not created:
                verification.code = str(random.randint(1000, 9999))
                verification.created_at = timezone.now()
                verification.verified = False
                verification.save()
            send_mail(
                "Your verification code",
                f"Your verification code is {verification.code}",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            request.session["email"] = email
            return Response(
                {"message": "Verification code sent."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    def post(self, request):
        email = request.session.get("email")
        if not email:
            return Response(
                {"error": "Email not found in session"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.data["email"] = email
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            code = serializer.validated_data["code"]
            try:
                verification = EmailVerification.objects.get(email=email, code=code)
                if verification.is_valid():
                    verification.verified = True
                    verification.save()
                    return Response(
                        {
                            "message": "Email verified. You can now complete the registration."
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"error": "Verification code expired"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except EmailVerification.DoesNotExist:
                return Response(
                    {"error": "Invalid verification code"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# csrf exempt for profile picture upload
@csrf_exempt
def upload_profile_picture(request):
    if request.method == "POST":
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({"error": "User not authenticated"}, status=401)

        profile_picture = request.FILES.get("profile")
        if not profile_picture:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        # Compress the image
        try:
            image = Image.open(profile_picture)
            image = image.convert("RGB")  # Ensure JPEG compatibility
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=70)
            buffer.seek(0)
            compressed_image = InMemoryUploadedFile(
                buffer,
                "ImageField",
                profile_picture.name.split(".")[0] + ".jpg",
                "image/jpeg",
                buffer.getbuffer().nbytes,
                None,
            )
            user.profile_picture = compressed_image
        except Exception as e:
            return JsonResponse(
                {"error": f"Image compression failed: {str(e)}"}, status=400
            )

        user.save()
        return JsonResponse(
            {"message": "Profile picture updated successfully"}, status=200
        )

    return JsonResponse({"error": "Invalid request method"}, status=405)
