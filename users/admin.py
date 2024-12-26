from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, EmailVerification


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("username", "email", "is_staff", "is_active", "first_name", "last_name")
    list_filter = ("username", "email", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("username", "email", "password", "first_name", "last_name")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = ( 
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email", "password1", "password2", "is_staff",
                "is_active", "groups", "user_permissions", "first_name", "last_name"
            )}
        ),
    )
    search_fields = ("username",)
    ordering = ("username",)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(EmailVerification)  # Register the EmailVerification model