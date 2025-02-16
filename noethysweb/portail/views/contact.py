# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import logging
logger = logging.getLogger(__name__)
from portail.views.base import CustomView
from django.views.generic import TemplateView
from core.models import Structure, PortailMessage
from django.db.models import Q, Count


class View(CustomView, TemplateView):
    menu_code = "portail_contact"
    template_name = "portail/contact.html"

    def get_context_data(self, **kwargs):
        context = super(View, self).get_context_data(**kwargs)
        context['page_titre'] = "Contact"

        # Importation de toutes les structures
        context['liste_structures'] = Structure.objects.all().order_by("nom")

        # Importation du nombre de messages non lus (regroupement par structure)
        context['dict_messages_non_lus'] = {valeur["structure"]: valeur["nbre"] for valeur in PortailMessage.objects.values("structure").filter(famille=self.request.user.famille, utilisateur__isnull=False, date_lecture__isnull=True).annotate(nbre=Count('pk'))}

        return context
