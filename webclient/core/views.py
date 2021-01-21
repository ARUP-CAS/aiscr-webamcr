from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
@login_required
def index(request):
    current_user = request.user

    return HttpResponse("Welcome to home page " + current_user.first_name)
