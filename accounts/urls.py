from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("register/", views.register, name="register"),
    path("login/", views.VestLoginView.as_view(), name="login"),
    path("login/key/", views.key_login, name="key_login"),
    path("logout/", views.VestLogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/login-key/regenerate/", views.regenerate_login_key_view, name="regenerate_login_key"),
    path("profile/", views.profile, name="profile"),
    path("profile/kyc/", views.kyc_submit, name="kyc_submit"),
    path("verify-email/<uidb64>/<token>/", views.verify_email, name="verify_email"),
    path("profile/resend-verification/", views.resend_verification, name="resend_verification"),
]
