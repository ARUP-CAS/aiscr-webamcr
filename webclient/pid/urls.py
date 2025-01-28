from django.urls import path

from . import views

app_name = "pid"

urlpatterns = [
    path("doi-autocomplete", views.DoiAutocompleteView.as_view(), name="doi-autocomplete"),
    path("orcid-autocomplete", views.OrcidAutocompleteView.as_view(), name="orcid-autocomplete"),
    path("ror-autocomplete", views.RorAutocompleteView.as_view(), name="ror-autocomplete"),
    path("wikidata-autocomplete", views.WikiDataAutocompleteView.as_view(), name="wikidata-autocomplete"),
    path(
        "continue-processing/<str:job_id>/<str:performed_action>",
        views.ContinuePidProcessing.as_view(),
        name="continue-processing",
    ),
]
