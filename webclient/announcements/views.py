from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import AnnouncementForm


@require_http_methods(["GET", "POST"])
def announce(request):

    if request.method == "POST":
        form = AnnouncementForm(request.POST)

        if form.is_valid():
            pass
    else:
        form = AnnouncementForm()

    return render(request, "announcements/announce.html", {"form": form})
