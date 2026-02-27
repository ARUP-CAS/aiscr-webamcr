import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from .config import get_config
from .fields import RepeatableSectionNameWithAccessor, SectionNameWithAccessor, SubSectionField, get_model

logger = logging.getLogger(__name__)


def add_section_data(instance, section, fields, sections_data, iterator=False, user=None):
    """Zajišťuje logiku funkce ``add_section_data``.
    
    :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
    :param section: Vstupní hodnota parametru ``section`` použitého při zpracování.
    :param fields: Vstupní hodnota parametru ``fields`` použitého při zpracování.
    :param sections_data: Vstupní hodnota parametru ``sections_data`` použitého při zpracování.
    :param iterator: Vstupní hodnota parametru ``iterator`` použitého při zpracování.
    :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    if fields["section_name"].get_permission(instance, user) is False:
        return None
    if isinstance(fields["section_name"], RepeatableSectionNameWithAccessor) and not iterator:
        logger.debug(
            "vypis.views.add_section_data", extra={"custom_message": f"Processing repeatable section {section}"}
        )
        sections = fields["section_name"].get_sections(instance)
        if not sections:
            return None
        else:
            for section_instance in sections:
                try:
                    logger.debug(
                        "vypis.views.add_section_data",
                        extra={"custom_message": f"Adding section {section} for {section_instance.ident_cely}"},
                    )
                    add_section_data(
                        section_instance,
                        f"{section}_{section_instance.ident_cely}",
                        fields,
                        sections_data,
                        iterator=True,
                        user=user,
                    )
                except Exception:
                    add_section_data(
                        section_instance,
                        f"{section}_{section_instance.nazev}",
                        fields,
                        sections_data,
                        iterator=True,
                        user=user,
                    )
            return None
    if isinstance(fields["section_name"], SectionNameWithAccessor):
        if not fields["section_name"].get_name(instance):
            return None
    sections_data[section] = {}
    for label, field in fields.items():
        if isinstance(field, SubSectionField):
            logger.debug("vypis.views.add_section_data", extra={"custom_message": f"Processing sub section {label}"})
            if not field.get_instance(instance):
                continue
            add_section_data(
                field.get_instance(instance),
                f"{section}_{label}",
                field.get_config(),
                sections_data[section],
                iterator=False,
                user=user,
            )
            continue
        if label == "section_name" or label == "template":
            sections_data[section][label] = mark_safe(field.get_name(instance))
        elif field.get_value(instance, user):
            sections_data[section][label] = {"label": field.get_label(), "value": field.get_value(instance, user)}
    if not any(k not in ["section_name", "template"] for k in sections_data[section].keys()) and not iterator:
        logger.debug("vypis.views.add_section_data", extra={"custom_message": f"Deleting empty section {section}"})
        del sections_data[section]


class VypisView(LoginRequiredMixin, TemplateView):
    """Zapouzdřuje chování třídy ``VypisView`` pro modul ``webclient.vypis.views``."""
    template_name = "vypis/vypis.html"

    def get_context_data(self, **kwargs):
        """Zajišťuje logiku funkce ``get_context_data``.
        
        :param kwargs: Pojmenované argumenty předané voláním.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        context = super().get_context_data(**kwargs)
        name = kwargs.get("typ_vazby")
        ident_cely = kwargs.get("ident_cely")

        config = get_config(name)
        if not config:
            raise Http404("Page not found")

        model = get_model(name)
        if not model:
            raise Http404("Model not found")

        instance = get_object_or_404(model, ident_cely=ident_cely)
        main_sections = config["main_sections"]
        main_section_data = {}
        for section, fields in main_sections.items():
            main_section_data[section] = {}
            for label, field in fields.items():
                if label == "section_name" or label == "template":
                    main_section_data[section][label] = field.get_name(instance)
                else:
                    main_section_data[section][label] = {"label": field.get_label(), "value": field.get_value(instance)}

        sections = config["sections"]
        sections_data = {}
        for section, fields in sections.items():
            logger.debug("vypis.views.vypisView", extra={"custom_message": f"Processing section {section}"})
            add_section_data(instance, section, fields, sections_data, False, self.request.user)

        context.update(
            {"title": config["title"], "main_section_data": main_section_data, "sections_data": sections_data}
        )
        return context


class VypisOnlyView(VypisView):
    """Zapouzdřuje chování třídy ``VypisOnlyView`` pro modul ``webclient.vypis.views``."""
    template_name = "vypis/vypis_only.html"


class VypisListView(LoginRequiredMixin, TemplateView):
    """Zapouzdřuje chování třídy ``VypisListView`` pro modul ``webclient.vypis.views``."""
    template_name = "vypis/vypis_list.html"

    def get_context_data(self, **kwargs):
        """Zajišťuje logiku funkce ``get_context_data``.
        
        :param kwargs: Pojmenované argumenty předané voláním.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        context = super().get_context_data(**kwargs)
        name = kwargs.get("typ_vazby")
        config = get_config(name)
        if not config:
            raise Http404("Page not found")
        context["title"] = config["title"]
        return context
