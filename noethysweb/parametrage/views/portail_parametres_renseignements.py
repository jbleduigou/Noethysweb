# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy
from django.core.cache import cache
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from parametrage.forms.portail_parametres_renseignements import Formulaire
from core.views.base import CustomView
from core.models import PortailChamp


class Modifier(CustomView, TemplateView):
    template_name = "core/crud/edit.html"
    compatible_demo = False

    def get_context_data(self, **kwargs):
        context = super(Modifier, self).get_context_data(**kwargs)
        context['page_titre'] = "Paramètres des renseignements du portail"
        context['box_titre'] = "Paramètres d'affichage"
        context['box_introduction'] = "Cochez les champs à afficher sur le portail pour chaque type de public et cliquez sur le bouton Enregistrer."
        context['form'] = context.get("form", Formulaire)
        return context

    def post(self, request, **kwargs):
        form = Formulaire(request.POST, request=self.request)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        # Enregistrement
        for champ, valeur in form.cleaned_data.items():
            page, code = champ.split(":")
            valeurs = {}
            for public in ("famille", "representant", "enfant", "contact"):
                valeurs[public] = "AFFICHER" if public in valeur else "MASQUER"
            PortailChamp.objects.update_or_create(page=page, code=code, defaults=valeurs)

        # Nettoyage du cache
        cache.delete("parametres_portail_champs")

        return HttpResponseRedirect(reverse_lazy("parametrage_toc"))
