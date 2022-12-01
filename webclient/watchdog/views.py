from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from core.message_constants import WATCHDOG_CREATED_SUCCESSFULLY, WATCHDOG_DELETED_SUCCESSFULLY
from uzivatel.models import User
from django.views.generic.edit import CreateView
from .models import Watchdog
from .forms import WatchdogCreateForm
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from heslar.models import RuianKraj, RuianOkres

KRAJ_CONTENT_TYPE = 'ruiankraj'
OKRES_CONTENT_TYPE = 'ruianokres'
ALLOWED_ROLES = ['admin', 'archeolog', 'archivar']


class WatchdogCreateView(CreateView):
    def get(self, request, *args, **kwargs):
        context = {'form': WatchdogCreateForm}
        return render(request, 'watchdog/watchdog_create.html', context=context)

    def post(self, request, *args, **kwargs):
        form = WatchdogCreateForm(request.POST)
        if form.is_valid():
            if (request.user.hlavni_role.name.lower() in ALLOWED_ROLES):
                self.store(form, user=request.user)
                messages.add_message(request, messages.SUCCESS, WATCHDOG_CREATED_SUCCESSFULLY)
                return render(request, "watchdog/watchdog_create.html", {'form': form})
            else:
                form._errors['kraj'] = form.error_class([_('Pro tento požadavek nemáte práva')])
                return render(request, "watchdog/watchdog_create.html", {'form': form})
        else:
            return render(request, "watchdog/watchdog_create.html", {'form': form})

    def store(self, form, user):
        kraj_id = form.cleaned_data['kraj']
        okres_id = form.cleaned_data['okres']
        model = None
        if (int(kraj_id) > 0):
            model = RuianKraj.objects.get(pk=kraj_id)
        if (int(okres_id) > 0):
            model = RuianOkres.objects.get(pk=okres_id)
        content_type = ContentType.objects.get_for_model(model=model)
        watchdog = Watchdog(content_type=content_type, object_id=model.pk, user=user)
        watchdog.save()


@login_required
def list(request):
    watchdogs = Watchdog.objects.filter(user=request.user)
    return render(request, "watchdog/watchdog_list.html", {"watchdogs": watchdogs})


@login_required
def delete(request, pk, *args, **kwargs):
    Watchdog.objects.filter(user=request.user, pk=pk).delete()
    messages.add_message(request, messages.SUCCESS, WATCHDOG_DELETED_SUCCESSFULLY)
    watchdogs = Watchdog.objects.filter(user=request.user)
    return render(request, "watchdog/watchdog_list.html", {"watchdogs": watchdogs})
