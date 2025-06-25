from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser, RegistrationMethod


class CustomUserCreationForm(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            email_method, _ = RegistrationMethod.objects.get_or_create(method="email")
            user.registration_methods.add(email_method)
        return user

    class Meta:
        model = CustomUser
        fields = "__all__"


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = "__all__"