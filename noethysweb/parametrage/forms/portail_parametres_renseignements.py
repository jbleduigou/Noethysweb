# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import copy
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Fieldset
from crispy_forms.bootstrap import Field, InlineCheckboxes
from core.forms.base import FormulaireBase
from core.utils.utils_commandes import Commandes
from core.models import PortailChamp
from portail.utils import utils_onglets, utils_champs


class Formulaire(FormulaireBase, forms.Form):
    def __init__(self, *args, **kwargs):
        super(Formulaire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'portail_parametres_renseignements_form'
        self.helper.form_method = 'post'

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-10'

        # Initialisation du layout
        self.helper.layout = Layout()
        self.helper.layout.append(Commandes(annuler_url="{% url 'parametrage_toc' %}", ajouter=False))

        # Importation des paramètres par défaut
        dict_champs = {(champ.page, champ.code): champ for champ in copy.copy(utils_champs.LISTE_CHAMPS)}
        for champ in PortailChamp.objects.all():
            for public in ("famille", "representant", "enfant", "contact"):
                if getattr(dict_champs[(champ.page, champ.code)], public):
                    setattr(dict_champs[(champ.page, champ.code)], public, getattr(champ, public))

        # Création des fields
        for onglet in utils_onglets.LISTE_ONGLETS:
            liste_fields = []
            for champ in utils_champs.LISTE_CHAMPS:
                if champ.page == onglet.code:
                    liste_checks = []
                    for public_code, public_label in (("famille", "Famille"), ("representant", "Représentant"), ("enfant", "Enfant"), ("contact", "Contact")):
                        if getattr(champ, public_code, None):
                            liste_checks.append((public_code, public_label))
                    code_field = "%s:%s" % (champ.page, champ.code)
                    self.fields[code_field] = forms.MultipleChoiceField(label=champ.label, required=False, widget=forms.CheckboxSelectMultiple, choices=liste_checks)
                    self.fields[code_field].initial = dict_champs[(champ.page, champ.code)].Get_champs_affiches()
                    liste_fields.append(InlineCheckboxes(code_field))
            self.helper.layout.append(Fieldset("<i class='fa %s margin-r-5'></i> %s" % (onglet.icone, onglet.label), *liste_fields))

        self.helper.layout.append(HTML("<br>"))
