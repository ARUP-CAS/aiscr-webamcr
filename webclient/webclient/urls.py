"""webclient URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from core.decorators import odstavka_in_progress
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from oznameni import views as oznameni_views
from uzivatel.views import (
    UserActivationView,
    UserLoginView,
    UserLogoutView,
    UserPasswordResetView,
    UserRegistrationView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("heslar/", include("heslar.urls")),
    path("oznameni/", include("oznameni.urls")),
    path("pian/", include("pian.urls")),
    path("projekt/", include("projekt.urls")),
    path("projekt/oznamovatel/edit/<str:ident_cely>", oznameni_views.edit, name="oznameni_edit"),
    path("pas/", include("pas.urls")),
    path("arch-z/", include("arch_z.urls")),
    path("", include("uzivatel.urls")),
    path("dokument/", include("dokument.urls")),
    path("nalez/", include("nalez.urls")),
    path("adb/", include("adb.urls")),
    path("komponenta/", include("komponenta.urls")),
    path("dj/", include("dj.urls")),
    path("historie/", include("historie.urls")),
    path(
        "accounts/register/",
        UserRegistrationView.as_view(),
        name="django_registration_register",
    ),
    path(
        "accounts/activate/complete/",
        odstavka_in_progress(TemplateView.as_view(template_name="django_registration/activation_complete.html")),
        name="django_registration_activation_complete",
    ),
    path(
        "accounts/register/complete/",
        odstavka_in_progress(TemplateView.as_view(template_name="django_registration/registration_complete.html")),
        name="django_registration_complete",
    ),
    path(
        "accounts/register/closed/",
        odstavka_in_progress(TemplateView.as_view(template_name="django_registration/registration_closed.html")),
        name="django_registration_disallowed",
    ),
    path("accounts/activate/<str:activation_key>/", UserActivationView.as_view(), name="django_registration_activate"),
    path(
        "accounts/login/",
        UserLoginView.as_view(),
        name="django_authentication_login",
    ),
    path(
        "accounts/logout/",
        UserLogoutView.as_view(),
        name="logout",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/password_reset", UserPasswordResetView.as_view(), name="password_reset"),
    path("arch-z/lokalita/", include("lokalita.urls")),
    path("ext-zdroj/", include("ez.urls")),
    path("neident-akce/", include("neidentakce.urls")),
    path("notifikace-projekty/", include("notifikace_projekty.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
]
urlpatterns += [re_path(r"^healthcheck/", include("healthcheck.urls"))]

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [re_path(r"^rosetta/", include("rosetta.urls"))]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
