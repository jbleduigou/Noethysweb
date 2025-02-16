
// Fonction 'icontains' qui rend la fonction contains case-insensitive (sert à la recherche)
$.expr[':'].icontains = $.expr.createPseudo(function(text) {
    text = text.toLowerCase();
    return function (el) {
        return ~$.text(el).toLowerCase().indexOf(text);
    }
});

// CRéaiton d'un UUID
function uuid() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

/*
* jQuery.ajaxQueue - A queue for ajax requests
*
* (c) 2011 Corey Frang
* Dual licensed under the MIT and GPL licenses.
*
* Requires jQuery 1.5+
*/
(function($) {

// jQuery on an empty object, we are going to use this as our Queue
var ajaxQueue = $({});

$.ajaxQueue = function( ajaxOpts ) {
    var jqXHR,
        dfd = $.Deferred(),
        promise = dfd.promise();

    // queue our ajax request
    ajaxQueue.queue( doRequest );

    // add the abort method
    promise.abort = function( statusText ) {

        // proxy abort to the jqXHR if it is active
        if ( jqXHR ) {
            return jqXHR.abort( statusText );
        }

        // if there wasn't already a jqXHR we need to remove from queue
        var queue = ajaxQueue.queue(),
            index = $.inArray( doRequest, queue );

        if ( index > -1 ) {
            queue.splice( index, 1 );
        }

        // and then reject the deferred
        dfd.rejectWith( ajaxOpts.context || ajaxOpts,
            [ promise, statusText, "" ] );

        return promise;
    };

    // run the actual query
    function doRequest( next ) {
        ajaxOpts.data.donnees = JSON.stringify(get_donnees_for_facturation(ajaxOpts.data.keys_cases_touchees));
        jqXHR = $.ajax( ajaxOpts )
            .done( dfd.resolve )
            .fail( dfd.reject )
            .then( next, next );
    }

    return promise;
};

})(jQuery);




// Variables globales
var dict_cases = {};
var dict_cases_memos = {};
var dict_conso = {};
var dict_memos = {};
var pressepapiers_unites = {};
var id_unique_multi = 1;
var dict_places_prises = {};
var cases_touchees = [];
var chrono;


class Case_memo {
    constructor(data) {
        this.key = null;
        this.inscription = null;
        this.date = null;
        this.texte = null;
        this.pk = null;
        this.dirty = false;

        if (data) {
            Object.assign(this, data);
        };
    };

    change() {
        // Envoie les données vers le modal
        if (this.texte) {$('#saisie_memo').val(this.texte)} else {$('#saisie_memo').val("")};
        $('#saisie_memo_key').val(this.key);
        $('#modal_saisir_memo').modal('show');
    }

    importe_memo(texte, pk) {
        this.texte = texte;
        if (pk) {this.pk = pk};
        if (texte === null) {texte = ""};
        $("#" + this.key).text(texte);
    };

    set_memo(texte) {
        if (this.texte !== texte) {this.dirty = true};
        this.texte = texte;
        if ((texte === "") && (this.pk !== null)) {
            dict_suppressions.memos.push(this.pk);
            this.pk = null;
        }
        $("#" + this.key).text(texte);
    };
};


class Case_base {
    constructor(data) {
        this.type_case = null;
        this.key_case_parente = null;
        this.key = null;
        this.individu = null;
        this.groupe = null;
        this.famille = null;
        this.date = null;
        this.unite = null;
        this.activite = null;
        this.inscription = null;
        this.evenement = null;
        this.categorie_tarif = null;
        this.consommations = [];

        // Remplit à partir du dict data fourni
        if (data) {Object.assign(this, data)};
    };

    importe_conso(conso) {
        this.consommations.push(new Conso(conso));
        this.maj_affichage();
    }

    check_compatilites_unites() {
        var self = this, resultat = true;
        var unites_incompatibles = dict_unites[self.unite].incompatibilites;
        $.each(dict_cases, function(key, valeurs) {
            if (valeurs.date === self.date && valeurs.inscription === self.inscription) {
                for (var conso of valeurs.consommations) {
                    if (jQuery.inArray(conso.etat, ["reservation", "present"]) !== -1 && jQuery.inArray(valeurs.unite, unites_incompatibles) !== -1) {
                        toastr.error("L'unité " + dict_unites[self.unite].nom + " est incompatible avec l'unité " + dict_unites[valeurs.unite].nom);
                        resultat = false;
                        return false;
                    };
                };
                if (resultat === false) {return false};
            };
        });
        return resultat;
    };

    creer_conso(data={}, maj_facturation=true) {
        // Message si jour complet
        var is_complet = $("#" + this.key).hasClass("complet");

        // Sélection du mode de saisie
        if (mode === "portail") {
            var mode_saisie = "reservation";
            if (is_complet) {
                toastr.warning("Attention, il n'y a plus de place sur cette date ! Une place a été réservée sur la liste d'attente.");
                var mode_saisie = "attente";
            };
        } else {
            var mode_saisie = $("#mode_saisie").val();
            if (is_complet) {
                toastr.warning("Attention, il n'y a plus de place sur cette date !");
            };
        }

        // Création de la nouvelle conso
        var conso = new Conso({fields:{
            pk: uuid(),
            etat: mode_saisie,
            individu: this.individu,
            groupe : this.groupe,
            inscription: this.inscription,
            date: this.date,
            unite: this.unite,
            activite: this.activite,
            famille: this.famille,
            categorie_tarif: this.categorie_tarif,
        }});
        // Assigne des valeurs si un dict data est donné
        if (data) {
            Object.assign(conso, data);
        };

        // Mémorise dans le pressepapiers
        pressepapiers_unites[this.unite] = {heure_debut: conso.heure_debut, heure_fin: conso.heure_fin, quantite: conso.quantite};

        // Si case parente existe, on lui envoie la conso
        if (this.key_case_parente) {
            if (!(conso in dict_cases[this.key_case_parente].consommations)) {
                dict_cases[this.key_case_parente].consommations.push(conso);
            };
        };

        // Enregistre la conso
        this.consommations.push(conso);
        this.maj_affichage();
        maj_remplissage(this.date);

        // Calcul de la facturation
        if (maj_facturation === true) {
            facturer(this);
        };

    };

    // Modifier une conso existante
    modifier_conso(data={}, maj_facturation=false) {
        var conso = this.consommations[0];
        Object.assign(conso, data);
        conso.dirty = true;
        this.consommations[0] = conso;
        this.maj_affichage();
        maj_remplissage(this.date);
        if (conso.facture) {
            // Par sécurité, pour éviter un recalcul d'une prestation facturée
            toastr.warning("La prestation de la consommation " + dict_unites[this.unite].nom + " ne sera pas recalculée car elle a déjà été facturée.");
            maj_facturation = false;
        };
        if (maj_facturation === true) {
            facturer(this);
        }
        return true;
    };

    detail(action="modifier") {
        // Envoie les infos de la conso vers le modal
        if (this.consommations.length > 0) {
            if (this.consommations[0].heure_debut) {$('#saisie_heure_debut').val(this.consommations[0].heure_debut)};
            if (this.consommations[0].heure_fin) {$('#saisie_heure_fin').val(this.consommations[0].heure_fin)};
            if (this.consommations[0].quantite) {$('#saisie_quantite').val(this.consommations[0].quantite)};
            $('#saisie_groupe').val(this.consommations[0].groupe);
            $("input[name='saisie_etat'][value='" + this.consommations[0].etat + "']").prop("checked",true);
        } else {
            // Envoie les infos par défaut si ajout
            if (dict_unites[this.unite].heure_debut) {$('#saisie_heure_debut').val(dict_unites[this.unite].heure_debut)};
            if (dict_unites[this.unite].heure_fin) {$('#saisie_heure_fin').val(dict_unites[this.unite].heure_fin)};
            $('#saisie_quantite').val(1);
            $('#saisie_groupe').val(this.groupe);
            $("input[name='saisie_etat'][value='" + $("#mode_saisie").val() + "']").prop("checked",true);
        };

        $('#saisie_detail_key').val(this.key);
        $('#saisie_detail_action').val(action);
        $('#modal_saisir_detail').modal('show');
    };

    // Calcule le remplissage
    calc_remplissage() {
        // Annule la maj si il y a déjà une conso affichée dans la case
        if (this.consommations.length > 0) {return false};

        var liste_places_restantes = [];
        var liste_seuils = [];
        var nbre_places_restantes = null;
        var seuil_alerte = null;

        // Recherche pour chaque unité de remplissage les valeurs
        for (var idunite_remplissage of dict_unites[this.unite].unites_remplissage) {

            // Recherche la capacité max sur le groupe
            var key1 = this.date + "_" + idunite_remplissage + "_" + this.groupe;
            if (key1 in dict_capacite) {var capacite_max = dict_capacite[key1]} else {var capacite_max = null};

            if (capacite_max) {
                // Recherche le nbre de places prises
                var nbre_places_prises = 0;
                for (var idunite_conso of dict_unites_remplissage[idunite_remplissage]["unites_conso"]) {
                    var key2 = this.date + "_" + idunite_conso + "_" + this.groupe;
                    if (key2 in dict_places_prises) {
                        nbre_places_prises += dict_places_prises[key2]
                    };
                };

                // Calcule le nombre de places disponibles
                liste_places_restantes.push(capacite_max - nbre_places_prises);
                liste_seuils.push(dict_unites_remplissage[idunite_remplissage]["seuil_alerte"]);
            };
        };

        // Conserve uniquement les valeurs les plus basses
        if (liste_places_restantes.length > 0) {nbre_places_restantes = Math.min.apply(null, liste_places_restantes)};
        if (liste_seuils.length > 0) {seuil_alerte = Math.min.apply(null, liste_seuils)};

        // Envoie les valeurs à l'affichage de la case
        if (nbre_places_restantes !== null && (!$("#" + this.key).hasClass("fermeture"))) {
            var klass = null;
            if (nbre_places_restantes > seuil_alerte) {klass = "disponible"};
            if ((nbre_places_restantes > 0) && (nbre_places_restantes <= seuil_alerte)) {klass = "dernieresplaces"};
            if (nbre_places_restantes <= 0) {klass = "complet"};

            if (!$("#" + this.key).hasClass(klass)) {
                $("#" + this.key).removeClass("disponible dernieresplaces complet");
                $("#" + this.key).addClass(klass);
            }
        };
    };
};

class Case_standard extends Case_base {
    constructor(data) {
        super(data);
        // Dessine la case
        $("#" + this.key).html("<span class='infos'></span><span class='icones'></span><span class='groupe'></span>");
    };

    has_conso() {
        if (this.consommations.length > 0) {return true} else {return false};
    };

    // MAJ de l'affichage du contenu de la case
    maj_affichage() {
        $("#" + this.key).removeClass("reservation attente refus present absentj absenti");
        $("#" + this.key + " .infos").html("");
        $("#" + this.key + " .groupe").html("");
        $("#" + this.key + " .icones").html("");

        // Si c'est une case event
        if (this.type_case === "event") {
            $("#" + this.key + " .infos").html(this.evenement.nom);
        };

        // Si la case est sélectionnée
        if (this.has_conso()) {
            var conso = this.consommations[0];

            // Dessine la couleur de fond
            $("#" + this.key).addClass(conso.etat);

            // Dessine les infos
            var infos = "";
            if ((this.type_case === "horaire" || this.type_case === "multi") && (mode !== "portail")) {
                infos = conso.heure_debut.substring(0,5).replace(":", "h") + "-" + conso.heure_fin.substring(0,5).replace(":", "h");
                $("#" + this.key + " .infos").html(infos);
            };
            if (this.type_case === "quantite") {
                if (conso.quantite) {infos = conso.quantite} else {infos = 1};
                $("#" + this.key + " .infos").html(infos);
            };

            // Dessine le nom du groupe
            if (Object.keys(dict_groupes).length > 1) {
                $("#" + this.key + " .groupe").html(dict_groupes[conso.groupe].nom);
            };
            if (mode === "portail") {
                if (conso.etat === "reservation") {$("#" + this.key + " .groupe").html("Réservé");}
                if (conso.etat === "attente") {$("#" + this.key + " .groupe").html("Attente");}
                if (conso.etat === "present") {$("#" + this.key + " .groupe").html("Présent");}
                if (conso.etat === "refus") {$("#" + this.key + " .groupe").html("Refus");}
                if ((conso.etat === "absenti") || (conso.etat === "absentj")) {$("#" + this.key + " .groupe").html("Absent");}
            }

            // Dessine les icones
            var texte_icones = "";
            if ((conso.prestation === null) && (mode !== "portail")) {texte_icones += " <i class='fa fa-exclamation-triangle text-orange' title='Aucune prestation'></i>"};
            if (conso.etat === "present") {texte_icones += " <i class='fa fa-check-circle-o text-green' title='Présent'></i>"};
            if (conso.etat === "absenti") {texte_icones += " <i class='fa fa-times-circle-o text-red' title='Absence injustifiée'></i>"};
            if (conso.etat === "absentj") {texte_icones += " <i class='fa fa-times-circle-o text-green' title='Absence justifiée'></i>"};
            if (conso.forfait === 2) {texte_icones += " <i class='fa fa-lock text-red' title='Cette consommation est non supprimable car elle est associée à un forfait daté'></i>"};
            if (conso.facture) {texte_icones += " <i class='fa fa-file-text-o text-black-50' title='La prestation associée apparaît sur une facture'></i>"};
            $("#" + this.key + " .icones").html(texte_icones);

            // Pour les tests, affiche l'id de la prestation
            // $("#" + this.key + " .groupe").html(conso.prestation);
        };
    };

    // Supprimer une conso
    supprimer(maj_facturation=true) {
        if (this.is_locked()) {return false}
        // Mémorisation de la suppression
        if ((this.consommations.length > 0) && (!(this.consommations[0].pk.toString().includes("-")))) {
            dict_suppressions.consommations.push(this.consommations[0].pk)
        };
        this.consommations = [];
        this.maj_affichage();
        maj_remplissage(this.date);

        // Calcul de la facturation
        if (maj_facturation === true) {
            facturer(this);
        };

        return true;
    };

    copier() {
        // Vérifie la compatiblité avec les autres unités
        if (this.check_compatilites_unites() === false) {return false};
        // Si une conso existe dans le pressepapiers, on la reproduit
        if (this.unite in pressepapiers_unites) {
            this.creer_conso(pressepapiers_unites[this.unite]);
            return true;
        };
    }

    // Attribue un état à la conso
    set_etat(etat) {
        if (this.has_conso()) {
            if ((jQuery.inArray(etat, ["present", "absenti", "absentj"]) !== -1) && (jQuery.inArray(this.consommations[0].etat, ["attente", "refus"]) !== -1)) {
                toastr.error("Vous ne pouvez pas pointer une réservation en attente ou en refus");
                return false;
            };

            if ((this.consommations[0].facture) && (jQuery.inArray(etat, ["attente", "refus"]) !== -1)) {
                toastr.error("Vous ne pouvez pas sélectionner cet état car la prestation est déjà facturée");
                return false;
            };

            // Vérifie la compatibilité avec les autres unités
            if ((etat === "reservation" || etat === "present") && this.check_compatilites_unites() === false) {return false};

            // Modifie l'état de la conso
            this.modifier_conso({etat: etat}, true);
            return true;
        }
    };

    // Attribue un groupe à la conso
    set_groupe(groupe) {
        if (this.has_conso()) {
            this.modifier_conso({groupe: groupe}, true);
            return true;
        };
    };

    // Attribue un groupe à la conso
    set_prestation(idprestation) {
        if (this.has_conso()) {
            this.modifier_conso({prestation: idprestation});
            return true;
        };
    };

    // Attribue un idconso à la conso
    set_idconso(idconso) {
        if (this.has_conso()) {
            this.modifier_conso({pk: idconso});
            return true;
        };
    };

    // Vérifie si la conso est verrouillée
    is_locked() {
        if ((this.consommations.length > 0) && (jQuery.inArray(this.consommations[0].etat, ["present", "absentj", "absenti"]) !== -1)) {
            toastr.error("Vous ne pouvez pas modifier ou supprimer une consommation déjà pointée");
            return true;
        }
        if ((this.consommations.length > 0) && (this.consommations[0].forfait === 2)) {
            toastr.error("Vous ne pouvez pas supprimer cette consommation car elle est associée à un forfait daté");
            return true;
        }
        if (this.consommations[0].facture) {
            toastr.error("Vous ne pouvez pas modifier ou supprimer une consommation dont la prestation associée apparaît sur une facture");
            return true;
        }
        return false;
    };

};

class Case_unitaire extends Case_standard {
    constructor(data) {
        super(data);
        this.type_case = "unitaire";
    };

    ajouter(data={}, maj_facturation=true) {
        // Vérifie la compatiblité avec les autres unités
        if (this.check_compatilites_unites() === false) {return false};

        // Mode pointeuse
        if (mode === 'pointeuse') {this.detail("ajouter"); return false};

        // Créer conso
        this.creer_conso(data, maj_facturation);
    };

    // Toggle une conso
    toggle() {
        if (this.has_conso()) {
            if (mode === 'pointeuse') {
                this.detail("modifier");
            } else {
                this.supprimer();
            };
        } else {
            this.ajouter();
        };
    };

};

class Case_horaire extends Case_standard {
    constructor(data) {
        super(data);
        this.type_case = "horaire";
    };

    ajouter(data={}, maj_facturation=true) {
        // Vérifie la compatiblité avec les autres unités
        if (this.check_compatilites_unites() === false) {return false};

        // Si saisie en mode portail
        if (mode === "portail") {
            data = {
                heure_debut: dict_unites[this.unite].heure_debut,
                heure_fin: dict_unites[this.unite].heure_fin,
            }
        };

        // Saisie directe si data donnée
        if (Object.keys(data).length > 0) {
            this.creer_conso(data, maj_facturation);
            return true;
        };

        // Mode pointeuse
        if (mode === 'pointeuse') {this.detail("ajouter"); return false};

        // Envoie les heures par défaut de l'unité vers le modal
        if (dict_unites[this.unite].heure_debut) {$('#saisie_heure_debut').val(dict_unites[this.unite].heure_debut)};
        if (dict_unites[this.unite].heure_fin) {$('#saisie_heure_fin').val(dict_unites[this.unite].heure_fin)};

        $('#saisie_heure_key').val(this.key);
        $('#saisie_heure_action').val("ajouter");
        $('#modal_saisir_horaires').modal('show');
    };

    modifier () {
        // Mode pointeuse
        if (mode === 'pointeuse') {this.detail("modifier"); return false};

        // Vérifie si verrouillage
        if (this.is_locked()) {return false};

        // Envoie les heures de la conso vers le modal
        if (this.consommations[0].heure_debut) {$('#saisie_heure_debut').val(this.consommations[0].heure_debut)};
        if (this.consommations[0].heure_fin) {$('#saisie_heure_fin').val(this.consommations[0].heure_fin)};

        $('#saisie_heure_key').val(this.key);
        $('#saisie_heure_action').val("modifier");
        $('#modal_saisir_horaires').modal('show');
    };

    // Toggle une conso
    toggle() {
        if (this.has_conso()) {
            if (mode === "portail") {
                this.supprimer();
            } else {
                this.modifier();
            };
        } else {
            this.ajouter();
        };
    };


};

class Case_quantite extends Case_standard {
    constructor(data) {
        super(data);
        this.type_case = "quantite";
    };

    ajouter(data={}, maj_facturation=true) {
        // Vérifie la compatiblité avec les autres unités
        if (this.check_compatilites_unites() === false) {return false};

        // Saisie directe si data donnée
        if (Object.keys(data).length > 0) {
            this.creer_conso(data, maj_facturation);
            return true;
        };

        // Mode pointeuse
        if (mode === 'pointeuse') {this.detail("ajouter"); return false};

        $('#saisie_quantite_key').val(this.key);
        $('#saisie_quantite_action').val("ajouter");
        $('#modal_saisir_quantite').modal('show');
    };

    modifier () {
        // Mode pointeuse
        if (mode === 'pointeuse') {this.detail("modifier"); return false};

        // Vérifie si verrouillage
        if (this.is_locked()) {return false};

        // Envoie la quantité de la conso vers le modal
        if (this.consommations[0].quantite) {$('#saisie_quantite').val(this.consommations[0].quantite)};

        $('#saisie_quantite_key').val(this.key);
        $('#saisie_quantite_action').val("modifier");
        $('#modal_saisir_quantite').modal('show');
    };

    // Toggle une conso
    toggle() {
        if (this.has_conso()) {
            this.modifier();
        } else {
            this.ajouter();
        };
    };

};


class Case_evenement extends Case_base {
    constructor(data) {
        super(data);
        this.type_case = "evenement";
        var self = this;

        // Dessine la case événement
        var key_evenement = this.date + "_" + this.unite;
        if (key_evenement in dict_evenements) {
            var liste_evenements = dict_evenements[key_evenement];

            // Création des cases html
            var html = "<table class='table table_evenements'><tbody><tr>";
            liste_evenements.forEach(function(evenement) {
                html += "<td class='case ouvert' id='event_" + self.key + "_" + evenement.pk + "'</td>";
            });
            html += "</tr></tbody></table>";
            $("#" + this.key).html(html);

            liste_evenements.forEach(function(evenement) {
                var key_case_event = "event_" + self.key + "_" + evenement.pk;
                data['key'] = key_case_event;
                data['evenement'] = evenement;
                data['key_case_parente'] = self.key;
                var case_event = new Case_event(data);
                dict_cases[key_case_event] = case_event;
            });
        }

    };

};


class Case_event extends Case_standard {
    constructor(data) {
        super(data);
        this.type_case = "event";
        this.key_case_parente = data.key_case_parente;
        this.maj_affichage();
    };

    ajouter() {
        // Vérifie la compatiblité avec les autres unités
        if (this.check_compatilites_unites() === false) {return false};
        // Créer conso
        this.creer_conso({evenement: this.evenement.pk});
    };

    // Toggle une conso
    toggle() {
        if (this.has_conso()) {
            if (mode === 'pointeuse') {
                this.detail("modifier");
            } else {
                this.supprimer();
            };
        } else {
            this.ajouter();
        };
    };

    // Calcule le remplissage
    calc_remplissage() {
        // Annule la maj si il y a déjà une conso affichée dans la case
        if (this.consommations.length > 0) {return false};

        // Récupération de la capacité max
        var capacite_max = this.evenement.capacite_max;

        // Recherche le nbre de places prises
        var nbre_places_prises = 0;
        var key = this.date + "_" + this.unite + "_" + this.groupe + "_" + this.evenement.pk;
        if (key in dict_places_prises) {
            var nbre_places_prises = dict_places_prises[key];
        } else {
            var nbre_places_prises = 0;
        }

        if (capacite_max) {
            // Calcule le nombre de places disponibles
            var nbre_places_restantes = capacite_max - nbre_places_prises;

            // MAJ de l'affichage de la couleur de fond
            if (nbre_places_restantes > 0) {
                var klass = "disponible";
            } else {
                var klass = "complet";
            };

            if (!$("#" + this.key).hasClass(klass)) {
                $("#" + this.key).removeClass("disponible dernieresplaces complet");
                $("#" + this.key).addClass(klass);
            };
        };
    };

};



class Case_multihoraires extends Case_base {
    constructor(data) {
        super(data);
        this.type_case = "multihoraires";
        this.data_case = data;

        // Dessine la case multihoraires
        var html = "<table class='table table_multihoraires'><tbody><tr>";
        html += "<td class='case multi_ajouter' style='border: 0px;'><a data-key='" + this.key + "' class='bouton_ajouter_multi' title='Ajouter une consommation' href='#'><i class='fa fa-plus-circle'></i></a></td>";
        html += "</tr></tbody></table>";
        $("#" + this.key).html(html);

        // Maj de l'affichage
        this.maj_affichage();
    };

    maj_affichage() {
        var key_case = this.key;
        var data_case = this.data_case;

        // Suppression des cases existantes
        $("#" + this.key + " td[class*='ouvert']").remove();
        for (var key of Object.keys(dict_cases)) {
            if (key.startsWith("multi_" + key_case)) {
                delete dict_cases[key];
            };
        }

        // Tri des conso par heure de début
        function compare(a, b) {
            if (a.heure_debut > b.heure_debut) {return -1};
            return 1;
        };
        this.consommations.sort(compare);

        // Prépare une liste de conso provisoire
        var liste_conso_temp = this.consommations.slice();
        if (liste_conso_temp.length === 0) {
            liste_conso_temp.push(null);
        };

        // Création des cases conso
        liste_conso_temp.forEach(function(conso) {
            // Attribue un key à la case multi
            var key_case_multi = "multi_" + key_case + "_" + id_unique_multi;
            id_unique_multi += 1;

            // Dessine la case
            $("#" + key_case + ' tr').prepend("<td class='case ouvert' id='" + key_case_multi + "'</td>");

            // Création de la case virtuelle
            var data_temp = data_case;
            data_temp['key'] = key_case_multi;
            if (conso) {
                data_temp['consommations'] = [conso];
            } else {
                data_temp['consommations'] = [];
            }
            data_temp['key_case_parente'] = key_case;
            var case_multi = new Case_multi(data_temp);
            dict_cases[key_case_multi] = case_multi;
        });
    };

    ajouter() {
        // Vérifie la compatiblité avec les autres unités
        if (this.check_compatilites_unites() === false) {return false};

        // Envoie les heures par défaut de l'unité vers le modal
        if (dict_unites[this.unite].heure_debut) {$('#saisie_heure_debut').attr({'value':dict_unites[this.unite].heure_debut})};
        if (dict_unites[this.unite].heure_fin) {$('#saisie_heure_fin').attr({'value':dict_unites[this.unite].heure_fin})};

        $('#saisie_heure_key').val(this.key);
        $('#saisie_heure_action').val("ajouter");
        $('#modal_saisir_horaires').modal('show');
    };

    supprimer(conso) {
        this.consommations.splice($.inArray(conso, this.consommations), 1);
        this.maj_affichage();
        maj_remplissage(this.date);
    }
};

class Case_multi extends Case_horaire {
    constructor(data) {
        super(data);
        this.type_case = "multi";
        this.key_case_parente = data.key_case_parente;
        this.maj_affichage();
    };

    // Supprimer une conso
    supprimer() {
        if (this.is_locked()) {return false}
        // Mémorisation de la suppression
        if (!(this.consommations[0].pk.toString().includes("-"))) {
            dict_suppressions.consommations.push(this.consommations[0].pk);
        };
        // Supprime également la conso dans la case parente
        dict_cases[this.key_case_parente].supprimer(this.consommations[0]);
        this.consommations = [];
        this.maj_affichage();
        facturer(dict_cases[this.key_case_parente])
        return true;
    };
};











class Conso {
    constructor(conso) {
        this.pk = null;
        this.activite = null;
        this.inscription = null;
        this.groupe = null;
        this.heure_debut = null;
        this.heure_fin = null;
        this.etat = null;
        this.verrouillage = null;
        this.date_saisie = null;
        this.utilisateur = null;
        this.categorie_tarif = null;
        this.famille = null;
        this.prestation = null;
        this.forfait = null;
        this.facture = null;
        this.quantite = 1;
        this.statut = null;
        this.case = null;
        this.etiquettes = [];
        this.evenement = null;
        this.badgeage_debut = null;
        this.badgeage_fin = null;
        this.dirty = false;

        // Importation depuis un array
        if (conso) {
            if ("fields" in conso) {
                Object.assign(this, conso.fields);
                if (conso.fields.pk) {
                    this.pk = conso.fields.pk;
                } else {
                    this.pk = conso.pk;
                }

            } else {
                Object.assign(this, conso);
                this.pk = conso.pk;
            }
        };

        // Importation des données de la prestation associée
        if (this.prestation in dict_prestations) {
            this.facture = dict_prestations[this.prestation].facture
        };

    }
};






$(function () {
    var case_contextmenu = null;

    // Mémorise la touche enfoncée
    var touche_clavier = null;
    $(window).keydown(function(evt) {touche_clavier = evt.which})
    .keyup(function(evt) {touche_clavier = null});

    // Clic sur les cases
    var isMouseDown = false, statut, ancienne_case;
    $(document).on('mousedown', ".table td[class*='ouvert']", function(e) {
        // Si clic gauche de la souris
        if (e.which === 1) {
            isMouseDown = true;
            var case_tableau = dict_cases[$(this).attr('id')];
            statut = case_tableau.has_conso();
            action_sur_clic(case_tableau, statut);
            return false; // prevent text selection
        }
    });
    $(document).on('mouseover', ".table td[class*='ouvert']", function(e) {
        var case_tableau = dict_cases[$(this).attr('id')];
        if (isMouseDown && ancienne_case !== case_tableau) {
            action_sur_clic(case_tableau, statut);
        }
        ancienne_case = case_tableau;
    });
    $(document).mouseup(function () {
        isMouseDown = false;
    });

    function action_sur_clic(case_tableau, statut) {
        if (touche_clavier === 65 && mode !== "portail") {case_tableau.set_etat("reservation")}
        else if (touche_clavier === 80 && mode !== "portail") {case_tableau.set_etat("present")}
        else if (touche_clavier === 74 && mode !== "portail") {case_tableau.set_etat("absentj")}
        else if (touche_clavier === 73 && mode !== "portail") {case_tableau.set_etat("absenti")}
        else if (touche_clavier === 67) {case_tableau.copier()}
        else if (touche_clavier === 83) {case_tableau.supprimer()}
        else {
            // Toggle sur la  case cliquée
            if (case_tableau.has_conso() === statut) {case_tableau.toggle()};

            // Toggle sur case bis sur touche raccourci unité
            if (touche_clavier in dict_touches_raccourcis) {
                var key_case_bis = case_tableau.date + "_" + case_tableau.inscription + "_" + dict_touches_raccourcis[touche_clavier];
                if (key_case_bis in dict_cases && key_case_bis !== case_tableau.key && dict_cases[key_case_bis].has_conso() === statut) {case_supp = dict_cases[key_case_bis].toggle()};
            }
        }
    };

    // Menu contextuel
    $(document).on('contextmenu', ".ouvert", function(e) {
        case_contextmenu = dict_cases[$(this).attr('id')];
        if (!$("#contextMenu").is(':visible') && case_contextmenu.has_conso()) {
            // Rajoute les groupes à la fin du menu
            $("#contextMenu .ctx_groupe").remove();
            liste_groupes.forEach(function(groupe) {
                if (groupe.fields.activite === case_contextmenu.activite) {
                    $("#contextMenu ul").append("<li><a tabindex='-1' href='#' class='dropdown-item ctx_groupe' data-groupe=" + groupe.pk + ">" + groupe.fields.nom + "</a></li>");
                };
            });

            // Met en évidence l'état et le groupe de la conso
            $("#contextMenu a").css('font-weight', 'normal');
            $("#contextMenu a").removeClass("menu-checked");
            $("#contextMenu a[data-etat='" + case_contextmenu.consommations[0].etat + "']").css('font-weight', 'bold').addClass("menu-checked");
            $("#contextMenu a[data-groupe='" + case_contextmenu.consommations[0].groupe + "']").css('font-weight', 'bold').addClass("menu-checked");

            // Affiche le menu
            $("#contextMenu").css({
                display: "block",
                left: e.clientX,
                top: e.clientY
            });
        } else {
            $("#contextMenu").css({display: "none"});
        }
        return false;
    });
    $('html').click(function() {
         $("#contextMenu").hide();
    });
    $(document).on('click', "#contextMenu li a", function(e) {
        var id = $(this).attr('id');
        if (id === "contextmenu_supprimer") {case_contextmenu.supprimer()};
        if (id === "contextmenu_reservation") {case_contextmenu.set_etat("reservation")};
        if (id === "contextmenu_attente") {case_contextmenu.set_etat("attente")};
        if (id === "contextmenu_refus") {case_contextmenu.set_etat("refus")};
        if (id === "contextmenu_present") {case_contextmenu.set_etat("present")};
        if (id === "contextmenu_absentj") {case_contextmenu.set_etat("absentj")};
        if (id === "contextmenu_absenti") {case_contextmenu.set_etat("absenti")};
        if ($(this).hasClass("ctx_groupe")) {case_contextmenu.set_groupe(this.dataset.groupe)};
        $("#contextMenu").hide();
        return false;
    });

    // Clic sur les cases mémo
    $(".table td[class*='memo']").click(function (e) {
        var case_memo = dict_cases_memos[$(this).attr('id')];
        case_memo.change();
        return false; // prevent text selection
    });

    // Clic sur le bouton Ajouter un multi
    $(".bouton_ajouter_multi").click(function(e){
        e.preventDefault();
        var case_multihoraires = dict_cases[this.dataset.key];
        case_multihoraires.ajouter();
        return false;
    });

    // Barre de recherche
    $('#rechercher').on('input',function(e){
        $(".table-grille tr[class*='masquer']").removeClass("masquer");
        $(".table-grille tbody th:not(:icontains('" + $(this).val() + "')):not('.date_regroupement')").closest("tr").addClass("masquer");
    });

});


// Calcul des places prises
function maj_remplissage(date) {
    dict_places_prises = {};
    // Recherche des places prises affichées
    $.each(dict_cases, function (key, case_tableau) {
        if (!(case_tableau.type_case === "evenement") && !(case_tableau.type_case === "multi")) {
            for (var conso of case_tableau.consommations) {

                // Mémorise les places pour chaque conso
                if (conso.etat === "reservation" || conso.etat === "present") {
                    var key = conso.date + "_" + conso.unite + "_" + conso.groupe;
                    if (!(key in dict_places_prises)) {dict_places_prises[key] = 0};
                    if (conso.quantite) {var quantite = conso.quantite} else {quantite = 1};
                    dict_places_prises[key] += quantite;

                    // Mémorise également les événements
                    if (conso.evenement) {
                        key += "_" + conso.evenement;
                        if (!(key in dict_places_prises)) {dict_places_prises[key] = 0};
                        dict_places_prises[key] += 1;
                    };
                };
            };
        };
    });

    // Ajout des places des individus non affichés
    Object.assign(dict_places_prises, dict_places);

    // Maj de la box totaux
    $("#table_totaux td[id^='total_']").each(function() {
        var key = periode_json.selections.jour + "_" + this.id.slice(6);
        if (key in dict_places_prises) {
            $(this).html(dict_places_prises[key]);
        } else {
            $(this).html(0);
        };
    });

    $("#table_totaux td[id^='total_remplissage_']").each(function() {
        idunite_remplissage = $(this).data("idunite");
        idgroupe = $(this).data("idgroupe");
        var nbre_places_prises = 0;
        if (idunite_remplissage in dict_unites_remplissage) {
            for (var idunite_conso of dict_unites_remplissage[idunite_remplissage]["unites_conso"]) {
                var key = periode_json.selections.jour + "_" + idunite_conso + "_" + idgroupe;
                if (key in dict_places_prises) {
                    nbre_places_prises += dict_places_prises[key]
                };
            };
        };
        $(this).html(nbre_places_prises);
    });

    // MAJ du remplissage des cases
    $.each(dict_cases, function (key, case_tableau) {
        if ((date === undefined) || (case_tableau.date === date)) {
            case_tableau.calc_remplissage();
        };
    });



};


// Actions au chargement de la page
$(document).ready(function() {

    // Importe les conso en mémoire
    $.each(dict_conso, function (key, liste_conso) {
        if (key in dict_cases) {
            liste_conso.forEach(function(conso) {
                dict_cases[key].importe_conso(conso);
            });
        };
    });

    // Importe les conso existantes
    for (var conso of liste_conso_existantes) {
        var key = conso.fields.date + "_" + conso.fields.inscription + "_" + conso.fields.unite;
        if (conso.fields.evenement !== null) {key = "event_" + key + "_" + conso.fields.evenement};
        if ((key in dict_cases) && !(key in dict_conso)) {
            dict_cases[key].importe_conso(conso);
        };
    };

    // Importe les mémos en mémoire
    $.each(dict_memos, function (key, valeurs) {
        if (key in dict_cases_memos) {
            dict_cases_memos[key].importe_memo(valeurs.texte, valeurs.pk);
        };
    });

    // Importe les mémos journaliers
    for (var memo of liste_memos_existants) {
        var key = memo.fields.date + "_" + memo.fields.inscription;
        if ((key in dict_cases_memos) && !(key in dict_memos)) {
            dict_cases_memos[key].importe_memo(memo.fields.texte, memo.pk);
        };
    };

    // MAJ du remplissage
    maj_remplissage();

    // MAJ du box facturation
    maj_box_facturation();

    // Affiche la table
    $(".table").removeClass("masquer");
    $("#in_progress").addClass("masquer");
    $("#in_progress").removeClass("overlay");

    // Initialise la librairie FreezeTable
    // $("#table_grille").freezeTable({
    //     'scrollBar': true,
    //     'fixedNavbar': "#panneau_commandes"
    // });

    $('[name=bouton_outils]').on('click', function(event) {
        $('#modal_outils').modal('show');
    });

    $('[name=bouton_enregistrer]').on('click', function(event) {
        // Si mode portail, on générer la facturation avant le submit
        var box = bootbox.dialog({
            message: "<p class='text-center mb-0'><i class='fa fa-spin fa-cog'></i> Enregistrement des données<br>Veuillez patienter...</p>",
            closeButton: false
        });
        tout_recalculer();
    });

    $('[name=bouton_annuler]').on('click', function(event) {
        var box = bootbox.dialog({
            title: "Fermer le planning",
            message: "Souhaitez-vous vraiment fermer le planning ? <br>Les éventuelles modifications effectuées seront perdues...",
            buttons: {
                ok: {
                    label: "<i class='fa fa-check'></i> Oui, je veux fermer",
                    className: 'btn-primary',
                    callback: function(){
                        window.location.href = url_annuler;
                    }
                },
                cancel: {
                    label: "<i class='fa fa-ban'></i> Non, je veux rester",
                    className: 'btn-danger',
                }
            }
        });
    });

    // Envoi des paramètres au format json vers le form de maj
    $("#form-maj").on('submit', function(event) {

        // Vérifie qu'il n'y a pas un calcul de facturation en cours
        if (mode !== "portail") {
            if (!($("#loader_facturation").hasClass("masquer"))) {
                event.preventDefault();
                toastr.error("Vous devez attendre la fin du calcul de la facturation avant de pouvoir quitter");
                return false;
            };
        };

        // Validation du formulaire
        return validation_form(event);
    });

});

function Get_activite() {
    // return selection_activite;
    return $('#selection_activite').val();
};


function validation_form(event) {

    // Mémorise les conso
    $.each(dict_cases, function (key, case_tableau) {
        if (!(case_tableau.type_case === "evenement") && !(case_tableau.type_case === "multi")) {
            dict_conso[key] = case_tableau.consommations;
        }
        ;
    });

    // Mémorise les mémos
    $.each(dict_cases_memos, function (key, case_memo) {
        dict_memos[key] = {
            "pk": case_memo.pk, "texte": case_memo.texte, "inscription": case_memo.inscription,
            "date": case_memo.date, "dirty": case_memo.dirty
        };
    });

    // Validation des données
    if (Get_periode() === false) {
        event.preventDefault();
        return false;
    };

    // Envoi des données à django
    var donnees = JSON.stringify({
        "individus": Get_individus(),
        "periode": Get_periode(),
        "activite": Get_activite(),
        "groupes": Get_groupes(),
        "classes": Get_classes(),
        "consommations": dict_conso,
        "memos": dict_memos,
        "options": dict_options,
        "suppressions": dict_suppressions,
        "prestations": dict_prestations,
    });
    $('#donnees').val(donnees);
    return true;
};


function afficher_loader_facturation(etat) {
    if (etat) {
        $("#loader_facturation").removeClass("masquer");
        $("#loader_facturation").addClass("overlay");
    } else {
        $("#loader_facturation").removeClass("overlay");
        $("#loader_facturation").addClass("masquer");
    }
};

function facturer(case_tableau) {
    // Si mode portail, on évite le calcul de la facturation
    if (mode === "portail") {
        return false;
    }
    afficher_loader_facturation(true);
    cases_touchees.push(case_tableau.key);
    clearTimeout(chrono);
    chrono = setTimeout(function () {
        ajax_facturer(cases_touchees);
        cases_touchees = [];
    }, 1000);
};



function get_donnees_for_facturation(keys_cases_touchees) {
    // Mémorise toutes les conso
    var dict_conso_facturation = {};
    $.each(dict_cases, function (key, case_tableau) {
        if (!(case_tableau.type_case === "evenement") && !(case_tableau.type_case === "multihoraires") && case_tableau.consommations.length > 0) {
            var key = case_tableau.date + "_" + case_tableau.inscription;
            if (!(key in dict_conso_facturation)) {
                dict_conso_facturation[key] = []
            };
            for (var conso of case_tableau.consommations) {
                conso["key_case"] = case_tableau.key;
                dict_conso_facturation[key].push(conso);
            };
        };
    });
    var dict_cases_touchees_temp = {};
    var liste_keys_pour_prestations = [];
    for (var key of keys_cases_touchees) {
        dict_cases_touchees_temp[key] = dict_cases[key];
        liste_keys_pour_prestations.push(dict_cases[key].date + "_" + dict_cases[key].famille + "_" + dict_cases[key].individu+ "_" + dict_cases[key].activite);
    };
    var dict_prestations_temp = {};
    var aides_temp = [];
    $.each(dict_prestations, function (idprestation, dict_prestation) {
        // Mémorisation des prestations de la ligne uniquement
        var key = dict_prestation.date + "_" + dict_prestation.famille + "_" + dict_prestation.individu + "_" + dict_prestation.activite;
        if (liste_keys_pour_prestations.includes(key)) {
            dict_prestations_temp[idprestation] = dict_prestation;
        }
        // Mémorisation de toutes les aides
        for (var dict_aide of dict_prestation.aides) {
            aides_temp.push({"idprestation": parseInt(idprestation), "famille": dict_prestation["famille"], "individu": dict_prestation["individu"],
                            "date": dict_prestation["date"], "montant": dict_aide["montant"], "aide": dict_aide["aide"]});
        };
    });
    return {
        consommations: dict_conso_facturation,
        prestations: dict_prestations_temp,
        dict_aides: aides_temp,
        cases_touchees: dict_cases_touchees_temp,
        liste_vacances: liste_vacances,
        dict_suppressions: dict_suppressions,
        mode: mode,
    };
};

// Facturation
function ajax_facturer(cases_touchees_temp) {
    // Appel ajax
    $.ajaxQueue({
        type: "POST",
        url: url_facturer,
        data: {
            keys_cases_touchees : cases_touchees_temp,
            csrfmiddlewaretoken: csrf_token
            },
        datatype: "json",
        success: function(data){
            // Envoie les nouvelles prestations au dict_prestations
            $.each(data.nouvelles_prestations, function (idprestation, dict_prestation) {
                dict_prestations[idprestation] = dict_prestation;
            });

            for (var idprestation of data.anciennes_prestations) {
                if (!(idprestation.toString().includes("-"))) {
                    dict_suppressions.prestations.push(parseInt(idprestation));
                }
                delete dict_prestations[idprestation];
            }

            // Met à jour les conso
            $.each(data.modifications_idprestation, function (key, idprestation) {
                dict_cases[key].set_prestation(idprestation);
            });

            if (data.modifications_idconso) {
                $.each(data.modifications_idconso, function (ancien_idconso, nouvel_idconso) {
                    $.each(dict_cases, function(key_case, valeurs) {
                        for (var conso of valeurs.consommations) {
                            if (conso.pk === ancien_idconso) {
                                dict_cases[key_case].set_idconso(nouvel_idconso);
                            };
                        };
                    });
                });
            };

            // MAJ du box facturation
            maj_box_facturation();

            // Masque loader du box facturation
            afficher_loader_facturation(false);

            // Si mode portail, on déclenche le submit
            if (mode === "portail") {
                $('#form-maj').submit();
            };

        },
        error: function(data) {
            console.log("Erreur de facturation !");
            if (mode === "portail") {
                box.modal("hide");
            };
        }
    });
};

function maj_box_facturation() {
    // Préparation des données
    var dict_prestations_temp = {};
    $.each(dict_prestations, function (idprestation, prestation) {
        if (prestation.activite === selection_activite) {
            var key = prestation.individu + "_" + prestation.famille;
            if (!(key in dict_prestations_temp)) {dict_prestations_temp[key] = {}};
            if (!(prestation.date in dict_prestations_temp[key])) {dict_prestations_temp[key][prestation.date] = []};
            dict_prestations_temp[key][prestation.date].push(idprestation);
        };
    });

    // Dessine la table facturation
    var montant_total_individus = 0;
    for (var key_individu of liste_key_individus) {
        var total_individu = 0;
        var html = "";
        var key = key_individu[0] + '_' + key_individu[1]
        if (key in dict_prestations_temp) {
            var dict_dates = dict_prestations_temp[key];
            for (var date of Object.keys(dict_dates).sort()) {
                // Vérifie que la date est comprise dans la période affichée
                var valide = false;
                for (var periode of periode_json.periodes) {
                    var date_min = periode.split(";")[0];
                    var date_max = periode.split(";")[1];
                    if ((date >= date_min) && (date <= date_max)) {valide = true};
                }
                // Affiche la date et la prestation
                if (valide === true) {
                    var datefr = new Date(date);
                    datefr = datefr.toLocaleDateString('fr-FR', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    });
                    if (mode == "individu") {
                        html += "<tr><td class='date_prestation'>" + datefr + "</td><td class='montant_prestation'></td></tr>";
                    };
                    for (var idprestation of dict_dates[date].sort()) {
                        var dict_prestation = dict_prestations[idprestation];
                        var label = dict_prestation.label;
                        if (dict_prestation.aides.length > 0) {label += " <span class='exposant'>(Aide)</span>"};
                        html += "<tr class='ligne_prestation'><td class='label_prestation'>" + label + "</td><td class='montant_prestation'>" + dict_prestation.montant.toFixed(2) + " €</td></tr>";
                        total_individu += dict_prestation.montant;
                    };
                };
            };
        };
        $('#detail_facturation_individu_' + key_individu[0] + '_' + key_individu[1]).html(html);
        $('#total_facturation_individu_' + key_individu[0] + '_' + key_individu[1]).html(total_individu.toFixed(2) + " €");
        montant_total_individus += total_individu;
    };
    $('#total_facturation_individus').html(montant_total_individus.toFixed(2) + " €");
};

function tout_recalculer() {
    afficher_loader_facturation(true);
    var liste_temp = [];
    $.each(dict_cases, function (key, case_tableau) {
        var key_temp = case_tableau.date + "_" + case_tableau.inscription;
        if (!(liste_temp.includes(key_temp))) {
            cases_touchees.push(key);
            liste_temp.push(key_temp);
        };
    });
    ajax_facturer(cases_touchees);
};

// Impression du PDF des réservations
function impression_pdf(email=false) {
    var liste_conso_impression = [];
    var dict_prestations_impression = {}
    $("td[class*='ouvert']").each(function() {
        var case_tableau = dict_cases[$(this).attr('id')];
        for (var conso of case_tableau.consommations) {
            liste_conso_impression.push(conso);
            if (conso.prestation in dict_prestations) {
                dict_prestations_impression[conso.prestation] = dict_prestations[conso.prestation]
            };
        };
    });
    $.ajax({
        type: "POST",
        url: url_impression_pdf,
        data: {
            consommations: JSON.stringify(liste_conso_impression),
            prestations: JSON.stringify(dict_prestations_impression),
            idfamille: idfamille,
            csrfmiddlewaretoken: csrf_token,
        },
        datatype: "json",
        success: function(data){
            if (email) {
                envoyer_email(data);
            } else {
                charge_pdf(data);
            }
        },
        error: function(data) {
            toastr.error(data.responseJSON.erreur);
        }
    })
};

