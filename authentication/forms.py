# authentication/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Document   # ✅ make sure Document exists in models.py

User = get_user_model()


# -------------------------
# Signup Form
# -------------------------
class SignupForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")


# -------------------------
# Login Form
# -------------------------
class LoginForm(forms.Form):
    identifier = forms.CharField(
        label="Username / Email / Phone",
        widget=forms.TextInput(attrs={"placeholder": "Enter username, email, or phone"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter your password"}),
    )


# -------------------------
# OTP Form
# -------------------------
class OTPForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={"placeholder": "Enter OTP"}),
    )


# -------------------------
# Document Upload Form
# -------------------------


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["file"]   # field name matches model


