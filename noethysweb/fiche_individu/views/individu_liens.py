# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy
from fiche_individu.forms.individu_liens import Formulaire
from fiche_individu.views.individu import Onglet
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from core.models import Lien
from core.data.data_liens import DICT_TYPES_LIENS


class Modifier(Onglet, TemplateView):
    template_name = "fiche_individu/individu_edit.html"

    def get_context_data(self, **kwargs):
        context = super(Modifier, self).get_context_data(**kwargs)
        context['box_titre'] = "Liens"
        context['box_introduction'] = "Renseignez les liens de l'individu avec les autres membres de la famille."
        context['onglet_actif'] = "liens"
        context['form'] = Formulaire(idfamille=self.kwargs['idfamille'], idindividu=self.kwargs['idindividu'])
        return context

    def post(self, request, **kwargs):
        form = Formulaire(request.POST, idfamille=self.kwargs['idfamille'], idindividu=self.kwargs['idindividu'])
        if form.is_valid() == False:
            return self.render_to_response(self.get_context_data(form=form))

        # Récupération des données du formulaire
        dict_liens = {}
        for key, valeur in form.cleaned_data.items():
            idindividu, type_valeur = key.split("-")
            idindividu = int(idindividu)
            dict_liens.setdefault(idindividu, {})
            dict_liens[idindividu][type_valeur] = int(valeur) if valeur else None

        # Analyse des liens
        for idindividu, valeurs in dict_liens.items():
            IDtype_lien = valeurs["lien"]
            autorisation = valeurs["autorisation"]

            # Sauvegarde du lien
            objet, created = Lien.objects.update_or_create(
                famille_id=self.kwargs['idfamille'], individu_sujet_id=idindividu, individu_objet_id=self.kwargs['idindividu'],
                defaults={"idtype_lien": IDtype_lien, "autorisation": autorisation}
            )

            # Application du lien inverse à l'autre individu
            lien_inverse = DICT_TYPES_LIENS[IDtype_lien]["lien"] if IDtype_lien else None

            objet, created = Lien.objects.update_or_create(
                famille_id=self.kwargs['idfamille'], individu_sujet_id=self.kwargs['idindividu'], individu_objet_id=idindividu,
                defaults={"idtype_lien": lien_inverse, "autorisation": None}
            )

        return HttpResponseRedirect(reverse_lazy("individu_resume", args=(self.kwargs['idfamille'], self.kwargs['idindividu'])))
