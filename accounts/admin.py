from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm
from .models import CustomUser


# Register your models here.

class CustomUserAdmin(UserAdmin):
    """
    Admin interface for the CustomUser model.
    Extends Django's built-in UserAdmin to include custom fields and functionality.
    """
    add_form = CustomUserCreationForm
    model = CustomUser
    list_display = [
        "username",
        "email",
        "is_staff",
    ]
    list_filter = ["is_staff"]
    fieldsets = (
        *UserAdmin.fieldsets[:2],  # Include default fieldsets
        (
            'Market Access Settings',  # No group name
            {"fields": ()},  # Add your custom fields
        ),
        *UserAdmin.fieldsets[2:],  # Include the rest of the default fieldsets
    )
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ()}),)

admin.site.register(CustomUser, CustomUserAdmin)
