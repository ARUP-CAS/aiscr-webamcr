import requests
from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse


class ApiView(autocomplete.Select2ListView):
    API_URL = None

    def get(self, request, *args, **kwargs):
        if self.q:
            results = self.get_list()
            results = self.autocomplete_results(results)
            return JsonResponse({"results": results})
        else:
            return JsonResponse({"results": []})

    def autocomplete_results(self, results):
        return [dict(id=x, text=y) for x, y in results]


class DoiAutocompleteView(LoginRequiredMixin, ApiView):
    API_URL = "https://api.test.datacite.org/dois"

    def get_list(self):
        params = {
            "query": f"doi:*{self.q.upper()}*",
        }
        results = []
        response = requests.get(self.API_URL, params=params)
        if response.status_code == 200:
            response = response.json()
            data = response.get("data", [])
            for record in data:
                title = record.get("attributes").get("titles")[0].get("title") or record.get("id")
                results.append([record.get("id"), title])
        return results


class OrcidAutocompleteView(LoginRequiredMixin, ApiView):
    API_URL = "https://pub.orcid.org/v3.0/expanded-search"
    HEADERS = {"Accept": "application/json", "User-Agent": "Python-Requests"}

    def get_list(self):
        params = {
            "q": f"{self.q}",
        }

        result_list = []
        response = requests.get(self.API_URL, headers=self.HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()

            for result in data.get("expanded-result", []):
                orcid_id = result.get("orcid-id", "")
                if result.get("family-names") and result.get("given-names"):
                    full_nane = f"{result['family-names']}, {result['given-names']} ({orcid_id})"
                else:
                    full_nane = orcid_id
                result_list.append([orcid_id, full_nane])

        return result_list
