# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django import forms
from django.forms import ModelForm
from core.forms.base import FormulaireBase
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Hidden, Submit, HTML, Row, Div, Fieldset, ButtonHolder
from crispy_forms.bootstrap import Field, FormActions, StrictButton
from core.utils.utils_commandes import Commandes
from core.models import Unite, Groupe, Activite
from django.db.models import Max
from core.widgets import DatePickerWidget
import datetime
from django_select2.forms import Select2MultipleWidget


class Formulaire(FormulaireBase, ModelForm):
    heure_debut = forms.TimeField(label="Heure de début", required=False, widget=forms.TimeInput(attrs={'type': 'time'}))
    heure_fin = forms.TimeField(label="Heure de fin", required=False, widget=forms.TimeInput(attrs={'type': 'time'}))

    # Durée de validité
    choix_validite = [("ILLIMITEE", "Durée illimitée"), ("LIMITEE", "Durée limitée")]
    validite_type = forms.TypedChoiceField(label="Type de validité", choices=choix_validite, initial='ILLIMITEE', required=True)
    validite_date_debut = forms.DateField(label="Date de début*", required=False, widget=DatePickerWidget())
    validite_date_fin = forms.DateField(label="Date de fin*", required=False, widget=DatePickerWidget())

    # Groupes
    choix_groupes = [("TOUS", "Tous les groupes"), ("SELECTION", "Uniquement certains groupes")]
    groupes_type = forms.TypedChoiceField(label="Groupes associés", choices=choix_groupes, initial='TOUS', required=True)
    groupes = forms.ModelMultipleChoiceField(label="Sélection des groupes", widget=Select2MultipleWidget({"lang": "fr", "data-width": "100%"}), queryset=Groupe.objects.none(), required=False)

    # Incompatibilités
    incompatibilites = forms.ModelMultipleChoiceField(label="Incompatibilités", widget=Select2MultipleWidget({"lang": "fr", "data-width": "100%"}), queryset=Unite.objects.none(), required=False)

    class Meta:
        model = Unite
        fields = ["ordre", "activite", "nom", "abrege", "type", "heure_debut", "heure_fin", "heure_debut_fixe", "heure_fin_fixe",
                  "repas", "restaurateur", "touche_raccourci", "date_debut", "date_fin", "groupes", "incompatibilites", "visible_portail"]

    def __init__(self, *args, **kwargs):
        idactivite = kwargs.pop("idactivite")
        super(Formulaire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'activites_unites_conso_form'
        self.helper.form_method = 'post'

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-10'

        # Définit l'activité associée
        if hasattr(self.instance, "activite") == False:
            activite = Activite.objects.get(pk=idactivite)
        else:
            activite = self.instance.activite

        # Incompatibilités
        self.fields['incompatibilites'].queryset = Unite.objects.filter(activite=activite).exclude(pk=self.instance.pk)

        # Importe la durée de validité
        if self.instance.date_fin in (None, datetime.date(2999, 1, 1)):
            self.fields['validite_type'].initial = "ILLIMITEE"
        else:
            self.fields['validite_type'].initial = "LIMITEE"
            self.fields['validite_date_debut'].initial = self.instance.date_debut
            self.fields['validite_date_fin'].initial = self.instance.date_fin

        # Ordre
        if self.instance.ordre == None:
            max = Unite.objects.filter(activite=activite).aggregate(Max('ordre'))['ordre__max']
            if max == None:
                max = 0
            self.fields['ordre'].initial = max + 1
        else:
            self.fields['ordre'].initial = self.instance.ordre

        # Importe les groupes
        self.fields['groupes'].queryset = Groupe.objects.filter(activite=activite)
        if self.instance.ordre != None:
            if len(self.instance.groupes.all()) > 0:
                self.fields['groupes_type'].initial = "SELECTION"

        # Affichage
        self.helper.layout = Layout(
            Commandes(annuler_url="{{ view.get_success_url }}"),
            Hidden('activite', value=activite.idactivite),
            Hidden('ordre', value=self.fields['ordre'].initial),
            Fieldset("Nom de l'unité",
                Field("nom"),
                Field("abrege"),
            ),
            Fieldset("Caractéristiques",
                Field("type"),
                Field("heure_debut"),
                Field("heure_fin"),
                Field("incompatibilites"),
                Field("heure_debut_fixe"),
                Field("heure_fin_fixe"),
                Field("repas"),
                Field("restaurateur"),
                Field("touche_raccourci"),
                Field("visible_portail"),
            ),
            Fieldset("Durée de validité",
                Field("validite_type"),
                Div(
                    Field("validite_date_debut"),
                    Field("validite_date_fin"),
                    id="bloc_periode",
                ),
            ),
            Fieldset("Groupes associés",
                Field("groupes_type"),
                Field("groupes"),
            ),
            HTML(EXTRA_SCRIPT),
        )

    def clean(self):
        # Durée de validité
        if self.cleaned_data["validite_type"] == "LIMITEE":
            if self.cleaned_data["validite_date_debut"] == None:
                self.add_error('validite_date_debut', "Vous devez sélectionner une date de début")
                return
            if self.cleaned_data["validite_date_fin"] == None:
                self.add_error('validite_date_fin', "Vous devez sélectionner une date de fin")
                return
            if self.cleaned_data["validite_date_debut"] > self.cleaned_data["validite_date_fin"] :
                self.add_error('validite_date_fin', "La date de fin doit être supérieure à la date de début")
                return
            self.cleaned_data["date_debut"] = self.cleaned_data["validite_date_debut"]
            self.cleaned_data["date_fin"] = self.cleaned_data["validite_date_fin"]
        else:
            self.cleaned_data["date_debut"] = datetime.date(1977, 1, 1)
            self.cleaned_data["date_fin"] = datetime.date(2999, 1, 1)

        # Groupes associés
        if self.cleaned_data["groupes_type"] == "SELECTION":
            if len(self.cleaned_data["groupes"]) == 0:
                self.add_error('groupes', "Vous devez cocher au moins un groupe")
                return
        else:
            self.cleaned_data["groupes"] = []

        return self.cleaned_data



EXTRA_SCRIPT = """
<script>

// groupes_type
function On_change_groupes_type() {
    $('#div_id_groupes').hide();
    if($(this).val() == 'SELECTION') {
        $('#div_id_groupes').show();
    }
}
$(document).ready(function() {
    $('#id_groupes_type').change(On_change_groupes_type);
    On_change_groupes_type.call($('#id_groupes_type').get(0));
});


// validite_type
function On_change_validite_type() {
    $('#bloc_periode').hide();
    if($(this).val() == 'LIMITEE') {
        $('#bloc_periode').show();
    }
}
$(document).ready(function() {
    $('#id_validite_type').change(On_change_validite_type);
    On_change_validite_type.call($('#id_validite_type').get(0));
});

// repas
function On_change_repas() {
    $('#div_id_restaurateur').hide();
    if(this.checked) {
        $('#div_id_restaurateur').show();
    }
}
$(document).ready(function() {
    $('#id_repas').change(On_change_repas);
    On_change_repas.call($('#id_repas'));
});


</script>
"""