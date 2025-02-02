from django.contrib import admin

from users.models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserModel(admin.ModelAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "avatar",
    )
    list_editable = (
        "username",
        "first_name",
        "last_name",
        "avatar",
    )
    search_fields = ("username", "email")


@admin.register(Subscription)
class Subscription(admin.ModelAdmin):
    list_display = ("follower", "publisher")
    list_editable = ("publisher",)
    list_display_links = ("follower",)
