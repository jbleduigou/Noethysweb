# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy, reverse
from core.views.mydatatableview import MyDatatable, columns, helpers
from core.views import crud
from core.models import Assurance
from fiche_individu.forms.individu_assurances import Formulaire
from fiche_individu.views.individu import Onglet
from django.db.models import Q


class Page(Onglet):
    model = Assurance
    url_liste = "individu_assurances_liste"
    url_ajouter = "individu_assurances_ajouter"
    url_modifier = "individu_assurances_modifier"
    url_supprimer = "individu_assurances_supprimer"
    description_liste = "Saisissez ici les assurances de l'individu."
    description_saisie = "Saisissez toutes les informations concernant l'assurance et cliquez sur le bouton Enregistrer."
    objet_singulier = "une assurance"
    objet_pluriel = "des assurances"

    def get_context_data(self, **kwargs):
        """ Context data spécial pour onglet """
        context = super(Page, self).get_context_data(**kwargs)
        if not hasattr(self, "verbe_action"):
            context['box_titre'] = "Assurances"
        context['onglet_actif'] = "assurances"
        context['boutons_liste'] = [
            {"label": "Ajouter", "classe": "btn btn-success", "href": reverse_lazy(self.url_ajouter, kwargs={'idindividu': self.Get_idindividu(), 'idfamille': self.kwargs.get('idfamille', None)}), "icone": "fa fa-plus"},
        ]
        return context

    def get_form_kwargs(self, **kwargs):
        """ Envoie l'idindividu au formulaire """
        form_kwargs = super(Page, self).get_form_kwargs(**kwargs)
        form_kwargs["idindividu"] = self.Get_idindividu()
        form_kwargs["idfamille"] = self.Get_idfamille()
        return form_kwargs

    def get_success_url(self):
        """ Renvoie vers la liste après le formulaire """
        url = self.url_liste
        if "SaveAndNew" in self.request.POST:
            url = self.url_ajouter
        return reverse_lazy(url, kwargs={'idindividu': self.Get_idindividu(), 'idfamille': self.kwargs.get('idfamille', None)})



class Liste(Page, crud.Liste):
    model = Assurance
    template_name = "fiche_individu/individu_liste.html"

    def get_queryset(self):
        return Assurance.objects.select_related("assureur").filter(Q(individu=self.Get_idindividu()) & Q(famille=self.Get_idfamille()) & self.Get_filtres("Q"))

    def get_context_data(self, **kwargs):
        context = super(Liste, self).get_context_data(**kwargs)
        context['impression_introduction'] = ""
        context['impression_conclusion'] = ""
        return context

    class datatable_class(MyDatatable):
        filtres = ["idassurance", "assureur__nom", "num_contrat", "date_debut", "date_fin"]
        actions = columns.TextColumn("Actions", sources=None, processor='Get_actions_speciales')

        class Meta:
            structure_template = MyDatatable.structure_template
            columns = ["idassurance", "assureur", "num_contrat", "date_debut", "date_fin"]
            ordering = ["date_debut"]
            processors = {
                'date_debut': helpers.format_date('%d/%m/%Y'),
                'date_fin': helpers.format_date('%d/%m/%Y'),
            }

        def Get_actions_speciales(self, instance, *args, **kwargs):
            """ Inclut l'idindividu dans les boutons d'actions """
            view = kwargs["view"]
            # Récupération idindividu et idfamille
            kwargs = view.kwargs
            # Ajoute l'id de la ligne
            kwargs["pk"] = instance.pk
            html = [
                self.Create_bouton_modifier(url=reverse(view.url_modifier, kwargs=kwargs)),
                self.Create_bouton_supprimer(url=reverse(view.url_supprimer, kwargs=kwargs)),
            ]
            return self.Create_boutons_actions(html)



class Ajouter(Page, crud.Ajouter):
    form_class = Formulaire
    template_name = "fiche_individu/individu_edit.html"

class Modifier(Page, crud.Modifier):
    form_class = Formulaire
    template_name = "fiche_individu/individu_edit.html"

class Supprimer(Page, crud.Supprimer):
    template_name = "fiche_individu/individu_delete.html"
