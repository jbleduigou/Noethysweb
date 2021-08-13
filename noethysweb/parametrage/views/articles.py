# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy
from core.views.mydatatableview import MyDatatable, columns, helpers
from core.views import crud
from core.models import Article
from parametrage.forms.articles import Formulaire


class Page(crud.Page):
    model = Article
    url_liste = "articles_liste"
    url_ajouter = "articles_ajouter"
    url_modifier = "articles_modifier"
    url_supprimer = "articles_supprimer"
    description_liste = "Voici ci-dessous la liste des articles à afficher sur le portail."
    description_saisie = "Saisissez toutes les informations concernant l'article et cliquez sur le bouton Enregistrer."
    objet_singulier = "un article"
    objet_pluriel = "des articles"
    boutons_liste = [
        {"label": "Ajouter", "classe": "btn btn-success", "href": reverse_lazy(url_ajouter), "icone": "fa fa-plus"},
    ]


class Liste(Page, crud.Liste):
    model = Article

    def get_queryset(self):
        return Article.objects.filter(self.Get_filtres("Q"), self.Get_condition_structure())

    def get_context_data(self, **kwargs):
        context = super(Liste, self).get_context_data(**kwargs)
        context['impression_introduction'] = ""
        context['impression_conclusion'] = ""
        context['afficher_menu_brothers'] = True
        return context

    class datatable_class(MyDatatable):
        filtres = ["idarticle", "titre", "date_debut", "date_fin"]
        actions = columns.TextColumn("Actions", sources=None, processor='Get_actions_standard')
        statut = columns.TextColumn("Statut", sources=["statut"], processor='Get_statut')

        class Meta:
            structure_template = MyDatatable.structure_template
            columns = ["idarticle", "titre", "date_debut", "date_fin", "statut"]
            ordering = ["date_debut"]
            processors = {
                "date_debut": helpers.format_date("%d/%m/%Y %H:%M"),
                "date_fin": helpers.format_date("%d/%m/%Y %H:%M"),
                "statut": "Get_statut",
            }

        def Get_statut(self, instance, *args, **kwargs):
            if instance.statut == "publie":
                return "<small class='badge badge-success'>Publié</small>"
            else:
                return "<small class='badge badge-danger'>Non publié</small>"


class Ajouter(Page, crud.Ajouter):
    form_class = Formulaire

class Modifier(Page, crud.Modifier):
    form_class = Formulaire

class Supprimer(Page, crud.Supprimer):
    pass
