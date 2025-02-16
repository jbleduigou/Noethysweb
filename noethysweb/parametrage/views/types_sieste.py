# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy, reverse
from core.views.mydatatableview import MyDatatable, columns, helpers
from core.views import crud
from core.models import TypeSieste
from parametrage.forms.types_sieste import Formulaire


class Page(crud.Page):
    model = TypeSieste
    url_liste = "types_sieste_liste"
    url_ajouter = "types_sieste_ajouter"
    url_modifier = "types_sieste_modifier"
    url_supprimer = "types_sieste_supprimer"
    description_liste = "Voici ci-dessous la liste des types de sieste."
    description_saisie = "Saisissez toutes les informations concernant le type de sieste à saisir et cliquez sur le bouton Enregistrer."
    objet_singulier = "un type de sieste"
    objet_pluriel = "des types de sieste"
    boutons_liste = [
        {"label": "Ajouter", "classe": "btn btn-success", "href": reverse_lazy(url_ajouter), "icone": "fa fa-plus"},
    ]


class Liste(Page, crud.Liste):
    model = TypeSieste

    def get_queryset(self):
        return TypeSieste.objects.filter(self.Get_filtres("Q"))

    def get_context_data(self, **kwargs):
        context = super(Liste, self).get_context_data(**kwargs)
        context['impression_introduction'] = ""
        context['impression_conclusion'] = ""
        context['afficher_menu_brothers'] = True
        return context

    class datatable_class(MyDatatable):
        filtres = ["idtype", "nom"]
        actions = columns.TextColumn("Actions", sources=None, processor='Get_actions_standard')

        class Meta:
            structure_template = MyDatatable.structure_template
            columns = ["idtype_sieste", "nom"]
            ordering = ["nom"]


class Ajouter(Page, crud.Ajouter):
    form_class = Formulaire

class Modifier(Page, crud.Modifier):
    form_class = Formulaire

class Supprimer(Page, crud.Supprimer):
    pass
