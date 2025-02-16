# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.core.cache import cache
from core.models import PortailParametre
from portail.utils import utils_champs


class Onglet():
    def __init__(self, *args, **kwargs):
        self.code = kwargs.get("code", None)
        self.label = kwargs.get("label", None)
        self.icone = kwargs.get("icone", None)
        self.url = kwargs.get("url", None)
        self.validation_auto = kwargs.get("validation_auto", True)

    def __repr__(self):
        return self.code

LISTE_ONGLETS = [
    Onglet(code="famille_caisse", label="Caisse", icone="fa-institution", url="portail_famille_caisse", validation_auto=False),
    Onglet(code="individu_identite", label="Identité", icone="fa-user", url="portail_individu_identite", validation_auto=False),
    Onglet(code="individu_questionnaire", label="Questionnaire", icone="fa-question", url="portail_individu_questionnaire", validation_auto=True),
    Onglet(code="individu_coords", label="Coordonnées", icone="fa-map-marker", url="portail_individu_coords", validation_auto=False),
    Onglet(code="individu_regimes_alimentaires", label="Régimes alimentaires", icone="fa-cutlery", url="portail_individu_regimes_alimentaires", validation_auto=False),
    Onglet(code="individu_maladies", label="Maladies", icone="fa-stethoscope", url="portail_individu_maladies", validation_auto=False),
    Onglet(code="individu_medecin", label="Médecin", icone="fa-user-md", url="portail_individu_medecin", validation_auto=False),
    Onglet(code="individu_vaccinations", label="Vaccinations", icone="fa-medkit", url="portail_individu_vaccinations", validation_auto=True),
    Onglet(code="individu_infos_medicales", label="Informations médicales", icone="fa-heartbeat", url="portail_individu_infos_medicales", validation_auto=True),
    Onglet(code="individu_assurances", label="Assurances", icone="fa-shield", url="portail_individu_assurances", validation_auto=True),
    Onglet(code="individu_contacts", label="Contacts", icone="fa-phone", url="portail_individu_contacts", validation_auto=True),
]

def Get_onglets(categorie=None):
    # Récupère la liste des champs actifs
    if categorie == 1: categorie = "representant"
    if categorie == 2: categorie = "enfant"
    if categorie == 3: categorie = "contact"
    liste_champs = []
    for champ in utils_champs.Get_liste_champs():
        if getattr(champ, categorie) != "MASQUER":
            liste_champs.append(champ)
    # Récupère la liste des onglets actifs
    liste_onglets = []
    onglets_actifs = list(set([champ.page for champ in liste_champs]))
    if categorie != "famille":
        categorie = "individu"
    for onglet in LISTE_ONGLETS:
        if onglet.code.startswith(categorie) and onglet.code in onglets_actifs:
            liste_onglets.append(onglet)
    return liste_onglets

def Get_onglet(code=""):
    for onglet in LISTE_ONGLETS:
        if onglet.code == code:
            # Récupération de la valeur validation_auto de l'onglet
            code_parametre = "validation_auto:%s" % onglet.code
            parametres_portail = cache.get('parametres_portail')
            if parametres_portail:
                validation_auto = parametres_portail.get(code_parametre)
            else:
                validation_auto = PortailParametre.objects.get(code=code_parametre).valeur
            onglet.validation_auto = validation_auto in ("True", True)
            return onglet
    return None
