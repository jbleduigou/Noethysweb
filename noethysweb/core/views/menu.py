# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import copy
from django.urls import reverse_lazy


def GetMenuPrincipal(organisateur=None, user=None):
    menu = Menu(titre="Menu principal", user=user)

    # ------------------------------------ Accueil ------------------------------------
    menu.Add(code="accueil", titre="Accueil", icone="home", toujours_afficher=True)

    # ------------------------------------ Paramétrage ------------------------------------
    menu_parametrage = menu.Add(code="parametrage_toc", titre="Paramétrage", icone="gear")

    menu_structure = menu_parametrage.Add(titre="Généralités")
    if organisateur:
        menu_structure.Add(code="organisateur_modifier", titre="Organisateur", icone="file-text-o", compatible_demo=False, args="1")
    else:
        menu_structure.Add(code="organisateur_ajouter", titre="Organisateur", icone="file-text-o", compatible_demo=False)
    menu_structure.Add(code="structures_liste", titre="Structures", icone="file-text-o", compatible_demo=False)

    # Activités
    menu_activites = menu_parametrage.Add(titre="Activités")
    menu_activites.Add(code="types_groupes_activites_liste", titre="Groupes d'activités", icone="file-text-o")
    menu_activites.Add(code="activites_liste", titre="Activités", icone="file-text-o")

    # Cotisations
    menu_cotisations = menu_parametrage.Add(titre="Adhésions")
    menu_cotisations.Add(code="types_cotisations_liste", titre="Types d'adhésions", icone="file-text-o")
    menu_cotisations.Add(code="unites_cotisations_liste", titre="Unités d'adhésions", icone="file-text-o")

    # Questionnaires
    menu_questionnaires = menu_parametrage.Add(titre="Questionnaires")
    menu_questionnaires.Add(code="questions_liste", titre="Questionnaires", icone="file-text-o")

    # Modèles
    menu_modeles = menu_parametrage.Add(titre="Modèles")
    menu_modeles.Add(code="modeles_documents_liste", titre="Modèles de documents", icone="file-text-o")
    menu_modeles.Add(code="modeles_emails_liste", titre="Modèles d'emails", icone="file-text-o")
    menu_modeles.Add(code="modeles_rappels_liste", titre="Modèles de lettres de rappel", icone="file-text-o")
    menu_modeles.Add(code="modeles_pes_liste", titre="Modèles d'exports vers le Trésor Public", icone="file-text-o")

    # Comptabilité
    menu_comptabilite = menu_parametrage.Add(titre="Comptabilité")
    menu_comptabilite.Add(code="comptes_bancaires_liste", titre="Comptes bancaires", icone="file-text-o")
    menu_comptabilite.Add(code="modes_reglements_liste", titre="Modes de règlements", icone="file-text-o")
    menu_comptabilite.Add(code="emetteurs_liste", titre="Emetteurs de règlements", icone="file-text-o")

    # Renseignements
    menu_renseignements = menu_parametrage.Add(titre="Renseignements")
    menu_renseignements.Add(code="types_pieces_liste", titre="Types de pièces", icone="file-text-o")
    menu_renseignements.Add(code="regimes_liste", titre="Régimes sociaux", icone="file-text-o")
    menu_renseignements.Add(code="caisses_liste", titre="Caisses", icone="file-text-o")
    menu_renseignements.Add(code="types_quotients_liste", titre="Types de quotients", icone="file-text-o")
    menu_renseignements.Add(code="categories_travail_liste", titre="Catégories socio-professionnelles", icone="file-text-o")
    menu_renseignements.Add(code="secteurs_liste", titre="Secteurs géographiques", icone="file-text-o")
    menu_renseignements.Add(code="types_sieste_liste", titre="Types de sieste", icone="file-text-o")
    menu_renseignements.Add(code="types_regimes_alimentaires_liste", titre="Types de régimes alimentaires", icone="file-text-o")
    menu_renseignements.Add(code="categories_medicales_liste", titre="Catégories médicales", icone="file-text-o")
    menu_renseignements.Add(code="types_maladies_liste", titre="Types de maladies", icone="file-text-o")
    menu_renseignements.Add(code="types_vaccins_liste", titre="Types de vaccins", icone="file-text-o")
    menu_renseignements.Add(code="medecins_liste", titre="Médecins", icone="file-text-o")
    menu_renseignements.Add(code="assureurs_liste", titre="Assureurs", icone="file-text-o")

    # Facturation
    menu_facturation = menu_parametrage.Add(titre="Facturation")
    menu_facturation.Add(code="lots_factures_liste", titre="Lots de factures", icone="file-text-o")
    menu_facturation.Add(code="prefixes_factures_liste", titre="Préfixes de factures", icone="file-text-o")
    menu_facturation.Add(code="messages_factures_liste", titre="Messages de factures", icone="file-text-o")
    menu_facturation.Add(code="regies_liste", titre="Régies", icone="file-text-o")

    # Scolarité
    menu_scolarite = menu_parametrage.Add(titre="Scolarité")
    menu_scolarite.Add(code="niveaux_scolaires_liste", titre="Niveaux scolaires", icone="file-text-o")
    menu_scolarite.Add(code="ecoles_liste", titre="Ecoles", icone="file-text-o")
    menu_scolarite.Add(code="classes_liste", titre="Classes", icone="file-text-o")

    # Restauration
    menu_restauration = menu_parametrage.Add(titre="Restauration")
    menu_restauration.Add(code="restaurateurs_liste", titre="Restaurateurs", icone="file-text-o")
    menu_restauration.Add(code="menus_categories_liste", titre="Catégories de menus", icone="file-text-o")
    menu_restauration.Add(code="menus_legendes_liste", titre="Légendes de menus", icone="file-text-o")

    # Notes
    menu_notes = menu_parametrage.Add(titre="Notes")
    menu_notes.Add(code="notes_categories_liste", titre="Catégories de notes", icone="file-text-o")

    # Emails
    menu_emails = menu_parametrage.Add(titre="Emails")
    menu_emails.Add(code="adresses_mail_liste", titre="Adresses d'expédition d'emails", icone="file-text-o", compatible_demo=False)
    menu_emails.Add(code="listes_diffusion_liste", titre="Listes de diffusion", icone="file-text-o")

    # Calendrier
    menu_calendrier = menu_parametrage.Add(titre="Calendrier")
    menu_calendrier.Add(code="vacances_liste", titre="Périodes de vacances", icone="file-text-o")
    menu_calendrier.Add(code="feries_fixes_liste", titre="Jours fériés fixes", icone="file-text-o")
    menu_calendrier.Add(code="feries_variables_liste", titre="Jours fériés variables", icone="file-text-o")

    # Portail
    menu_portail = menu_parametrage.Add(titre="Portail")
    menu_portail.Add(code="portail_parametres_modifier", titre="Paramètres généraux", icone="file-text-o", compatible_demo=False)
    menu_portail.Add(code="portail_parametres_renseignements_modifier", titre="Paramètres des renseignements", icone="file-text-o", compatible_demo=False)
    menu_portail.Add(code="categories_compte_internet_liste", titre="Catégories de compte internet", icone="file-text-o")
    menu_portail.Add(code="types_consentements_liste", titre="Types de consentements", icone="file-text-o")
    menu_portail.Add(code="unites_consentements_liste", titre="Unités de consentements", icone="file-text-o")
    menu_portail.Add(code="albums_liste", titre="Albums photos", icone="file-text-o")
    menu_portail.Add(code="images_articles_liste", titre="Banque d'images des articles", icone="file-text-o")
    menu_portail.Add(code="articles_liste", titre="Articles", icone="file-text-o")
    menu_portail.Add(code="images_fond_liste", titre="Banque d'images de fond", icone="file-text-o")
    menu_portail.Add(code="portail_documents_liste", titre="Documents à télécharger", icone="file-text-o")


    # ------------------------------------ Outils ------------------------------------
    menu_outils = menu.Add(code="outils_toc", titre="Outils", icone="wrench")

    # Statistiques
    menu_stats = menu_outils.Add(titre="Statistiques")
    menu_stats.Add(code="statistiques", titre="Statistiques", icone="file-text-o")

    # Communication
    menu_emails = menu_outils.Add(titre="Emails")
    menu_emails.Add(code="contacts_liste", titre="Carnets d'adresses", icone="file-text-o")
    menu_emails.Add(code="editeur_emails", titre="Editeur d'Emails", icone="file-text-o")
    menu_emails.Add(code="emails_liste", titre="Listes des Emails", icone="file-text-o")

    # Outils
    menu_historique = menu_outils.Add(titre="Historique")
    menu_historique.Add(code="historique", titre="Historique", icone="file-text-o")
    menu_historique.Add(code="notes_liste", titre="Notes", icone="file-text-o")

    # Maintenance
    menu_maintenance = menu_outils.Add(titre="Maintenance")
    menu_maintenance.Add(code="update", titre="Mise à jour de l'application", icone="file-text-o")
    menu_maintenance.Add(code="notes_versions", titre="Notes de versions", icone="file-text-o")

    # Calendrier
    menu_calendrier = menu_outils.Add(titre="Calendrier")
    menu_calendrier.Add(code="calendrier_annuel", titre="Calendrier annuel", icone="file-text-o")

    # Sauvegarde
    menu_sauvegarde = menu_outils.Add(titre="Sauvegarde")
    menu_sauvegarde.Add(code="sauvegarde_creer", titre="Créer une sauvegarde", icone="file-text-o", compatible_demo=False)
    menu_sauvegarde.Add(code="sauvegarde_restaurer", titre="Restaurer une sauvegarde", icone="file-text-o", compatible_demo=False)

    # Portail
    menu_portail = menu_outils.Add(titre="Portail")
    menu_portail.Add(code="messagerie_portail", titre="Messages non lus à traiter", icone="file-text-o")
    menu_portail.Add(code="messages_portail_liste", titre="Messages du portail", icone="file-text-o")
    menu_portail.Add(code="demandes_portail_liste", titre="Renseignements à valider", icone="file-text-o")

    # ------------------------------------ Individus ------------------------------------
    menu_individus = menu.Add(code="individus_toc", titre="Individus", icone="user")

    # Liste des individus
    menu_gestion_individus = menu_individus.Add(titre="Gestion des individus")
    menu_gestion_individus.Add(code="famille_liste", titre="Liste des familles", icone="file-text-o")
    menu_gestion_individus.Add(code="individu_liste", titre="Liste des individus rattachés", icone="file-text-o")
    menu_gestion_individus.Add(code="individus_detaches_liste", titre="Liste des individus détachés", icone="file-text-o")

    # Inscriptions
    menu_inscriptions = menu_individus.Add(titre="Inscriptions")
    menu_inscriptions.Add(code="inscriptions_liste", titre="Liste des inscriptions", icone="file-text-o")
    menu_inscriptions.Add(code="liste_inscriptions_attente", titre="Liste des inscriptions en attente", icone="file-text-o")
    menu_inscriptions.Add(code="liste_inscriptions_refus", titre="Liste des inscriptions refusées", icone="file-text-o")
    menu_inscriptions.Add(code="suivi_inscriptions", titre="Suivi des inscriptions", icone="file-text-o")
    menu_inscriptions.Add(code="inscriptions_impression", titre="Imprimer des inscriptions", icone="file-text-o")
    menu_inscriptions.Add(code="inscriptions_email", titre="Envoyer des inscriptions par Email", icone="file-text-o")

    # Inscriptions scolaires
    menu_scolarite = menu_individus.Add(titre="Scolarité")
    menu_scolarite.Add(code="inscriptions_scolaires_liste", titre="Inscriptions scolaires", icone="file-text-o")
    menu_scolarite.Add(code="scolarites_liste", titre="Etapes de scolarité", icone="file-text-o")

    # Pièces
    menu_pieces_individus = menu_individus.Add(titre="Pièces")
    menu_pieces_individus.Add(code="liste_pieces_manquantes", titre="Liste des pièces manquantes", icone="file-text-o")
    menu_pieces_individus.Add(code="liste_pieces_fournies", titre="Liste des pièces fournies", icone="file-text-o")

    # Photos
    menu_photos_individus = menu_individus.Add(titre="Photos")
    menu_photos_individus.Add(code="importation_photos", titre="Importer des photos individuelles", icone="file-text-o")

    # Informations
    menu_infos_individus = menu_individus.Add(titre="Informations")
    menu_infos_individus.Add(code="liste_anniversaires", titre="Liste des anniversaires", icone="file-text-o")
    menu_infos_individus.Add(code="liste_regimes_caisses", titre="Liste des régimes et des caisses", icone="file-text-o")
    menu_infos_individus.Add(code="liste_quotients", titre="Liste des quotients familiaux/revenus", icone="file-text-o")
    menu_infos_individus.Add(code="liste_codes_comptables", titre="Liste des codes comptables", icone="file-text-o")
    menu_infos_individus.Add(code="mandats_liste", titre="Liste des mandats SEPA", icone="file-text-o")
    menu_infos_individus.Add(code="contacts_urgence_liste", titre="Liste des contacts d'urgence et de sortie", icone="file-text-o")
    menu_infos_individus.Add(code="regimes_alimentaires_liste", titre="Liste des régimes alimentaires", icone="file-text-o")
    menu_infos_individus.Add(code="maladies_liste", titre="Liste des maladies", icone="file-text-o")
    menu_infos_individus.Add(code="liste_comptes_internet", titre="Liste des comptes internet", icone="file-text-o")

    # Questionnaires
    menu_infos_questionnaires = menu_individus.Add(titre="Questionnaires")
    menu_infos_questionnaires.Add(code="questionnaires_familles_liste", titre="Liste des questionnaires familiaux", icone="file-text-o")
    menu_infos_questionnaires.Add(code="questionnaires_individus_liste", titre="Liste des questionnaires individuels", icone="file-text-o")

    # Impression
    menu_impression_individus = menu_individus.Add(titre="Impression")
    menu_impression_individus.Add(code="etiquettes_individus", titre="Edition d'étiquettes et de badges", icone="file-text-o")


    # ------------------------------------ Cotisations ------------------------------------
    menu_cotisations = menu.Add(code="cotisations_toc", titre="Adhésions", icone="folder-o")

    # Etat
    menu_etat_cotisations = menu_cotisations.Add(titre="Etat des adhésions")
    menu_etat_cotisations.Add(code="cotisations_liste", titre="Liste des adhésions", icone="file-text-o")
    menu_etat_cotisations.Add(code="cotisations_impression", titre="Imprimer des adhésions", icone="file-text-o")
    menu_etat_cotisations.Add(code="cotisations_email", titre="Envoyer des adhésions par Email", icone="file-text-o")

    menu_etat_cotisations.Add(code="liste_cotisations_manquantes", titre="Liste des adhésions manquantes", icone="file-text-o")

    # Gestion
    menu_gestion_cotisations = menu_cotisations.Add(titre="Gestion des adhésions")
    menu_gestion_cotisations.Add(code="saisie_lot_cotisations", titre="Saisir un lot d'adhésions", icone="file-text-o")

    # Dépôts
    menu_depots_cotisations = menu_cotisations.Add(titre="Dépôts d'adhésions")
    menu_depots_cotisations.Add(code="liste_cotisations_disponibles", titre="Liste des adhésions non déposées", icone="file-text-o")
    menu_depots_cotisations.Add(code="depots_cotisations_liste", titre="Dépôts d'adhésions", icone="file-text-o")


    # ------------------------------------ Consommations ------------------------------------
    menu_consommations = menu.Add(code="consommations_toc", titre="Consommations", icone="calendar")

    # Gestion des consommations
    menu_gestion_conso = menu_consommations.Add(titre="Gestion des consommations")
    menu_gestion_conso.Add(code="edition_liste_conso", titre="Edition de la liste des consommations", icone="file-text-o")
    menu_gestion_conso.Add(code="gestionnaire_conso", titre="Gestionnaire des consommations", icone="file-text-o")
    menu_gestion_conso.Add(code="pointeuse_conso", titre="Pointeuse en temps réel", icone="file-text-o")
    menu_gestion_conso.Add(code="suivi_consommations", titre="Suivi des consommations", icone="file-text-o")

    # Liste par état
    menu_listes_etat = menu_consommations.Add(titre="Listes par état")
    menu_listes_etat.Add(code="liste_attente", titre="Liste d'attente", icone="file-text-o")
    menu_listes_etat.Add(code="liste_refus", titre="Liste des places refusées", icone="file-text-o")
    menu_listes_etat.Add(code="liste_absences", titre="Liste des absences", icone="file-text-o")

    # Analyse
    menu_analyse = menu_consommations.Add(titre="Analyse")
    menu_analyse.Add(code="etat_global", titre="Etat global", icone="file-text-o")
    menu_analyse.Add(code="synthese_consommations", titre="Synthèse des consommations", icone="file-text-o")



    # ------------------------------------ Facturation ------------------------------------
    menu_facturation = menu.Add(code="facturation_toc", titre="Facturation", icone="euro")

    # Factures
    menu_factures = menu_facturation.Add(titre="Factures")
    menu_factures.Add(code="factures_generation", titre="Génération des factures", icone="file-text-o")
    menu_factures.Add(code="lots_pes_liste", titre="Exports vers le Trésor Public", icone="file-text-o")
    menu_factures.Add(code="factures_impression", titre="Imprimer des factures", icone="file-text-o")
    menu_factures.Add(code="factures_email", titre="Envoyer des factures par Email", icone="file-text-o")
    menu_factures.Add(code="liste_factures", titre="Liste des factures", icone="file-text-o")

    # Rappels
    menu_rappels = menu_facturation.Add(titre="Rappels")
    menu_rappels.Add(code="rappels_generation", titre="Génération des lettres de rappel", icone="file-text-o")
    menu_rappels.Add(code="liste_rappels", titre="Liste des lettres de rappel", icone="file-text-o")
    menu_rappels.Add(code="rappels_impression", titre="Imprimer des lettres de rappel", icone="file-text-o")
    menu_rappels.Add(code="rappels_email", titre="Envoyer des lettres de rappel par Email", icone="file-text-o")

    # Tarifs
    menu_tarifs = menu_facturation.Add(titre="Tarifs")
    menu_tarifs.Add(code="liste_tarifs", titre="Liste des tarifs", icone="file-text-o")

    # Prestations
    menu_prestations = menu_facturation.Add(titre="Prestations")
    menu_prestations.Add(code="liste_prestations", titre="Liste des prestations", icone="file-text-o")
    menu_prestations.Add(code="liste_deductions", titre="Liste des déductions", icone="file-text-o")
    menu_prestations.Add(code="liste_soldes", titre="Liste des soldes", icone="file-text-o")
    menu_prestations.Add(code="synthese_prestations", titre="Synthèse des prestations", icone="file-text-o")
    menu_prestations.Add(code="recalculer_prestations", titre="Recalculer des prestations", icone="file-text-o")

    # Impayés
    menu_impayes = menu_facturation.Add(titre="Impayés")
    menu_impayes.Add(code="synthese_impayes", titre="Synthèse des impayés", icone="file-text-o")




    # ------------------------------------ Règlements ------------------------------------
    menu_reglements = menu.Add(code="reglements_toc", titre="Règlements", icone="money")

    # Listes
    menu_listes = menu_reglements.Add(titre="Listes")
    menu_listes.Add(code="liste_recus", titre="Liste des reçus de règlements", icone="file-text-o")
    menu_listes.Add(code="liste_reglements", titre="Liste des règlements", icone="file-text-o")
    menu_listes.Add(code="liste_detaillee_reglements", titre="Liste détaillée des règlements", icone="file-text-o")

    # Analyse
    menu_analyse_reglements = menu_reglements.Add(titre="Analyse")
    menu_analyse_reglements.Add(code="detail_prestations_depot", titre="Détail des prestations d'un dépôt", icone="file-text-o")
    menu_analyse_reglements.Add(code="synthese_modes_reglements", titre="Synthèse des modes de règlements", icone="file-text-o")

    # Dépôts
    menu_depots_reglements = menu_reglements.Add(titre="Dépôts de règlements")
    menu_depots_reglements.Add(code="liste_reglements_disponibles", titre="Liste des règlements non déposés", icone="file-text-o")
    menu_depots_reglements.Add(code="depots_reglements_liste", titre="Dépôts de règlements", icone="file-text-o")

    # Ventilation
    menu_ventilation = menu_reglements.Add(titre="Ventilation")
    menu_ventilation.Add(code="corriger_ventilation", titre="Corriger la ventilation", icone="file-text-o")


    # ------------------------------------ Aide ------------------------------------
    menu_aide = menu.Add(code="aide_toc", titre="Aide", icone="support", toujours_afficher=True)




    if user:
        # Suppression des menus vides
        suppressions_rubriques = []
        for rubrique in menu.children:

            # Suppression des sous-rubriques vides
            suppressions_sousrubriques = []
            for sous_rubrique in rubrique.children:
                if not sous_rubrique.children and not sous_rubrique.toujours_afficher:
                    suppressions_sousrubriques.append(sous_rubrique)
            [rubrique.children.remove(item) for item in suppressions_sousrubriques]

            # Suppression des rubriques vides
            if not rubrique.children and not rubrique.toujours_afficher:
                suppressions_rubriques.append(rubrique)
        [menu.children.remove(item) for item in suppressions_rubriques]

    return menu




class Menu():
    def __init__(self, parent=None, code="", titre="", icone=None, url=None, user=None, toujours_afficher=False, compatible_demo=True, args=None):
        self.parent = parent
        self.code = code
        self.titre = titre
        self.icone = icone
        self.url = url
        self.args = args
        self.children = []
        self.user = user
        self.toujours_afficher = toujours_afficher
        self.compatible_demo = compatible_demo

    def __repr__(self):
        return "<Menu '%s'>" % self.titre

    def GetParent(self):
        return self.parent

    def Add(self, code="", titre="", icone="", url=None, toujours_afficher=False, compatible_demo=True, args=None):
        menu = Menu(self, code=code, titre=titre, icone=icone, url=url, args=args, user=self.user, compatible_demo=compatible_demo, toujours_afficher=toujours_afficher)
        if not code or not self.user or toujours_afficher or code.endswith("_toc") or self.user.has_perm("core.%s" % code):
            self.children.append(menu)
        return menu

    def GetUrl(self):
        if self.args:
            return reverse_lazy(self.code, args=self.args)
        return reverse_lazy(self.code)

    def GetChildren(self):
        return self.children

    def GetChildrenParts(self):
        """ Divise la liste des items en 2 colonnes """
        liste = copy.copy(self.GetChildren())
        nbre_parts = 2
        for i in range(0, nbre_parts):
            yield liste[i::nbre_parts]
        return liste

    def GetBrothers(self):
        brothers = copy.copy(self.parent.children)
        brothers.remove(self)
        return brothers

    def HasChildren(self):
        return len(self.children) > 0

    def Find(self, code=""):
        def boucle(children):
            for child in children:
                if child.code == code:
                    return child
                resultat = boucle(child.GetChildren())
                if resultat != None :
                    return resultat
        return boucle(self.GetChildren())

    def GetBreadcrumb(self):
        breadcrumb = [self,]

        def boucle(menu):
            parent = menu.GetParent()
            breadcrumb.append(parent)
            if parent.GetParent() != None:
                boucle(menu=parent)

        boucle(menu=self)
        breadcrumb.reverse()

        return breadcrumb[1:]
