# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy
from core.views import crud
from core.models import Individu
from fiche_individu.forms.individu_coords import Formulaire
from fiche_individu.views.individu import Onglet
from django.http import JsonResponse
import requests, json
import urllib.parse


def Get_coords_gps(request):
    rue = request.POST.get("rue")
    cp = request.POST.get("cp")
    ville = request.POST.get("ville")
    try:
        adresse = "%s %s %s" % (rue, cp, ville)
        req = requests.get("https://api-adresse.data.gouv.fr/search/?q=" + urllib.parse.quote(adresse))
        resultat = json.loads(req.content.decode('unicode_escape'))
        coords = resultat["features"][0]["geometry"]["coordinates"]
        coords = {"lon": coords[0], "lat": coords[1]}
    except:
        return JsonResponse({"erreur": "Localisation introuvable"}, status=401)
    return JsonResponse({"coords": json.dumps(coords)})



class Modifier(Onglet, crud.Modifier):
    form_class = Formulaire
    template_name = "fiche_individu/individu_edit.html"

    def get_context_data(self, **kwargs):
        context = super(Modifier, self).get_context_data(**kwargs)
        context['box_titre'] = "Coordonnées"
        context['box_introduction'] = "Renseignez les coordonnées de l'individu."
        context['onglet_actif'] = "coords"
        return context

    def get_success_url(self):
        # MAJ des infos des familles rattachées
        self.Maj_infos_famille()
        return reverse_lazy("individu_resume", kwargs={'idindividu': self.kwargs['idindividu'], 'idfamille': self.kwargs.get('idfamille', None)})

    def get_object(self):
        return Individu.objects.get(pk=self.kwargs['idindividu'])

    def get_form_kwargs(self, **kwargs):
        """ Envoie l'idfamille au formulaire """
        form_kwargs = super(Modifier, self).get_form_kwargs(**kwargs)
        form_kwargs["idfamille"] = self.Get_idfamille()
        return form_kwargs
