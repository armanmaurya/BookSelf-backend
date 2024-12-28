from django.shortcuts import redirect
from rest_framework import serializers
from .models import CustomUser as User, EmailVerification, RegisterAccountTemp
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class GoogleAuthInputSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    redirect_path = serializers.CharField(required=False)


class RegisterAccountTempSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisterAccountTemp
        fields = ["email", "first_name", "last_name"]


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    # def validate(self, attrs):
    #     email = attrs.get("email")
    #     try:
    #         verification = EmailVerification.objects.get(email=email)
    #         if not verification.verified:
    #             raise serializers.ValidationError(
    #                 {
    #                     "email": "This email is not verified. Please verify your email before registering."
    #                 }
    #             )
    #     except EmailVerification.DoesNotExist:
    #         raise serializers.ValidationError(
    #             {
    #                 "email": "This email is not verified. Please verify your email before registering."
    #             }
    #         )

    #     if attrs["password"] != attrs["password2"]:
    #         raise serializers.ValidationError(
    #             {"password": "Password fields didn't match."}
    #         )

    #     # Check if email is verified

    #     return attrs

    # def create(self, validated_data):
    #     user = User.objects.create(
    #         email=validated_data["email"],
    #         first_name=validated_data["first_name"],
    #         last_name=validated_data["last_name"],
    #     )
    #     user.set_password(validated_data["password"])
    #     user.save()
    #     return user

    def validate(self, attrs):
        username = attrs.get("username")
        if len(username) < 4:
            raise serializers.ValidationError(
                {"username": "Username must be at least 4 characters long."}
            )
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Email and password are required.")

        attrs["user"] = user
        return attrs


class EmailVerificationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = EmailVerification
        fields = ["email"]

    def validate(self, attrs):
        # Check if email is verified
        email = attrs.get("email")
        try:
            user = User.objects.get(email=email)
            if user:
                raise serializers.ValidationError(
                    {
                        "email": "Account With this email is already Exist. Please login to continue."
                    }
                )
        except User.DoesNotExist:
            pass
        return attrs


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4)

    class Meta:
        fields = ["email", "code"]

    def validate(self, attrs):
        email = attrs.get("email")
        try:
            user = User.objects.get(email=email)
            if user:
                raise serializers.ValidationError(
                    {
                        "email": "Account With this email is already Exist. Please login to continue."
                    }
                )
        except User.DoesNotExist:
            pass
        return attrs
