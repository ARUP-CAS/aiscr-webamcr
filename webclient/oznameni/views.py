from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import OznamovatelForm, ProjektOznameniForm


@require_http_methods(["GET", "POST"])
def index(request):

    if request.method == "POST":
        form_oznamovatel = OznamovatelForm(request.POST)
        form_projekt = ProjektOznameniForm(request.POST)

        if form_oznamovatel.is_valid() and form_projekt.is_valid():
            pass
    else:
        form_oznamovatel = OznamovatelForm()
        form_projekt = ProjektOznameniForm()

    return render(
        request,
        "oznameni/index.html",
        {"form_oznamovatel": form_oznamovatel, "form_projekt": form_projekt},
    )
