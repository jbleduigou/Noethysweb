# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy
from core.views import crud
from core.models import PortailRenseignement, Assurance
from portail.forms.individu_assurances import Formulaire
from portail.views.fiche import Onglet, ConsulterBase
from django.views.generic import TemplateView


class Page(Onglet):
    model = Assurance
    url_liste = "portail_individu_assurances"
    url_ajouter = "portail_individu_assurances_ajouter"
    url_modifier = "portail_individu_assurances_modifier"
    url_supprimer = "portail_individu_assurances_supprimer"
    description_liste = "Cliquez sur le bouton Ajouter au bas de la page pour ajouter une nouvelle assurance."
    description_saisie = "Saisissez les informations concernant l'assurance et cliquez sur le bouton Enregistrer."
    objet_singulier = "une assurance"
    objet_pluriel = "des assurances"
    onglet_actif = "individu_assurances"
    categorie = "individu_assurances"


    def get_context_data(self, **kwargs):
        """ Context data spécial pour onglet """
        context = super(Page, self).get_context_data(**kwargs)
        context['onglet_actif'] = self.onglet_actif
        if not self.get_dict_onglet_actif().validation_auto:
            context['box_introduction'] = self.description_saisie + " Ces informations devront être validées par l'administrateur de l'application."
        return context

    def get_object(self):
        if not self.kwargs.get("idassurance"):
            return None
        return Assurance.objects.get(pk=self.kwargs.get("idassurance"))

    def get_success_url(self):
        url = self.url_liste
        if "SaveAndNew" in self.request.POST:
            url = self.url_ajouter
        return reverse_lazy(url, kwargs={'idrattachement': self.kwargs['idrattachement']})


class Liste(Page, TemplateView):
    model = Assurance
    template_name = "portail/individu_assurances.html"

    def get_context_data(self, **kwargs):
        context = super(Liste, self).get_context_data(**kwargs)
        context['box_titre'] = "Assurances"
        context['box_introduction'] = "Cliquez sur le bouton Ajouter au bas de la page pour ajouter une nouvelle assurance."
        context['liste_assurances'] = Assurance.objects.filter(famille=self.get_rattachement().famille, individu=self.get_rattachement().individu).order_by("-date_debut")
        return context


class Ajouter(Page, crud.Ajouter):
    form_class = Formulaire
    template_name = "portail/fiche_edit.html"

class Modifier(Page, crud.Modifier):
    form_class = Formulaire
    template_name = "portail/fiche_edit.html"

class Supprimer(Page, crud.Supprimer):
    template_name = "portail/fiche_delete.html"
