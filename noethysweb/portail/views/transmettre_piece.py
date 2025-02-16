# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import logging, datetime
logger = logging.getLogger(__name__)
from django.urls import reverse_lazy
from core.views import crud
from core.models import PortailMessage
from portail.forms.transmettre_piece import Formulaire
from portail.views.base import CustomView


class Page(CustomView):
    model = PortailMessage
    menu_code = "portail_documents"

    def get_context_data(self, **kwargs):
        context = super(Page, self).get_context_data(**kwargs)
        context['page_titre'] = "Transmettre un document"
        context['box_titre'] = None
        context['box_introduction'] = "Renseignez les caractéristiques du document et cliquez sur le bouton Envoyer."
        return context

    def get_success_url(self):
        return reverse_lazy("portail_documents")


class Ajouter(Page, crud.Ajouter):
    form_class = Formulaire
    texte_confirmation = "Le document a bien été transmis"
    titre_historique = "Ajouter une pièce"

    def Get_detail_historique(self, instance):
        return "Famille=%s, Pièce=%s" % (instance.famille, instance.Get_nom())
