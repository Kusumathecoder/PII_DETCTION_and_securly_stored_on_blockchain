# authentication/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


# -------------------------
# Custom User Model
# -------------------------
class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username or self.email or str(self.pk)


# -------------------------
# OTP Model
# -------------------------
class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    purpose = models.CharField(max_length=20, default='login')  # e.g., login, signup, reset-password
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    def __str__(self):
        return f"OTP {self.code} for {self.user} (used={self.is_used})"


# -------------------------
# Document Upload Model
# -------------------------
class Document(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="documents/")  # stores in MEDIA_ROOT/documents/
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} uploaded by {self.user.username}"
