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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path, URLPattern, URLResolver
from django.utils.decorators import method_decorator
from core.decorators import odstavka_in_progress
from django.views.generic import TemplateView

from oznameni import views as oznameni_views
from uzivatel.views import UserRegistrationView, UserLoginView, UserLogoutView, UserActivationView, UserPasswordResetView

import django_registration.backends.activation.urls as reg_urls

def apply_decorators_to_included_urls(urlpatterns, decorator):
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):  # if the pattern is a view
            pattern.callback = decorator(pattern.callback)
        elif isinstance(pattern, URLResolver):  # if the pattern includes other patterns
            apply_decorators_to_included_urls(pattern.url_patterns, decorator)

# Get the URL patterns from the external library
registration_patterns = reg_urls.urlpatterns

# Apply the CSRF exemption decorator to all views in the included URL patterns
apply_decorators_to_included_urls(registration_patterns, method_decorator(odstavka_in_progress, name='dispatch'))


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("heslar/", include("heslar.urls")),
    path("oznameni/", include("oznameni.urls")),
    path("pian/", include("pian.urls")),
    path("projekt/", include("projekt.urls")),
    path(
        "projekt/oznamovatel/edit/<str:ident_cely>", oznameni_views.edit, name="oznameni_edit"
    ),
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
        TemplateView.as_view(
            template_name="django_registration/activation_complete.html"
        ),
        name="django_registration_activation_complete",
    ),
    path("accounts/activate/<str:activation_key>/", UserActivationView.as_view()),
    path('accounts/', include((registration_patterns, 'django_registration'), namespace='django_registration')),
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
    path("notifikace-projekty/",  include("notifikace_projekty.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
]
urlpatterns+=[re_path(r'^healthcheck/', include("healthcheck.urls"))]

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [re_path(r"^rosetta/", include("rosetta.urls"))]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
