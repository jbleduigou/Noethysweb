# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy
from core.views import crud
from core.models import Individu, Famille
from fiche_individu.forms.individu_identite import Formulaire
from fiche_individu.views.individu import Onglet



class Modifier(Onglet, crud.Modifier):
    form_class = Formulaire
    template_name = "fiche_individu/individu_edit.html"

    def get_context_data(self, **kwargs):
        context = super(Modifier, self).get_context_data(**kwargs)
        context['box_titre'] = "Identité"
        context['box_introduction'] = "Renseignez les informations concernant l'identité de l'individu."
        context['onglet_actif'] = "identite"
        return context

    def get_success_url(self):
        # MAJ des infos des familles rattachées
        self.Maj_infos_famille()
        return reverse_lazy("individu_resume", kwargs={'idindividu': self.kwargs['idindividu'], 'idfamille': self.kwargs.get('idfamille', None)})

    def get_object(self):
        return Individu.objects.get(pk=self.kwargs['idindividu'])
