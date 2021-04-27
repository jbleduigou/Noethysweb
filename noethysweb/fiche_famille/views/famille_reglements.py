# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy, reverse
from core.views.mydatatableview import MyDatatable, columns, helpers
from core.views import crud
from core.models import Famille, Reglement, Payeur, Emetteur, ModeReglement, Prestation, Ventilation
from fiche_famille.forms.famille_reglements import Formulaire
from fiche_famille.views.famille import Onglet
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Sum, Q
from decimal import Decimal
import json
from core.utils import utils_dates, utils_texte



def Get_ventilation(request):
    """ Renvoie une liste d'activités """
    mode_regroupement = request.POST.get("regroupement", "mois")
    idfamille = request.POST.get("idfamille", 0)
    idreglement = request.POST.get("idreglement", 0)

    # Importation de la ventilation antérieure
    ventilations_anterieures = Ventilation.objects.values('prestation').filter(famille_id=idfamille).exclude(reglement_id=idreglement).annotate(total=Sum("montant"))
    dict_ventilations_anterieures = {x["prestation"]: x["total"] for x in ventilations_anterieures}

    # Importation de la ventilation du règlement
    ventilations_reglement = Ventilation.objects.values('prestation').filter(reglement_id=idreglement).annotate(total=Sum("montant"))
    dict_ventilations_reglement = {x["prestation"]: x["total"] for x in ventilations_reglement}

    # Importation des prestations de la famille
    prestations = Prestation.objects.select_related('individu', 'facture').filter(famille_id=idfamille).order_by("date")
    liste_prestations = []
    for prestation in prestations:
        ventilation_anterieure = dict_ventilations_anterieures.get(prestation.pk, Decimal(0))
        ventilation_reglement = dict_ventilations_reglement.get(prestation.pk, Decimal(0))
        montant_ventile = ventilation_anterieure + ventilation_reglement

        if (prestation.montant >= Decimal(0) and montant_ventile < prestation.montant) or (prestation.montant < Decimal(0) and montant_ventile > prestation.montant) or ventilation_reglement > Decimal(0):
            prestation.ventilation_anterieure = ventilation_anterieure
            prestation.ventilation_reglement = ventilation_reglement
            prestation.reste_ventilation = prestation.montant - ventilation_reglement - ventilation_anterieure
            liste_prestations.append(prestation)

    context = {"prestations": liste_prestations, "mode_regroupement": mode_regroupement}
    return render(request, "fiche_famille/widgets/ventilation_ajax.html", context)


def On_selection_mode_reglement(request):
    idmode = request.POST.get("idmode")
    if not idmode or idmode == "None":
        return JsonResponse({"numero_piece": None, "emetteurs": []})
    mode = ModeReglement.objects.get(pk=int(idmode))
    emetteurs = Emetteur.objects.filter(mode_id=int(idmode)).order_by("nom")
    return JsonResponse({"numero_piece": mode.numero_piece, "emetteurs": [{"id": emetteur.pk, "text": emetteur.nom, "image": emetteur.image.name} for emetteur in emetteurs]})


def Modifier_payeur(request):
    action = request.POST.get("action")
    idpayeur = request.POST.get("id")
    nom = request.POST.get("valeur")
    donnees_extra = json.loads(request.POST.get("donnees_extra"))

    # Ajouter un payeur
    if action == "ajouter":
        payeur = Payeur.objects.create(famille_id=int(donnees_extra["idfamille"]), nom=nom)
        return JsonResponse({"action": action, "id": payeur.pk, "valeur": payeur.nom})

    # Modifier un payeur
    if action == "modifier":
        payeur = Payeur.objects.get(idpayeur=int(idpayeur))
        payeur.nom = nom
        payeur.save()
        return JsonResponse({"action": action, "id": payeur.pk, "valeur": payeur.nom})

    # Supprimer un payeur
    if action == "supprimer":
        try:
            payeur = Payeur.objects.get(idpayeur=int(idpayeur))
            payeur.delete()
            return JsonResponse({"action": action, "id": int(idpayeur)})
        except:
            return JsonResponse({"erreur": "Vous ne pouvez pas supprimer cette donnée"}, status=401)

    return JsonResponse({"erreur": "Erreur !"}, status=401)


class Page(Onglet):
    model = Reglement
    url_liste = "famille_reglements_liste"
    url_ajouter = "famille_reglements_ajouter"
    url_modifier = "famille_reglements_modifier"
    url_supprimer = "famille_reglements_supprimer"
    url_supprimer_plusieurs = "famille_reglements_supprimer_plusieurs"
    description_liste = "Saisissez ici les règlements de la famille."
    description_saisie = "Saisissez toutes les informations concernant le règlement et cliquez sur le bouton Enregistrer."
    objet_singulier = "un règlement"
    objet_pluriel = "des règlements"
    format_historique = "Règlement ID{0.pk} Date={0.date} Mode={0.mode} Numéro={0.numero_piece} Montant={0.montant}"

    def get_context_data(self, **kwargs):
        """ Context data spécial pour onglet """
        context = super(Page, self).get_context_data(**kwargs)
        context['box_titre'] = "Règlements"
        context['onglet_actif'] = "reglements"
        context['boutons_liste'] = [
            {"label": "Ajouter", "classe": "btn btn-success", "href": reverse_lazy(self.url_ajouter, kwargs={'idfamille': self.kwargs.get('idfamille', None)}), "icone": "fa fa-plus"},
        ]
        # Ajout l'idfamille à l'URL de suppression groupée
        context['url_supprimer_plusieurs'] = reverse_lazy(self.url_supprimer_plusieurs, kwargs={'idfamille': self.kwargs.get('idfamille', None), "listepk": "xxx"})
        return context

    def get_form_kwargs(self, **kwargs):
        """ Envoie l'idindividu au formulaire """
        form_kwargs = super(Page, self).get_form_kwargs(**kwargs)
        form_kwargs["idfamille"] = self.Get_idfamille()
        return form_kwargs

    def get_success_url(self):
        """ Renvoie vers la liste après le formulaire """
        url = self.url_liste
        if "SaveAndNew" in self.request.POST:
            url = self.url_ajouter
        return reverse_lazy(url, kwargs={'idfamille': self.kwargs.get('idfamille', None)})



class Liste(Page, crud.Liste):
    model = Reglement
    template_name = "fiche_famille/famille_reglements.html"

    def get_queryset(self):
        return Reglement.objects.select_related('mode', 'emetteur', 'payeur', 'depot').annotate(ventile=Sum("ventilation__montant")).filter(Q(famille__pk=self.Get_idfamille()) & self.Get_filtres("Q"))

    def get_context_data(self, **kwargs):
        context = super(Liste, self).get_context_data(**kwargs)
        context['impression_introduction'] = ""
        context['impression_conclusion'] = ""
        context['active_checkbox'] = True
        return context

    class datatable_class(MyDatatable):
        filtres = ['idreglement', 'date', 'mode__label', 'emetteur__nom', 'numero_piece', 'payeur__nom', 'montant', 'depot__date']

        check = columns.CheckBoxSelectColumn(label="")
        actions = columns.TextColumn("Actions", sources=None, processor='Get_actions_speciales')
        mode = columns.TextColumn("Mode", sources=['mode__label'])
        emetteur = columns.TextColumn("Emetteur", sources=['emetteur__nom'])
        payeur = columns.TextColumn("Payeur", sources=['payeur__nom'])
        depot = columns.TextColumn("Dépôt", sources=['depot__date'], processor='Get_date_depot')
        montant = columns.TextColumn("Montant", sources=['montant'], processor='Formate_montant')
        ventile = columns.TextColumn("Ventilé", sources=['ventile'], processor='Formate_ventile')

        class Meta:
            structure_template = MyDatatable.structure_template
            columns = ['check', 'idreglement', 'date', 'mode', 'emetteur', 'numero_piece', 'payeur', 'montant', 'ventile', 'depot']
            #hidden_columns = = ["idreglement"]
            processors = {
                'date': helpers.format_date('%d/%m/%Y'),
                'depot': helpers.format_date('%d/%m/%Y'),
            }
            ordering = ['date']

        def Formate_montant(self, instance, **kwargs):
            return utils_texte.Formate_montant(instance.montant)

        def Formate_ventile(self, instance, **kwargs):
            if instance.ventile == Decimal(0):
                classe = "text-red"
            elif instance.ventile == instance.montant:
                classe = "text-green"
            else:
                classe = "text-orange"
            return "<span class='%s'>%s</span>" % (classe, utils_texte.Formate_montant(instance.ventile))

        def Get_date_depot(self, instance, *args, **kwargs):
            if instance.depot:
                return utils_dates.ConvertDateToFR(instance.depot.date)
            return ""

        def Get_actions_speciales(self, instance, *args, **kwargs):
            """ Inclut l'idindividu dans les boutons d'actions """
            view = kwargs["view"]
            # Récupération idfamille
            kwargs = view.kwargs

            # Ajoute l'id de la ligne
            kwargs["pk"] = instance.pk
            html = [
                self.Create_bouton_modifier(url=reverse(view.url_modifier, kwargs=kwargs)),
                self.Create_bouton_supprimer(url=reverse(view.url_supprimer, kwargs=kwargs)),
                self.Create_bouton_imprimer(url=reverse("famille_recus_ajouter", kwargs={"idfamille": kwargs["idfamille"], "idreglement": instance.pk}), title="Editer un reçu"),
            ]
            return self.Create_boutons_actions(html)


class ClasseCommune(Page):
    form_class = Formulaire
    template_name = "fiche_famille/famille_reglements.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super(ClasseCommune, self).get_context_data(**kwargs)
        return context_data

    def form_valid(self, form):
        # Enregistrement du règlement
        reglement = form.save(commit=True)

        # Enregistrement de la ventilation
        liste_ventilations = json.loads(self.request.POST.get("ventilation"))

        # Importe les ventilations existantes
        ventilations_reglement = Ventilation.objects.filter(reglement_id=reglement.pk)

        # Enregistre les ventilations
        liste_IDtraitees = []
        for dict_temp in liste_ventilations:
            Ventilation.objects.update_or_create(famille=reglement.famille, prestation_id=dict_temp["idprestation"],
                                                 reglement=reglement, defaults={"montant": Decimal(dict_temp["montant"])})
            liste_IDtraitees.append(dict_temp["idprestation"])

        # Supprime les ventilations obsolètes
        for ventilation in ventilations_reglement:
            if ventilation.prestation_id not in liste_IDtraitees:
                ventilation.delete()

        return super().form_valid(form) # return HttpResponseRedirect(self.get_success_url())



class Ajouter(ClasseCommune, crud.Ajouter):
    form_class = Formulaire
    template_name = "fiche_famille/famille_edit.html"


class Modifier(ClasseCommune, crud.Modifier):
    form_class = Formulaire
    template_name = "fiche_famille/famille_edit.html"


class Supprimer(Page, crud.Supprimer):
    template_name = "fiche_famille/famille_delete.html"

    # def delete(self, request, *args, **kwargs):
    #     """ Empêche la suppression de règlement déjà inclus dans dépôt """
    #     if self.get_object().depot:
    #         messages.add_message(request, messages.ERROR, "La suppression est impossible car ce règlement est déjà inclus dans un dépôt")
    #         return HttpResponseRedirect(self.get_success_url(), status=303)
    #     reponse = super(Supprimer, self).delete(request, *args, **kwargs)
    #     return reponse

class Supprimer_plusieurs(Page, crud.Supprimer_plusieurs):
    template_name = "fiche_famille/famille_delete.html"

