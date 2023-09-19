from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import ClientsForm,ClientChangeForm
from django.contrib.auth import get_user_model

from .models import Clients

# class ClientAdmin:
#     add_form = ClientsForm
#     form = ClientChangeForm
#     model = Clients
#     list_display = ("email", "is_staff", "is_active",)
#     list_filter = ("email", "is_staff", "is_active",)
#     fieldsets = (
#         (None, {"fields": ("email", "password")}),
#         ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
#     )
#     add_fieldsets = (
#         (None, {
#             "classes": ("wide",),
#             "fields": (
#                 "email", "password1", "password2", "is_staff",
#                 "is_active", "groups", "user_permissions"
#             )}
#          ),
#     )
#     search_fields = ("email",)
#     ordering = ("email",)

# Register your models here.
# admin.register(Clients,ClientAdmin)
# admin.site.unregister(get_user_model())
admin.site.register(get_user_model())