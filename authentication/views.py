from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login as auth_login, logout as auth_logout, get_user_model
from django.core.mail import send_mail
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth.decorators import login_required
from datetime import timedelta
import random
import logging

from .forms import SignupForm, LoginForm, OTPForm, DocumentUploadForm
from .models import OTP, Document

User = get_user_model()
logger = logging.getLogger(__name__)


# -------------------------
# Helper Functions
# -------------------------
def _generate_numeric_otp(length=settings.OTP_LENGTH):
    return f"{random.randint(0, 10**length - 1):0{length}d}"


def send_otp_email(user, code):
    subject = "Your OTP code"
    message = (
        f"Hi {user.username},\n\n"
        f"Your OTP code is: {code}\n"
        f"It expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n\n"
        f"If you didn't request this, ignore this message."
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        logger.info(f"OTP email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Email send error: {e}")
        print("Email send error:", e)
        return False


def send_otp_sms(user, code):
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        to_number = user.phone
        if not to_number:
            return False
        if not to_number.startswith("+"):
            to_number = "+91" + to_number  # default country code
        client.messages.create(
            body=f"Your OTP: {code} (expires in {settings.OTP_EXPIRY_MINUTES} minutes)",
            from_=settings.TWILIO_FROM_NUMBER,
            to=to_number
        )
        logger.info(f"OTP SMS sent to {user.phone}")
        return True
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        print("OTP for", user.phone, "is", code)  # fallback to console
        return False


def _increment_failed_attempts(key, timeout_seconds=15*60):
    count = cache.get(key, 0) + 1
    cache.set(key, count, timeout=timeout_seconds)
    return count


def _get_failed_attempts(key):
    return cache.get(key, 0)


# -------------------------
# Views
# -------------------------
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password1'])
                user.is_active = True
                user.save()
            messages.success(request, "Signup successful. Please login.")
            return redirect('authentication:login')
        else:
            messages.error(request, "Please fix errors below.")
    else:
        form = SignupForm()
    return render(request, 'authentication/signup.html', {'form': form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['identifier'].strip()
        password = form.cleaned_data['password']

        ip_key = f"login_fail_ip:{request.META.get('REMOTE_ADDR', 'unknown')}"
        user_key = f"login_fail_user:{identifier}"

        if _get_failed_attempts(ip_key) >= 10 or _get_failed_attempts(user_key) >= 7:
            messages.error(request, "Too many failed attempts. Try again later.")
            return render(request, 'authentication/login.html', {'form': form})

        user = (
            User.objects.filter(username__iexact=identifier).first()
            or User.objects.filter(email__iexact=identifier).first()
            or User.objects.filter(phone__iexact=identifier).first()
        )

        if not user or not user.check_password(password):
            _increment_failed_attempts(ip_key)
            _increment_failed_attempts(user_key)
            messages.error(request, "Invalid credentials.")
            return render(request, 'authentication/login.html', {'form': form})

        # generate OTP
        code = _generate_numeric_otp()
        otp = OTP.objects.create(user=user, code=code)

        email_sent = sms_sent = False
        if user.email:
            email_sent = send_otp_email(user, code)
        if user.phone:
            sms_sent = send_otp_sms(user, code)

        if not email_sent and not sms_sent:
            messages.warning(request, "OTP could not be delivered. Check console.")
        else:
            messages.info(request, "OTP sent. Enter below.")

        request.session['otp_user_id'] = user.id
        request.session['otp_created_at'] = otp.created_at.isoformat()
        return redirect('authentication:verify_otp')

    return render(request, 'authentication/login.html', {'form': form})


def verify_otp_view(request):
    form = OTPForm(request.POST or None)
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, "Session expired. Please login again.")
        return redirect('authentication:login')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code'].strip()
        try:
            otp = OTP.objects.filter(user=user, code=code, is_used=False).latest('created_at')
        except OTP.DoesNotExist:
            messages.error(request, "Invalid OTP.")
            return render(request, 'authentication/verify_otp.html', {'form': form})

        if otp.expired():
            messages.error(request, "OTP expired. Please login again.")
            return redirect('authentication:login')

        otp.is_used = True
        otp.save()
        auth_login(request, user)

        request.session.pop('otp_user_id', None)
        request.session.pop('otp_created_at', None)

        messages.success(request, "Logged in successfully.")
        return redirect('pii_app:pii_upload')
  # ✅ correct namespace

    return render(request, 'authentication/verify_otp.html', {'form': form})


@login_required
def home(request):
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'authentication/home.html', {'documents': documents})


@login_required
def old_upload_file(request):
    return redirect('pii_app:pii_upload')


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('authentication:login')


# -------------------------
# New Pages
# -------------------------
def landing_page(request):
    """Intro / Landing page before login"""
    return render(request, 'authentication/landing.html')  # ✅ fixed (removed comma)
