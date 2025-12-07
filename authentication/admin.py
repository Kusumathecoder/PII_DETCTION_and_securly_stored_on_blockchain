# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, Document


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra', {'fields': ('phone',)}),
    )
    list_display = ('username', 'email', 'phone', 'is_staff', 'is_active')


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'purpose', 'created_at', 'is_used')
    readonly_fields = ('created_at',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_name', 'user', 'uploaded_at')
    list_filter = ('uploaded_at', 'user')
    search_fields = ('file', 'user__username', 'user__email')
    readonly_fields = ('uploaded_at',)

    def file_name(self, obj):
        return obj.file.name.split("/")[-1]  # show only filename, not full path
    file_name.short_description = "File"
