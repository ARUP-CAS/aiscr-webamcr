import logging
from functools import wraps

from core.repository_connector import FedoraError
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)


def handle_fedora_error(view_func):
    @wraps(view_func)
    def _wrapped(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except FedoraError as err:
            logger.info("fedora_management.decorators.handle_fedora_error", extra={"error": err})
            if err.fedora_transaction:
                err.fedora_transaction.rollback_transaction()
            transaction.set_rollback(True)
            if err.redirect or err.redirect_url:
                if err.redirect_url:
                    return redirect(err.redirect_url)
                if err.ident_cely:
                    return redirect(reverse("core:redirect_ident", kwargs={"ident_cely": err.ident_cely}))

    return _wrapped
