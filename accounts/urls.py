from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("register/", views.register, name="register"),
    path("login/", views.VestLoginView.as_view(), name="login"),
    path("logout/", views.VestLogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("profile/kyc/", views.kyc_submit, name="kyc_submit"),
]
