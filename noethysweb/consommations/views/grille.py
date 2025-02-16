# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import logging
logger = logging.getLogger(__name__)
from django.http import JsonResponse
from django.contrib import messages
from core.models import Ouverture, Remplissage, UniteRemplissage, Vacance, Unite, Consommation, MemoJournee, Evenement, Groupe, Individu, \
                        Tarif, CombiTarif, TarifLigne, Quotient, Prestation, Aide, Deduction, CombiAide, Ferie, Individu, Activite, Classe
from core.utils import utils_dates, utils_dictionnaires, utils_db, utils_texte, utils_decimal, utils_historique
from consommations.utils import utils_consommations
from django.utils.safestring import mark_safe
from django.db.models import Q, Count
from django.core import serializers
import json, datetime, time, decimal, math, re, copy
from uuid import uuid4


def Get_individus(request):
    """ Renvoie une liste d'individus pour le Select2 """
    recherche = request.GET.get("term", "")
    liste_individus = []
    for individu in Individu.objects.all().filter(Q(nom__icontains=recherche) | Q(prenom__icontains=recherche)).order_by("nom", "prenom"):
        liste_individus.append({"id": individu.pk, "text": individu.Get_nom()})
    return JsonResponse({"results": liste_individus, "pagination": {"more": True}})


def Get_periode(data):
    # Récupération de la période
    listes_dates = []
    if data["periode"] and data["periode"]["periodes"]:
        conditions_periodes = Q()
        for p in data["periode"]["periodes"]:
            date_debut = utils_dates.ConvertDateENGtoDate(p.split(";")[0])
            date_fin = utils_dates.ConvertDateENGtoDate(p.split(";")[1])
            listes_dates.extend([date_debut, date_fin])
            conditions_periodes |= Q(date__gte=date_debut) & Q(date__lte=date_fin)
    else:
        d = datetime.date(3000, 1, 1)
        conditions_periodes = Q(date__gte=d) & Q(date__lte=d)
        listes_dates.extend([d, d])
    data["conditions_periodes"] = conditions_periodes

    # Récupération des dates extrêmes
    date_min, date_max = min(listes_dates), max(listes_dates)
    data["date_min"] = date_min
    data["date_max"] = date_max
    return data


def Get_generic_data(data={}):
    """ Renvoie les données communes à la grille des conso et au gestionnaire des conso """
    # Création de listes de données
    data["liste_individus"] = []
    data["liste_familles"] = []
    data["liste_key_individus"] = []
    for inscription in data["liste_inscriptions"]:
        if inscription.individu not in data["liste_individus"]: data["liste_individus"].append(inscription.individu)
        if inscription.famille not in data["liste_familles"]: data["liste_familles"].append(inscription.famille)
        key = (inscription.individu_id, inscription.famille_id)
        if key not in data["liste_key_individus"]: data["liste_key_individus"].append(key)

    # Permet de trouver les différences entre les inscriptions multiples d'un seul individu
    # Pour afficher le texte d'informations complémentaires des inscriptions
    dict_differences = {}
    for inscription in data["liste_inscriptions"]:
        dict_differences.setdefault(inscription.individu, {})
        dict_differences[inscription.individu].setdefault(inscription.activite, {"groupe": [], "famille": [], "categorie_tarif": []})
        if inscription.groupe not in dict_differences[inscription.individu][inscription.activite]["groupe"]: dict_differences[inscription.individu][inscription.activite]["groupe"].append(inscription.groupe)
        if inscription.famille not in dict_differences[inscription.individu][inscription.activite]["famille"]: dict_differences[inscription.individu][inscription.activite]["famille"].append(inscription.famille)
        if inscription.categorie_tarif not in dict_differences[inscription.individu][inscription.activite]["categorie_tarif"]: dict_differences[inscription.individu][inscription.activite]["categorie_tarif"].append(inscription.categorie_tarif)
    for inscription in data["liste_inscriptions"]:
        inscription.infos_diffentes = []
        for info in ("groupe", "famille", "categorie_tarif"):
            if len(dict_differences[inscription.individu][inscription.activite][info]) > 1:
                inscription.infos_diffentes.append(getattr(inscription, info).nom)
        inscription.infos_diffentes = " | ".join(inscription.infos_diffentes)

    # Regroupe les inscriptions par individu
    dict_resultats = {}
    for inscription in data["liste_inscriptions"]:
        key = (inscription.individu, inscription.famille_id)
        dict_resultats.setdefault(key, [])
        dict_resultats[key].append(inscription)
    data['dict_inscriptions_by_individu'] = dict_resultats

    #-------------------------- Importation des données des individus ------------------------------

    # Importation des consommations existantes
    if "liste_conso_json" not in data:
        liste_inscriptions = []
        # for key_individu, inscriptions in data['dict_inscriptions_by_individu'].items():
        #     liste_inscriptions.extend(inscriptions)
        liste_conso = Consommation.objects.select_related("inscription").filter(data["conditions_periodes"] & Q(inscription__in=data["liste_inscriptions"]))
        data["liste_conso"] = liste_conso
        data["liste_conso_json"] = serializers.serialize('json', liste_conso)

    # Importation des mémos journaliers
    liste_memos = MemoJournee.objects.filter(date__gte=data["date_min"], date__lte=data["date_max"], inscription__in=data["liste_inscriptions"])
    data['liste_memos_json'] = serializers.serialize('json', liste_memos)

    # Importation des déductions
    dict_deductions = {}
    for deduction in Deduction.objects.filter(famille_id__in=data["liste_familles"], date__gte=data["date_min"], date__lte=data["date_max"]):
        dict_deductions.setdefault(deduction.prestation_id, [])
        dict_deductions[deduction.prestation_id].append({"label": deduction.label, "date": str(deduction.date), "aide": deduction.aide_id, "montant": float(deduction.montant)})

    # Importation des prestations
    conditions = data["conditions_periodes"]
    if data["mode"] in ("individu", "portail"):
        conditions &= Q(famille_id=data["idfamille"]) & Q(individu__in=data["liste_individus"])
    liste_prestations = Prestation.objects.filter(conditions)
    for p in liste_prestations:
        if p.pk not in data["dict_suppressions"]["prestations"]:
            data["prestations"][p.pk] = {
                "date": str(p.date), "categorie": p.categorie, "label": p.label, "montant_initial": float(p.montant_initial),
                "montant": float(p.montant), "activite": p.activite_id, "tarif": p.tarif_id, "facture": p.facture_id,
                "famille": p.famille_id, "individu": p.individu_id, "categorie_tarif": p.categorie_tarif_id, "temps_facture": utils_dates.DeltaEnStr(p.temps_facture, separateur=":"),
                "quantite": p.quantite, "tva": float(p.tva) if p.tva else None, "code_compta": p.code_compta, "aides": [],
            }
            if p.pk in dict_deductions:
                data["prestations"][p.pk]["aides"] = dict_deductions[p.pk]

    data['dict_prestations_json'] = mark_safe(json.dumps(data["prestations"]))
    logger.debug("prestations=" + str(data['dict_prestations_json']))


    #-------------------------- Importation des données du calendrier ------------------------------

    # Importation des ouvertures
    liste_ouvertures = []
    liste_dates = []
    for ouverture in Ouverture.objects.filter(data["conditions_periodes"] & Q(activite=data['selection_activite'])):
        liste_ouvertures.append("%s_%s_%s" % (ouverture.date, ouverture.groupe_id, ouverture.unite_id))
        if ouverture.date not in liste_dates:
            liste_dates.append(ouverture.date)
    data['liste_ouvertures'] = liste_ouvertures

    # Récupération des dates
    liste_dates.sort()
    data['liste_dates'] = liste_dates

    # Importation des vacances
    liste_vacances = Vacance.objects.filter(date_fin__gte=data["date_min"], date_debut__lte=data["date_max"])
    data['liste_vacances'] = liste_vacances
    data['liste_vacances_json'] = mark_safe(json.dumps([(str(vac.date_debut), str(vac.date_fin)) for vac in liste_vacances]))

    # Importation des événements
    liste_evenements = Evenement.objects.filter(data["conditions_periodes"] & Q(activite=data['selection_activite'])).order_by("date", "heure_debut")
    data["liste_evenements_json"] = serializers.serialize('json', liste_evenements)
    data["liste_evenements"] = liste_evenements

    # Importation des remplissages
    liste_remplissage = Remplissage.objects.filter(data["conditions_periodes"] & Q(activite=data['selection_activite']))
    data['dict_capacite_json'] = mark_safe(json.dumps({'%s_%d_%d' % (r.date, r.unite_remplissage_id, r.groupe_id): r.places for r in liste_remplissage}))

    # Importation des unités de remplissage
    liste_unites_remplissage = UniteRemplissage.objects.prefetch_related('unites').filter(activite=data['selection_activite']).order_by("ordre")
    data['liste_unites_remplissage'] = liste_unites_remplissage

    # Prépare un dict unités de remplissage par unité de conso pour le dict des unités de conso
    dict_unites_remplissage_unites = {}
    dict_unites_remplissage_json = {}
    for unite in liste_unites_remplissage:
        for unite_conso in unite.unites.all():
            dict_unites_remplissage_json.setdefault(unite.pk, {"unites_conso": [], "seuil_alerte": unite.seuil_alerte})
            dict_unites_remplissage_json[unite.pk]["unites_conso"].append(unite_conso.pk)
            dict_unites_remplissage_unites.setdefault(unite_conso.pk, [])
            dict_unites_remplissage_unites[unite_conso.pk].append(unite.pk)
    data['dict_unites_remplissage_json'] = mark_safe(json.dumps(dict_unites_remplissage_json))

    # Importation des places prises
    liste_places = Consommation.objects.values('date', 'unite', 'groupe', 'quantite', 'evenement').annotate(nbre=Count('pk')).filter(data["conditions_periodes"] & Q(activite=data['selection_activite']) & Q(etat__in=("reservation", "present"))).exclude(inscription__in=data["liste_inscriptions"])
    dict_places = {}
    for p in liste_places:
        key = "%s_%d_%d" % (p["date"], p["unite"], p["groupe"])
        quantite = p["nbre"] * p["quantite"] if p["quantite"] else p["nbre"]
        dict_places[key] = quantite
    data['dict_places_json'] = mark_safe(json.dumps(dict_places))

    # Importation des groupes
    data['liste_groupes'] = Groupe.objects.filter(activite=data['selection_activite']).order_by("ordre")
    data['liste_groupes_json'] = serializers.serialize('json', data['liste_groupes'])

    # Sélection des groupes
    if data["mode"] in ("date", "pointeuse") and not data['selection_groupes']:
        data['selection_groupes'] = [groupe.pk for groupe in data['liste_groupes']]

    # Importation des unités de conso
    groupes_utilises = list({inscription.groupe: True for inscription in data['liste_inscriptions']}.keys()) + data.get("selection_groupes", [])
    conditions = (Q(groupes__in=groupes_utilises) | Q(groupes__isnull=True))
    data["liste_unites"] = Unite.objects.select_related('activite').prefetch_related('groupes', 'incompatibilites').filter(conditions, activite=data['selection_activite']).distinct().order_by("ordre")

    # Sélection des unités visibles
    data["liste_unites_visibles"] = [unite for unite in data["liste_unites"] if unite.visible_portail or data["mode"] != "portail"]

    # Conversion des unités de conso en JSON
    liste_unites_json = []
    for unite in data["liste_unites"]:
        liste_unites_json.append({"pk": unite.pk, "fields": {"activite": unite.activite_id, "nom": unite.nom, "abrege": unite.abrege, "type": unite.type,
                "heure_debut": str(unite.heure_debut), "heure_fin": str(unite.heure_fin), "heure_debut_fixe": unite.heure_debut_fixe,
                "heure_fin_fixe": unite.heure_fin_fixe, "touche_raccourci": unite.touche_raccourci, "largeur": unite.largeur,
                "groupes": [groupe.pk for groupe in unite.groupes.all()], "incompatibilites": [u.pk for u in unite.incompatibilites.all()],
                "visible_portail": unite.visible_portail, "unites_remplissage": dict_unites_remplissage_unites.get(unite.pk, [])}})
    data['liste_unites_json'] = json.dumps(liste_unites_json)

    # Conversion au format json
    data["periode_json"] = mark_safe(json.dumps(data["periode"]))
    data["consommations_json"] = mark_safe(json.dumps(data["consommations"]))
    data["memos_json"] = mark_safe(json.dumps(data["memos"]))
    data["options_json"] = mark_safe(json.dumps(data.get("options", {})))
    data["dict_suppressions_json"] = mark_safe(json.dumps(data["dict_suppressions"]))
    # data["liste_idindividus_json"] = mark_safe(json.dumps(data["liste_idindividus"]))
    data["liste_key_individus_json"] = mark_safe(json.dumps(data["liste_key_individus"]))

    # Suppression de données inutiles
    for key in ("liste_familles", "periode", "consommations", "memos", "options", "dict_suppressions", "liste_idindividus", "liste_key_individus", "liste_evenements", "prestations"):
        if key in data:
            del data[key]

    # Pour les tests de performance
    # Facturer()

    return data


def Save_grille(request=None, donnees={}):
    logger.debug("Sauvegarde de la grille...")
    logger.debug("prestations : " + str(donnees["prestations"]))
    logger.debug("suppressions : " + str(donnees["suppressions"]))
    chrono = time.time()

    liste_historique = []

    # ----------------------------------- PRESTATIONS --------------------------------------

    # Enregistrement des nouvelles prestations
    dict_idprestation = {}
    for IDprestation, dict_prestation in donnees["prestations"].items():

        if "-" in IDprestation:
            logger.debug("Prestation à ajouter : ID" + str(IDprestation) + " > " + str(dict_prestation))

            # Enregistre la prestation
            prestation = Prestation.objects.create(
                date=dict_prestation["date"], categorie="consommation", label=dict_prestation["label"], montant_initial=dict_prestation["montant_initial"],
                montant=dict_prestation["montant"], activite_id=dict_prestation["activite"], tarif_id=dict_prestation["tarif"], famille_id=dict_prestation["famille"],
                individu_id=dict_prestation["individu"], temps_facture=utils_dates.HeureStrEnDelta(dict_prestation["temps_facture"]), categorie_tarif_id=dict_prestation["categorie_tarif"],
                quantite=dict_prestation["quantite"], tva=dict_prestation["tva"], code_compta=dict_prestation["code_compta"],
            )

            liste_historique.append({"titre": "Ajout d'une prestation", "detail": "%s du %s" % (dict_prestation["label"], utils_dates.ConvertDateToFR(dict_prestation["date"])), "utilisateur": request.user if request else None,
                                     "famille_id": dict_prestation["famille"], "individu_id": dict_prestation["individu"], "objet": "Prestation", "idobjet": prestation.pk, "classe": "Prestation"})

            # Mémorise la correspondante du nouvel IDprestation avec l'ancien IDprestation
            dict_idprestation[IDprestation] = prestation.pk

            # Enregistrement des aides
            for dict_aide in dict_prestation["aides"]:
                deduction = Deduction.objects.create(date=dict_prestation["date"], label=dict_aide["label"], aide_id=dict_aide["aide"], famille_id=dict_prestation["famille"], prestation=prestation, montant=dict_aide["montant"])
                liste_historique.append({"titre": "Ajout d'une déduction", "detail": "%s du %s" % (dict_aide["label"], utils_dates.ConvertDateToFR(dict_prestation["date"])), "utilisateur": request.user if request else None,
                                         "famille_id": dict_prestation["famille"], "individu_id": dict_prestation["individu"], "objet": "Déduction", "idobjet": deduction.pk, "classe": "Deduction"})

    # ---------------------------------- CONSOMMATIONS -------------------------------------

    dict_unites = {unite.pk: unite for unite in Unite.objects.all()}

    # Analyse et préparation des consommations
    liste_ajouts = []
    dict_modifications = {}
    dict_idconso = {}
    for key_case, consommations in donnees["consommations"].items():
        for dict_conso in consommations:
            # Recherche du nouvel IDprestation
            dict_conso["prestation"] = dict_idprestation.get(dict_conso["prestation"], dict_conso["prestation"])

            if "-" in str(dict_conso["pk"]):
                liste_ajouts.append(Consommation(
                    individu_id=dict_conso["individu"], inscription_id=dict_conso["inscription"], activite_id=dict_conso["activite"], date=dict_conso["date"],
                    unite_id=dict_conso["unite"], groupe_id=dict_conso["groupe"], heure_debut=dict_conso["heure_debut"], heure_fin=dict_conso["heure_fin"],
                    etat=dict_conso["etat"], categorie_tarif_id=dict_conso["categorie_tarif"], prestation_id=dict_conso["prestation"], quantite=dict_conso["quantite"],
                    evenement_id=dict_conso["evenement"], badgeage_debut=dict_conso["badgeage_debut"], badgeage_fin=dict_conso["badgeage_fin"],
                ))
                logger.debug("Consommation à ajouter : " + str(dict_conso))
                liste_historique.append({"titre": "Ajout d'une consommation", "detail": "%s du %s (%s)" % (dict_unites[dict_conso["unite"]].nom, utils_dates.ConvertDateToFR(dict_conso["date"]), utils_consommations.Get_label_etat(dict_conso["etat"])), "utilisateur": request.user if request else None,
                                         "famille_id": dict_conso["famille"], "individu_id": dict_conso["individu"], "objet": "Consommation", "idobjet": None, "classe": "Consommation"})

                # Mode pointeuse pour récupérer l'idconso
                if donnees.get("mode", None) == "pointeuse":
                    liste_ajouts[0].save()
                    dict_idconso[dict_conso["pk"]] = liste_ajouts[0].pk
                    liste_ajouts = []

            elif dict_conso["dirty"]:
                dict_modifications[dict_conso["pk"]] = dict_conso
                logger.debug("Consommation à modifier : " + str(dict_conso))
                liste_historique.append({"titre": "Modification d'une consommation", "detail": "%s du %s (%s)" % (dict_unites[dict_conso["unite"]].nom, utils_dates.ConvertDateToFR(dict_conso["date"]), utils_consommations.Get_label_etat(dict_conso["etat"])), "utilisateur": request.user if request else None,
                                         "famille_id": dict_conso["famille"], "individu_id": dict_conso["individu"], "objet": "Consommation", "idobjet": dict_conso["pk"], "classe": "Consommation"})

    # Récupère la liste des conso à modifier
    liste_modifications = []
    for conso in Consommation.objects.filter(pk__in=dict_modifications.keys()):
        conso.groupe_id = dict_modifications[conso.pk]["groupe"]
        conso.heure_debut = dict_modifications[conso.pk]["heure_debut"]
        conso.heure_fin = dict_modifications[conso.pk]["heure_fin"]
        conso.etat = dict_modifications[conso.pk]["etat"]
        conso.categorie_tarif_id = dict_modifications[conso.pk]["categorie_tarif"]
        conso.prestation_id = dict_modifications[conso.pk]["prestation"]
        conso.quantite = dict_modifications[conso.pk]["quantite"]

        if conso.prestation_id in dict_idprestation:
            conso.prestation_id = dict_idprestation[conso.prestation_id]

        liste_modifications.append(conso)

    # Traitement dans la base
    texte_notification = []
    if liste_ajouts:
        Consommation.objects.bulk_create(liste_ajouts)
        texte_notification.append("%s ajout%s" % (len(liste_ajouts), "s" if len(liste_ajouts) > 1 else ""))
    if liste_modifications:
        Consommation.objects.bulk_update(liste_modifications, ["groupe", "heure_debut", "heure_fin", "etat", "categorie_tarif", "prestation", "quantite"], batch_size=50)
        texte_notification.append("%s modification%s" % (len(liste_modifications), "s" if len(liste_modifications) > 1 else ""))
    if donnees["suppressions"]["consommations"]:
        logger.debug("Consommations à supprimer : " + str(donnees["suppressions"]["consommations"]))
        liste_conso_suppr = list(Consommation.objects.select_related("unite", "inscription").filter(pk__in=donnees["suppressions"]["consommations"]))
        utils_db.bulk_delete(listeID=donnees["suppressions"]["consommations"], nom_table="consommations", nom_id="IDconso")
        texte_notification.append("%s suppression%s" % (len(donnees["suppressions"]["consommations"]), "s" if len(donnees["suppressions"]["consommations"]) > 1 else ""))
        for conso in liste_conso_suppr:
            liste_historique.append({"titre": "Suppression d'une consommation", "detail": "%s du %s (%s)" % (conso.unite.nom, utils_dates.ConvertDateToFR(conso.date), conso.get_etat_display()),
                                     "utilisateur": request.user if request else None, "famille_id": conso.inscription.famille_id, "individu_id": conso.individu_id, "objet": "Consommation", "idobjet": conso.pk, "classe": "Consommation"})

    # Notification d'enregistrement des consommations
    # if texte_notification and request:
    #     messages.add_message(request, messages.SUCCESS, "Consommations enregistrées : %s" % utils_texte.Convert_liste_to_texte_virgules(texte_notification))

    # Suppression des prestations obsolètes (après la suppression des consommations associées)
    logger.debug("Prestations à supprimer : " + str(donnees["suppressions"]["prestations"]))
    if donnees["suppressions"]["prestations"]:
        liste_prestations_suppr = list(Prestation.objects.filter(pk__in=donnees["suppressions"]["prestations"]))
        utils_db.bulk_delete(listeID=donnees["suppressions"]["prestations"], nom_table="deductions", nom_id="prestation_id")
        utils_db.bulk_delete(listeID=donnees["suppressions"]["prestations"], nom_table="prestations", nom_id="IDprestation")
        for prestation in liste_prestations_suppr:
            liste_historique.append({"titre": "Suppression d'une prestation", "detail": "%s du %s" % (prestation.label, utils_dates.ConvertDateToFR(prestation.date)),
                                     "utilisateur": request.user if request else None, "famille_id": prestation.famille_id, "individu_id": prestation.individu_id, "objet": "Prestation", "idobjet": prestation.pk, "classe": "Prestation"})

    # ---------------------------------- MEMOS JOURNALIERS -------------------------------------

    if "memos" in donnees:

        # Analyse et préparation des mémos
        liste_ajouts = []
        dict_modifications = {}
        for key_case, dict_memo in donnees["memos"].items():
            if dict_memo["texte"]:
                if not dict_memo["pk"]:
                    liste_ajouts.append(MemoJournee(date=dict_memo["date"], inscription_id=dict_memo["inscription"], texte=dict_memo["texte"]))
                elif dict_memo["dirty"]:
                    dict_modifications[dict_memo["pk"]] = dict_memo

        # Récupère la liste des mémos à modifier
        liste_modifications = []
        for memo in MemoJournee.objects.filter(pk__in=dict_modifications.keys()):
            memo.texte = dict_modifications[memo.pk]["texte"]
            liste_modifications.append(memo)

        # Traitement dans la base
        if liste_ajouts: MemoJournee.objects.bulk_create(liste_ajouts)
        if liste_modifications: MemoJournee.objects.bulk_update(liste_modifications, ["texte"])
        if donnees["suppressions"]["memos"]: utils_db.bulk_delete(listeID=donnees["suppressions"]["memos"], nom_table="memo_journee", nom_id="IDmemo")

    # Sauvegarde de l'historique
    utils_historique.Ajouter_plusieurs(liste_historique)

    # Affiche le chrono
    logger.debug("Temps d'enregistrement de la grille : " + str(time.time() - chrono))

    return dict_idprestation, dict_idconso


def CompareDict(dict1={}, dict2={}, keys=[]):
    """ Compare les valeurs de 2 dictionnaires selon les clés données """
    for key in keys:
        if dict1[key] != dict2[key]:
            return False
    return True


def Facturer(request=None):
    donnees_aller = json.loads(request.POST.get("donnees", {}))
    logger.debug("============== Facturation ================")
    logger.debug("données aller : " + str(donnees_aller))
    facturation = Facturation(donnees=donnees_aller)
    donnees_retour = facturation.Facturer()
    logger.debug("données retour : " + str(donnees_retour))

    # Si mode pointage, sauvegarde les données
    if donnees_aller.get("mode", None) == "pointeuse":

        # Attribue les nouvelles prestations aux consommations
        for key_case, idprestation in donnees_retour["modifications_idprestation"].items():
            for key_conso, liste_conso in donnees_aller["consommations"].items():
                for dict_conso in liste_conso:
                    if dict_conso["key_case"] == key_case:
                        dict_conso["prestation"] = idprestation

        # Ajouter les nouvelles prestations pour la sauvegarde
        donnees_aller["prestations"].update(donnees_retour["nouvelles_prestations"])
        donnees_save = {
            "mode": donnees_aller.get("mode", None),
            "consommations": donnees_aller["consommations"],
            "prestations": donnees_aller["prestations"],
            "suppressions": {
                "consommations": donnees_aller["dict_suppressions"]["consommations"],
                "prestations": [int(idprestation) for idprestation in donnees_retour["anciennes_prestations"] if "-" not in str(idprestation)],
                "memos": [],
            },
        }
        dict_idprestation, dict_idconso = Save_grille(request=request, donnees=donnees_save)
        donnees_retour["modifications_idconso"] = dict_idconso

        # Remplacement des anciens idprestation par les nouveaux idprestation
        for idprestation in list(donnees_retour["nouvelles_prestations"].keys()):
            if idprestation in dict_idprestation:
                nouvel_idprestation = dict_idprestation[idprestation]
                donnees_retour["nouvelles_prestations"][nouvel_idprestation] = donnees_retour["nouvelles_prestations"][idprestation]
                donnees_retour["nouvelles_prestations"][nouvel_idprestation]["prestation"] = nouvel_idprestation
                del donnees_retour["nouvelles_prestations"][idprestation]

    return JsonResponse(donnees_retour)



class Facturation():
    def __init__(self, donnees={}):
        self.donnees = donnees

        self.dict_modif_cases = {}
        self.liste_anciennes_prestations = []
        self.dict_nouvelles_prestations = {}
        self.dict_lignes_tarifs = {}
        self.dict_quotients = {}
        self.dict_tarifs = {}
        self.dict_combi_tarif = {}
        self.dict_aides = {}


    def Facturer(self):
        for key_case, case_tableau in self.donnees["cases_touchees"].items():
            logger.debug("Case étudiée : " + str(key_case))

            if key_case not in self.dict_modif_cases:

                action = "saisie" # todo : PROVISOIRE
                modeSilencieux = False # todo : PROVISOIRE
                self.dictForfaits = {} # todo : PROVISOIRE


                # Recherche les unités utilisées de la ligne
                dictUnitesUtilisees = {}
                dictQuantites = {}
                for conso in self.donnees["consommations"].get("%s_%s" % (case_tableau["date"], case_tableau["inscription"]), []):
                    if not conso["forfait"] and (conso["unite"] not in dictUnitesUtilisees or dictUnitesUtilisees[conso["unite"]] in (None, "attente", "refus")):
                        dictUnitesUtilisees[conso["unite"]] = conso["etat"]
                    dictQuantites[conso["unite"]] = conso["quantite"]
                logger.debug("Unités utilisées sur la ligne : " + str(dictUnitesUtilisees))

                # Mémorise les tarifs
                key = (case_tableau["activite"], case_tableau["categorie_tarif"])
                if key not in self.dict_tarifs:
                    self.dict_tarifs[key] = Tarif.objects.prefetch_related('groupes').filter(activite_id=case_tableau["activite"], categories_tarifs=case_tableau["categorie_tarif"]).order_by("date_debut")

                # Recherche un tarif valable pour cette date
                tarifs_valides1 = []
                liste_id_tarif = []
                for tarif in self.dict_tarifs[key]:
                    if self.Recherche_tarif_valide(tarif, case_tableau):
                        tarifs_valides1.append(tarif)
                        liste_id_tarif.append(str(tarif.pk))
                liste_id_tarif.sort()
                liste_id_tarif_str = ";".join(liste_id_tarif)

                # Importation des combi de ces tarifs
                dict_combi_by_activite = {}
                if liste_id_tarif_str not in self.dict_combi_tarif:
                    self.dict_combi_tarif[liste_id_tarif_str] = CombiTarif.objects.prefetch_related('unites').filter(tarif__in=tarifs_valides1)
                for combi in self.dict_combi_tarif[liste_id_tarif_str]:
                    dict_combi_by_activite.setdefault(combi.tarif_id, [])
                    dict_combi_by_activite[combi.tarif_id].append(combi)

                # Recherche des combinaisons présentes
                tarifs_valides2 = []
                for tarif in tarifs_valides1:
                    tarif.nbre_max_unites_combi = 0
                    for combinaison in dict_combi_by_activite.get(tarif.pk, []):
                        unites_combi = [unite.pk for unite in combinaison.unites.all()]
                        unites_combi.sort()
                        if self.Recherche_combinaison(dictUnitesUtilisees, unites_combi, tarif):
                            if len(unites_combi) > tarif.nbre_max_unites_combi:
                                tarif.nbre_max_unites_combi = len(unites_combi)
                                tarif.combi_retenue = unites_combi
                                tarifs_valides2.append(tarif)

                # Tri des tarifs par date de début puis par nbre d'unités
                tarifs_valides2.sort(key=lambda tarif: tarif.date_debut, reverse=True)
                tarifs_valides2.sort(key=lambda tarif: tarif.nbre_max_unites_combi, reverse=True)

                #-----------------------------------------------------------
                # Si forfaits au crédits présents dans les tarifs
                # todo : Prise en charge forfait-crédit à coder ici
                #-----------------------------------------------------------

                # Sélection des tarifs qui ont le plus grand nombre d'unités
                liste_tarifs_retenus = []
                liste_unites_traitees = []
                for tarif in tarifs_valides2:
                    # Recherche des unités non traitées
                    valide = True
                    for idunite in tarif.combi_retenue:
                        if idunite in liste_unites_traitees:
                            valide = False
                    # Si le tarif est finalement retenu
                    if valide:
                        liste_tarifs_retenus.append(tarif)
                        for idunite in tarif.combi_retenue:
                            liste_unites_traitees.append(idunite)

                # Calcul des tarifs des prestations
                dictUnitesPrestations = {}
                for tarif in liste_tarifs_retenus:

                    # Recherche des évènements dans une des cases de la combinaison
                    liste_evenements = [None,]
                    logger.debug("Méthode de calcul du tarif : " + tarif.methode)

                    if "evenement" in tarif.methode:
                        # Recherche les évènements pour lesquels une conso est saisie
                        liste_evenements = []
                        for conso in self.donnees["consommations"].get("%s_%s" % (case_tableau["date"], case_tableau["inscription"]), []):
                            if conso["evenement"] and conso["etat"] not in ("attente", "refus"):
                                idevenement = conso["evenement"]
                                evenement = Evenement.objects.filter(pk=idevenement).first()
                                liste_evenements.append(evenement)
                                logger.debug("Evenement trouvé sur la ligne : ID" + str(idevenement))


                    # Mémorise le tarif initial pour les évènements
                    tarif_base = copy.deepcopy(tarif)
                    for evenement in liste_evenements:
                        # Recherche un tarif spécial évènement
                        if evenement:
                            for tarif_evenement in Tarif.objects.filter(evenement=evenement).order_by("date_debut"):
                                if self.Recherche_tarif_valide(tarif_evenement, case_tableau):
                                    tarif = tarif_evenement
                                    tarif.nom_evenement = evenement.nom
                                    logger.debug("Un tarif spécial événement a été trouvé : IDtarif " + str(tarif.pk))

                        # Forfait crédit
                        # if "CREDIT" in tarif:
                        #     forfait_credit = tarif["CREDIT"]
                        # else:
                        #     forfait_credit = False
                        forfait_credit = False # Provisoire : doit être remplacé par le code ci-dessus

                        # Recherche du temps facturé par défaut
                        temps_facture = None
                        liste_temps = []
                        for conso in self.donnees["consommations"].get("%s_%s" % (case_tableau["date"], case_tableau["inscription"]), []):
                            if conso["unite"] in tarif_base.combi_retenue:
                                heure_debut = conso["heure_debut"]
                                heure_fin = conso["heure_fin"]
                                if heure_debut and heure_fin:
                                    liste_temps.append((heure_debut, heure_fin))
                        if liste_temps:
                            temps_facture = utils_dates.Additionne_intervalles_temps(liste_temps)

                        # Recherche de la quantité
                        # quantite = 0
                        # for idunite in tarif_base.combi_retenue:
                        #     if idunite in dictQuantites:
                        #         if dictQuantites[idunite]:
                        #             quantite += dictQuantites[idunite]
                        quantite = 0
                        for idunite in tarif_base.combi_retenue:
                            if idunite in dictQuantites:
                                if dictQuantites[idunite] and dictQuantites[idunite] > quantite:
                                    quantite = dictQuantites[idunite]

                        # Calcul du tarif
                        resultat = self.Calcule_tarif(tarif, tarif_base.combi_retenue, case_tableau, temps_facture, quantite, evenement, modeSilencieux, action)
                        if resultat == False:
                            return False
                        elif resultat == "break":
                            break
                        else:
                            montant_tarif, nom_tarif, temps_facture = resultat

                        logger.debug("Montant trouvé : Montant=%s (tarif=%s temps_facturé=%s Quantité=%d)" % (montant_tarif, nom_tarif, temps_facture, quantite))

                        # -------------------------------------------------------------------------
                        # ------------------- Déduction d'une aide journalière --------------------
                        # -------------------------------------------------------------------------

                        # Recherche si une aide est valable à cette date et pour cet individu et pour cette activité
                        key_aide = "%d_%d_%d" % (case_tableau["famille"], case_tableau["individu"], case_tableau["activite"])
                        if key_aide not in self.dict_aides:
                            self.dict_aides[key_aide] = Aide.objects.filter(famille_id=case_tableau["famille"], individus__pk=case_tableau["individu"], activite_id=case_tableau["activite"])

                        liste_aide_retenues = []
                        if key_aide in self.dict_aides:
                            logger.debug("Aides potentielles trouvées = " + str(self.dict_aides[key_aide]))

                            for aide in self.dict_aides[key_aide]:
                                if str(aide.date_debut) <= case_tableau["date"] and str(aide.date_fin) >= case_tableau["date"] and self.Verification_periodes(aide.jours_scolaires, aide.jours_vacances, case_tableau["date"]):
                                    liste_combi_valides = []

                                    # On recherche si des combinaisons sont présentes sur cette ligne
                                    for combi in CombiAide.objects.prefetch_related('unites').filter(aide=aide):
                                        if tarif.combi_retenue == [unite.pk for unite in combi.unites.all().order_by("pk")]:
                                            combi.nbre_max_unites = len(tarif.combi_retenue)
                                            liste_combi_valides.append(combi)

                                    if liste_combi_valides:
                                        # Tri des combinaisons par nombre d'unités et on garde la combi qui a le plus grand nombre d'unités
                                        liste_combi_valides.sort(key=lambda combi: combi.nbre_max_unites, reverse=True)
                                        combi_retenue = liste_combi_valides[0]
                                        logger.debug("Combi aide retenue : " + str(combi_retenue))

                                        # Vérifie que le montant max ou le nbre de dates max n'est pas déjà atteint avant application
                                        aide_valide = True
                                        liste_aides_utilisees = []
                                        if aide.nbre_dates_max or aide.montant_max:

                                            def Ajoute_aide(IDprestation, date, IDindividu, montant):
                                                if IDprestation not in self.liste_anciennes_prestations and (IDindividu != case_tableau["individu"] or date != case_tableau["date"]):
                                                    liste_aides_utilisees.append({"idprestation": IDprestation, "date": date, "montant": montant})

                                            # Recherche dans les nouvelles prestations
                                            for IDprestation, dict_prestation in self.dict_nouvelles_prestations.items():
                                                for dict_aide in dict_prestation["aides"]:
                                                    if dict_aide["aide"] == combi_retenue.aide_id:
                                                        Ajoute_aide(IDprestation, dict_prestation["date"], dict_prestation["individu"], dict_aide["montant"])

                                            # Recherche dans les aides affichées
                                            liste_id_temp = []
                                            for dict_aide in self.donnees["dict_aides"]:
                                                if dict_aide["famille"] == case_tableau["famille"] and dict_aide["aide"] == combi_retenue.aide_id:
                                                    Ajoute_aide(dict_aide["idprestation"], dict_aide["date"], dict_aide["individu"], dict_aide["montant"])
                                                    liste_id_temp.append(dict_aide["idprestation"])

                                            # Recherche dans la base de données
                                            for deduction in Deduction.objects.filter(famille_id=case_tableau["famille"], aide=combi_retenue.aide).prefetch_related('prestation'):
                                                if deduction.prestation_id not in self.donnees["dict_suppressions"]["prestations"] and deduction.prestation_id not in liste_id_temp:
                                                    Ajoute_aide(deduction.prestation_id, str(deduction.date), deduction.prestation.individu_id, float(deduction.montant))

                                            logger.debug("%d déductions utilisent déjà cette aide : %s" % (len(liste_aides_utilisees), liste_aides_utilisees))

                                            montant_total = decimal.Decimal(0.0)
                                            dict_dates = {}
                                            for dict_aide in liste_aides_utilisees:
                                                montant_total += decimal.Decimal(dict_aide["montant"])
                                                dict_dates[dict_aide["date"]] = None

                                            if aide.nbre_dates_max and (len(dict_dates.keys()) >= aide.nbre_dates_max):
                                                logger.debug("Le nombre de dates max de l'aide est dépassé. Aide non appliquée.")
                                                aide_valide = False

                                            if aide.montant_max and (montant_total + combi_retenue.montant > aide.montant_max):
                                                logger.debug("Le montant max de l'aide est dépassé. Aide non appliquée.")
                                                aide_valide = False

                                        # Mémorisation de l'aide retenue
                                        if aide_valide:
                                            liste_aide_retenues.append(combi_retenue)


                        if forfait_credit == False :
                            # Application de la déduction
                            montant_initial = montant_tarif
                            montant_final = montant_initial
                            for combi_aide in liste_aide_retenues:
                                logger.debug("Déduction d'une aide de " + str(combi_aide.montant))
                                montant_final = montant_final - combi_aide.montant

                            # Formatage du temps facturé
                            if temps_facture != None:
                                temps_facture = time.strftime("%H:%M", time.gmtime(temps_facture.seconds))

                            # -------------------------Mémorisation de la prestation ---------------------------------------------
                            dict_resultat = self.Memorise_prestation(case_tableau, tarif, nom_tarif, montant_initial, montant_final, liste_aides=liste_aide_retenues, temps_facture=temps_facture, evenement=evenement, quantite=quantite)
                            IDprestation = dict_resultat["IDprestation"]
                            if dict_resultat["nouveau"]:
                                self.dict_nouvelles_prestations[IDprestation] = dict_resultat["dictPrestation"]
                                logger.debug("Ajout de la nouvelle prestation " + str(IDprestation))

                        else:
                            IDprestation = forfait_credit

                        # Attribue à chaque unité un IDprestation
                        for IDunite in tarif_base.combi_retenue:
                            IDevenement = evenement.pk if evenement else None
                            dictUnitesPrestations[(IDunite, IDevenement)] = IDprestation


                # 7 - Parcourt toutes les unités de la date pour modifier le IDprestation
                for conso in self.donnees["consommations"].get("%s_%s" % (case_tableau["date"], case_tableau["inscription"]), []):
                    if not conso["forfait"]:

                        # Retrouve le IDprestation
                        if (conso["unite"], conso["evenement"]) in list(dictUnitesPrestations.keys()):
                            IDprestation = dictUnitesPrestations[(conso["unite"], conso["evenement"])]
                        elif (conso["unite"], None) in list(dictUnitesPrestations.keys()):
                            IDprestation = dictUnitesPrestations[(conso["unite"], None)]
                        else:
                            IDprestation = None

                        # Modification de la case
                        self.dict_modif_cases[conso["key_case"]] = IDprestation

                # Supprime des prestations qui ne sont plus utilisées sur la ligne
                for idprestation, dict_prestation in self.donnees["prestations"].items():
                    if dict_prestation["date"] == case_tableau["date"] and dict_prestation["famille"] == case_tableau["famille"] and dict_prestation["individu"] == case_tableau["individu"] and dict_prestation["activite"] == case_tableau["activite"]:
                        if idprestation not in dictUnitesPrestations.values() and idprestation not in self.liste_anciennes_prestations:
                            logger.debug("La prestation suivante ne semble plus utilisée, on la supprime : " + str(idprestation))
                            self.liste_anciennes_prestations.append(idprestation)

        donnees_retour = {
            "anciennes_prestations": self.liste_anciennes_prestations,
            "nouvelles_prestations": self.dict_nouvelles_prestations,
            "modifications_idprestation": self.dict_modif_cases,
        }
        return donnees_retour




    def Memorise_prestation(self, case_tableau, tarif, nom_tarif, montant_initial, montant_final, liste_aides=[],
                           temps_facture=None, forfait_date_debut=None, forfait_date_fin=None, evenement=None, quantite=1):
        """ Mémorisation de la prestation """
        # Préparation des valeurs à mémoriser
        dictPrestation = {
            "date": case_tableau["date"], "categorie": "consommation", "label": nom_tarif, "montant_initial": float(montant_initial),
            "montant": float(montant_final), "activite": case_tableau["activite"], "tarif": tarif.pk, "facture": None,
            "famille": case_tableau["famille"], "individu": case_tableau["individu"], "temps_facture": temps_facture,
            "categorie_tarif": case_tableau["categorie_tarif"], "forfait_date_debut": forfait_date_debut,
            "forfait_date_fin": forfait_date_fin, "code_compta": tarif.code_compta, "tva": tarif.tva, "forfait": None, "aides": [],
            "quantite": quantite,
        }

        # Recherche si une prestation identique existe déjà en mémoire
        for dict_temp in (self.donnees["prestations"].items(), self.dict_nouvelles_prestations.items()):
            for IDprestation, dict_prestation_1 in dict_temp:
                dict_prestation_2 = dict_prestation_1.copy()

                # Renvoie prestation existante si la prestation apparaît déjà sur une facture même si le montant est différent
                keys = ["date", "individu", "tarif", "famille"]
                if evenement:
                    keys.append("label")
                if dict_prestation_2["facture"] != None and CompareDict(dictPrestation, dict_prestation_2, keys=keys) == True:
                    logger.debug("Récupération d'un IDprestation facturé existant : " + str(IDprestation))
                    return {"IDprestation": IDprestation, "dictPrestation": dict_prestation_2, "nouveau": False}

                # Renvoie prestation existante si la prestation semble identique avec montants identiques
                keys = ["date", "individu", "tarif", "montant_initial", "montant", "categorie_tarif", "famille", "label", "temps_facture", "quantite"]
                if CompareDict(dictPrestation, dict_prestation_2, keys=keys) == True:
                    logger.debug("Récupération d'un IDprestation existant : " + str(IDprestation))
                    return {"IDprestation": IDprestation, "dictPrestation": dict_prestation_2, "nouveau": False}

        # Génération d'un nouvel IDprestation
        IDprestation = str(uuid4())
        logger.debug("Génération d'un nouveau IDprestation : " + str(IDprestation))

        # Mémorisation de la prestation
        dictPrestation["prestation"] = IDprestation

        # Création des déductions pour les aides journalières
        for combi in liste_aides:
            dictPrestation["aides"].append({"label": combi.aide.nom, "date": case_tableau["date"], "aide": combi.aide_id, "montant": float(combi.montant)})

        return {"IDprestation": IDprestation, "dictPrestation": dictPrestation, "nouveau": True}


    def Recherche_combinaison(self, dictUnitesUtilisees={}, unites_combi=[], tarif=None):
        """ Recherche une combinaison donnée dans une ligne de la grille """
        for idunite in unites_combi:
            # Vérifie si chaque unité est dans la combinaison
            if idunite not in dictUnitesUtilisees:
                return False
            if dictUnitesUtilisees[idunite] == None:
                return False
            # Vérifie si l'état est valide
            if tarif.type == "JOURN":
                etat = dictUnitesUtilisees[idunite]
                if etat not in tarif.etats:
                    return False
        return True


    def Recherche_tarif_valide(self, tarif=None, case_tableau=None):
        # Vérifie si dates validité ok
        date_fin = tarif.date_fin
        if not date_fin: date_fin = datetime.date(2999, 1, 1)
        if case_tableau["date"] < str(tarif.date_debut) or case_tableau["date"] > str(date_fin):
            return False

        # todo: Autres conditions à coder :

        # Vérifie si groupe ok
        if tarif.groupes.exists():
            if case_tableau["groupe"] not in [groupe.pk for groupe in tarif.groupes.all()]:
                return False

        # Vérifie si étiquette ok
        # listeEtiquettes = dictTarif["etiquettes"]
        # if listeEtiquettes != None:
        #     valide = False
        #     for IDetiquette in etiquettes:
        #         if IDetiquette in listeEtiquettes:
        #             valide = True
        #     if valide == False:
        #         return False

        # Vérifie si cotisation à jour
        # if dictTarif["cotisations"] != None:
        #     cotisationsValide = self.VerificationCotisations(listeCotisations=dictTarif["cotisations"], date=date, IDindividu=IDindividu, IDfamille=IDfamille)
        #     if cotisationsValide == False:
        #         return False

        # Vérifie si caisse à jour
        # if dictTarif["caisses"] != None:
        #     caissesValide = self.VerificationCaisses(listeCaisses=dictTarif["caisses"], IDfamille=IDfamille)
        #     if caissesValide == False:
        #         return False

        # Vérifie si période ok
        if tarif.jours_scolaires or tarif.jours_vacances:
            if self.Verification_periodes(tarif.jours_scolaires, tarif.jours_vacances, case_tableau["date"]) == False:
                return False

        # Vérifie si filtres de questionnaires ok
        # if len(dictTarif["filtres"]) > 0:
        #     filtresValide = self.VerificationFiltres(listeFiltres=dictTarif["filtres"], date=date, IDindividu=IDindividu, IDfamille=IDfamille)
        #     if filtresValide == False:
        #         return False

        return True

    def Recherche_QF(self, tarif=None, case_tableau=None):
        """ Recherche du QF de la famille """
        IDfamille = case_tableau["famille"]
        date = utils_dates.ConvertDateENGtoDate(case_tableau["date"])

        # Si la famille a un QF :
        if IDfamille not in self.dict_quotients:
            self.dict_quotients[IDfamille] = Quotient.objects.filter(famille_id=IDfamille).order_by("date_debut")
        for quotient in self.dict_quotients[IDfamille]:
            if quotient.date_debut <= date <= quotient.date_fin and (not tarif.type_quotient or tarif.type_quotient == quotient.type_quotient):
                return quotient.quotient
        return None

    def Verification_periodes(self, jours_scolaires, jours_vacances, date):
        """ Vérifie si jour est scolaire ou vacances """
        def EstEnVacances(date_temp=None):
            for vac_debut, vac_fin in self.donnees["liste_vacances"]:
                if vac_debut >= str(date_temp) >= vac_fin:
                    return True
            return False
        date = utils_dates.ConvertDateENGtoDate(date)
        valide = False
        if jours_scolaires:
            if not EstEnVacances(date) and str(date.weekday()) in jours_scolaires:
                valide = True
        if jours_vacances:
            if EstEnVacances(date) and str(date.weekday()) in jours_vacances:
                valide = True
        return valide

    def Calcule_duree(self, case_tableau=None, combinaisons_unites=[]):
        """ Pour Facturation """
        liste_temps = []
        heure_min = None
        heure_max = None
        for conso in self.donnees["consommations"].get("%s_%s" % (case_tableau["date"], case_tableau["inscription"]), []):
            if conso["unite"] in combinaisons_unites:
                if conso["etat"] in ("reservation", "present", "absenti"):
                    heure_debut = conso["heure_debut"]
                    heure_fin = conso["heure_fin"]
                    if heure_debut and heure_fin:
                        liste_temps.append((heure_debut, heure_fin))
                        if not heure_min or utils_dates.HeureStrEnDelta(heure_debut) < heure_min:
                            heure_min = utils_dates.HeureStrEnDelta(heure_debut)
                        if not heure_max or utils_dates.HeureStrEnDelta(heure_fin) > heure_max:
                            heure_max = utils_dates.HeureStrEnDelta(heure_fin)

        if not heure_min: heure_min = datetime.timedelta(hours=0, minutes=0)
        if not heure_max: heure_max = datetime.timedelta(hours=0, minutes=0)

        if liste_temps:
            duree = utils_dates.Additionne_intervalles_temps(liste_temps)
        else:
            duree = None
        return duree, heure_min, heure_max

    def Calcule_tarif(self, tarif=None, combinaisons_unites=[], case_tableau=None, temps_facture=None, quantite=None, evenement=None, modeSilencieux=False, action="saisie"):
        nom_tarif = tarif.nom_tarif.nom
        if hasattr(tarif, "nom_evenement"):
            nom_tarif = tarif.nom_evenement
        description_tarif = tarif.description
        montant_tarif = 0.0
        methode_calcul = tarif.methode

        # Label de la prestation personnalisé
        if tarif.label_prestation == "description_tarif":
            nom_tarif = description_tarif
        if tarif.label_prestation and tarif.label_prestation.startswith("autre:"):
            nom_tarif = tarif.label_prestation[6:]

        # Récupération des lignes de tarifs mémorisés
        def Get_lignes_tarif():
            if tarif in self.dict_lignes_tarifs:
                return self.dict_lignes_tarifs[tarif]
            self.dict_lignes_tarifs[tarif] = TarifLigne.objects.filter(tarif=tarif).order_by("num_ligne").all()
            return self.dict_lignes_tarifs[tarif]


        # Recherche du montant du tarif : MONTANT UNIQUE
        if methode_calcul == "montant_unique":
            lignes_calcul = Get_lignes_tarif()
            montant_tarif = lignes_calcul.first().montant_unique

            # montant_questionnaire = self.GetQuestionnaire(lignes_calcul[0]["montant_questionnaire"], IDfamille, IDindividu)
            # if montant_questionnaire not in (None, 0.0):
            #     montant_tarif = montant_questionnaire

        # Recherche du montant à appliquer : QUOTIENT FAMILIAL
        if methode_calcul == "qf":
            lignes_calcul = Get_lignes_tarif()
            qf_famille = self.Recherche_QF(tarif, case_tableau)
            for ligne in lignes_calcul:
                montant_tarif = ligne.montant_unique
                if qf_famille and qf_famille >= ligne.qf_min and qf_famille <= ligne.qf_max:
                    break

        # Recherche du montant du tarif : HORAIRE - MONTANT UNIQUE OU SELON QF
        if methode_calcul in ("horaire_montant_unique", "horaire_qf"):
            montant_tarif = 0.0
            lignes_calcul = Get_lignes_tarif()

            # Recherche des heures debut et fin des unités cochées
            heure_debut = None
            heure_fin = None
            for conso in self.donnees["consommations"].get("%s_%s" % (case_tableau["date"], case_tableau["inscription"]), []):
                if conso["unite"] in combinaisons_unites:
                    heure_debut_temp = utils_dates.HeureStrEnTime(conso["heure_debut"])
                    heure_fin_temp = utils_dates.HeureStrEnTime(conso["heure_fin"])
                    if not heure_debut or heure_debut_temp < heure_debut:
                        heure_debut = heure_debut_temp
                    if not heure_fin or heure_fin_temp > heure_fin:
                        heure_fin = heure_fin_temp

            if "qf" in methode_calcul:
                qf_famille = self.Recherche_QF(tarif, case_tableau)

            for ligne_calcul in lignes_calcul:
                # montant_questionnaire = self.GetQuestionnaire(ligneCalcul["montant_questionnaire"], IDfamille, IDindividu)
                # if montant_questionnaire not in (None, 0.0):
                #     montant_tarif_ligne = montant_questionnaire

                if "qf" in methode_calcul and qf_famille:
                    if qf_famille < ligne_calcul.qf_min or qf_famille > ligne_calcul.qf_max:
                        break

                if ligne_calcul.heure_debut_min <= heure_debut <= ligne_calcul.heure_debut_max and ligne_calcul.heure_fin_min <= heure_fin <= ligne_calcul.heure_fin_max:
                    montant_tarif = ligne_calcul.montant_unique
                    if ligne_calcul.temps_facture:
                        temps_facture = datetime.timedelta(hours=ligne_calcul.temps_facture.hour, minutes=ligne_calcul.temps_facture.minute)
                    else:
                        temps_facture = utils_dates.SoustractionHeures(ligne_calcul.heure_fin_max, ligne_calcul.heure_debut_min)

                    heure_debut_delta = datetime.timedelta(hours=heure_debut.hour, minutes=heure_debut.minute)
                    heure_fin_delta = datetime.timedelta(hours=heure_fin.hour, minutes=heure_fin.minute)
                    duree_delta = heure_fin_delta - heure_debut_delta

                    # Création du label personnalisé
                    label = ligne_calcul.label
                    if label:
                        if "{TEMPS_REALISE}" in label: label = label.replace("{TEMPS_REALISE}", utils_dates.DeltaEnStr(duree_delta))
                        if "{TEMPS_FACTURE}" in label: label = label.replace("{TEMPS_FACTURE}", utils_dates.DeltaEnStr(temps_facture))
                        if "{HEURE_DEBUT}" in label: label = label.replace("{HEURE_DEBUT}", utils_dates.DeltaEnStr(heure_debut_delta))
                        if "{HEURE_FIN}" in label: label = label.replace("{HEURE_FIN}", utils_dates.DeltaEnStr(heure_fin_delta))
                        nom_tarif = label
                    break

        # Recherche du montant du tarif : DUREE - MONTANT UNIQUE OU SELON QF
        if methode_calcul in ("duree_montant_unique", "duree_qf"):
            montant_tarif = 0.0
            lignes_calcul = Get_lignes_tarif()

            # Recherche des heures debut et fin des unités cochées
            duree, heure_debut_delta, heure_fin_delta = self.Calcule_duree(case_tableau, combinaisons_unites)
            duree_delta = heure_fin_delta - heure_debut_delta

            if "qf" in methode_calcul:
                qf_famille = self.Recherche_QF(tarif, case_tableau)

            for ligne_calcul in lignes_calcul:
                # montant_questionnaire = self.GetQuestionnaire(ligneCalcul["montant_questionnaire"], IDfamille, IDindividu)
                # if montant_questionnaire not in (None, 0.0):
                #     montant_tarif_ligne = montant_questionnaire

                if utils_dates.TimeEnDelta(ligne_calcul.duree_min) <= duree <= utils_dates.TimeEnDelta(ligne_calcul.duree_max):
                    montant_tarif = ligne_calcul.montant_unique
                    if ligne_calcul.temps_facture:
                        temps_facture = datetime.timedelta(hours=ligne_calcul.temps_facture.hour, minutes=ligne_calcul.temps_facture.minute)
                    else:
                        temps_facture = ligne_calcul.duree_max

                    # Création du label personnalisé
                    label = ligne_calcul.label
                    if label:
                        if "{TEMPS_REALISE}" in label: label = label.replace("{TEMPS_REALISE}", utils_dates.DeltaEnStr(duree_delta))
                        if "{TEMPS_FACTURE}" in label: label = label.replace("{TEMPS_FACTURE}", utils_dates.DeltaEnStr(temps_facture))
                        if "{HEURE_DEBUT}" in label: label = label.replace("{HEURE_DEBUT}", utils_dates.DeltaEnStr(heure_debut_delta))
                        if "{HEURE_FIN}" in label: label = label.replace("{HEURE_FIN}", utils_dates.DeltaEnStr(heure_fin_delta))
                        nom_tarif = label

                    if "qf" in methode_calcul and qf_famille:
                        if qf_famille < ligne_calcul.qf_min or qf_famille > ligne_calcul.qf_max:
                            break


        # Recherche du montant du tarif : EN FONCTION DE LA DATE - MONTANT UNIQUE OU QF
        if methode_calcul in ("montant_unique_date", "qf_date"):
            montant_tarif = 0.0
            lignes_calcul = TarifLigne.objects.filter(tarif=tarif, date=case_tableau["date"]).order_by("num_ligne").all()

            if "qf" in methode_calcul:
                qf_famille = self.Recherche_QF(tarif, case_tableau)

            for ligne_calcul in lignes_calcul:
                montant_tarif = ligne_calcul.montant_unique
                if ligne_calcul.label:
                    nom_tarif = ligne_calcul.label

                if "qf" in methode_calcul and qf_famille:
                    if qf_famille < ligne_calcul.qf_min or qf_famille > ligne_calcul.qf_max:
                        break


        # Recherche du montant du tarif : MONTANT DE L'EVENEMENT
        if methode_calcul == "montant_evenement":
            if evenement:
                montant_tarif = evenement.montant
                nom_tarif = evenement.nom


        # Recherche du montant du tarif : VARIABLE (MONTANT ET LABEL SAISIS PAR L'UTILISATEUR)
        # if methode_calcul == "variable":
        #     if action == "saisie" and case.IDunite in combinaisons_unites and modeSilencieux == False:
        #         # Nouvelle saisie si clic sur la case
        #         from Dlg import DLG_Saisie_montant_prestation
        #         dlg = DLG_Saisie_montant_prestation.Dialog(self, label=nom_tarif, montant=0.0)
        #         dlg.ShowModal()
        #         nom_tarif = dlg.GetLabel()
        #         montant_tarif = dlg.GetMontant()
        #         dlg.Destroy()
        #     else:
        #         # Sinon pas de nouvelle saisie : on cherche l'ancienne prestation déjà saisie
        #         for IDprestation, dictValeurs in self.dictPrestations.items():
        #             if dictValeurs["date"] == date and dictValeurs["IDfamille"] == IDfamille and dictValeurs["IDindividu"] == IDindividu and dictValeurs["IDtarif"] == IDtarif:
        #                 nom_tarif = dictValeurs["label"]
        #                 montant_tarif = dictValeurs["montant"]

        # Recherche du montant du tarif : CHOIX (MONTANT ET LABEL SELECTIONNES PAR L'UTILISATEUR)
        # if methode_calcul == "choix":
        #     if case != None and action == "saisie" and case.IDunite in combinaisons_unites and modeSilencieux == False:
        #         # Nouvelle saisie si clic sur la case
        #         lignes_calcul = dictTarif["lignes_calcul"]
        #         from Dlg import DLG_Selection_montant_prestation
        #         dlg = DLG_Selection_montant_prestation.Dialog(self, lignes_calcul=lignes_calcul, label=nom_tarif, montant=0.0)
        #         dlg.ShowModal()
        #         nom_tarif = dlg.GetLabel()
        #         montant_tarif = dlg.GetMontant()
        #         dlg.Destroy()
        #     else:
        #         # Sinon pas de nouvelle saisie : on cherche l'ancienne prestation déjà saisie
        #         for IDprestation, dictValeurs in self.dictPrestations.items():
        #             if dictValeurs["date"] == date and dictValeurs["IDfamille"] == IDfamille and dictValeurs["IDindividu"] == IDindividu and dictValeurs["IDtarif"] == IDtarif:
        #                 nom_tarif = dictValeurs["label"]
        #                 montant_tarif = dictValeurs["montant"]

        # Recherche du montant du tarif : EN FONCTION DU NBRE D'INDIVIDUS
        # if "nbre_ind" in methode_calcul:
        #     pass # todo: méthode en fonction du nbre d'individus non codé

        # Recherche du montant du tarif : AU PRORATA DE LA DUREE (Montant unique OU QF)
        if methode_calcul in ("duree_coeff_montant_unique", "duree_coeff_qf"):
            montant_tarif = 0.0
            lignes_calcul = Get_lignes_tarif()

            # Recherche des heures debut et fin des unités cochées
            duree, heure_debut_delta, heure_fin_delta = self.Calcule_duree(case_tableau, combinaisons_unites)

            if "qf" in methode_calcul:
                qf_famille = self.Recherche_QF(tarif, case_tableau)

            for ligne_calcul in lignes_calcul:
                duree_min = utils_dates.TimeEnDelta(ligne_calcul.duree_min)
                duree_max = utils_dates.TimeEnDelta(ligne_calcul.duree_max)
                duree_seuil = utils_dates.TimeEnDelta(ligne_calcul.duree_seuil)
                duree_plafond = utils_dates.TimeEnDelta(ligne_calcul.duree_plafond)
                unite_horaire = utils_dates.TimeEnDelta(ligne_calcul.unite_horaire)

                # montant_questionnaire = self.GetQuestionnaire(ligneCalcul["montant_questionnaire"], IDfamille, IDindividu)
                # if montant_questionnaire not in (None, 0.0):
                #     montant_tarif_ligne = montant_questionnaire

                if duree_min == None:
                    duree_min = datetime.timedelta(0)
                if duree_max == None or duree_max == datetime.timedelta(0):
                    duree_max = datetime.timedelta(hours=23, minutes=59)

                # Condition QF
                conditionQF = True
                if "qf" in methode_calcul and qf_famille:
                    if qf_famille >= ligne_calcul.qf_min and qf_famille <= ligne_calcul.qf_max:
                        conditionQF = True
                    else:
                        conditionQF = False

                if duree_min <= duree <= duree_max and conditionQF == True:
                    duree_temp = duree
                    # Vérifie durées seuil et plafond
                    if duree_seuil:
                        if duree_temp < duree_seuil: duree_temp = duree_seuil
                    if duree_plafond and duree_plafond.seconds > 0:
                        if duree_temp > duree_plafond: duree_temp = duree_plafond

                    # Calcul du tarif
                    nbre = int(math.ceil(1.0 * duree_temp.seconds / unite_horaire.seconds))  # Arrondi à l'entier supérieur
                    montant_tarif = nbre * ligne_calcul.montant_unique
                    montant_tarif = float(decimal.Decimal(str(montant_tarif)))

                    # Montants seuil et plafond
                    if ligne_calcul.montant_min:
                        if montant_tarif < ligne_calcul.montant_min:
                            montant_tarif = ligne_calcul.montant_min
                    if ligne_calcul.montant_max:
                        if montant_tarif > ligne_calcul.montant_max:
                            montant_tarif = ligne_calcul.montant_max

                    # Application de l'ajustement (majoration ou déduction)
                    if ligne_calcul.ajustement:
                        montant_tarif = montant_tarif + ligne_calcul.ajustement
                        if montant_tarif < 0.0:
                            montant_tarif = 0.0

                    # Calcul du temps facturé
                    temps_facture = unite_horaire * nbre

                    # Création du label personnalisé
                    label = ligne_calcul.label
                    if label:
                        if "{QUANTITE}" in label: label = label.replace("{QUANTITE}", str(nbre))
                        if "{TEMPS_REALISE}" in label: label = label.replace("{TEMPS_REALISE}", utils_dates.DeltaEnStr(duree_temp))
                        if "{TEMPS_FACTURE}" in label: label = label.replace("{TEMPS_FACTURE}", utils_dates.DeltaEnStr(temps_facture))
                        if "{HEURE_DEBUT}" in label: label = label.replace("{HEURE_DEBUT}", utils_dates.DeltaEnStr(heure_debut_delta))
                        if "{HEURE_FIN}" in label: label = label.replace("{HEURE_FIN}", utils_dates.DeltaEnStr(heure_fin_delta))
                        nom_tarif = label
                    break

        # Recherche du montant du tarif : TAUX D'EFFORT
        if methode_calcul in ("taux_montant_unique", "taux_qf", "taux_date"):
            montant_tarif = 0.0
            lignes_calcul = Get_lignes_tarif()

            # Recherche QF de la famille
            qf_famille = self.Recherche_QF(tarif, case_tableau)

            for ligne_calcul in lignes_calcul:
                # Vérifie si QF ok pour le calcul basé également sur paliers de QF
                conditions = True
                if "qf" in methode_calcul and qf_famille:
                    if qf_famille >= ligne_calcul.qf_min and qf_famille <= ligne_calcul.qf_max:
                        conditions = True
                    else:
                        conditions = False

                if methode_calcul == "taux_date":
                    if ligne_calcul.date != case_tableau["date"]:
                        conditions = False

                if conditions == True:

                    # Calcul du tarif
                    if qf_famille:
                        montant_tarif = qf_famille * ligne_calcul.taux
                        montant_tarif = float(decimal.Decimal(str(montant_tarif)))
                    else:
                        if ligne_calcul.montant_max:
                            montant_tarif = ligne_calcul.montant_max

                    # Montants seuil et plafond
                    if ligne_calcul.montant_min:
                        if montant_tarif < ligne_calcul.montant_min:
                            montant_tarif = ligne_calcul.montant_min
                    if ligne_calcul.montant_max:
                        if montant_tarif > ligne_calcul.montant_max:
                            montant_tarif = ligne_calcul.montant_max

                    # Application de l'ajustement (majoration ou déduction)
                    if ligne_calcul.ajustement:
                        montant_tarif = montant_tarif + ligne_calcul.ajustement
                        if montant_tarif < 0.0:
                            montant_tarif = 0.0

                    # Création du label personnalisé
                    label = ligne_calcul.label
                    if label:
                        if "{TAUX}" in label: label = label.replace("{TAUX}", str(ligne_calcul.taux))
                        nom_tarif = label
                    break

        # Recherche du montant du tarif : PAR TAUX D'EFFORT ET PAR DUREE (+ QF)
        if methode_calcul in ("duree_taux_montant_unique", "duree_taux_qf"):
            montant_tarif = 0.0
            lignes_calcul = Get_lignes_tarif()

            # Recherche QF de la famille
            qf_famille = self.Recherche_QF(tarif, case_tableau)

            # Recherche de la durée
            duree, heure_debut_delta, heure_fin_delta = self.Calcule_duree(case_tableau, combinaisons_unites)

            for ligne_calcul in lignes_calcul:
                duree_min = utils_dates.TimeEnDelta(ligne_calcul.duree_min)
                duree_max = utils_dates.TimeEnDelta(ligne_calcul.duree_max)

                if not duree_min:
                    duree_min = datetime.timedelta(0)
                if not duree_max or duree_max == datetime.timedelta(0):
                    duree_max = datetime.timedelta(hours=23, minutes=59)

                # Vérifie si QF ok pour le calcul basé également sur paliers de QF
                conditionQF = True
                if "qf" in methode_calcul and qf_famille:
                    if qf_famille >= ligne_calcul.qf_min and qf_famille <= ligne_calcul.qf_max:
                        conditionQF = True
                    else:
                        conditionQF = False

                if duree_min <= duree <= duree_max and conditionQF == True:
                    # Calcul du tarif
                    if qf_famille:
                        montant_tarif = qf_famille * ligne_calcul.taux
                        montant_tarif = float(decimal.Decimal(str(montant_tarif)))
                    else:
                        if ligne_calcul.montant_max:
                            montant_tarif = ligne_calcul.montant_max

                    # Montants seuil et plafond
                    if ligne_calcul.montant_min:
                        if montant_tarif < ligne_calcul.montant_min:
                            montant_tarif = ligne_calcul.montant_min
                    if ligne_calcul.montant_max:
                        if montant_tarif > ligne_calcul.montant_max:
                            montant_tarif = ligne_calcul.montant_max

                    # Application de l'ajustement (majoration ou déduction)
                    if ligne_calcul.ajustement:
                        montant_tarif = montant_tarif + ligne_calcul.ajustement
                        if montant_tarif < 0.0:
                            montant_tarif = 0.0

                    # Calcul du temps facturé
                    if ligne_calcul.temps_facture:
                        temps_facture = datetime.timedelta(hours=ligne_calcul.temps_facture.hour, minutes=ligne_calcul.temps_facture.minute)
                    else:
                        temps_facture = duree_max

                    # Création du label personnalisé
                    label = ligne_calcul.label
                    if label != None and label != "":
                        if "{TAUX}" in label: label = label.replace("{TAUX}", str(ligne_calcul.taux))
                        if "{HEURE_DEBUT}" in label: label = label.replace("{HEURE_DEBUT}", utils_dates.DeltaEnStr(heure_debut_delta))
                        if "{HEURE_FIN}" in label: label = label.replace("{HEURE_FIN}", utils_dates.DeltaEnStr(heure_fin_delta))
                        nom_tarif = label
                    break

        # Si unité de type QUANTITE
        if quantite and quantite > 1:
            montant_tarif = montant_tarif * quantite
            # nom_tarif = "%d %s" % (quantite, nom_tarif)

        # Arrondit le montant à pour enlever les décimales en trop. Ex : 3.05678 -> 3.05
        montant_tarif = utils_decimal.FloatToDecimal(montant_tarif, plusProche=True)

        return montant_tarif, nom_tarif, temps_facture

def Valider_traitement_lot(request):
    # Récupération des données générales
    action = request.POST.get("action_type")
    date_debut = utils_dates.ConvertDateFRtoDate(request.POST.get("date_debut"))
    date_fin = utils_dates.ConvertDateFRtoDate(request.POST.get("date_fin"))
    jours_scolaires = request.POST.getlist("jours_scolaires")
    jours_vacances = request.POST.getlist("jours_vacances")
    semaines = request.POST.get("frequence_type")
    feries = request.POST.get("inclure_feries") == "on"

    # Vérification des données
    erreurs = []
    if not date_debut: erreurs.append("date de début")
    if not date_fin: erreurs.append("date de fin")
    if date_debut and date_fin and date_fin < date_debut: erreurs.append("date de début supérieure à la date de début")
    if not jours_scolaires and not jours_vacances: erreurs.append("jours")

    # Récupération des unités
    dict_unites = {}
    for key, valeur in request.POST.items():
        if key.startswith("unite_"):
            chaine = key.split("_")
            IDunite = int(chaine[1])
            if len(chaine) == 2:
                dict_unites.setdefault(IDunite, {})
            if len(chaine) == 3 and IDunite in dict_unites:
                option = chaine[2]
                if option == "debut":
                    option = "heure_debut"
                    if utils_dates.HeureStrEnTime(valeur) == datetime.time(0, 0):
                        erreurs.append("l'heure de début n'est pas valide")
                if option == "fin":
                    option = "heure_fin"
                    if utils_dates.HeureStrEnTime(valeur) == datetime.time(0, 0):
                        erreurs.append("l'heure de fin n'est pas valide")
                if option == "quantite":
                    try:
                        valeur = int(valeur)
                    except:
                        erreurs.append("La quantité n'est pas valide")
                dict_unites[IDunite][option] = valeur

    if not dict_unites:
        erreurs.append("unités")

    # Affichage des erreurs
    if erreurs:
        return JsonResponse({"erreur": "Les champs suivants ne sont pas valides : %s." % ", ".join(erreurs)}, status=401)

    # Importation de données
    liste_vacances = Vacance.objects.filter(date_fin__gte=date_debut, date_debut__lte=date_fin)
    liste_feries = Ferie.objects.all()

    # Génération des dates
    listeDates = [date_debut,]
    tmp = date_debut
    while tmp < date_fin:
        tmp += datetime.timedelta(days=1)
        listeDates.append(tmp)

    donnees = {}
    liste_dates_valides = []
    date = date_debut
    numSemaine = int(semaines)
    dateTemp = date
    for date in listeDates:

        # Vérifie période et jour
        valide = False
        if utils_dates.EstEnVacances(date, liste_vacances):
            if str(date.weekday()) in jours_vacances:
                valide = True
        else:
            if str(date.weekday()) in jours_scolaires:
                valide = True

        # Calcul le numéro de semaine
        if listeDates:
            if date.weekday() < dateTemp.weekday():
                numSemaine += 1

        # Fréquence semaines
        if semaines in (2, 3, 4):
            if numSemaine % semaines != 0:
                valide = False

        # Semaines paires et impaires
        if valide and semaines in (5, 6):
            numSemaineAnnee = date.isocalendar()[1]
            if numSemaineAnnee % 2 == 0 and semaines == 6:
                valide = False
            if numSemaineAnnee % 2 != 0 and semaines == 5:
                valide = False

        # Vérifie si férié
        if not feries and utils_dates.EstFerie(date, liste_feries):
            valide = False

        if valide:
            liste_dates_valides.append(date)

        dateTemp = date

    # Données renvoyées vers la page
    donnees = {
        "success": True,
        "action": action,
        "dates": liste_dates_valides,
        "unites": dict_unites,
    }
    return JsonResponse(donnees)


def Impression_pdf(request):
    # Récupération des données du formulaire
    liste_conso = json.loads(request.POST.get("consommations"))
    dict_prestations = json.loads(request.POST.get("prestations"))
    idfamille = int(request.POST.get("idfamille"))

    # Importation des données de la DB
    liste_dates = []
    dict_prepa = {"individus": [], "activites": [], "unites": []}
    for conso in liste_conso:
        if conso["individu"] not in dict_prepa["individus"]: dict_prepa["individus"].append(conso["individu"])
        if conso["activite"] not in dict_prepa["activites"]: dict_prepa["activites"].append(conso["activite"])
        if conso["unite"] not in dict_prepa["unites"]: dict_prepa["unites"].append(conso["unite"])
        liste_dates.append(utils_dates.ConvertDateENGtoDate(conso["date"]))
    dict_individus = {individu.pk: individu for individu in Individu.objects.filter(pk__in=dict_prepa["individus"])}
    dict_activites = {activite.pk: activite for activite in Activite.objects.filter(pk__in=dict_prepa["activites"])}
    dict_unites = {unite.pk: unite for unite in Unite.objects.filter(pk__in=dict_prepa["unites"])}
    if liste_dates:
        date_min = min(liste_dates)

    # Préparation des données pour le pdf
    dict_donnees = {"reservations": {}}
    for conso in liste_conso:
        individu = dict_individus[conso["individu"]]
        activite = dict_activites[conso["activite"]]
        unite = dict_unites[conso["unite"]]

        if str(conso["prestation"]) in dict_prestations:
            prestation = dict_prestations[str(conso["prestation"])]
        else:
            prestation = None

        dict_donnees["reservations"].setdefault(conso["individu"], {"nom": individu.nom, "prenom": individu.prenom, "date_naiss": individu.date_naiss, "sexe": individu.Get_sexe(), "activites": {}})
        dict_donnees["reservations"][conso["individu"]]["activites"].setdefault(conso["activite"], {"nom": activite.nom, "agrement": activite.Get_agrement(date=date_min), "dates": {}})
        dict_donnees["reservations"][conso["individu"]]["activites"][conso["activite"]]["dates"].setdefault(conso["date"], {})
        dict_donnees["reservations"][conso["individu"]]["activites"][conso["activite"]]["dates"][conso["date"]].setdefault(conso["unite"],
            {"nomUnite": unite.nom, "etat": conso["etat"], "type": unite.type, "heure_debut": conso["heure_debut"], "heure_fin": conso["heure_fin"], "IDprestation": str(conso["prestation"]), "prestation": prestation}
        )

    # Création du PDF
    from consommations.utils import utils_impression_reservations
    impression = utils_impression_reservations.Impression(titre="Réservations", dict_donnees=dict_donnees)
    nom_fichier = impression.Get_nom_fichier()
    champs = {
        "{SOLDE}": impression.dict_donnees["{SOLDE}"],
    }

    # Récupération des valeurs de fusion
    return JsonResponse({"nom_fichier": nom_fichier, "categorie": "reservations", "label_fichier": "Réservations", "champs": champs, "idfamille": idfamille})


