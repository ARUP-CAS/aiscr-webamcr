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
from django.urls import include, path
from uzivatel.views import UserRegistrationView, UserLoginView

urlpatterns = [
    # path("admin/", admin.site.urls),
    # path("", include("core.urls")),
    # path("heslar/", include("heslar.urls")),
    # path("oznameni/", include("oznameni.urls")),
    # path("pian/", include("pian.urls")),
    # path("projekt/", include("projekt.urls")),
    # path("pas/", include("pas.urls")),
    # path("arch_z/", include("arch_z.urls")),
    # path("uzivatel/", include("uzivatel.urls")),
    # path("dokument/", include("dokument.urls")),
    # path("nalez/", include("nalez.urls")),
    # path("adb/", include("adb.urls")),
    # path("komponenta/", include("komponenta.urls")),
    # path("dj/", include("dj.urls")),
    # path("historie/", include("historie.urls")),
    # path(
    #     "accounts/register/",
    #     UserRegistrationView.as_view(),
    #     name="django_registration_register",
    # ),
    # path("accounts/", include("django_registration.backends.activation.urls")),
    # path(
    #     "accounts/login/",
    #     UserLoginView.as_view(),
    #     name="django_authentication_login",
    # ),
    # path("accounts/", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
