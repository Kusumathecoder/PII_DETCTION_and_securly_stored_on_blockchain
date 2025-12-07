from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    path("", views.landing_page, name="landing"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("home/", views.home, name="home"),
    path("logout/", views.logout_view, name="logout"),

    path("upload/", views.old_upload_file, name="upload"),

]
