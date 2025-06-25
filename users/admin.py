from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, EmailVerification, RegistrationMethod


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("username", "email", "is_staff", "is_active", "first_name", "last_name", "profile_picture", "get_registration_methods")
    list_filter = ("username", "email", "is_staff", "is_active", "registration_methods")
    fieldsets = (
        (None, {"fields": ("username", "email", "password", "first_name", "last_name", "profile_picture", "registration_methods")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = ( 
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email", "password1", "password2", "is_staff",
                "is_active", "groups", "user_permissions", "first_name", "last_name", "profile_picture", "registration_methods"
            )}
        ),
    )
    search_fields = ("username",)
    ordering = ("username",)

    def get_registration_methods(self, obj):
        return ", ".join([m.method for m in obj.registration_methods.all()])
    get_registration_methods.short_description = 'Registration Methods'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(EmailVerification)
admin.site.register(RegistrationMethod)